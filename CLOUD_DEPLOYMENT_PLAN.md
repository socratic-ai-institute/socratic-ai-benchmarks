# Cloud Deployment Plan: Automated Weekly Socratic AI Benchmarking

**Objective**: Deploy end-to-end serverless infrastructure for automated weekly testing of 25 models with cost tracking

**Current State**: ✅ Phase 1 complete (local testing, 25 models evaluated)
**Target State**: ☁️ Phase 2 deployed (fully automated weekly runs, public dashboard, cost tracking)

---

## Architecture Overview

```
EventBridge (weekly cron)
    ↓
Planner Lambda → Creates manifest, enqueues 25 models × scenarios
    ↓
SQS dialogue-jobs (fan-out to 50 jobs)
    ↓
Runner Lambda (25 parallel) → Executes Socratic dialogues via Bedrock
    ↓
SQS judge-jobs (fan-out to 250 turns)
    ↓
Judge Lambda (25 parallel) → Scores turns with LLM-as-judge + cost tracking
    ↓
EventBridge run.judged event
    ↓
Curator Lambda → Aggregates results + calculates total costs
    ↓
DynamoDB + S3 (results + cost data)
    ↓
API Gateway + Read Lambda
    ↓
CloudFront Static UI (comprehensive dashboard with cost charts)
```

---

## Deployment Steps

### Phase 1: Prerequisites ✅ (10 minutes)

**Check AWS Setup**:
```bash
cd /Users/williamprior/Development/GitHub/socratic-ai-benchmarks/serverless

# Verify tools
aws --version        # Need v2.x
python3 --version    # Need 3.12+
node --version       # Need 20+
cdk --version        # Need 2.120+

# Verify AWS credentials
aws sts get-caller-identity --profile mvp

# Verify Bedrock access
aws bedrock list-foundation-models --region us-east-1 --profile mvp \
  --query 'modelSummaries[?contains(modelId, `claude`)].modelId'
```

**Expected Output**: Should see Claude models available

---

### Phase 2: Configuration Update (15 minutes)

**Update config with 25 tested models**:

Create `serverless/config-25-models.json`:

