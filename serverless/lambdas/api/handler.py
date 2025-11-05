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
