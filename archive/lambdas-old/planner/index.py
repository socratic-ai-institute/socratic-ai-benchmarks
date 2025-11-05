"""
Planner Lambda - Creates benchmark manifests and enqueues dialogue jobs

Responsibilities:
1. Create run_manifest (frozen configuration)
2. Generate job matrix (model × seed combinations)
3. Enqueue jobs to dialogue-jobs SQS queue
4. Handle API Gateway requests for manifest creation and run queries
"""

import os
import json
import boto3
from typing import Dict, List, Any
from decimal import Decimal

# Add shared utilities to path
import sys
sys.path.append('/opt/python')  # Lambda layer path
sys.path.append('../shared')  # Local development

from utils import generate_ulid, compute_sha256, now_iso, build_pk_sk, to_json

# AWS clients
dynamodb = boto3.resource('dynamodb')
sqs = boto3.client('sqs')

# Environment variables
TABLE_NAME = os.environ['TABLE_NAME']
DIALOGUE_QUEUE_URL = os.environ['DIALOGUE_QUEUE_URL']

table = dynamodb.Table(TABLE_NAME)


def handler(event, context):
    """
    Lambda handler for planner

    Handles:
    - POST /manifests - Create new benchmark manifest
    - GET /runs - List all runs
    - GET /runs/{run_id} - Get run details
    """
    print(f'Event: {json.dumps(event)}')

    # API Gateway request
    if 'httpMethod' in event:
        return handle_api_request(event)

    # Direct invocation (for testing)
    return create_manifest_and_queue_jobs(event)


