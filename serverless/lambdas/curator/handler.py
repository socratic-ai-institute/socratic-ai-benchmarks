"""
Curator Lambda - Aggregates and materializes run results.

Triggered by: EventBridge run.judged event
Output: Curated JSON to S3, SUMMARY items to DynamoDB

Flow:
1. Load all TURN + JUDGE items for run_id
2. Compute aggregate metrics:
   - Overall score (mean)
   - Compliance rate (% with score >= 3)
   - Half-life (first turn where score drops below threshold)
   - Violation rates (heuristic failures)
3. Write RUN#SUMMARY to DynamoDB
4. Materialize curated/runs/<run_id>.json to S3
5. Update weekly aggregate (WEEK#YYYY-WW#MODEL)
"""

import json
import os
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List

import boto3


class DecimalEncoder(json.JSONEncoder):
    """JSON encoder that handles DynamoDB Decimal types."""

    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


# AWS clients
s3 = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")

TABLE_NAME = os.environ["TABLE_NAME"]
BUCKET_NAME = os.environ["BUCKET_NAME"]

table = dynamodb.Table(TABLE_NAME)


def lambda_handler(event, context):
    """
    Main handler for Curator Lambda.

    Triggered by EventBridge run.judged event.
    """
    print(f"Curator started: {json.dumps(event)}")

    # Extract run_id from event detail
    run_id = event["detail"]["run_id"]

    result = curate_run(run_id)

    print(f"Curator complete: {run_id}, overall={result.get('overall_score', 0)}")

    return result


def curate_run(run_id: str) -> Dict[str, Any]:
    """
    Curate a completed run.

    Args:
        run_id: Run identifier

    Returns:
        Summary of curated run
    """
    # 1. Load run metadata
    run_meta = load_run_meta(run_id)

    # 2. Load all turns and judges
    turns, judges = load_turn_data(run_id)

    if not turns or not judges:
        raise ValueError(f"No turn/judge data found for {run_id}")

    # 3. Compute aggregate metrics
    metrics = compute_metrics(turns, judges)

    # 4. Build curated summary
    # Support both old "vector" and new "dimension" terminology
    dimension_or_vector = run_meta.get("dimension") or run_meta.get("vector", "unknown")

    summary = {
        "run_id": run_id,
        "manifest_id": run_meta["manifest_id"],
        "model_id": run_meta["model_id"],
        "scenario_id": run_meta["scenario_id"],
        "dimension": dimension_or_vector,  # New field name
        "vector": dimension_or_vector,  # Deprecated, for backward compat
        "created_at": run_meta["created_at"],
        "curated_at": datetime.now(timezone.utc).isoformat(),
        **metrics,
    }

    # 5. Save to DynamoDB
    save_summary(run_id, summary)

    # 6. Materialize to S3
    materialize_run_json(run_id, summary, turns, judges)

    # 7. Update weekly aggregate
    update_weekly_aggregate(run_meta, summary)

    return summary


def load_run_meta(run_id: str) -> Dict[str, Any]:
    """Load RUN#META item."""
    response = table.get_item(Key={"PK": f"RUN#{run_id}", "SK": "META"})

    if "Item" not in response:
        raise ValueError(f"Run not found: {run_id}")

    return response["Item"]


def load_turn_data(run_id: str) -> tuple[List[Dict], List[Dict]]:
    """
    Load all TURN and JUDGE items for a run.

    Returns:
        (turns, judges) sorted by turn_index
    """
    response = table.query(
        KeyConditionExpression="PK = :pk AND begins_with(SK, :sk_prefix)",
        ExpressionAttributeValues={
            ":pk": f"RUN#{run_id}",
            ":sk_prefix": "TURN#",
        },
    )

    turns = sorted(
        [item for item in response["Items"] if item["SK"].startswith("TURN#")],
        key=lambda x: x["turn_index"],
    )

    response = table.query(
        KeyConditionExpression="PK = :pk AND begins_with(SK, :sk_prefix)",
        ExpressionAttributeValues={
            ":pk": f"RUN#{run_id}",
            ":sk_prefix": "JUDGE#",
        },
    )

    judges = sorted(
        [item for item in response["Items"] if item["SK"].startswith("JUDGE#")],
        key=lambda x: x["turn_index"],
    )

    return turns, judges


def compute_metrics(turns: List[Dict], judges: List[Dict]) -> Dict[str, Any]:
    """
    Compute aggregate metrics from turns and judges.

    Updated for new 0-1 score scale (vector-based scoring):
    - overall_score: Mean of all judge scores (0-1 scale)
    - compliance_rate: % turns with score >= 0.5 (50% threshold)
    - half_life: First turn where score drops below 0.5
    - violation_rate: % turns without questions
    - open_ended_rate: % turns with open-ended questions
    """
    scores = []
    compliant_count = 0
    half_life = None

    # Updated threshold for 0-1 scale (was 3.0 for 0-10 scale)
    COMPLIANCE_THRESHOLD = 0.5

    for judge in judges:
        score = float(judge.get("overall_score", 0))
        scores.append(score)

        if score >= COMPLIANCE_THRESHOLD:
            compliant_count += 1
        elif half_life is None:
            half_life = judge["turn_index"]

    overall_score = sum(scores) / len(scores) if scores else 0.0
    compliance_rate = compliant_count / len(scores) if scores else 0.0

    # Heuristic metrics
    has_question_count = sum(1 for j in judges if j.get("has_question", False))
    open_ended_count = sum(1 for j in judges if j.get("is_open_ended", False))

    violation_rate = 1.0 - (has_question_count / len(judges)) if judges else 0.0
    open_ended_rate = open_ended_count / len(judges) if judges else 0.0

    # Token stats
    total_input_tokens = sum(t.get("input_tokens", 0) for t in turns)
    total_output_tokens = sum(t.get("output_tokens", 0) for t in turns)

    return {
        "turn_count": len(turns),
        "overall_score": round(overall_score, 2),
        "compliance_rate": round(compliance_rate, 2),
        "half_life": half_life if half_life is not None else len(turns),
        "violation_rate": round(violation_rate, 2),
        "open_ended_rate": round(open_ended_rate, 2),
        "total_input_tokens": total_input_tokens,
        "total_output_tokens": total_output_tokens,
    }


