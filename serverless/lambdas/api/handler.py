"""
Read API Lambda - Serves benchmark data to the UI.

Routes:
- GET /weekly?week=YYYY-WW → Weekly aggregate data
- GET /runs/{run_id}/summary → Run summary
- GET /runs/{run_id}/turns?offset=0&limit=10 → Turn headers with pagination

Auth: API key (simple MVP)
"""

import json
import os
from typing import Any, Dict, Optional

import boto3

# AWS clients
s3 = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")

TABLE_NAME = os.environ["TABLE_NAME"]
BUCKET_NAME = os.environ["BUCKET_NAME"]

table = dynamodb.Table(TABLE_NAME)


# Scenario ID to friendly name mapping
SCENARIO_NAMES = {
    "EL-ETH": "Ethical Dilemma",
    "MAI-BIO": "Vague Concept",
    "APO-PHY": "Educational Challenge",
}


def get_scenario_name(scenario_id: str) -> str:
    """Map scenario ID to friendly name. If unknown, return formatted version."""
    if scenario_id in SCENARIO_NAMES:
        return SCENARIO_NAMES[scenario_id]
    # Fallback: try to extract base scenario ID (e.g., "APO-PHY" from "APO-PHY-HEAT-TEMP-01")
    base_id = "-".join(scenario_id.split("-")[:2]) if scenario_id else ""
    return SCENARIO_NAMES.get(base_id, scenario_id)


def lambda_handler(event, context):
    """
    Main handler for Read API Lambda.

    Routes requests based on path and method.
    """
    print(f"API request: {event['httpMethod']} {event['path']}")

    path = event.get("path", "")
    method = event.get("httpMethod", "GET")
    query_params = event.get("queryStringParameters") or {}
    path_params = event.get("pathParameters") or {}

    try:
        if method != "GET":
            return error_response(405, "Method not allowed")

        # Route handling
        if path == "/weekly":
            return get_weekly(query_params)

        elif path.startswith("/runs/") and path.endswith("/summary"):
            run_id = path_params.get("run_id")
            return get_run_summary(run_id)

        elif path.startswith("/runs/") and path.endswith("/turns"):
            run_id = path_params.get("run_id")
            offset = int(query_params.get("offset", 0))
            limit = int(query_params.get("limit", 10))
            return get_run_turns(run_id, offset, limit)

        elif path == "/api/timeseries":
            return get_timeseries(query_params)

        elif path == "/api/latest-rankings":
            return get_latest_rankings(query_params)

        elif path == "/api/cost-analysis":
            return get_cost_analysis(query_params)

        elif path == "/api/model-comparison":
            return get_model_comparison(query_params)

        elif path == "/api/detailed-results":
            return get_detailed_results(query_params)

        else:
            return error_response(404, "Not found")

    except Exception as e:
        print(f"Error: {e}")
        return error_response(500, str(e))


def get_weekly(params: Dict[str, str]) -> Dict[str, Any]:
    """
    GET /weekly?week=YYYY-WW

    Returns weekly aggregate data for all models.
    If week not specified, returns current week.
    """
    from datetime import datetime

    week = params.get("week")
    if not week:
        # Default to current ISO week
        week = datetime.now().strftime("%Y-W%V")

    # Query all models for this week
    # PK pattern: WEEK#{week}#MODEL#{model_id}
    results = []

    try:
        # Scan for all WEEK items (not ideal, but OK for MVP with small data)
        response = table.scan(
            FilterExpression="begins_with(PK, :prefix)",
            ExpressionAttributeValues={":prefix": f"WEEK#{week}#"},
        )

        for item in response.get("Items", []):
            if item.get("SK") == "SUMMARY":
                results.append(
                    {
                        "week": item.get("week"),
                        "model_id": item.get("model_id"),
                        "run_count": int(item.get("run_count", 0)),
                        "mean_score": float(item.get("mean_score", 0)),
                        "mean_compliance": float(item.get("mean_compliance", 0)),
                        "updated_at": item.get("updated_at"),
                    }
                )

        return success_response(
            {
                "week": week,
                "models": results,
            }
        )

    except Exception as e:
        return error_response(500, f"Failed to load weekly data: {e}")


def get_run_summary(run_id: str) -> Dict[str, Any]:
    """
    GET /runs/{run_id}/summary

    Returns curated run summary from S3.
    """
    if not run_id:
        return error_response(400, "run_id required")

    try:
        # Load from S3 curated JSON
        s3_key = f"curated/runs/{run_id}.json"
        response = s3.get_object(Bucket=BUCKET_NAME, Key=s3_key)
        data = json.loads(response["Body"].read())

        return success_response(data)

    except s3.exceptions.NoSuchKey:
        return error_response(404, f"Run not found: {run_id}")
    except Exception as e:
        return error_response(500, f"Failed to load run: {e}")


