"""
Dialogue Runner Lambda - Runs Socratic dialogue tests

Responsibilities:
1. Receive job from SQS (model × seed)
2. Load scenario and prompt from DynamoDB
3. Execute 3-turn Socratic dialogue using Bedrock
4. Store each turn to DynamoDB + S3
5. Enqueue judge jobs for each turn
6. Update run status
"""

import os
import json
import boto3
from typing import Dict, List, Any
from decimal import Decimal
from datetime import datetime

# Add shared utilities
import sys

sys.path.append("/opt/python")
sys.path.append("../shared")

from utils import generate_ulid, now_iso, build_pk_sk, s3_path, s3_key

# AWS clients
dynamodb = boto3.resource("dynamodb")
bedrock = boto3.client("bedrock-runtime")
s3 = boto3.client("s3")
sqs = boto3.client("sqs")

# Environment variables
TABLE_NAME = os.environ["TABLE_NAME"]
BUCKET_NAME = os.environ["BUCKET_NAME"]
JUDGE_QUEUE_URL = os.environ["JUDGE_QUEUE_URL"]

table = dynamodb.Table(TABLE_NAME)

# Constants
NUM_TURNS = 3  # Socratic dialogues have 3 questions


def handler(event, context):
    """
    Lambda handler for dialogue runner

    Receives SQS message:
    {
        'run_id': str,
        'model_id': str,
        'seed_id': str,
        'vector': str,
        'temperature': float,
        'prompt_id': str
    }
    """
    print(f"Event: {json.dumps(event)}")

    # Process SQS messages
    for record in event["Records"]:
        message = json.loads(record["body"])
        process_dialogue_job(message)

    return {"statusCode": 200}


def process_dialogue_job(job: Dict[str, Any]):
    """
    Process a single dialogue job

    Steps:
    1. Load scenario (seed) and prompt
    2. Run 3-turn dialogue
    3. Store each turn
    4. Enqueue judge jobs
    5. Mark run complete
    """
    run_id = job["run_id"]
    model_id = job["model_id"]
    seed_id = job["seed_id"]
    vector = job["vector"]
    temperature = job["temperature"]
    prompt_id = job["prompt_id"]

    print(f"Processing dialogue job: {run_id} ({model_id} × {seed_id})")

    try:
        # Update run status to 'running'
        update_run_status(run_id, "running")

        # Load scenario
        scenario = load_scenario(seed_id)
        print(f"Scenario loaded: {scenario['title']} ({vector})")

        # Load tutor prompt
        tutor_prompt = load_prompt(prompt_id)
        print(f"Tutor prompt loaded: {tutor_prompt['title']}")

        # Run dialogue (3 turns)
        conversation_history = []
        total_prompt_tokens = 0
        total_completion_tokens = 0
        total_time_ms = 0

        for turn_num in range(1, NUM_TURNS + 1):
            print(f"  Turn {turn_num}/{NUM_TURNS}...")

            # Generate question
            question_result = generate_socratic_question(
                model_id=model_id,
                temperature=temperature,
                tutor_prompt=tutor_prompt["body"],
                scenario=scenario,
                conversation_history=conversation_history,
                turn_num=turn_num,
            )

            # Simulate student answer (for testing; in production this would be real students)
            answer_result = simulate_student_answer(
                model_id=model_id,
                scenario=scenario,
                question=question_result["text"],
                conversation_history=conversation_history,
            )

            # Update conversation history
            conversation_history.append(
                {
                    "question": question_result["text"],
                    "answer": answer_result["text"],
                }
            )

            # Save turn to DynamoDB + S3
            turn_id = save_turn(
                run_id=run_id,
                turn_num=turn_num,
                question=question_result,
                answer=answer_result,
            )

            # Enqueue judge job
            enqueue_judge_job(run_id, turn_num, turn_id)

            # Accumulate metrics
            total_prompt_tokens += question_result["prompt_tokens"]
            total_completion_tokens += question_result["completion_tokens"]
            total_time_ms += question_result["generation_time_ms"]

        # Mark run complete
        finish_run(
            run_id=run_id,
            total_prompt_tokens=total_prompt_tokens,
            total_completion_tokens=total_completion_tokens,
            total_time_ms=total_time_ms,
        )

        print(f"Dialogue complete: {run_id} (3 turns, {total_time_ms}ms)")

    except Exception as e:
        print(f"Error processing dialogue job: {e}")
        update_run_status(run_id, "failed", error=str(e))
        raise


def load_scenario(seed_id: str) -> Dict[str, Any]:
    """Load scenario from DynamoDB"""
    pk, sk = build_pk_sk("SEED", seed_id.replace("SEED#", ""))
    response = table.get_item(Key={"PK": pk, "SK": sk})

    if "Item" not in response:
        raise ValueError(f"Scenario not found: {seed_id}")

    return response["Item"]


