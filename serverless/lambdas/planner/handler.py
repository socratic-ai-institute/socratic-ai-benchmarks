"""
Planner Lambda - Orchestrates weekly benchmark runs.

Triggered by: EventBridge (weekly cron)
Output: Enqueues dialogue jobs to SQS

Flow:
1. Read active config (models, scenarios, params)
2. Create manifest (SHA-pinned, deterministic)
3. Write manifest to S3 + DynamoDB
4. Enqueue one message per run onto dialogue-jobs queue
5. Idempotent: uses manifest_id + run_id to avoid duplicates
"""

import json
import os
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, List
import boto3
import ulid

# AWS clients
s3 = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")
sqs = boto3.client("sqs")

TABLE_NAME = os.environ["TABLE_NAME"]
BUCKET_NAME = os.environ["BUCKET_NAME"]
DIALOGUE_QUEUE_URL = os.environ["DIALOGUE_QUEUE_URL"]

table = dynamodb.Table(TABLE_NAME)


def lambda_handler(event, context):
    """
    Main handler for Planner Lambda.

    Args:
        event: EventBridge cron event or manual invoke
        context: Lambda context
    """
    print(f"Planner started: {json.dumps(event)}")

    # 1. Load active configuration
    config = load_config()

    # 2. Create manifest
    manifest_id = generate_manifest_id(config)
    manifest = create_manifest(manifest_id, config)

    # 3. Save manifest
    save_manifest(manifest_id, manifest)

    # 4. Generate run jobs
    jobs = generate_run_jobs(manifest_id, config)

    # 5. Enqueue jobs (idempotent)
    enqueued_count = enqueue_jobs(jobs)

    result = {
        "manifest_id": manifest_id,
        "total_jobs": len(jobs),
        "enqueued": enqueued_count,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    print(f"Planner complete: {json.dumps(result)}")
    return result


def load_config() -> Dict[str, Any]:
    """
    Load active benchmark configuration.

    For MVP: read from S3 artifacts/config.json
    For production: could read from DynamoDB with versioning
    """
    try:
        response = s3.get_object(Bucket=BUCKET_NAME, Key="artifacts/config.json")
        config = json.loads(response["Body"].read())
        print(
            f"Loaded config: {len(config.get('models', []))} models, "
            f"{len(config.get('scenarios', []))} scenarios"
        )
        return config
    except s3.exceptions.NoSuchKey:
        # Fallback to default config
        print("No config found, using defaults")
        return get_default_config()


def get_default_config() -> Dict[str, Any]:
    """Default configuration for MVP."""
    return {
        "models": [
            {
                "model_id": "anthropic.claude-3-5-sonnet-20241022-v2:0",
                "provider": "anthropic",
                "temperature": 0.7,
                "max_tokens": 200,
            },
            {
                "model_id": "anthropic.claude-3-5-haiku-20241022-v1:0",
                "provider": "anthropic",
                "temperature": 0.7,
                "max_tokens": 200,
            },
        ],
        "scenarios": [
            "EL-ETH-UTIL-DEON-01",
            "EL-CIV-FREE-HARM-01",
            "MAI-BIO-CRISPR-01",
            "MAI-ECO-INFL-01",
            "APO-PHY-HEAT-TEMP-01",
            "APO-BIO-GENE-DETERM-01",
        ],
        "parameters": {
            "max_turns": 5,
            "judge_model": "anthropic.claude-3-5-sonnet-20240620-v1:0",
        },
    }


def generate_manifest_id(config: Dict[str, Any]) -> str:
    """
    Generate deterministic manifest ID from config.

    Uses content hash to ensure same config = same manifest ID.
    """
    # Create stable JSON representation
    canonical = json.dumps(config, sort_keys=True, separators=(",", ":"))
    content_hash = hashlib.sha256(canonical.encode()).hexdigest()[:12]

    # Format: M-<date>-<hash>
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    return f"M-{date_str}-{content_hash}"


def create_manifest(manifest_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """Create full manifest document."""
    return {
        "manifest_id": manifest_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "config": config,
        "version": "1.0",
    }


def save_manifest(manifest_id: str, manifest: Dict[str, Any]) -> None:
    """
    Save manifest to S3 and DynamoDB.

    Idempotent: won't duplicate if manifest_id already exists.
    """
    # Check if already exists
    try:
        existing = table.get_item(Key={"PK": f"MANIFEST#{manifest_id}", "SK": "META"})
        if existing.get("Item"):
            print(f"Manifest {manifest_id} already exists, skipping save")
            return
    except Exception as e:
        print(f"Error checking manifest: {e}")

    # Save to S3
    s3_key = f"manifests/{manifest_id}.json"
    s3.put_object(
        Bucket=BUCKET_NAME,
        Key=s3_key,
        Body=json.dumps(manifest, indent=2),
        ContentType="application/json",
    )

    # Save to DynamoDB
    table.put_item(
        Item={
            "PK": f"MANIFEST#{manifest_id}",
            "SK": "META",
            "manifest_id": manifest_id,
            "created_at": manifest["created_at"],
            "s3_key": s3_key,
            "model_count": len(manifest["config"]["models"]),
            "scenario_count": len(manifest["config"]["scenarios"]),
        }
    )

    print(f"Saved manifest {manifest_id} to S3 and DynamoDB")


def generate_run_jobs(manifest_id: str, config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Generate all run jobs for this manifest.

    Each job = one model × one scenario combination.
    """
    jobs = []

    for model in config["models"]:
        for scenario in config["scenarios"]:
            # Generate deterministic run_id
            run_id = str(ulid.new())

            # Extract provider from model_id (e.g., "anthropic.claude-..." -> "anthropic")
            model_id = model["model_id"]
            provider = model_id.split(".")[0] if "." in model_id else "unknown"

            job = {
                "run_id": run_id,
                "manifest_id": manifest_id,
                "model_id": model_id,
                "model_name": model.get("name", model_id),
                "provider": provider,
                "temperature": config["parameters"].get("temperature", 0.7),
                "max_tokens": config["parameters"].get("max_tokens", 500),
                "scenario_id": scenario["id"],
                "scenario_name": scenario.get("name", scenario["id"]),
                "max_turns": scenario.get("max_turns", 5),
                "judge_model": config["parameters"].get("judge_model"),
            }
            jobs.append(job)

    print(f"Generated {len(jobs)} run jobs")
    return jobs


def enqueue_jobs(jobs: List[Dict[str, Any]]) -> int:
    """
    Enqueue jobs to SQS dialogue-jobs queue.

    Uses batching for efficiency (up to 10 per batch).
    Returns count of successfully enqueued jobs.
    """
    enqueued = 0
    batch_size = 10

    for i in range(0, len(jobs), batch_size):
        batch = jobs[i : i + batch_size]

        entries = [
            {
                "Id": str(idx),
                "MessageBody": json.dumps(job),
                "MessageDeduplicationId": job["run_id"],
                "MessageGroupId": "socratic-runs",  # For FIFO queue
            }
            for idx, job in enumerate(batch)
        ]

        try:
            # Note: Using standard queue for MVP, not FIFO
            # Remove MessageDeduplicationId and MessageGroupId for standard queue
            entries = [
                {
                    "Id": str(idx),
                    "MessageBody": json.dumps(job),
                }
                for idx, job in enumerate(batch)
            ]

            response = sqs.send_message_batch(
                QueueUrl=DIALOGUE_QUEUE_URL,
                Entries=entries,
            )

            enqueued += len(response.get("Successful", []))

            if response.get("Failed"):
                print(
                    f"Failed to enqueue {len(response['Failed'])} messages: {response['Failed']}"
                )

        except Exception as e:
            print(f"Error enqueueing batch: {e}")

    print(f"Enqueued {enqueued}/{len(jobs)} jobs")
    return enqueued