def get_run_turns(run_id: str, offset: int, limit: int) -> Dict[str, Any]:
    """
    GET /runs/{run_id}/turns?offset=0&limit=10

    Returns paginated turn headers from DynamoDB.
    UI can fetch full turn JSON from S3 using signed URLs.
    """
    if not run_id:
        return error_response(400, "run_id required")

    try:
        # Query TURN items
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

        # Paginate
        paginated = turns[offset : offset + limit]

        # Generate signed URLs for S3 turn bundles
        turn_data = []
        for turn in paginated:
            s3_key = turn.get("s3_key")
            signed_url = None
            if s3_key:
                signed_url = s3.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": BUCKET_NAME, "Key": s3_key},
                    ExpiresIn=3600,  # 1 hour
                )

            turn_data.append(
                {
                    "turn_index": turn["turn_index"],
                    "latency_ms": turn.get("latency_ms", 0),
                    "input_tokens": turn.get("input_tokens", 0),
                    "output_tokens": turn.get("output_tokens", 0),
                    "has_question": turn.get("has_question", False),
                    "word_count": turn.get("word_count", 0),
                    "s3_url": signed_url,
                }
            )

        return success_response(
            {
                "run_id": run_id,
                "offset": offset,
                "limit": limit,
                "total": len(turns),
                "turns": turn_data,
            }
        )

    except Exception as e:
        return error_response(500, f"Failed to load turns: {e}")


def get_timeseries(params: Dict[str, str]) -> Dict[str, Any]:
    """
    GET /api/timeseries

    Returns time-series data for all models across 52 weeks.
    Week 1 = this week (with actual data), weeks 2-52 = empty placeholders.
    """
    from datetime import datetime, timedelta

    try:
        # Get all models that have ever run
        # Scan for all WEEK items to find unique models and weeks with data
        response = table.scan(
            FilterExpression="begins_with(PK, :prefix) AND SK = :sk",
            ExpressionAttributeValues={":prefix": "WEEK#", ":sk": "SUMMARY"},
        )

        # Extract unique model IDs and weeks with actual data
        model_ids = set()
        week_data_map = {}  # {week: {model_id: mean_score}}
        weeks_with_data = set()

        for item in response.get("Items", []):
            model_id = item.get("model_id")
            week = item.get("week")
            mean_score = (
                float(item.get("mean_score", 0)) / 10
            )  # Normalize 0-100 to 0-10 for UI

            if model_id and week:
                model_ids.add(model_id)
                weeks_with_data.add(week)
                if week not in week_data_map:
                    week_data_map[week] = {}
                week_data_map[week][model_id] = mean_score

        # Sort weeks chronologically (only weeks with actual data)
        weeks = sorted(list(weeks_with_data))

        # Build time-series for each model (only include weeks with data)
        series = []
        for model_id in sorted(model_ids):
            data_points = []
            for week in weeks:
                # If we have data for this week/model, use it; otherwise null
                score = week_data_map.get(week, {}).get(model_id, None)
                data_points.append({"week": week, "score": score})

            series.append({"model_id": model_id, "data": data_points})

        return success_response({"weeks": weeks, "series": series})

    except Exception as e:
        return error_response(500, f"Failed to load timeseries: {e}")


def get_latest_rankings(params: Dict[str, str]) -> Dict[str, Any]:
    """
    GET /api/latest-rankings

    Returns latest model rankings sorted by overall_score.
    """
    try:
        # Get current week's data
        from datetime import datetime

        current_week = datetime.now().strftime("%Y-W%V")

        response = table.scan(
            FilterExpression="begins_with(PK, :prefix) AND SK = :sk",
            ExpressionAttributeValues={
                ":prefix": f"WEEK#{current_week}#",
                ":sk": "SUMMARY",
            },
        )

        rankings = []
        for item in response.get("Items", []):
            rankings.append(
                {
                    "model_id": item.get("model_id"),
                    "mean_score": float(item.get("mean_score", 0))
                    / 10,  # Normalize 0-100 to 0-10 for UI
                    "mean_compliance": float(item.get("mean_compliance", 0)),
                    "run_count": int(item.get("run_count", 0)),
                }
            )

        # Sort by score descending
        rankings.sort(key=lambda x: x["mean_score"], reverse=True)

        return success_response({"week": current_week, "rankings": rankings})

    except Exception as e:
        return error_response(500, f"Failed to load rankings: {e}")


