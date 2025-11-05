# Socratic AI Benchmarks - Serverless MVP

Dead-simple, all-Lambda serverless architecture for weekly Socratic AI benchmarking.

## Architecture Overview

```
EventBridge (weekly) → Planner Lambda
                         ↓
                    SQS dialogue-jobs
                         ↓
                    Runner Lambda (parallel)
                         ↓
                    SQS judge-jobs
                         ↓
                    Judge Lambda (parallel)
                         ↓
                    EventBridge run.judged
                         ↓
                    Curator Lambda
                         ↓
                    DynamoDB + S3
                         ↓
                    API Gateway + UI
```

## Components

### Data Layer
- **DynamoDB**: Single table (`socratic_core`) with GSIs
- **S3**: Raw turn data + curated JSON

### Compute Layer
1. **Planner Lambda**: Orchestrates weekly runs
2. **Runner Lambda**: Executes Socratic dialogues
3. **Judge Lambda**: Scores turns with LLM-as-judge
4. **Curator Lambda**: Aggregates and materializes results
5. **Read API Lambda**: Serves data to UI

### UI Layer
- **Static Site**: S3 + CloudFront
- **API**: API Gateway with API key auth

## Prerequisites

- AWS Account with credentials configured
- Python 3.12+
- Node.js 20+ (for CDK)
- AWS CDK CLI (`npm install -g aws-cdk`)
- Bedrock model access (Claude 3.5 Sonnet v2, Claude 3.5 Haiku)

## Quick Start

### 1. Install Dependencies

```bash
# Install CDK dependencies
cd serverless/infra
pip install -r requirements.txt

# Install Lambda layer dependencies
cd ../lib
pip install -r requirements.txt -t python/
```

### 2. Bootstrap CDK (first time only)

```bash
cd serverless/infra
cdk bootstrap
```

### 3. Deploy Infrastructure

```bash
cdk deploy
```

This will:
- Create DynamoDB table + GSIs
- Create S3 buckets (data + UI)
- Create SQS queues
- Create EventBridge rule + custom bus
- Deploy 5 Lambda functions
- Create API Gateway
- Deploy static UI to CloudFront

### 4. Upload Initial Configuration

```bash
# Create default config
cat > /tmp/config.json << EOF
{
  "models": [
    {
      "model_id": "anthropic.claude-3-5-sonnet-20241022-v2:0",
      "provider": "anthropic",
      "temperature": 0.7,
      "max_tokens": 200
    },
    {
      "model_id": "anthropic.claude-3-5-haiku-20241022-v1:0",
      "provider": "anthropic",
      "temperature": 0.7,
      "max_tokens": 200
    }
  ],
  "scenarios": [
    "EL-ETH-UTIL-DEON-01",
    "EL-CIV-FREE-HARM-01",
    "MAI-BIO-CRISPR-01",
    "MAI-ECO-INFL-01",
    "APO-PHY-HEAT-TEMP-01",
    "APO-BIO-GENE-DETERM-01"
  ],
  "parameters": {
    "max_turns": 5,
    "judge_model": "anthropic.claude-3-5-sonnet-20241022-v2:0"
  }
}
EOF

# Upload to S3
BUCKET_NAME=$(aws cloudformation describe-stacks \
  --stack-name SocraticBenchStack \
  --query 'Stacks[0].Outputs[?OutputKey==`BucketName`].OutputValue' \
  --output text)

aws s3 cp /tmp/config.json s3://$BUCKET_NAME/artifacts/config.json
```

### 5. Get API Key and Update UI

```bash
# Get API URL
API_URL=$(aws cloudformation describe-stacks \
  --stack-name SocraticBenchStack \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
  --output text)

# Get API Key
API_KEY_ID=$(aws cloudformation describe-stacks \
  --stack-name SocraticBenchStack \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiKeyId`].OutputValue' \
  --output text)

API_KEY=$(aws apigateway get-api-key --api-key $API_KEY_ID --include-value \
  --query 'value' --output text)

echo "API URL: $API_URL"
echo "API Key: $API_KEY"

# Update UI config
sed -i "s|YOUR_API_GATEWAY_URL|$API_URL|g" ../ui/app.js
sed -i "s|YOUR_API_KEY|$API_KEY|g" ../ui/app.js

# Redeploy UI
cdk deploy
```

### 6. Access the Dashboard

```bash
UI_URL=$(aws cloudformation describe-stacks \
  --stack-name SocraticBenchStack \
  --query 'Stacks[0].Outputs[?OutputKey==`UIUrl`].OutputValue' \
  --output text)

echo "Dashboard: $UI_URL"
open $UI_URL  # macOS
```

## Manual Testing

### Trigger a Run Manually

```bash
# Invoke Planner Lambda
aws lambda invoke \
  --function-name SocraticBenchStack-PlannerFunction \
  --payload '{}' \
  /tmp/planner-response.json