def handle_api_request(event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle API Gateway request"""
    method = event['httpMethod']
    path = event['path']

    try:
        if method == 'POST' and path == '/manifests':
            body = json.loads(event['body'])
            result = create_manifest_and_queue_jobs(body)
            return {
                'statusCode': 200,
                'body': json.dumps(result),
                'headers': {'Content-Type': 'application/json'},
            }

        elif method == 'GET' and path == '/runs':
            result = list_runs()
            return {
                'statusCode': 200,
                'body': json.dumps(result, default=str),
                'headers': {'Content-Type': 'application/json'},
            }

        elif method == 'GET' and path.startswith('/runs/'):
            run_id = path.split('/')[-1]
            result = get_run_details(run_id)
            return {
                'statusCode': 200,
                'body': json.dumps(result, default=str),
                'headers': {'Content-Type': 'application/json'},
            }

        else:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'Not found'}),
            }

    except Exception as e:
        print(f'Error handling API request: {e}')
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)}),
        }


def create_manifest_and_queue_jobs(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create run manifest and enqueue dialogue jobs

    Args:
        config: {
            'prompt_id': str,
            'judge_prompt_id': str,
            'rubric_id': str,
            'seed_ids': List[str],  # SEED#... IDs
            'model_configs': List[{'model_id': str, 'temperature': float}]
        }

    Returns:
        {
            'manifest_id': str,
            'jobs_queued': int,
            'runs': List[str]  # RUN#... IDs
        }
    """
    print(f'Creating manifest with config: {json.dumps(config)}')

    # Generate manifest ID
    manifest_id = generate_ulid()
    timestamp = now_iso()

    # Fetch seed details to include vector information
    seed_set = []
    for seed_id in config['seed_ids']:
        pk, sk = build_pk_sk('SEED', seed_id.replace('SEED#', ''))
        response = table.get_item(Key={'PK': pk, 'SK': sk})
        if 'Item' in response:
            seed_item = response['Item']
            seed_set.append({
                'id': seed_id,
                'vector': seed_item.get('vector', 'unknown'),
                'title': seed_item.get('title', ''),
            })

    # Build manifest
    manifest_data = {
        'prompt_id': config['prompt_id'],
        'judge_prompt_id': config['judge_prompt_id'],
        'rubric_id': config['rubric_id'],
        'seed_set': seed_set,
        'model_set': config['model_configs'],
    }

    # Compute content-addressed hash
    manifest_sha256 = compute_sha256(manifest_data)

    # Create manifest item
    manifest_item = {
        'PK': f'MANIFEST#{manifest_id}',
        'SK': 'METADATA',
        'GSI3PK': f'MANIFEST#{manifest_id}',
        'GSI3SK': timestamp,
        'entity_type': 'manifest',
        'sha256': manifest_sha256,
        'manifest': manifest_data,
        'created_at': timestamp,
    }

    # Save manifest
    table.put_item(Item=manifest_item)
    print(f'Created manifest: MANIFEST#{manifest_id} (sha256={manifest_sha256})')

    # Generate job matrix (model × seed)
    run_ids = []
    jobs_queued = 0

    for model_config in config['model_configs']:
        for seed in seed_set:
            # Create run ID
            run_id = generate_ulid()
            run_ids.append(f'RUN#{run_id}')

            # Create run item (write-once)
            run_item = {
                'PK': f'RUN#{run_id}',
                'SK': 'METADATA',
                'GSI1PK': model_config['model_id'],
                'GSI1SK': timestamp,
                'GSI2PK': f"VECTOR#{seed['vector']}",
                'GSI2SK': timestamp,
                'GSI3PK': f'MANIFEST#{manifest_id}',
                'GSI3SK': timestamp,
                'entity_type': 'run',
                'manifest_id': f'MANIFEST#{manifest_id}',
                'model_id': model_config['model_id'],
                'seed_id': seed['id'],
                'vector': seed['vector'],
                'temperature': Decimal(str(model_config['temperature'])),
                'started_at': timestamp,
                'status': 'pending',
                'cost_prompt_tokens': 0,
                'cost_completion_tokens': 0,
                'turns_completed': 0,
            }

            table.put_item(Item=run_item)
            print(f"Created run: RUN#{run_id} ({model_config['model_id']} × {seed['id']})")

            # Enqueue dialogue job
            message = {
                'run_id': run_id,
                'manifest_id': manifest_id,
                'model_id': model_config['model_id'],
                'seed_id': seed['id'],
                'vector': seed['vector'],
                'temperature': model_config['temperature'],
                'prompt_id': config['prompt_id'],
            }

            sqs.send_message(
                QueueUrl=DIALOGUE_QUEUE_URL,
                MessageBody=json.dumps(message),
                MessageAttributes={
                    'vector': {'StringValue': seed['vector'], 'DataType': 'String'},
                    'model_id': {'StringValue': model_config['model_id'], 'DataType': 'String'},
                },
            )
            jobs_queued += 1

    print(f'Queued {jobs_queued} jobs to dialogue-jobs queue')

    return {
        'manifest_id': f'MANIFEST#{manifest_id}',
        'jobs_queued': jobs_queued,
        'runs': run_ids,
    }


def list_runs() -> Dict[str, Any]:
    """List all runs (paginated)"""
    # Scan for all RUN# items (in production, use GSI3 to filter by manifest)
    response = table.scan(
        FilterExpression='begins_with(PK, :prefix) AND SK = :sk',
        ExpressionAttributeValues={
            ':prefix': 'RUN#',
            ':sk': 'METADATA',
        },
        Limit=100,
    )

    runs = response.get('Items', [])
    return {
        'runs': runs,
        'count': len(runs),
    }


def get_run_details(run_id: str) -> Dict[str, Any]:
    """Get complete run details (metadata + all turns + judges + summary)"""
    # Query all items for this run
    response = table.query(
        KeyConditionExpression='PK = :pk',
        ExpressionAttributeValues={
            ':pk': run_id if run_id.startswith('RUN#') else f'RUN#{run_id}',
        },
    )

    items = response.get('Items', [])

    # Organize by type
    metadata = None
    turns = []
    judges = []
    summary = None

    for item in items:
        sk = item['SK']
        if sk == 'METADATA':
            metadata = item
        elif sk.startswith('TURN#'):
            turns.append(item)
        elif sk.startswith('JUDGE#'):
            judges.append(item)
        elif sk == 'SUMMARY':
            summary = item

    return {
        'metadata': metadata,
        'turns': sorted(turns, key=lambda x: x['turn_index']),
        'judges': sorted(judges, key=lambda x: x['turn_index']),
        'summary': summary,
    }