def save_summary(run_id: str, summary: Dict[str, Any]) -> None:
    """Save RUN#SUMMARY to DynamoDB."""
    # Convert floats to Decimal for DynamoDB
    item = {
        k: (Decimal(str(v)) if isinstance(v, float) else v) for k, v in summary.items()
    }

    item["PK"] = f"RUN#{run_id}"
    item["SK"] = "SUMMARY"

    table.put_item(Item=item)
    print(f"Saved summary for {run_id}")


def materialize_run_json(
    run_id: str,
    summary: Dict[str, Any],
    turns: List[Dict],
    judges: List[Dict],
) -> None:
    """
    Materialize curated run JSON to S3.

    This is the stable, queryable format for the UI.
    """
    curated = {
        "run_id": run_id,
        "summary": summary,
        "turns": [
            {
                "turn_index": t["turn_index"],
                "latency_ms": t.get("latency_ms", 0),
                "input_tokens": t.get("input_tokens", 0),
                "output_tokens": t.get("output_tokens", 0),
                "s3_key": t.get("s3_key"),
            }
            for t in turns
        ],
        "judges": [
            {
                "turn_index": j["turn_index"],
                "overall_score": float(j.get("overall_score", 0)),
                "has_question": j.get("has_question", False),
                "is_open_ended": j.get("is_open_ended", False),
                "s3_key": j.get("s3_key"),
            }
            for j in judges
        ],
    }

    s3_key = f"curated/runs/{run_id}.json"
    s3.put_object(
        Bucket=BUCKET_NAME,
        Key=s3_key,
        Body=json.dumps(curated, indent=2, cls=DecimalEncoder),
        ContentType="application/json",
    )

    print(f"Materialized curated JSON: {s3_key}")


def update_weekly_aggregate(run_meta: Dict[str, Any], summary: Dict[str, Any]) -> None:
    """
    Update weekly aggregate for this model.

    PK=WEEK#YYYY-WW#MODEL#<model_id>
    SK=SUMMARY

    Tracks: run count, mean overall score, compliance rate, etc.
    """
    # Get ISO week
    created_dt = datetime.fromisoformat(run_meta["created_at"].replace("Z", "+00:00"))
    iso_week = created_dt.strftime("%Y-W%V")

    model_id = run_meta["model_id"]
    pk = f"WEEK#{iso_week}#MODEL#{model_id}"

    # Try to load existing aggregate
    try:
        response = table.get_item(Key={"PK": pk, "SK": "SUMMARY"})
        existing = response.get("Item", {})
    except Exception:
        existing = {}

    # Compute updated aggregate
    run_count = int(existing.get("run_count", 0)) + 1
    prev_total_score = float(existing.get("total_score", 0))
    new_total_score = prev_total_score + summary["overall_score"]
    mean_score = new_total_score / run_count

    prev_total_compliance = float(existing.get("total_compliance", 0))
    new_total_compliance = prev_total_compliance + summary["compliance_rate"]
    mean_compliance = new_total_compliance / run_count

    # Update item
    table.put_item(
        Item={
            "PK": pk,
            "SK": "SUMMARY",
            "week": iso_week,
            "model_id": model_id,
            "run_count": run_count,
            "total_score": Decimal(str(new_total_score)),
            "mean_score": Decimal(str(round(mean_score, 2))),
            "total_compliance": Decimal(str(new_total_compliance)),
            "mean_compliance": Decimal(str(round(mean_compliance, 2))),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            # GSI key for querying by model
            "GSI1PK": f"MODEL#{model_id}",
            "GSI1SK": f"WEEK#{iso_week}",
        }
    )

    # Also materialize weekly JSON
    materialize_weekly_json(iso_week, model_id, run_count, mean_score, mean_compliance)

    print(f"Updated weekly aggregate: {pk}")


def materialize_weekly_json(
    iso_week: str,
    model_id: str,
    run_count: int,
    mean_score: float,
    mean_compliance: float,
) -> None:
    """Materialize weekly aggregate to S3."""
    curated = {
        "week": iso_week,
        "model_id": model_id,
        "run_count": run_count,
        "mean_score": round(mean_score, 2),
        "mean_compliance": round(mean_compliance, 2),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    s3_key = f"curated/weekly/{iso_week}/{model_id}.json"
    s3.put_object(
        Bucket=BUCKET_NAME,
        Key=s3_key,
        Body=json.dumps(curated, indent=2),
        ContentType="application/json",
    )

    print(f"Materialized weekly JSON: {s3_key}")
