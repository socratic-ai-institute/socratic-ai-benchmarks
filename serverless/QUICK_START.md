# Quick Start - Socratic Bench Serverless

Get up and running in 10 minutes.

## TL;DR

```bash
# 1. Deploy infrastructure
cd serverless
./scripts/deploy.sh

# 2. Upload config
./scripts/upload-config.sh

# 3. Test run
./scripts/test-run.sh

# 4. Access dashboard
# URL from stack outputs
```

## Prerequisites

✅ AWS account with Bedrock access (Claude 3.5 Sonnet v2, Claude 3.5 Haiku)
✅ AWS CLI configured
✅ Python 3.12+
✅ Node.js 20+
✅ AWS CDK installed (`npm install -g aws-cdk`)

## 5-Minute Deployment

### Step 1: Bootstrap (first time only)

```bash
cdk bootstrap
```

### Step 2: Deploy

```bash
cd serverless/infra
cdk deploy
```

Say "yes" when prompted.

### Step 3: Upload Config

```bash
cd ..
./scripts/upload-config.sh
```

### Step 4: Test

```bash
./scripts/test-run.sh
```

Watch logs:

```bash
aws logs tail /aws/lambda/SocraticBenchStack-RunnerFunction --follow
```

### Step 5: Get Dashboard URL

```bash
aws cloudformation describe-stacks \
  --stack-name SocraticBenchStack \
  --query 'Stacks[0].Outputs[?OutputKey==`UIUrl`].OutputValue' \
  --output text
```

Open URL in browser.

## What You Get

- **Weekly automated runs** (Monday 3 AM UTC)
- **2 models** tested by default (Claude 3.5 Sonnet v2, Haiku)
- **6 scenarios** across 3 Socratic vectors
- **~$2/week** cost (~$8/month)
- **Web dashboard** for viewing results
- **API** for programmatic access

## Architecture

```
EventBridge → Planner → SQS → Runner → SQS → Judge → Curator → DynamoDB/S3 → API → UI
```

## Quick Commands

```bash
# Deploy
./scripts/deploy.sh

# Upload config
./scripts/upload-config.sh

# Test run
./scripts/test-run.sh

# Check queues
./scripts/check-queues.sh

# View logs
aws logs tail /aws/lambda/SocraticBenchStack-RunnerFunction --follow

# Destroy
cd infra && cdk destroy
```

## Customization

Edit `s3://{bucket}/artifacts/config.json`:

```json
{
  "models": [
    {"model_id": "anthropic.claude-3-5-sonnet-20241022-v2:0", "provider": "anthropic"}
  ],
  "scenarios": ["EL-ETH-UTIL-DEON-01", "MAI-BIO-CRISPR-01"],
  "parameters": {"max_turns": 5}
}
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Lambda timeout | Increase timeout in `infra/stack.py` |
| API 403 | Check API key in UI config |
| No data | Check Curator Lambda logs |
| High cost | Reduce models/scenarios in config |

## Next Steps

- Read full deployment guide: `DEPLOYMENT_GUIDE.md`
- Read architecture docs: `README.md`
- Customize scenarios: `lib/socratic_bench/scenarios.py`
- Set up monitoring: CloudWatch dashboards

## Support

- Docs: `serverless/README.md`
- Issues: GitHub repository
- Logs: CloudWatch Logs
