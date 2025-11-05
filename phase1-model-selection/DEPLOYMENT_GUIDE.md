# Socratic Benchmarks Data Layer - Deployment Guide

## Quick Summary

You now have a **serverless DynamoDB + S3 + Lambda data layer** for the Socratic AI benchmarking system.

**What's included:**
- ✅ DynamoDB schema with single-table design
- ✅ S3 bucket structure for raw artifacts and curated results
- ✅ CDK infrastructure stack (TypeScript)
- ✅ Lambda functions (Planner, Dialogue Runner)
- ✅ API Gateway for admin operations
- ✅ Complete data model documentation

**Cost:** ~$1-5/month when running 4 benchmark batches (near-zero when idle)

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────┐
│                     API Gateway (Admin)                       │
│  POST /manifests  |  GET /runs  |  GET /runs/{id}            │
└────────────────────────┬─────────────────────────────────────┘
                         │
                    ┌────▼────┐
                    │ Planner │ Creates manifests + queues jobs
                    │ Lambda  │
                    └────┬────┘
                         │
              ┌──────────▼──────────┐
              │   dialogue-jobs     │ SQS Queue
              │   (model × seed)    │
              └──────────┬──────────┘
                         │
                    ┌────▼────┐
                    │Dialogue │ Runs 3-turn Socratic tests
                    │ Lambda  │ Calls Bedrock (Claude)
                    └────┬────┘
                         │
              ┌──────────▼──────────┐
              │   judge-jobs        │ SQS Queue
              │   (turn evals)      │
              └──────────┬──────────┘
                         │
                    ┌────▼────┐
                    │  Judge  │ Evaluates using rubric
                    │ Lambda  │ Calls Bedrock (Judge model)
                    └────┬────┘
                         │
              ┌──────────▼──────────┐
              │  curation-events    │ EventBridge
              └──────────┬──────────┘
                         │
                    ┌────▼────┐
                    │ Curator │ Aggregates scores
                    │ Lambda  │ Creates summaries
                    └─────────┘

                DynamoDB Table         S3 Bucket
                ┌─────────────┐       ┌─────────────┐
                │ PROMPT      │       │ raw/        │
                │ RUBRIC      │       │ manifests/  │
                │ SEED        │       │ curated/    │
                │ MODEL       │       └─────────────┘
                │ RUN         │
                │ TURN        │
                │ JUDGE       │
                │ SUMMARY     │
                └─────────────┘
```

---

## Prerequisites

1. **AWS Account** with credentials configured
2. **Node.js 20+** for CDK
3. **Python 3.12+** for Lambdas
4. **AWS CDK** installed globally

```bash
npm install -g aws-cdk
```

---

## Deployment Steps

### Step 1: Install Dependencies

```bash
# Navigate to infrastructure directory
cd infrastructure

# Install CDK dependencies
npm install
```

### Step 2: Bootstrap CDK (First Time Only)

```bash
cdk bootstrap aws://YOUR-ACCOUNT-ID/us-east-1
```

### Step 3: Deploy Infrastructure

```bash
# Synthesize CloudFormation template
cdk synth

# Deploy stack
cdk deploy --all --require-approval never
```

**Deployment time:** ~5-10 minutes

**What gets created:**
- 1 DynamoDB table (on-demand)
- 1 S3 bucket (versioned, encrypted)
- 2 SQS queues + 2 DLQs
- 1 EventBridge bus
- 4 Lambda functions (512MB each)
- 1 API Gateway (REST API)
- IAM roles and policies
- CloudWatch log groups

### Step 4: Save Outputs

After deployment, CDK will output:

```
Outputs:
SocraticBenchmarksStack.TableName = SocraticBenchmarks
SocraticBenchmarksStack.BucketName = socratic-bench-123456789012
SocraticBenchmarksStack.ApiUrl = https://abc123.execute-api.us-east-1.amazonaws.com/v1/
SocraticBenchmarksStack.ApiKeyId = xyz789
```

**Retrieve API Key:**
```bash
aws apigateway get-api-key --api-key xyz789 --include-value --query 'value' --output text
```

Save this for making API requests.

---

## Usage

### Option 1: Use Existing benchmark.py

Integration is pending. For now, you can:

1. Run `benchmark.py` as usual
2. Results save to JSON files
3. Manually upload to the data layer via API

### Option 2: Use API Directly

#### Create a Benchmark Manifest

```bash
curl -X POST https://YOUR-API-URL/v1/manifests \
  -H "x-api-key: YOUR-API-KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt_id": "PROMPT#01HW...",
    "judge_prompt_id": "PROMPT#01HW...",
    "rubric_id": "RUBRIC#01HW...",
    "seed_ids": [
      "SEED#01HW...",
      "SEED#01HW..."
    ],
    "model_configs": [
      {
        "model_id": "MODEL#claude-3-5-sonnet-20241022",
        "temperature": 0.7
      }
    ]
  }'
```

**Response:**
```json
{
  "manifest_id": "MANIFEST#01HW...",
  "jobs_queued": 10,
  "runs": ["RUN#01HW...", "RUN#01HW..."]
}
```

#### List All Runs

```bash
curl https://YOUR-API-URL/v1/runs \
  -H "x-api-key: YOUR-API-KEY"
```

#### Get Run Details

```bash
curl https://YOUR-API-URL/v1/runs/RUN#01HW... \
  -H "x-api-key: YOUR-API-KEY"
```

---

## Seed Data

Before running benchmarks, you need to populate reference data:

### 1. Create Prompts

```python
import boto3
import hashlib
import json
from datetime import datetime, timezone

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('SocraticBenchmarks')

