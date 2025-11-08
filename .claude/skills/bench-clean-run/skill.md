# Bench Clean Run

Automated workflow to clean all stale data from DynamoDB and S3, then trigger a fresh benchmark test run.

## Description

This skill automates the repetitive task of clearing old benchmark data and starting fresh runs. It:
1. Deletes all items from DynamoDB table `socratic_core`
2. Deletes all files from S3 bucket `socratic-bench-data-*` (raw/ and curated/ prefixes)
3. Triggers a fresh planner run via API
4. Returns the manifest ID for tracking

## When to Use

- After deploying code changes to judge, runner, or curator
- When test data becomes inconsistent or corrupted
- Before running clean baseline tests
- After fixing bugs that require fresh evaluation

## Usage

```bash
claude-flow run bench-clean-run
```

## Implementation

```python
import boto3
import json
import requests
import os

# Initialize AWS clients
session = boto3.Session(profile_name='mvp')
dynamodb = session.resource('dynamodb', region_name='us-east-1')
s3 = session.client('s3', region_name='us-east-1')

# Get configuration
table = dynamodb.Table('socratic_core')
api_url = "https://wcyf23uxxe.execute-api.us-east-1.amazonaws.com/prod"

print("🧹 Starting clean run workflow...\n")

# Step 1: Delete all DynamoDB items
print("Step 1: Deleting DynamoDB items...")
count = 0
scan_kwargs = {}

while True:
    response = table.scan(**scan_kwargs)

    with table.batch_writer() as batch:
        for item in response['Items']:
            batch.delete_item(Key={'PK': item['PK'], 'SK': item['SK']})
            count += 1

    if 'LastEvaluatedKey' not in response:
        break
    scan_kwargs['ExclusiveStartKey'] = response['LastEvaluatedKey']

print(f"✅ Deleted {count} items from DynamoDB\n")

# Step 2: Delete all S3 objects
print("Step 2: Deleting S3 objects...")

# Get bucket name
buckets_response = s3.list_buckets()
bucket_name = None
for bucket in buckets_response['Buckets']:
    if bucket['Name'].startswith('socratic-bench-data-'):
        bucket_name = bucket['Name']
        break

if not bucket_name:
    print("❌ Could not find S3 bucket")
    exit(1)

# Delete all objects with raw/ and curated/ prefixes
s3_count = 0
for prefix in ['raw/', 'curated/']:
    paginator = s3.get_paginator('list_objects_v2')
    pages = paginator.paginate(Bucket=bucket_name, Prefix=prefix)

    for page in pages:
        if 'Contents' in page:
            delete_keys = [{'Key': obj['Key']} for obj in page['Contents']]
            if delete_keys:
                s3.delete_objects(Bucket=bucket_name, Delete={'Objects': delete_keys})
                s3_count += len(delete_keys)

print(f"✅ Deleted {s3_count} objects from S3 bucket {bucket_name}\n")

# Step 3: Trigger fresh planner run
print("Step 3: Triggering fresh planner run...")

response = requests.post(
    f"{api_url}/trigger-planner",
    headers={"Content-Type": "application/json"}
)

if response.status_code == 200:
    result = response.json()
    manifest_id = result.get('manifest_id', 'Unknown')
    total_jobs = result.get('total_jobs', 'Unknown')
    print(f"✅ Triggered planner run: {manifest_id}")
    print(f"   Total jobs: {total_jobs}\n")
    print(f"🎯 Clean run complete! Track progress with manifest: {manifest_id}")
else:
    print(f"❌ Failed to trigger planner: {response.status_code}")
    print(f"   Response: {response.text}")
```

## Output

```
🧹 Starting clean run workflow...

Step 1: Deleting DynamoDB items...
✅ Deleted 210 items from DynamoDB

Step 2: Deleting S3 objects...
✅ Deleted 847 objects from S3 bucket socratic-bench-data-984906149037

Step 3: Triggering fresh planner run...
✅ Triggered planner run: M-20251108-727952e3f7a8
   Total jobs: 48

🎯 Clean run complete! Track progress with manifest: M-20251108-727952e3f7a8
```

## Notes

- Uses AWS profile 'mvp' - ensure credentials are configured
- Requires `boto3` and `requests` Python packages
- Deletes ALL data - use with caution
- Returns manifest ID for tracking run progress