```json
{
  "models": [
    {"model_id": "anthropic.claude-sonnet-4-5-20250929-v1:0", "name": "Claude Sonnet 4.5", "cost_per_1k_input": 0.003, "cost_per_1k_output": 0.015},
    {"model_id": "meta.llama4-maverick-17b-instruct-v1:0", "name": "Llama 4 Maverick", "cost_per_1k_input": 0.0001, "cost_per_1k_output": 0.0003},
    {"model_id": "meta.llama4-scout-17b-instruct-v1:0", "name": "Llama 4 Scout", "cost_per_1k_input": 0.0001, "cost_per_1k_output": 0.0003},
    {"model_id": "amazon.nova-lite-v1:0", "name": "Amazon Nova Lite", "cost_per_1k_input": 0.00006, "cost_per_1k_output": 0.00024},
    {"model_id": "meta.llama3-1-70b-instruct-v1:0", "name": "Llama 3.1 70B", "cost_per_1k_input": 0.00026, "cost_per_1k_output": 0.00035},
    {"model_id": "meta.llama3-2-90b-instruct-v1:0", "name": "Llama 3.2 90B", "cost_per_1k_input": 0.00027, "cost_per_1k_output": 0.00035},
    {"model_id": "ai21.jamba-1-5-large-v1:0", "name": "AI21 Jamba 1.5 Large", "cost_per_1k_input": 0.0002, "cost_per_1k_output": 0.0004},
    {"model_id": "anthropic.claude-opus-4-1-20250805-v1:0", "name": "Claude Opus 4.1", "cost_per_1k_input": 0.015, "cost_per_1k_output": 0.075},
    {"model_id": "amazon.nova-premier-v1:0", "name": "Amazon Nova Premier", "cost_per_1k_input": 0.0008, "cost_per_1k_output": 0.0032},
    {"model_id": "cohere.command-r-v1:0", "name": "Cohere Command R", "cost_per_1k_input": 0.00015, "cost_per_1k_output": 0.0006},
    {"model_id": "anthropic.claude-3-7-sonnet-20250219-v1:0", "name": "Claude 3.7 Sonnet", "cost_per_1k_input": 0.003, "cost_per_1k_output": 0.015},
    {"model_id": "amazon.nova-pro-v1:0", "name": "Amazon Nova Pro", "cost_per_1k_input": 0.0008, "cost_per_1k_output": 0.0032},
    {"model_id": "anthropic.claude-3-5-haiku-20241022-v1:0", "name": "Claude 3.5 Haiku", "cost_per_1k_input": 0.0008, "cost_per_1k_output": 0.004},
    {"model_id": "cohere.command-r-plus-v1:0", "name": "Cohere Command R+", "cost_per_1k_input": 0.0003, "cost_per_1k_output": 0.0015},
    {"model_id": "qwen.qwen3-32b-v1:0", "name": "Qwen3 32B", "cost_per_1k_input": 0.00015, "cost_per_1k_output": 0.0003},
    {"model_id": "anthropic.claude-3-5-sonnet-20240620-v1:0", "name": "Claude 3.5 Sonnet", "cost_per_1k_input": 0.003, "cost_per_1k_output": 0.015},
    {"model_id": "mistral.mistral-large-2402-v1:0", "name": "Mistral Large", "cost_per_1k_input": 0.0002, "cost_per_1k_output": 0.0006},
    {"model_id": "meta.llama3-3-70b-instruct-v1:0", "name": "Llama 3.3 70B", "cost_per_1k_input": 0.00026, "cost_per_1k_output": 0.00035},
    {"model_id": "mistral.mixtral-8x7b-instruct-v0:1", "name": "Mixtral 8x7B", "cost_per_1k_input": 0.00015, "cost_per_1k_output": 0.0002},
    {"model_id": "anthropic.claude-haiku-4-5-20251001-v1:0", "name": "Claude Haiku 4.5", "cost_per_1k_input": 0.0008, "cost_per_1k_output": 0.004},
    {"model_id": "deepseek.r1-v1:0", "name": "DeepSeek R1", "cost_per_1k_input": 0.00014, "cost_per_1k_output": 0.00028},
    {"model_id": "anthropic.claude-3-sonnet-20240229-v1:0", "name": "Claude 3 Sonnet", "cost_per_1k_input": 0.003, "cost_per_1k_output": 0.015},
    {"model_id": "openai.gpt-oss-120b-1:0", "name": "OpenAI GPT-OSS 120B", "cost_per_1k_input": 0.0002, "cost_per_1k_output": 0.0004},
    {"model_id": "meta.llama3-2-11b-instruct-v1:0", "name": "Llama 3.2 11B", "cost_per_1k_input": 0.00016, "cost_per_1k_output": 0.00016},
    {"model_id": "anthropic.claude-3-opus-20240229-v1:0", "name": "Claude 3 Opus", "cost_per_1k_input": 0.015, "cost_per_1k_output": 0.075}
  ],
  "scenarios": [
    "CONSISTENCY-LEADERSHIP-01",
    "CONSISTENCY-PRODUCTIVITY-01"
  ],
  "parameters": {
    "max_turns": 5,
    "judge_model": "anthropic.claude-3-5-sonnet-20241022-v2:0",
    "temperature": 0.7,
    "max_tokens": 500
  }
}
```

---

### Phase 3: Add Cost Tracking (30 minutes)

**Update Lambda functions to track costs**:

1. **Update `serverless/lambdas/runner/handler.py`**:
   - Add token counting
   - Calculate costs per model
   - Store in turn metadata

2. **Update `serverless/lambdas/curator/handler.py`**:
   - Aggregate costs across all runs
   - Store weekly cost summaries
   - Calculate cost per model per scenario

