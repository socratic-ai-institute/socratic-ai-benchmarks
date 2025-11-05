# Socratic Bench - Complete Deployment Guide

Step-by-step guide to deploy the serverless Socratic AI benchmarking platform.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [AWS Setup](#aws-setup)
3. [Local Setup](#local-setup)
4. [Deployment](#deployment)
5. [Configuration](#configuration)
6. [Testing](#testing)
7. [Monitoring](#monitoring)
8. [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Tools

- **AWS CLI** (v2.x): `aws --version`
- **Python** (3.12+): `python3 --version`
- **Node.js** (20+): `node --version`
- **AWS CDK** (2.120+): `cdk --version`

### Install Missing Tools

```bash
# AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Node.js (via nvm)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
nvm install 20

# AWS CDK
npm install -g aws-cdk@latest

# Verify
aws --version
python3 --version
node --version
cdk --version
```

## AWS Setup

### 1. Configure AWS Credentials

```bash
# Configure default profile
aws configure

# Or use named profile
aws configure --profile mvp
export AWS_PROFILE=mvp
```

**Required information:**
- AWS Access Key ID
- AWS Secret Access Key
- Default region: `us-east-1` (recommended)
- Default output format: `json`

### 2. Request Bedrock Model Access

1. Go to AWS Console → Bedrock → Model Access
2. Request access for:
   - **Claude 3.5 Sonnet v2** (required for judge)
   - **Claude 3.5 Haiku** (recommended for cost-effective runs)
   - **Claude 3 Opus** (optional, for quality comparison)

3. Wait for approval (usually instant, sometimes 1-2 hours)

4. Verify access:

```bash
aws bedrock list-foundation-models \
  --region us-east-1 \
  --query 'modelSummaries[?contains(modelId, `claude`)].modelId'
```

### 3. Check IAM Permissions

Your AWS user/role needs:
- CloudFormation full access
- Lambda full access
- DynamoDB full access
- S3 full access
- SQS full access
- EventBridge full access
- API Gateway full access
- CloudFront full access
- IAM role creation
- Bedrock InvokeModel permission

**Quick check:**

```bash
aws sts get-caller-identity
```

## Local Setup

### 1. Clone Repository

```bash
git clone <your-repo-url>
cd socratic-ai-benchmarks/serverless
```

### 2. Install Dependencies

```bash
# CDK dependencies
cd infra
pip install -r requirements.txt

# Verify
cdk doctor
```

### 3. Bootstrap CDK (first time only)

```bash
cdk bootstrap aws://ACCOUNT-ID/us-east-1

# Or let CDK detect account
cdk bootstrap
```

This creates the CDK toolkit stack (S3 bucket for assets, IAM roles, etc.).

## Deployment

### Option A: Automated Script

```bash
cd serverless
./scripts/deploy.sh
```

This will:
1. Install dependencies
2. Synthesize CloudFormation
3. Deploy entire stack
4. Save outputs to `outputs.json`

### Option B: Manual Steps

```bash
cd serverless/infra

# Preview changes
cdk diff

# Deploy
cdk deploy

# Approve changes when prompted
```

### Deployment Time

- First deployment: ~10-15 minutes
- Subsequent deployments: ~3-5 minutes

### What Gets Created

| Resource | Count | Purpose |
|----------|-------|---------|
| DynamoDB Tables | 1 | `socratic_core` with 2 GSIs |
| S3 Buckets | 2 | Data bucket + UI bucket |
| Lambda Functions | 5 | Planner, Runner, Judge, Curator, API |
| SQS Queues | 4 | 2 main queues + 2 DLQs |
| EventBridge | 2 | Weekly cron + custom bus |
| API Gateway | 1 | REST API with 3 routes |
| CloudFront Distribution | 1 | Serves static UI |
| IAM Roles | 5 | One per Lambda |
| Lambda Layer | 1 | Shared `socratic_bench` library |

## Configuration

### 1. Upload Initial Config

```bash
./scripts/upload-config.sh
```

This uploads default config to `s3://{bucket}/artifacts/config.json`.

### 2. Customize Config (Optional)

```bash
# Download current config
BUCKET=$(aws cloudformation describe-stacks \
  --stack-name SocraticBenchStack \
  --query 'Stacks[0].Outputs[?OutputKey==`BucketName`].OutputValue' \
  --output text)

aws s3 cp s3://$BUCKET/artifacts/config.json config.json

# Edit config.json
nano config.json

# Upload modified config
aws s3 cp config.json s3://$BUCKET/artifacts/config.json
```

**Config structure:**

```json
{
  "models": [
    {
      "model_id": "anthropic.claude-3-5-sonnet-20241022-v2:0",
      "provider": "anthropic",
      "temperature": 0.7,
      "max_tokens": 200
    }
  ],
  "scenarios": [
    "EL-ETH-UTIL-DEON-01",
    "MAI-BIO-CRISPR-01"
  ],
  "parameters": {
    "max_turns": 5,
    "judge_model": "anthropic.claude-3-5-sonnet-20241022-v2:0"
  }
}
```

### 3. Update UI Configuration

The UI needs the API URL and API key. Get them from stack outputs:

```bash
# Get outputs
aws cloudformation describe-stacks \
  --stack-name SocraticBenchStack \
  --query 'Stacks[0].Outputs[*].[OutputKey,OutputValue]' \
  --output table

# Or use jq
./scripts/get-ui-config.sh
```

Manually update `ui/app.js`:

```javascript
const CONFIG = {
    apiUrl: 'https://xxxxx.execute-api.us-east-1.amazonaws.com/prod',
    apiKey: 'xxxxx',
};
```

Then redeploy:

```bash
cdk deploy
```

## Testing

### 1. Manual Test Run

Trigger a single benchmark run:

```bash
./scripts/test-run.sh
```

This invokes the Planner Lambda, which:
1. Reads config
2. Creates manifest
3. Enqueues dialogue jobs
4. Runner Lambdas execute dialogues
5. Judge Lambdas score turns
6. Curator Lambda aggregates results

### 2. Monitor Progress

```bash
# Watch Planner logs
aws logs tail /aws/lambda/SocraticBenchStack-PlannerFunction --follow

# Watch Runner logs
aws logs tail /aws/lambda/SocraticBenchStack-RunnerFunction --follow

# Watch Judge logs
aws logs tail /aws/lambda/SocraticBenchStack-JudgeFunction --follow

# Check queue depths
./scripts/check-queues.sh
```

### 3. Check Results

**Via API:**

```bash
API_URL=$(aws cloudformation describe-stacks \
  --stack-name SocraticBenchStack \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
  --output text)

API_KEY=$(aws cloudformation describe-stacks \
  --stack-name SocraticBenchStack \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiKeyId`].OutputValue' \
  --output text)

API_KEY=$(aws apigateway get-api-key --api-key $API_KEY --include-value --query 'value' --output text)

# Get weekly data
curl -H "x-api-key: $API_KEY" "$API_URL/weekly"
```

**Via DynamoDB:**

```bash
# List recent runs
aws dynamodb scan \
  --table-name socratic_core \
  --filter-expression "begins_with(PK, :prefix)" \
  --expression-attribute-values '{":prefix":{"S":"RUN#"}}' \
  --max-items 10
```

**Via S3:**

```bash
# List curated runs
aws s3 ls s3://$BUCKET/curated/runs/

# View a run summary
aws s3 cp s3://$BUCKET/curated/runs/{run_id}.json - | jq .
```

### 4. Access Dashboard

```bash
UI_URL=$(aws cloudformation describe-stacks \
  --stack-name SocraticBenchStack \
  --query 'Stacks[0].Outputs[?OutputKey==`UIUrl`].OutputValue' \
  --output text)

echo "Dashboard: $UI_URL"
open $UI_URL  # macOS
```

## Monitoring

### CloudWatch Dashboards

Create a custom dashboard:

```bash
aws cloudwatch put-dashboard \
  --dashboard-name SocraticBench \
  --dashboard-body file://dashboards/cloudwatch.json
```

### Alarms

Set up alarms for:

```bash
# Lambda errors
aws cloudwatch put-metric-alarm \
  --alarm-name SocraticBench-RunnerErrors \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 1

# DLQ depth
aws cloudwatch put-metric-alarm \
  --alarm-name SocraticBench-DLQDepth \
  --metric-name ApproximateNumberOfMessagesVisible \
  --namespace AWS/SQS \
  --statistic Average \
  --period 300 \
  --threshold 1 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 1
```

## Troubleshooting

### Lambda Timeout

**Symptom:** Runner or Judge Lambdas timing out

**Fix:** Increase timeout in `infra/stack.py`:

```python
self.runner_fn = lambda_.Function(
    # ...
    timeout=Duration.minutes(15),  # Increase from default
)
```

Redeploy: `cdk deploy`

### SQS Messages in DLQ

**Symptom:** Messages appearing in dead-letter queue

**Check:**

```bash
./scripts/check-queues.sh

# View DLQ messages
DLQ_URL=$(aws sqs get-queue-url --queue-name socratic-dialogue-dlq --query 'QueueUrl' --output text)

aws sqs receive-message --queue-url $DLQ_URL
```

**Common causes:**
- Bedrock throttling (increase reserved concurrency)
- Invalid scenario IDs
- Missing Bedrock permissions

### API Returns 403

**Symptom:** `{"message":"Forbidden"}`

**Fix:** Check API key:

```bash
# Verify API key in request
curl -v -H "x-api-key: YOUR_KEY" "$API_URL/weekly"

# Regenerate API key if needed
aws apigateway create-api-key \
  --name SocraticBenchApiKey \
  --enabled
```

### No Data in Dashboard

**Symptom:** Dashboard shows "No data for this week"

**Check:**

1. Has a run completed?

```bash
aws dynamodb scan \
  --table-name socratic_core \
  --filter-expression "begins_with(PK, :prefix)" \
  --expression-attribute-values '{":prefix":{"S":"WEEK#"}}'
```

2. Check Curator Lambda logs:

```bash
aws logs tail /aws/lambda/SocraticBenchStack-CuratorFunction --follow
```

3. Manually trigger run:

```bash
./scripts/test-run.sh
```

### Cost Overruns

**Symptom:** Unexpected AWS charges

**Check:**

```bash
# View cost by service
aws ce get-cost-and-usage \
  --time-period Start=2025-11-01,End=2025-11-30 \
  --granularity MONTHLY \
  --metrics UnblendedCost \
  --group-by Type=SERVICE
```

**Mitigation:**
- Reduce model count in config
- Reduce scenario count
- Decrease weekly run frequency
- Set reserved concurrency lower

## Cleanup

### Full Cleanup

```bash
cd serverless/infra
cdk destroy

# Confirm deletion when prompted
```

### Partial Cleanup (Keep Data)

Keep S3 buckets, delete compute:

```bash
# Disable EventBridge rule (stop weekly runs)
aws events disable-rule --name SocraticBenchStack-WeeklyTrigger

# Delete Lambda functions only
aws lambda delete-function --function-name SocraticBenchStack-PlannerFunction
aws lambda delete-function --function-name SocraticBenchStack-RunnerFunction
aws lambda delete-function --function-name SocraticBenchStack-JudgeFunction
aws lambda delete-function --function-name SocraticBenchStack-CuratorFunction
aws lambda delete-function --function-name SocraticBenchStack-ApiFunction
```

## Next Steps

1. **Schedule Weekly Runs**: EventBridge rule runs every Monday at 3 AM UTC
2. **Add More Models**: Edit config to test additional models
3. **Extend Scenarios**: Add scenarios in `lib/socratic_bench/scenarios.py`
4. **Set Up Alerts**: Configure CloudWatch alarms for failures
5. **CI/CD**: Automate deployments with GitHub Actions

## Support

- **Documentation**: See `README.md` in `serverless/`
- **Logs**: Check CloudWatch Logs for each Lambda
- **Issues**: File issues on GitHub repository

---

**Deployment Status Checklist:**

- [ ] AWS credentials configured
- [ ] Bedrock access approved
- [ ] CDK bootstrapped
- [ ] Stack deployed successfully
- [ ] Config uploaded to S3
- [ ] UI config updated
- [ ] Manual test run completed
- [ ] Dashboard accessible
- [ ] Weekly cron enabled