cat /tmp/planner-response.json
```

This will:
1. Create a manifest
2. Enqueue dialogue jobs
3. Run dialogues (Runner Lambdas)
4. Judge turns (Judge Lambdas)
5. Aggregate results (Curator Lambda)
6. Data appears in dashboard

## Cost Estimate (MVP)

### Weekly Run (2 models × 6 scenarios = 12 runs)

**Compute:**
- Planner: $0.00 (1 invocation/week)
- Runner: ~$0.60 (12 runs × 5 turns × ~1s)
- Judge: ~$0.30 (60 turns × ~0.5s)
- Curator: ~$0.02 (12 invocations)

**Bedrock:**
- Runner: ~$0.50 (60 dialogue turns, Claude 3.5 Haiku)
- Judge: ~$0.30 (60 judge calls, Claude 3.5 Sonnet)

**Storage:**
- DynamoDB: ~$0.10/month
- S3: ~$0.05/month (< 1GB)
- CloudFront: ~$0.10/month (minimal traffic)

**Total: ~$2/week or ~$8/month**

## DynamoDB Schema

### Single Table Design

| PK | SK | Type |
|----|----|----|
| `MANIFEST#<id>` | `META` | Manifest metadata |
| `RUN#<run_id>` | `META` | Run metadata |
| `RUN#<run_id>` | `TURN#NNN` | Turn pointer |
| `RUN#<run_id>` | `JUDGE#NNN` | Judge scores |
| `RUN#<run_id>` | `SUMMARY` | Aggregated metrics |
| `WEEK#YYYY-WW#MODEL#<id>` | `SUMMARY` | Weekly aggregate |

**GSI1**: Query by model (`GSI1PK=MODEL#<id>`)
**GSI2**: Query by manifest (`GSI2PK=MANIFEST#<id>`)

## S3 Structure

```
socratic-bench-data-{account}/
├── artifacts/
│   ├── config.json          # Active configuration
│   ├── prompts/             # System prompts
│   └── rubrics/             # Judge rubrics
├── manifests/
│   └── M-YYYYMMDD-{hash}.json
├── raw/
│   └── runs/{run_id}/
│       ├── turn_000.json
│       ├── turn_001.json
│       ├── judge_000.json
│       └── judge_001.json
└── curated/
    ├── runs/{run_id}.json
    └── weekly/YYYY-WW/{model_id}.json
```

## Monitoring

### CloudWatch Logs

```bash
# Planner logs
aws logs tail /aws/lambda/SocraticBenchStack-PlannerFunction --follow

# Runner logs
aws logs tail /aws/lambda/SocraticBenchStack-RunnerFunction --follow

# Judge logs
aws logs tail /aws/lambda/SocraticBenchStack-JudgeFunction --follow
```

### Check Queue Depth

```bash
QUEUE_URL=$(aws sqs get-queue-url --queue-name socratic-dialogue-jobs --query 'QueueUrl' --output text)

aws sqs get-queue-attributes \
  --queue-url $QUEUE_URL \
  --attribute-names ApproximateNumberOfMessages
```

## Cleanup

```bash
cd serverless/infra
cdk destroy

# Manually delete S3 buckets if needed (CDK won't delete non-empty buckets)
```

## Extending

### Add a New Model

Edit `artifacts/config.json` in S3:

```json
{
  "models": [
    {
      "model_id": "anthropic.claude-3-opus-20240229-v1:0",
      "provider": "anthropic",
      "temperature": 0.7,
      "max_tokens": 200
    }
  ]
}
```

### Add a New Scenario

Scenarios are defined in `lib/socratic_bench/scenarios.py`. Add new scenarios there and update the config.

### Change Weekly Schedule

Edit `infra/stack.py`:

```python
weekly_rule = events.Rule(
    self,
    "WeeklyTrigger",
    schedule=events.Schedule.cron(minute="0", hour="3", week_day="MON"),
    #                                                    ^^^^^^^^^^^
    # Change to: day="1" for monthly, or rate(Duration.days(1)) for daily
)
```

## Troubleshooting

### Lambdas Timeout

Increase timeout in `infra/stack.py`:

```python
self.runner_fn = lambda_.Function(
    # ...
    timeout=Duration.minutes(15),  # Increase if needed
)
```

### SQS Messages in DLQ

Check DLQ messages:

```bash
DLQ_URL=$(aws sqs get-queue-url --queue-name socratic-dialogue-dlq --query 'QueueUrl' --output text)

aws sqs receive-message --queue-url $DLQ_URL
```

### API Returns 403

Check API key is correct and included in request headers:

```bash
curl -H "x-api-key: YOUR_API_KEY" $API_URL/weekly
```

## Next Steps

1. **Add More Models**: Test Llama, Mistral, etc.
2. **Multi-Turn Scenarios**: Extend beyond single-turn testing
3. **CSD Scoring**: Add Content-Specific Dimensions (CSD) to judge
4. **Alerting**: Add CloudWatch alarms for failures
5. **CI/CD**: Automate deployments with GitHub Actions

## Architecture Decisions

### Why SQS over Step Functions?

- **Cost**: Free tier covers 1M requests/month
- **Simplicity**: No state machine JSON
- **Durability**: Built-in retries + DLQ
- **Concurrency**: Natural throttling with reserved concurrency

### Why Single Table DynamoDB?

- **Cost**: One table = one billable entity
- **Simplicity**: Fewer connections, simpler permissions
- **Performance**: GSIs enable flexible queries
- **Standard practice**: Recommended by AWS for serverless

### Why Lambda Layers for Shared Code?

- **DRY**: Single source of truth for `socratic_bench` library
- **Versioning**: Layer versions enable safe rollouts
- **Size**: Keep Lambda packages small
- **Reuse**: CLI and Lambdas use same code

## License

Research code. License TBD pending publication.