3. **Update `serverless/lib/socratic_bench/models.py`**:
   - Add cost calculation utilities
   - Track input/output tokens
   - Log costs to CloudWatch

---

### Phase 4: Deploy Infrastructure (20 minutes)

```bash
cd /Users/williamprior/Development/GitHub/socratic-ai-benchmarks/serverless/infra

# Install CDK dependencies
pip install -r requirements.txt

# Bootstrap CDK (first time only)
export AWS_PROFILE=mvp
cdk bootstrap

# Deploy stack
cdk deploy --require-approval never

# Outputs will show:
# - API Gateway URL
# - CloudFront UI URL
# - S3 bucket names
# - Lambda function names
```

**Resources Created**:
- ✅ 5 Lambda functions (Planner, Runner, Judge, Curator, API)
- ✅ 2 SQS queues + DLQs
- ✅ 1 DynamoDB table with 2 GSIs
- ✅ 2 S3 buckets (data + UI)
- ✅ 1 EventBridge rule (weekly cron)
- ✅ 1 API Gateway with API key
- ✅ 1 CloudFront distribution

---

### Phase 5: Upload Configuration (10 minutes)

```bash
# Get bucket name from stack outputs
BUCKET_NAME=$(aws cloudformation describe-stacks \
  --stack-name SocraticBenchStack \
  --profile mvp \
  --query 'Stacks[0].Outputs[?OutputKey==`DataBucketName`].OutputValue' \
  --output text)

# Upload config
aws s3 cp config-25-models.json s3://$BUCKET_NAME/artifacts/config.json --profile mvp

# Upload test scenarios
aws s3 cp ../phase1-model-selection/socratic_eval/context_growth/test_scenarios.py \
  s3://$BUCKET_NAME/artifacts/scenarios/ --profile mvp

# Verify upload
aws s3 ls s3://$BUCKET_NAME/artifacts/ --profile mvp --recursive
```

---

### Phase 6: Deploy Dashboard to CloudFront (15 minutes)

```bash
# Update dashboard with API endpoint
API_URL=$(aws cloudformation describe-stacks \
  --stack-name SocraticBenchStack \
  --profile mvp \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
  --output text)

API_KEY_ID=$(aws cloudformation describe-stacks \
  --stack-name SocraticBenchStack \
  --profile mvp \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiKeyId`].OutputValue' \
  --output text)

API_KEY=$(aws apigateway get-api-key \
  --api-key $API_KEY_ID \
  --include-value \
  --profile mvp \
  --query 'value' \
  --output text)

# Copy comprehensive dashboard to UI directory
cp /Users/williamprior/Development/GitHub/socratic-ai-benchmarks/comprehensive_dashboard.html \
   serverless/ui/index.html

# Update API config in dashboard
sed -i "s|YOUR_API_URL|$API_URL|g" serverless/ui/index.html
sed -i "s|YOUR_API_KEY|$API_KEY|g" serverless/ui/index.html

# Upload to S3
UI_BUCKET=$(aws cloudformation describe-stacks \
  --stack-name SocraticBenchStack \
  --profile mvp \
  --query 'Stacks[0].Outputs[?OutputKey==`UIBucketName`].OutputValue' \
  --output text)

aws s3 sync serverless/ui/ s3://$UI_BUCKET/ --profile mvp