def load_prompt(prompt_id: str) -> Dict[str, Any]:
    """Load prompt from DynamoDB"""
    pk, sk = build_pk_sk("PROMPT", prompt_id.replace("PROMPT#", ""))
    response = table.get_item(Key={"PK": pk, "SK": sk})

    if "Item" not in response:
        raise ValueError(f"Prompt not found: {prompt_id}")

    return response["Item"]


def generate_socratic_question(
    model_id: str,
    temperature: float,
    tutor_prompt: str,
    scenario: Dict[str, Any],
    conversation_history: List[Dict[str, str]],
    turn_num: int,
) -> Dict[str, Any]:
    """
    Generate a Socratic question using Bedrock

    Returns:
    {
        'text': str,
        'generation_time_ms': int,
        'prompt_tokens': int,
        'completion_tokens': int,
    }
    """
    start_time = datetime.now()

    # Build conversation context
    context_parts = [
        f"Persona: {scenario['scenario']['persona']}",
        f"Student statement: {scenario['scenario']['student_statement']}",
        f"Goal: {scenario['scenario']['goal']}",
    ]

    if conversation_history:
        context_parts.append("\nPrevious conversation:")
        for i, turn in enumerate(conversation_history, 1):
            context_parts.append(f"Q{i}: {turn['question']}")
            context_parts.append(f"A{i}: {turn['answer']}")

    context = "\n".join(context_parts)

    # Build prompt
    user_message = f"{context}\n\nGenerate question #{turn_num}:"

    # Call Bedrock
    request_body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 200,
        "temperature": temperature,
        "system": tutor_prompt,
        "messages": [
            {
                "role": "user",
                "content": user_message,
            }
        ],
    }

    bedrock_model_id = get_bedrock_model_id(model_id)

    response = bedrock.invoke_model(
        modelId=bedrock_model_id,
        body=json.dumps(request_body),
    )

    response_body = json.loads(response["body"].read())
    end_time = datetime.now()

    # Extract response
    question_text = response_body["content"][0]["text"]
    generation_time_ms = int((end_time - start_time).total_seconds() * 1000)

    return {
        "text": question_text.strip(),
        "generation_time_ms": generation_time_ms,
        "prompt_tokens": response_body["usage"]["input_tokens"],
        "completion_tokens": response_body["usage"]["output_tokens"],
    }


def simulate_student_answer(
    model_id: str,
    scenario: Dict[str, Any],
    question: str,
    conversation_history: List[Dict[str, str]],
) -> Dict[str, Any]:
    """
    Simulate a student answer using Bedrock

    In production, this would be replaced with real student responses.
    For benchmarking, we simulate realistic student answers.

    Returns:
    {
        'text': str,
        'word_count': int,
    }
    """
    # Build student simulation prompt
    persona = scenario["scenario"]["persona"]
    student_statement = scenario["scenario"]["student_statement"]

    history_str = ""
    if conversation_history:
        for i, turn in enumerate(conversation_history, 1):
            history_str += f"\nTutor: {turn['question']}\nYou: {turn['answer']}"

    prompt = f"""You are a student with this persona: {persona}

Your initial statement was: "{student_statement}"

{history_str}

Now the tutor asks: "{question}"

Respond naturally as this student would. Keep your answer brief (1-3 sentences). Think about what you said before. Be authentic to the persona."""

    request_body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 150,
        "temperature": 0.8,
        "messages": [
            {
                "role": "user",
                "content": prompt,
            }
        ],
    }

    bedrock_model_id = get_bedrock_model_id(model_id)

    response = bedrock.invoke_model(
        modelId=bedrock_model_id,
        body=json.dumps(request_body),
    )

    response_body = json.loads(response["body"].read())
    answer_text = response_body["content"][0]["text"].strip()

    return {
        "text": answer_text,
        "word_count": len(answer_text.split()),
    }


