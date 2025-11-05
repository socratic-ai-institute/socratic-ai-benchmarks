"""
Runner Lambda - Executes Socratic dialogue tests.

Triggered by: SQS dialogue-jobs queue
Output: Turn data to S3/DynamoDB, judge jobs to SQS

Flow:
1. Receive job from SQS (run_id, model, scenario, params)
2. Load scenario and model config
3. Run dialogue using socratic_bench.run_dialogue()
4. For each turn:
   - Write turn bundle to S3 (raw/runs/<run_id>/turn_<N>.json)
   - Write TURN item to DynamoDB
   - Enqueue judge job to SQS
5. Mark RUN status as completed
"""
import json
import os
from datetime import datetime, timezone
from typing import Dict, Any
import boto3

# Import from layer
from socratic_bench import run_dialogue, get_scenario, ModelConfig, BedrockClient

# AWS clients
s3 = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")
sqs = boto3.client("sqs")

TABLE_NAME = os.environ["TABLE_NAME"]
BUCKET_NAME = os.environ["BUCKET_NAME"]
JUDGE_QUEUE_URL = os.environ["JUDGE_QUEUE_URL"]

table = dynamodb.Table(TABLE_NAME)


def lambda_handler(event, context):
    """
    Main handler for Runner Lambda.

    Processes SQS messages (batch of 1).
    """
    print(f"Runner started: processing {len(event['Records'])} messages")

    for record in event["Records"]:
        try:
            job = json.loads(record["body"])
            print(f"Processing run: {job['run_id']}")

            result = process_run(job)

            print(f"Run complete: {job['run_id']}, {result['turn_count']} turns")

        except Exception as e:
            print(f"Error processing run: {e}")
            raise  # Let SQS retry or send to DLQ

    return {"statusCode": 200, "message": "Runs processed"}


def process_run(job: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a single benchmark run.

    Args:
        job: Job parameters from SQS

    Returns:
        Summary of run execution
    """
    run_id = job["run_id"]
    scenario_id = job["scenario_id"]

    # 1. Load scenario
    scenario = get_scenario(scenario_id)
    if not scenario:
        raise ValueError(f"Scenario not found: {scenario_id}")

    # 2. Configure model
    model_config = ModelConfig(
        model_id=job["model_id"],
        provider=job["provider"],
        max_tokens=job.get("max_tokens", 200),
        temperature=job.get("temperature", 0.7),
    )

    # 3. Create RUN item in DynamoDB
    create_run_item(job, scenario)

    # 4. Run dialogue
    bedrock_client = BedrockClient()

    try:
        result = run_dialogue(
            scenario=scenario,
            model_config=model_config,
            max_turns=job.get("max_turns", 5),
            bedrock_client=bedrock_client,
        )

        # 5. Save turns and enqueue judge jobs
        for turn in result.turns:
            save_turn(run_id, job, scenario, turn)
            enqueue_judge_job(run_id, turn.turn_index)

        # 6. Update RUN status
        update_run_status(run_id, "completed", len(result.turns))

        return {
            "run_id": run_id,
            "status": "completed",
            "turn_count": len(result.turns),
        }

    except Exception as e:
        # Mark run as failed
        update_run_status(run_id, "failed", 0, error=str(e))
        raise


def create_run_item(job: Dict[str, Any], scenario: Dict[str, Any]) -> None:
    """Create initial RUN item in DynamoDB."""
    run_id = job["run_id"]

    table.put_item(
        Item={
            "PK": f"RUN#{run_id}",
            "SK": "META",
            "run_id": run_id,
            "manifest_id": job["manifest_id"],
            "model_id": job["model_id"],
            "scenario_id": job["scenario_id"],
            "vector": scenario["vector"],
            "status": "running",
            "created_at": datetime.now(timezone.utc).isoformat(),
            # GSI keys for querying
            "GSI1PK": f"MODEL#{job['model_id']}",
            "GSI1SK": f"RUN#{run_id}",
            "GSI2PK": f"MANIFEST#{job['manifest_id']}",
            "GSI2SK": f"RUN#{run_id}",
        }
    )


def save_turn(
    run_id: str,
    job: Dict[str, Any],
    scenario: Dict[str, Any],
    turn: Any,
) -> None:
    """
    Save turn data to S3 and DynamoDB.

    S3: Full turn bundle with all details
    DynamoDB: Compact pointer + key fields
    """
    turn_index = turn.turn_index

    # Turn bundle for S3
    turn_bundle = {
        "run_id": run_id,
        "turn_index": turn_index,
        "scenario_id": job["scenario_id"],
        "vector": scenario["vector"],
        "persona": scenario["persona"],
        "student": turn.student_utterance,
        "ai": turn.ai_response,
        "latency_ms": turn.latency_ms,
        "input_tokens": turn.input_tokens,
        "output_tokens": turn.output_tokens,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    # Save to S3
    s3_key = f"raw/runs/{run_id}/turn_{turn_index:03d}.json"
    s3.put_object(
        Bucket=BUCKET_NAME,
        Key=s3_key,
        Body=json.dumps(turn_bundle, indent=2),
        ContentType="application/json",
    )

    # Save compact item to DynamoDB
    table.put_item(
        Item={
            "PK": f"RUN#{run_id}",
            "SK": f"TURN#{turn_index:03d}",
            "run_id": run_id,
            "turn_index": turn_index,
            "s3_key": s3_key,
            "latency_ms": int(turn.latency_ms),
            "input_tokens": turn.input_tokens,
            "output_tokens": turn.output_tokens,
            "has_question": "?" in turn.ai_response,
            "word_count": len(turn.ai_response.split()),
        }
    )

    print(f"Saved turn {turn_index} to S3 and DynamoDB")


def enqueue_judge_job(run_id: str, turn_index: int) -> None:
    """Enqueue a judge job for this turn."""
    job = {
        "run_id": run_id,
        "turn_index": turn_index,
    }

    sqs.send_message(
        QueueUrl=JUDGE_QUEUE_URL,
        MessageBody=json.dumps(job),
    )


def update_run_status(
    run_id: str,
    status: str,
    turn_count: int,
    error: str = None,
) -> None:
    """Update RUN item status."""
    update_expr = "SET #status = :status, turn_count = :count, updated_at = :updated"
    expr_values = {
        ":status": status,
        ":count": turn_count,
        ":updated": datetime.now(timezone.utc).isoformat(),
    }
    expr_names = {"#status": "status"}

    if error:
        update_expr += ", error = :error"
        expr_values[":error"] = error

    table.update_item(
        Key={"PK": f"RUN#{run_id}", "SK": "META"},
        UpdateExpression=update_expr,
        ExpressionAttributeValues=expr_values,
        ExpressionAttributeNames=expr_names,
    )

    print(f"Updated run {run_id} status to {status}")