def get_cost_analysis(params: Dict[str, str]) -> Dict[str, Any]:
    """
    GET /api/cost-analysis

    Returns cost vs performance scatter plot data.
    Uses Bedrock pricing API.
    """
    try:
        # Bedrock pricing (as of 2024 - approximate, per 1K tokens)
        pricing = {
            "anthropic.claude-3-5-sonnet-20241022-v2:0": {
                "input": 0.003,
                "output": 0.015,
            },
            "anthropic.claude-3-5-haiku-20241022-v1:0": {
                "input": 0.00025,
                "output": 0.00125,
            },
            "anthropic.claude-sonnet-4-5": {"input": 0.003, "output": 0.015},
            "anthropic.claude-opus-4-1": {"input": 0.015, "output": 0.075},
            # Add more as needed - these are approximations
        }

        # Get all RUN#SUMMARY items to calculate costs
        response = table.scan(
            FilterExpression="SK = :sk", ExpressionAttributeValues={":sk": "SUMMARY"}
        )

        # Aggregate by model
        model_data = {}

        for item in response.get("Items", []):
            model_id = item.get("model_id")
            overall_score = float(item.get("overall_score", 0))
            input_tokens = int(item.get("total_input_tokens", 0))
            output_tokens = int(item.get("total_output_tokens", 0))

            if model_id not in model_data:
                model_data[model_id] = {
                    "scores": [],
                    "total_input_tokens": 0,
                    "total_output_tokens": 0,
                    "run_count": 0,
                }

            model_data[model_id]["scores"].append(overall_score)
            model_data[model_id]["total_input_tokens"] += input_tokens
            model_data[model_id]["total_output_tokens"] += output_tokens
            model_data[model_id]["run_count"] += 1

        # Calculate cost and average score per model
        scatter_data = []
        for model_id, data in model_data.items():
            # Scores are now 0-1 scale (vector-based), no need to normalize
            avg_score = (
                (sum(data["scores"]) / len(data["scores"])) if data["scores"] else 0
            )

            # Get pricing for this model (default to mid-range if not found)
            model_pricing = pricing.get(model_id, {"input": 0.002, "output": 0.010})

            # Calculate cost per run
            cost_per_run = (
                (
                    (data["total_input_tokens"] / 1000) * model_pricing["input"]
                    + (data["total_output_tokens"] / 1000) * model_pricing["output"]
                )
                / data["run_count"]
                if data["run_count"] > 0
                else 0
            )

            scatter_data.append(
                {
                    "model_id": model_id,
                    "avg_score": round(avg_score, 2),
                    "cost_per_run": round(cost_per_run, 4),
                    "run_count": data["run_count"],
                    "provider": model_id.split(".")[0]
                    if "." in model_id
                    else "unknown",
                }
            )

        return success_response({"scatter_data": scatter_data})

    except Exception as e:
        return error_response(500, f"Failed to load cost analysis: {e}")


def get_model_comparison(params: Dict[str, str]) -> Dict[str, Any]:
    """
    GET /api/model-comparison - V2 judge metrics ONLY (3 metrics, not 5).

    Returns each model with v2 metrics:
    - conciseness: Inverted token count (lower tokens = higher score, 0-10 scale)
    - ends_with_question: Percentage of runs ending with Socratic question (0-10 scale)
    - directionally_socratic: How Socratic the approach is (0-10 scale)
    - overall: Composite score (0-1 scale, converted to 0-10 for display)
    """
    try:
        summary_response = table.scan(
            FilterExpression="SK = :sk", ExpressionAttributeValues={":sk": "SUMMARY"}
        )

        # Group runs by model
        model_data = {}

        for item in summary_response.get("Items", []):
            model_id = item.get("model_id")
            run_id = item.get("PK", "").replace("RUN#", "")
            overall_score = float(item.get("overall_score", 0))

            if not model_id or not run_id or overall_score < 0.01:  # Skip failed runs
                continue

            if model_id not in model_data:
                model_data[model_id] = {
                    "token_counts": [],
                    "ends_with_question_count": 0,
                    "total_runs": 0,
                    "directionally_socratic_scores": [],
                    "overall_scores": [],
                }

            # Load v2 judge metrics from S3
            try:
                s3_key = f"raw/runs/{run_id}/judge_000.json"
                s3_response = s3.get_object(Bucket=BUCKET_NAME, Key=s3_key)
                judge_data = json.loads(s3_response["Body"].read())
                scores = judge_data.get("scores", {})

                token_count = scores.get("token_count", 0)
                ends_with_question = scores.get("ends_with_socratic_question", False)
                directionally_socratic = float(scores.get("directionally_socratic", 0))

                model_data[model_id]["token_counts"].append(token_count)
                if ends_with_question:
                    model_data[model_id]["ends_with_question_count"] += 1
                model_data[model_id]["total_runs"] += 1
                model_data[model_id]["directionally_socratic_scores"].append(directionally_socratic)
                model_data[model_id]["overall_scores"].append(overall_score)

            except Exception as e:
                print(f"Failed to load judge data for {run_id}: {e}")
                continue

        # Aggregate into final model objects with v2 metrics (0-10 scale)
        models = []
        for model_id, data in model_data.items():
            if data["total_runs"] == 0:
                continue

            # 1. Conciseness (inverted token count: lower = better)
            # Ideal range: 40-100 tokens. Convert to 0-10 scale.
            avg_tokens = sum(data["token_counts"]) / len(data["token_counts"])
            if avg_tokens < 40:
                conciseness = 5.0  # Too terse
            elif avg_tokens <= 100:
                conciseness = 10.0  # Ideal
            else:
                # Penalty for verbosity: 100 tokens = 10, 200 tokens = 5, 300+ = 0
                conciseness = max(0, 10.0 - ((avg_tokens - 100) / 20))

            # 2. Ends with Question (percentage converted to 0-10 scale)
            question_pct = (data["ends_with_question_count"] / data["total_runs"]) * 10

            # 3. Directionally Socratic (already 0-1, multiply by 10 for 0-10 scale)
            avg_socratic = sum(data["directionally_socratic_scores"]) / len(data["directionally_socratic_scores"])
            directionally_socratic = avg_socratic * 10

            # 4. Overall (average of the 3 v2 metrics, already 0-10 scale)
            overall = (conciseness + question_pct + directionally_socratic) / 3

            models.append(
                {
                    "model_id": model_id,
                    "overall": round(overall, 2),
                    "conciseness": round(conciseness, 2),
                    "ends_with_question": round(question_pct, 2),
                    "directionally_socratic": round(directionally_socratic, 2),
                    "run_count": data["total_runs"],
                }
            )

        models = sorted(models, key=lambda x: x["overall"], reverse=True)
        return success_response(
            {"models": models, "winner": models[0] if models else None}
        )
    except Exception as e:
        return error_response(500, f"Failed to load model comparison: {e}")