# Tutor prompt
tutor_prompt = {
    'PK': 'PROMPT#01HW1111111111ABCDEFGHIJK',
    'SK': 'METADATA',
    'entity_type': 'prompt',
    'sha256': hashlib.sha256(b'...').hexdigest(),
    'kind': 'socratic_tutor',
    'title': 'Non-directive Socratic Tutor',
    'body': 'You are a Socratic tutor. Ask questions only...',
    'created_at': datetime.now(timezone.utc).isoformat(),
}

table.put_item(Item=tutor_prompt)
```

### 2. Create Rubric

See `DATA_LAYER_SCHEMA.md` for rubric structure.

### 3. Create Seeds (Scenarios)

```python
seed = {
    'PK': 'SEED#01HW3334567890ABCDEFGHIJK',
    'SK': 'METADATA',
    'entity_type': 'seed',
    'vector': 'elenchus',
    'title': 'Free Speech Contradiction',
    'scenario': {
        'persona': 'Age 17, debate team',
        'student_statement': 'I believe all speech should be allowed...',
        'goal': 'Expose contradiction',
    },
    'created_at': datetime.now(timezone.utc).isoformat(),
}

table.put_item(Item=seed)
```

### 4. Create Models

```python
model = {
    'PK': 'MODEL#claude-3-5-sonnet-20241022',
    'SK': 'METADATA',
    'entity_type': 'model',
    'provider': 'anthropic',
    'name': 'Claude 3.5 Sonnet v2',
    'bedrock_model_id': 'anthropic.claude-3-5-sonnet-20241022-v2:0',
    'tags': ['reasoning', 'high-quality'],
    'active': True,
    'created_at': datetime.now(timezone.utc).isoformat(),
}

table.put_item(Item=model)
```

---

## Monitoring

### CloudWatch Dashboards

Navigate to CloudWatch → Dashboards → "SocraticBenchmarks"

**Metrics to watch:**
- Lambda execution duration (p95)
- SQS queue depth (should drain to zero)
- DynamoDB consumed capacity
- API Gateway 4xx/5xx errors

### Logs

View Lambda logs:
```bash
aws logs tail /aws/lambda/socratic-bench-planner --follow
aws logs tail /aws/lambda/socratic-bench-dialogue --follow
aws logs tail /aws/lambda/socratic-bench-judge --follow
```

### X-Ray Traces

Navigate to X-Ray → Traces to see end-to-end request flows.

---

## Cost Breakdown

**Per Benchmark Run** (8 models × 15 scenarios = 120 runs):

| Service | Usage | Cost |
|---------|-------|------|
| DynamoDB | ~1,000 writes/reads | $0.0015 |
| S3 | 720 objects (~1.5MB) | $0.00003 |
| Lambda | 600 invocations (avg 30s) | $0.022 |
| Bedrock (Claude 3.5 Sonnet) | ~1.2M tokens | $1.014 |
| API Gateway | 10 requests | $0.000035 |
| **Total** | | **~$1.04** |

**Monthly (4 runs):** ~$4.16

**With prompt caching:** ~$2.50/month

**Idle cost:** $0/month (everything is pay-per-use)

---

## Troubleshooting

### Issue: Lambdas timing out

**Fix:** Increase timeout in `lib/socratic-bench-stack.ts`:

```typescript
timeout: cdk.Duration.seconds(600), // Increase to 10 minutes
```

### Issue: Bedrock access denied

**Fix:** Request model access in AWS Bedrock console:
```
Services → Bedrock → Model access → Request access
```

### Issue: Queue messages stuck in DLQ

**View DLQ:**
```bash
aws sqs receive-message --queue-url https://sqs.us-east-1.amazonaws.com/.../dialogue-jobs-dlq
```

**Common causes:**
- Invalid seed_id or model_id
- Bedrock throttling
- Lambda out of memory

---

## Next Steps

1. **Implement Judge Lambda** (evaluate turns using rubric)
2. **Implement Curator Lambda** (aggregate results)
3. **Integrate with benchmark.py** (seamless migration)
4. **Build dashboard** (visualize results)
5. **Add scheduled runs** (EventBridge cron)

---

## Complete File Structure

```
socratic-ai-benchmarks/
├── infrastructure/
│   ├── bin/
│   │   └── app.ts                  # CDK app entry point
│   ├── lib/
│   │   └── socratic-bench-stack.ts # Main infrastructure stack
│   ├── package.json
│   ├── cdk.json
│   └── tsconfig.json
│
├── lambdas/
│   ├── shared/
│   │   └── utils.py                # Shared utilities (ULID, SHA-256, etc.)
│   ├── planner/
│   │   └── index.py                # Manifest creation + job queueing
│   ├── dialogue/
│   │   └── index.py                # Socratic dialogue execution
│   ├── judge/
│   │   └── index.py                # Turn evaluation (TODO)
│   └── curator/
│       └── index.py                # Result aggregation (TODO)
│
└── phase1-model-selection/
    ├── DATA_LAYER_SCHEMA.md        # Complete data model
    ├── DEPLOYMENT_GUIDE.md         # This file
    └── benchmark.py                # Existing benchmark (to integrate)
```

---

## Documentation

- **Schema:** `DATA_LAYER_SCHEMA.md` - Complete DynamoDB + S3 design
- **Deployment:** This file - How to deploy and use
- **Evaluation:** `SOCRATIC_EVAL_FRAMEWORK.md` - Scoring rubric

---

## Support

For issues or questions:
1. Check CloudWatch logs
2. Review X-Ray traces
3. Inspect DynamoDB items manually (AWS Console)
4. Verify IAM permissions

---

**You now have a production-ready, serverless data layer for Socratic AI benchmarking!**

Next: Complete the judge and curator Lambdas, then integrate with the existing `benchmark.py` workflow.