def save_turn(
    run_id: str,
    turn_num: int,
    question: Dict[str, Any],
    answer: Dict[str, Any],
) -> str:
    """
    Save turn to DynamoDB and S3

    Returns:
        turn_id (for reference)
    """
    timestamp = now_iso()
    turn_index_str = f"{turn_num:03d}"  # e.g., "001", "002", "003"

    # Build full turn data (for S3)
    turn_data = {
        "run_id": run_id,
        "turn_index": turn_num,
        "question": {
            "text": question["text"],
            "generated_at": timestamp,
            "generation_time_ms": question["generation_time_ms"],
            "prompt_tokens": question["prompt_tokens"],
            "completion_tokens": question["completion_tokens"],
        },
        "answer": {
            "text": answer["text"],
            "word_count": answer["word_count"],
            "received_at": timestamp,
        },
        "created_at": timestamp,
    }

    # Upload to S3
    date_str = datetime.now().strftime("%Y-%m-%d")
    key = s3_key("raw", f"dt={date_str}", run_id, f"turn_{turn_index_str}.json")

    s3.put_object(
        Bucket=BUCKET_NAME,
        Key=key,
        Body=json.dumps(turn_data, indent=2),
        ContentType="application/json",
    )

    s3_url = s3_path(BUCKET_NAME, key)
    print(f"  Saved turn to S3: {s3_url}")

    # Save minimal turn record to DynamoDB
    turn_item = {
        "PK": run_id if run_id.startswith("RUN#") else f"RUN#{run_id}",
        "SK": f"TURN#{turn_index_str}",
        "entity_type": "turn",
        "run_id": run_id,
        "turn_index": turn_num,
        "question": {
            "text": question["text"],
            "generated_at": timestamp,
            "generation_time_ms": Decimal(str(question["generation_time_ms"])),
            "prompt_tokens": question["prompt_tokens"],
            "completion_tokens": question["completion_tokens"],
        },
        "answer": {
            "text": answer["text"],
            "word_count": answer["word_count"],
            "received_at": timestamp,
        },
        "s3_path": s3_url,
        "created_at": timestamp,
    }

    table.put_item(Item=turn_item)
    print(f"  Saved turn to DynamoDB: {turn_item['PK']}/{turn_item['SK']}")

    return f"{run_id}/TURN#{turn_index_str}"


def enqueue_judge_job(run_id: str, turn_num: int, turn_id: str):
    """Enqueue judge job for this turn"""
    message = {
        "run_id": run_id,
        "turn_num": turn_num,
        "turn_id": turn_id,
    }

    sqs.send_message(
        QueueUrl=JUDGE_QUEUE_URL,
        MessageBody=json.dumps(message),
    )

    print(f"  Enqueued judge job for turn {turn_num}")


def update_run_status(run_id: str, status: str, error: str = None):
    """Update run status"""
    pk = run_id if run_id.startswith("RUN#") else f"RUN#{run_id}"

    update_expr = "SET #status = :status, updated_at = :now"
    expr_values = {
        ":status": status,
        ":now": now_iso(),
    }
    expr_names = {"#status": "status"}

    if error:
        update_expr += ", error = :error"
        expr_values[":error"] = error

    table.update_item(
        Key={"PK": pk, "SK": "METADATA"},
        UpdateExpression=update_expr,
        ExpressionAttributeValues=expr_values,
        ExpressionAttributeNames=expr_names,
    )


def finish_run(
    run_id: str,
    total_prompt_tokens: int,
    total_completion_tokens: int,
    total_time_ms: int,
):
    """Mark run as completed with final metrics"""
    pk = run_id if run_id.startswith("RUN#") else f"RUN#{run_id}"

    # Rough cost estimate (Claude 3.5 Sonnet pricing)
    input_cost = (total_prompt_tokens / 1_000_000) * 3.0  # $3/M input tokens
    output_cost = (total_completion_tokens / 1_000_000) * 15.0  # $15/M output tokens
    total_cost = input_cost + output_cost

    table.update_item(
        Key={"PK": pk, "SK": "METADATA"},
        UpdateExpression="SET #status = :status, ended_at = :now, cost_prompt_tokens = :pt, cost_completion_tokens = :ct, cost_usd = :cost, turns_completed = :turns, avg_generation_time_ms = :avg_time",
        ExpressionAttributeValues={
            ":status": "completed",
            ":now": now_iso(),
            ":pt": total_prompt_tokens,
            ":ct": total_completion_tokens,
            ":cost": Decimal(str(round(total_cost, 6))),
            ":turns": NUM_TURNS,
            ":avg_time": Decimal(str(round(total_time_ms / NUM_TURNS, 2))),
        },
        ExpressionAttributeNames={"#status": "status"},
    )

    print(
        f"Run completed: {run_id} (cost=${total_cost:.4f}, avg_time={total_time_ms / NUM_TURNS:.0f}ms)"
    )


def get_bedrock_model_id(model_id: str) -> str:
    """Map our model IDs to Bedrock model IDs"""
    mapping = {
        "MODEL#claude-3-5-sonnet-20241022": "anthropic.claude-3-5-sonnet-20241022-v2:0",
        "MODEL#claude-3-opus-20240229": "anthropic.claude-3-opus-20240229-v1:0",
        "MODEL#claude-3-haiku-20240307": "anthropic.claude-3-haiku-20240307-v1:0",
        "MODEL#claude-3-sonnet-20240229": "anthropic.claude-3-sonnet-20240229-v1:0",
    }

    if model_id in mapping:
        return mapping[model_id]

    # Try to extract bedrock_model_id from DynamoDB
    pk, sk = build_pk_sk("MODEL", model_id.replace("MODEL#", ""))
    response = table.get_item(Key={"PK": pk, "SK": sk})

    if "Item" in response and "bedrock_model_id" in response["Item"]:
        return response["Item"]["bedrock_model_id"]

    raise ValueError(f"Unknown model ID: {model_id}")