def get_detailed_results(params: Dict[str, str]) -> Dict[str, Any]:
    """GET /api/detailed-results - Returns latest run per model with v2 judge metrics (3 metrics, NOT 5)."""
    try:
        summary_response = table.scan(
            FilterExpression="SK = :sk", ExpressionAttributeValues={":sk": "SUMMARY"}
        )
        model_to_latest = {}

        for item in summary_response.get("Items", []):
            model_id = item.get("model_id")
            run_id = item.get("PK", "").replace("RUN#", "")
            created_at = item.get("created_at", item.get("curated_at", ""))
            scenario_id = item.get("scenario_id", "")

            if not model_id or not run_id:
                continue

            if (
                model_id not in model_to_latest
                or created_at > model_to_latest[model_id]["created_at"]
            ):
                try:
                    s3_key = f"raw/runs/{run_id}/judge_000.json"
                    s3_response = s3.get_object(Bucket=BUCKET_NAME, Key=s3_key)
                    judge_data = json.loads(s3_response["Body"].read())
                    scores = judge_data.get("scores", {})

                    # NEW LLM-based scoring system (0-1 scale from judge, convert to 0-10 for API)
                    token_count = scores.get("token_count", 0)
                    ends_with_question = scores.get("ends_with_socratic_question", False)
                    directionally_socratic = float(scores.get("directionally_socratic", 0)) * 10  # Convert 0-1 to 0-10
                    overall = float(scores.get("overall", 0)) * 10  # Convert 0-1 to 0-10

                    # Penalty breakdown (for transparency, convert 0-1 to 0-10 scale)
                    verbosity_penalty = float(scores.get("verbosity_penalty", 0)) * 10
                    question_penalty = float(scores.get("question_penalty", 0)) * 10
                    socratic_penalty = float(scores.get("socratic_penalty", 0)) * 10

                    model_to_latest[model_id] = {
                        "created_at": created_at,
                        "run_id": run_id,
                        "model_id": model_id,
                        "scenario_name": get_scenario_name(scenario_id),
                        "test_type": "disposition",
                        "overall_score": round(overall, 2),
                        # NEW metrics
                        "token_count": token_count,
                        "ends_with_socratic_question": ends_with_question,
                        "directionally_socratic": round(directionally_socratic, 2),
                        # Penalty breakdown
                        "verbosity_penalty": round(verbosity_penalty, 2),
                        "question_penalty": round(question_penalty, 2),
                        "socratic_penalty": round(socratic_penalty, 2),
                        "judged_at": item.get("curated_at", ""),
                    }
                except Exception as e:
                    print(f"Failed to load judge data for {run_id}: {e}")
                    continue

        results = sorted(
            list(model_to_latest.values()),
            key=lambda x: x["overall_score"],
            reverse=True,
        )
        return success_response({"total": len(results), "results": results})
    except Exception as e:
        return error_response(500, f"Failed to load detailed results: {e}")


def success_response(data: Any) -> Dict[str, Any]:
    """Build successful API response."""
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(data),
    }


def error_response(status_code: int, message: str) -> Dict[str, Any]:
    """Build error API response."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps({"error": message}),
    }