# Get CloudFront URL
DASHBOARD_URL=$(aws cloudformation describe-stacks \
  --stack-name SocraticBenchStack \
  --profile mvp \
  --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontUrl`].OutputValue' \
  --output text)

echo "🎉 Dashboard available at: $DASHBOARD_URL"
```

---

### Phase 7: Configure Weekly Automation (5 minutes)

**EventBridge rule is already deployed** (Monday 3am UTC)

To change schedule, edit `serverless/infra/stack.py`:

```python
weekly_rule = events.Rule(
    self,
    "WeeklyTrigger",
    schedule=events.Schedule.cron(
        minute="0",
        hour="3",     # 3am UTC
        week_day="MON"  # Every Monday
    ),
    targets=[targets.LambdaFunction(self.planner_fn)]
)
```

Then redeploy: `cdk deploy`

---

### Phase 8: Test End-to-End (30 minutes)

```bash
# Trigger manual run
aws lambda invoke \
  --function-name SocraticBenchStack-PlannerFunction \
  --profile mvp \
  --payload '{}' \
  /tmp/planner-response.json

cat /tmp/planner-response.json

# Monitor progress
aws logs tail /aws/lambda/SocraticBenchStack-RunnerFunction \
  --profile mvp \
  --follow

# Check SQS queue depth
QUEUE_URL=$(aws sqs get-queue-url \
  --queue-name socratic-dialogue-jobs \
  --profile mvp \
  --query 'QueueUrl' \
  --output text)

aws sqs get-queue-attributes \
  --queue-url $QUEUE_URL \
  --profile mvp \
  --attribute-names ApproximateNumberOfMessages

# Wait ~10-15 minutes for completion
# Then check dashboard at $DASHBOARD_URL
```

---

### Phase 9: Cost Monitoring (15 minutes)

**Set up CloudWatch Cost Alarms**:

```bash
# Create alarm for weekly costs exceeding $20
aws cloudwatch put-metric-alarm \
  --alarm-name socratic-bench-weekly-cost \
  --profile mvp \
  --alarm-description "Alert if weekly benchmark costs exceed $20" \
  --metric-name EstimatedCharges \
  --namespace AWS/Billing \
  --statistic Maximum \
  --period 86400 \
  --evaluation-periods 1 \
  --threshold 20.0 \
  --comparison-operator GreaterThanThreshold

# Create custom metric for Bedrock costs
# (This will be logged by Lambda functions)
```

**Add cost dashboard**:

```bash
# Create CloudWatch dashboard
aws cloudwatch put-dashboard \
  --dashboard-name SocraticBenchCosts \
  --profile mvp \
  --dashboard-body file://cloudwatch-dashboard.json
```

---

## Cost Estimates

### Weekly Run (25 models × 2 scenarios = 50 runs)

**Bedrock API Costs** (largest component):
- Claude Sonnet 4.5: ~$0.45 (2 runs × 5 turns × ~500 tokens × $0.009/1k)
- Claude Opus 4.1: ~$2.25 (2 runs × 5 turns × ~500 tokens × $0.045/1k)
- Llama models: ~$0.50 (6 models × 2 runs × 5 turns × ~$0.001/1k avg)
- Nova models: ~$0.40 (3 models × 2 runs × 5 turns × ~$0.0008/1k avg)
- Other models: ~$1.40 (14 models × varying costs)

**Subtotal Bedrock: ~$5.00/week**

**Judge Calls** (250 turns × Claude Sonnet):
- ~$2.25 (250 turns × ~500 tokens × $0.009/1k)

**AWS Services**:
- Lambda: ~$0.20 (250 invocations × 2s avg × $0.0000166667/GB-s)
- DynamoDB: ~$0.10/week (500 writes, 100 reads)
- S3: ~$0.05/week (<100MB)
- CloudFront: ~$0.10/week (minimal traffic)
- SQS: $0.00 (free tier)
- EventBridge: $0.00 (free tier)
- API Gateway: ~$0.05/week (minimal requests)

**Total Weekly Cost: ~$7.75**
**Total Monthly Cost: ~$31**

### Cost Breakdown by Model (per week):

| Model | Runs | Cost/Run | Weekly Cost |
|-------|------|----------|-------------|
| Claude Opus 4.1 | 2 | $1.125 | $2.25 |
| Claude Sonnet 4.5 | 2 | $0.225 | $0.45 |
| Claude 3 Opus | 2 | $1.125 | $2.25 |
| **All Llama models** | 12 | $0.04 avg | $0.48 |
| **All Nova models** | 6 | $0.07 avg | $0.42 |
| **All other models** | 26 | $0.05 avg | $1.30 |
| **Judge (Sonnet)** | 250 | $0.009 | $2.25 |

**Savings Opportunity**:
- Remove Claude 3 Opus (worst performer, $2.25/week)
- Use cheaper models for initial screening
- **Potential savings: ~$2.25/week or ~$9/month**

---

## Deployment Timeline

| Phase | Duration | Status |
|-------|----------|--------|
| Prerequisites check | 10 min | ⏸️ Pending |
| Configuration update | 15 min | ⏸️ Pending |
| Cost tracking integration | 30 min | ⏸️ Pending |
| Infrastructure deployment | 20 min | ⏸️ Pending |
| Config upload | 10 min | ⏸️ Pending |
| Dashboard deployment | 15 min | ⏸️ Pending |
| Weekly automation | 5 min | ⏸️ Pending |
| End-to-end test | 30 min | ⏸️ Pending |
| Cost monitoring | 15 min | ⏸️ Pending |
| **Total** | **~2.5 hours** | ⏸️ Ready to execute |

---

## Post-Deployment Monitoring

### Week 1 Checklist:
- ✅ Verify weekly cron triggers successfully
- ✅ Monitor Lambda errors/timeouts
- ✅ Verify all 25 models complete successfully
- ✅ Check actual costs vs. estimates
- ✅ Validate dashboard updates with new data
- ✅ Set cost alarms if actuals differ from estimates

### Ongoing Maintenance:
- **Weekly**: Review cost report in dashboard
- **Monthly**: Analyze model performance trends
- **Quarterly**: Re-evaluate model selection based on scores
- **As needed**: Add new models when released

---

## Risk Mitigation

### Potential Issues:

1. **Bedrock Throttling** (25 models × parallel calls)
   - **Mitigation**: SQS with reserved concurrency (5-10 concurrent Lambdas)
   - **Fallback**: Increase SQS visibility timeout

2. **Cost Overrun** (if models generate more tokens than expected)
   - **Mitigation**: CloudWatch alarm at $20/week
   - **Fallback**: Lambda env var for max_tokens hard limit

3. **Lambda Timeout** (complex scenarios)
   - **Mitigation**: 15-minute timeout
   - **Fallback**: DLQ captures failures for retry

4. **Model Access Denied** (Bedrock permissions)
   - **Mitigation**: Pre-deployment access verification
   - **Fallback**: Skip unavailable models, log error

---

## Success Criteria

✅ **Infrastructure deployed successfully** - All CloudFormation resources created
✅ **Manual test run completes** - All 25 models evaluated, results in DynamoDB
✅ **Dashboard accessible** - Public CloudFront URL displays results
✅ **Weekly automation works** - EventBridge triggers Monday 3am
✅ **Costs within budget** - Weekly costs <$10
✅ **No errors in logs** - Clean Lambda execution

---

## Next Steps After Deployment

1. **Optimize costs**:
   - Remove poorly performing expensive models (Claude 3 Opus)
   - Test if smaller/cheaper models maintain quality

2. **Expand testing**:
   - Add complexity, ambiguity, interrupt tests (5 total test types)
   - Add fidelity tests (15 context-specific scenarios)

3. **Improve cognitive depth**:
   - Test few-shot prompting with Socratic examples
   - Evaluate chain-of-thought prompting
   - Compare different system prompt variations

4. **Add alerting**:
   - Slack/Email notifications on failures
   - Weekly summary email with top performers

5. **Scale for production**:
   - Add more models as they're released
   - Increase test coverage
   - Add A/B testing for prompt variations

---

**Ready to execute?** Start with Phase 1 (Prerequisites check) and work through sequentially.

**Estimated Total Time**: 2.5 hours
**Estimated Weekly Cost**: $7.75
**Estimated Monthly Cost**: $31
