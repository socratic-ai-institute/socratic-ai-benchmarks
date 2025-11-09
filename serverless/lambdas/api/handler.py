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
from typing import Dict, Any, Optional
import boto3

# AWS clients
s3 = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")

TABLE_NAME = os.environ["TABLE_NAME"]
BUCKET_NAME = os.environ["BUCKET_NAME"]

table = dynamodb.Table(TABLE_NAME)


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
                results.append({
                    "week": item.get("week"),
                    "model_id": item.get("model_id"),
                    "run_count": int(item.get("run_count", 0)),
                    "mean_score": float(item.get("mean_score", 0)),
                    "mean_compliance": float(item.get("mean_compliance", 0)),
                    "updated_at": item.get("updated_at"),
                })

        return success_response({
            "week": week,
            "models": results,
        })

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
        paginated = turns[offset:offset + limit]

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

            turn_data.append({
                "turn_index": turn["turn_index"],
                "latency_ms": turn.get("latency_ms", 0),
                "input_tokens": turn.get("input_tokens", 0),
                "output_tokens": turn.get("output_tokens", 0),
                "has_question": turn.get("has_question", False),
                "word_count": turn.get("word_count", 0),
                "s3_url": signed_url,
            })

        return success_response({
            "run_id": run_id,
            "offset": offset,
            "limit": limit,
            "total": len(turns),
            "turns": turn_data,
        })

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
        # Get current week
        current_date = datetime.now()
        current_week = current_date.strftime("%Y-W%V")

        # Generate 52 weeks starting from current week
        weeks = []
        for i in range(52):
            week_date = current_date + timedelta(weeks=i)
            week_str = week_date.strftime("%Y-W%V")
            weeks.append(week_str)

        # Get all models that have ever run
        # Scan for all WEEK items to find unique models
        response = table.scan(
            FilterExpression="begins_with(PK, :prefix) AND SK = :sk",
            ExpressionAttributeValues={
                ":prefix": "WEEK#",
                ":sk": "SUMMARY"
            }
        )

        # Extract unique model IDs
        model_ids = set()
        week_data_map = {}  # {week: {model_id: mean_score}}

        for item in response.get("Items", []):
            model_id = item.get("model_id")
            week = item.get("week")
            mean_score = float(item.get("mean_score", 0)) / 10  # Normalize 0-100 to 0-10 for UI

            if model_id:
                model_ids.add(model_id)
                if week not in week_data_map:
                    week_data_map[week] = {}
                week_data_map[week][model_id] = mean_score

        # Build time-series for each model
        series = []
        for model_id in sorted(model_ids):
            data_points = []
            for week in weeks:
                # If we have data for this week/model, use it; otherwise null
                score = week_data_map.get(week, {}).get(model_id, None)
                data_points.append({
                    "week": week,
                    "score": score
                })

            series.append({
                "model_id": model_id,
                "data": data_points
            })

        return success_response({
            "weeks": weeks,
            "series": series
        })

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
                ":sk": "SUMMARY"
            }
        )

        rankings = []
        for item in response.get("Items", []):
            rankings.append({
                "model_id": item.get("model_id"),
                "mean_score": float(item.get("mean_score", 0)) / 10,  # Normalize 0-100 to 0-10 for UI
                "mean_compliance": float(item.get("mean_compliance", 0)),
                "run_count": int(item.get("run_count", 0)),
            })

        # Sort by score descending
        rankings.sort(key=lambda x: x["mean_score"], reverse=True)

        return success_response({
            "week": current_week,
            "rankings": rankings
        })

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
            "anthropic.claude-3-5-sonnet-20241022-v2:0": {"input": 0.003, "output": 0.015},
            "anthropic.claude-3-5-haiku-20241022-v1:0": {"input": 0.00025, "output": 0.00125},
            "anthropic.claude-sonnet-4-5": {"input": 0.003, "output": 0.015},
            "anthropic.claude-opus-4-1": {"input": 0.015, "output": 0.075},
            # Add more as needed - these are approximations
        }

        # Get all RUN#SUMMARY items to calculate costs
        response = table.scan(
            FilterExpression="SK = :sk",
            ExpressionAttributeValues={":sk": "SUMMARY"}
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
                    "run_count": 0
                }

            model_data[model_id]["scores"].append(overall_score)
            model_data[model_id]["total_input_tokens"] += input_tokens
            model_data[model_id]["total_output_tokens"] += output_tokens
            model_data[model_id]["run_count"] += 1

        # Calculate cost and average score per model
        scatter_data = []
        for model_id, data in model_data.items():
            avg_score = (sum(data["scores"]) / len(data["scores"]) / 10) if data["scores"] else 0  # Normalize 0-100 to 0-10

            # Get pricing for this model (default to mid-range if not found)
            model_pricing = pricing.get(model_id, {"input": 0.002, "output": 0.010})

            # Calculate cost per run
            cost_per_run = (
                (data["total_input_tokens"] / 1000) * model_pricing["input"] +
                (data["total_output_tokens"] / 1000) * model_pricing["output"]
            ) / data["run_count"] if data["run_count"] > 0 else 0

            scatter_data.append({
                "model_id": model_id,
                "avg_score": round(avg_score, 2),
                "cost_per_run": round(cost_per_run, 4),
                "run_count": data["run_count"],
                "provider": model_id.split(".")[0] if "." in model_id else "unknown"
            })

        return success_response({
            "scatter_data": scatter_data
        })

    except Exception as e:
        return error_response(500, f"Failed to load cost analysis: {e}")


