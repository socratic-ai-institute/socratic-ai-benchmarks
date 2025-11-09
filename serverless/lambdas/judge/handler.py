"""
Judge Lambda - Scores dialogue turns using LLM-as-judge.

Triggered by: SQS judge-jobs queue
Output: Judge scores to S3/DynamoDB, run.judged events to EventBridge

Flow:
1. Receive job from SQS (run_id, turn_index)
2. Load turn bundle from S3
3. Run heuristics (cheap pre-scoring)
4. Call judge model for full scoring
5. Write JUDGE item to DynamoDB + full rationale JSON to S3
6. Check if all turns judged → emit run.judged event
"""
import json
import os
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import boto3

# Import from layer
from socratic_bench import judge_turn, compute_heuristic_scores, compute_vector_scores, BedrockClient

# AWS clients
s3 = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")
events = boto3.client("events")

TABLE_NAME = os.environ["TABLE_NAME"]
BUCKET_NAME = os.environ["BUCKET_NAME"]
EVENT_BUS_NAME = os.environ["EVENT_BUS_NAME"]

table = dynamodb.Table(TABLE_NAME)


def lambda_handler(event, context):
    """
    Main handler for Judge Lambda.

    Processes SQS messages (batch of 1).
    """
    print(f"Judge started: processing {len(event['Records'])} messages")

    for record in event["Records"]:
        try:
            job = json.loads(record["body"])
            print(f"Judging turn: {job['run_id']} / {job['turn_index']}")

            result = judge_turn_job(job)

            print(f"Judge complete: {job['run_id']} / {job['turn_index']}, "
                  f"score={result.get('overall_score', 0)}")

        except Exception as e:
            print(f"Error judging turn: {e}")
            raise  # Let SQS retry or send to DLQ

    return {"statusCode": 200, "message": "Turns judged"}


def judge_turn_job(job: Dict[str, Any]) -> Dict[str, Any]:
    """
    Judge a single turn.

    Args:
        job: {"run_id": str, "turn_index": int}

    Returns:
        Summary of judge result
    """
    run_id = job["run_id"]
    turn_index = job["turn_index"]

    # 1. Load turn bundle from S3
    turn_bundle = load_turn_bundle(run_id, turn_index)

    # 2. Run heuristics (fast, cheap, backward compatibility)
    heuristics = compute_heuristic_scores(turn_bundle["ai"])

    # 3. Compute vector scores (new system - replaces LLM judge)
    bedrock_client = BedrockClient()

    # Use token count from turn bundle if available
    token_count = turn_bundle.get("output_tokens")

    judge_result = compute_vector_scores(
        ai_response=turn_bundle["ai"],
        token_count=token_count,
        use_llm_exploratory=False,  # Use heuristic for speed
        bedrock_client=bedrock_client,
    )

    # Set turn index on result
    judge_result.turn_index = turn_index

    # 4. Save judge result
    save_judge_result(run_id, turn_index, turn_bundle, heuristics, judge_result)

    # 5. Check if all turns are judged
    if check_all_turns_judged(run_id):
        emit_run_judged_event(run_id)

    return {
        "run_id": run_id,
        "turn_index": turn_index,
        "overall_score": judge_result.overall_score,
        "heuristics": heuristics,
    }


def load_turn_bundle(run_id: str, turn_index: int) -> Dict[str, Any]:
    """Load turn bundle from S3."""
    s3_key = f"raw/runs/{run_id}/turn_{turn_index:03d}.json"

    response = s3.get_object(Bucket=BUCKET_NAME, Key=s3_key)
    turn_bundle = json.loads(response["Body"].read())

    return turn_bundle


def save_judge_result(
    run_id: str,
    turn_index: int,
    turn_bundle: Dict[str, Any],
    heuristics: Dict[str, Any],
    judge_result: Any,
) -> None:
    """
    Save judge result to S3 and DynamoDB.

    S3: Full judge JSON with rationale and evidence
    DynamoDB: Compact summary fields
    """
    # Full judge JSON for S3
    judge_json = {
        "run_id": run_id,
        "turn_index": turn_index,
        "scores": judge_result.scores,
        "heuristics": heuristics,
        "judge_model": judge_result.judge_model_id,
        "latency_ms": judge_result.latency_ms,
        "error": judge_result.error,
        "judged_at": datetime.now(timezone.utc).isoformat(),
    }

    # Save to S3
    s3_key = f"raw/runs/{run_id}/judge_{turn_index:03d}.json"
    s3.put_object(
        Bucket=BUCKET_NAME,
        Key=s3_key,
        Body=json.dumps(judge_json, indent=2),
        ContentType="application/json",
    )

    # Extract key scores for DynamoDB
    scores = judge_result.scores or {}
    # New format: vector scores are on 0-1 scale
    # Handle both old format (0-100 dict) and new format (0-1 flat values)
    overall = scores.get("overall", 0.0)
    if isinstance(overall, dict):
        # Old LLM judge format: {"score": X, "evidence": "..."}
        overall_score = float(overall.get("score", 0.0)) / 100.0  # Convert 0-100 to 0-1
    else:
        # New vector format: already 0-1 scale
        overall_score = float(overall)

    # Save to DynamoDB
    table.put_item(
        Item={
            "PK": f"RUN#{run_id}",
            "SK": f"JUDGE#{turn_index:03d}",
            "run_id": run_id,
            "turn_index": turn_index,
            "s3_key": s3_key,
            "overall_score": str(overall_score),  # DynamoDB doesn't support float natively
            "has_question": heuristics["has_question"],
            "is_open_ended": heuristics["is_open_ended"],
            "judge_model": judge_result.judge_model_id,
            "error": judge_result.error,
            "judged_at": judge_json["judged_at"],
        }
    )

    print(f"Saved judge result for turn {turn_index}")


def check_all_turns_judged(run_id: str) -> bool:
    """
    Check if all turns for this run have been judged.

    Compare TURN count vs JUDGE count.
    """
    # Query all items for this run
    response = table.query(
        KeyConditionExpression="PK = :pk",
        ExpressionAttributeValues={":pk": f"RUN#{run_id}"},
    )

    items = response.get("Items", [])

    # Count TURNs and JUDGEs
    turn_count = sum(1 for item in items if item["SK"].startswith("TURN#"))
    judge_count = sum(1 for item in items if item["SK"].startswith("JUDGE#"))

    print(f"Run {run_id}: {judge_count}/{turn_count} turns judged")

    return turn_count > 0 and turn_count == judge_count


def emit_run_judged_event(run_id: str) -> None:
    """
    Emit EventBridge run.judged event.

    This triggers the Curator Lambda.
    """
    event_detail = {
        "run_id": run_id,
        "judged_at": datetime.now(timezone.utc).isoformat(),
    }

    events.put_events(
        Entries=[
            {
                "Source": "socratic.judge",
                "DetailType": "run.judged",
                "Detail": json.dumps(event_detail),
                "EventBusName": EVENT_BUS_NAME,
            }
        ]
    )

    print(f"Emitted run.judged event for {run_id}")