def get_model_comparison(params: Dict[str, str]) -> Dict[str, Any]:
    """GET /api/model-comparison - Returns latest run per model with Socratic dimension scores from S3."""
    try:
        summary_response = table.scan(FilterExpression="SK = :sk", ExpressionAttributeValues={":sk": "SUMMARY"})
        model_to_latest = {}

        for item in summary_response.get("Items", []):
            model_id = item.get("model_id")
            run_id = item.get("PK", "").replace("RUN#", "")
            created_at = item.get("created_at", item.get("curated_at", ""))

            if not model_id or not run_id:
                continue

            if model_id not in model_to_latest or created_at > model_to_latest[model_id]["created_at"]:
                try:
                    s3_key = f"raw/runs/{run_id}/judge_000.json"
                    s3_response = s3.get_object(Bucket=BUCKET_NAME, Key=s3_key)
                    judge_data = json.loads(s3_response["Body"].read())
                    scores = judge_data.get("scores", {})

                    open_ended = float(scores.get("open_ended", 0))
                    probing_depth = float(scores.get("probing_depth", 0))
                    non_directive = float(scores.get("non_directive", 0))
                    age_appropriate = float(scores.get("age_appropriate", 0))
                    content_relevant = float(scores.get("content_relevant", 0))
                    overall = float(scores.get("overall", 0))

                    model_to_latest[model_id] = {
                        "run_id": run_id,
                        "created_at": created_at,
                        "model_id": model_id,
                        "overall": round(overall / 10, 2),
                        # Accurate Socratic dimension names (new)
                        "open_ended": round(open_ended / 10, 2),
                        "probing_depth": round(probing_depth / 10, 2),
                        "non_directive": round(non_directive / 10, 2),
                        "age_appropriate": round(age_appropriate / 10, 2),
                        "content_relevant": round(content_relevant / 10, 2),
                        # Deprecated fidelity names (backwards compatibility - remove in 2 weeks)
                        "persistence": round(open_ended / 10, 2),
                        "cognitive_depth": round(probing_depth / 10, 2),
                        "context_adaptation": round(age_appropriate / 10, 2),
                        "resistance_to_drift": round(non_directive / 10, 2),
                        "memory_preservation": round(content_relevant / 10, 2),
                        "run_count": 1
                    }
                except Exception as e:
                    print(f"Failed to load judge data for {run_id}: {e}")
                    continue

        models = sorted(list(model_to_latest.values()), key=lambda x: x["overall"], reverse=True)
        return success_response({"models": models, "winner": models[0] if models else None})
    except Exception as e:
        return error_response(500, f"Failed to load model comparison: {e}")


def get_detailed_results(params: Dict[str, str]) -> Dict[str, Any]:
    """GET /api/detailed-results - Returns latest run per model with Socratic dimension scores from S3."""
    try:
        summary_response = table.scan(FilterExpression="SK = :sk", ExpressionAttributeValues={":sk": "SUMMARY"})
        model_to_latest = {}

        for item in summary_response.get("Items", []):
            model_id = item.get("model_id")
            run_id = item.get("PK", "").replace("RUN#", "")
            created_at = item.get("created_at", item.get("curated_at", ""))
            scenario_id = item.get("scenario_id", "")

            if not model_id or not run_id:
                continue

            if model_id not in model_to_latest or created_at > model_to_latest[model_id]["created_at"]:
                try:
                    s3_key = f"raw/runs/{run_id}/judge_000.json"
                    s3_response = s3.get_object(Bucket=BUCKET_NAME, Key=s3_key)
                    judge_data = json.loads(s3_response["Body"].read())
                    scores = judge_data.get("scores", {})

                    open_ended = float(scores.get("open_ended", 0))
                    probing_depth = float(scores.get("probing_depth", 0))
                    non_directive = float(scores.get("non_directive", 0))
                    age_appropriate = float(scores.get("age_appropriate", 0))
                    overall = float(scores.get("overall", 0))

                    model_to_latest[model_id] = {
                        "created_at": created_at,
                        "run_id": run_id,
                        "model_id": model_id,
                        "scenario_name": scenario_id,
                        "test_type": "disposition",
                        "overall_score": round(overall / 10, 2),
                        # Accurate Socratic dimension names (new)
                        "open_ended_score": round(open_ended / 10, 2),
                        "probing_depth_score": round(probing_depth / 10, 2),
                        "non_directive_score": round(non_directive / 10, 2),
                        "age_appropriate_score": round(age_appropriate / 10, 2),
                        # Deprecated fidelity names (backwards compatibility - remove in 2 weeks)
                        "persistence_score": round(open_ended / 10, 2),
                        "cognitive_depth_score": round(probing_depth / 10, 2),
                        "context_adaptation_score": round(age_appropriate / 10, 2),
                        "judged_at": item.get("curated_at", ""),
                    }
                except Exception as e:
                    print(f"Failed to load judge data for {run_id}: {e}")
                    continue

        results = sorted(list(model_to_latest.values()), key=lambda x: x["overall_score"], reverse=True)
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
