# Deployment Checklist

**AWS Socratic Benchmark System**

Use this checklist to deploy the system from scratch.

---

## Phase 1: Prerequisites (15 minutes)

- [ ] **AWS Account** with admin access
- [ ] **AWS CLI** installed and configured (`aws --version` ≥ 2.x)
- [ ] **AWS CDK** installed (`npm install -g aws-cdk`)
- [ ] **Python 3.12+** installed
- [ ] **Docker** installed and running
- [ ] **Bedrock Model Access**:
  - [ ] Claude 3.5 Sonnet
  - [ ] Claude 3 Opus (judge)
  - [ ] Llama 3.1 70B
  - [ ] Mistral Large
  - [ ] (Optional) Other models to test
- [ ] **IAM Permissions**:
  - [ ] S3: Create bucket, Put/Get objects, Set lifecycle
  - [ ] DynamoDB: Create tables, Put/Get items
  - [ ] Batch: Create job definitions/queues, Submit jobs
  - [ ] Step Functions: Create state machines
  - [ ] Lambda: Create functions
  - [ ] EventBridge: Create rules
  - [ ] ECR: Create repositories, Push images
  - [ ] CloudWatch: Create log groups, Put metrics
  - [ ] SNS: Create topics, Publish
  - [ ] Athena: Create databases/tables, Run queries
  - [ ] Glue: Create databases/tables
  - [ ] QuickSight: Create data sources/dashboards

---

## Phase 2: Infrastructure Setup (30 minutes)

### S3 Bucket

- [ ] Create bucket:
  ```bash
  aws s3 mb s3://socratic-bench --region us-east-1
  ```

- [ ] Enable versioning:
  ```bash
  aws s3api put-bucket-versioning \
    --bucket socratic-bench \
    --versioning-configuration Status=Enabled
  ```

- [ ] Enable encryption:
  ```bash
  aws s3api put-bucket-encryption \
    --bucket socratic-bench \
    --server-side-encryption-configuration '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'
  ```

- [ ] Apply bucket policy (see `infrastructure/iam_policies.json`)

- [ ] Create lifecycle rules (see `infrastructure/s3_layout.md`)

### DynamoDB Tables

- [ ] Review schemas: `infrastructure/dynamodb_tables.md`

- [ ] Deploy via CDK (recommended) OR manually:
  ```bash
  # Runs table
  aws dynamodb create-table \
    --table-name SocraticBench-Runs \
    --attribute-definitions \
      AttributeName=run_id,AttributeType=S \
      AttributeName=model_phase_seed_temp,AttributeType=S \
      AttributeName=week,AttributeType=S \
      AttributeName=half_life_turn,AttributeType=N \
    --key-schema \
      AttributeName=run_id,KeyType=HASH \
      AttributeName=model_phase_seed_temp,KeyType=RANGE \
    --billing-mode PAY_PER_REQUEST \
    --global-secondary-indexes ... # (see dynamodb_tables.md)
  ```

- [ ] **WeeklySummary** table (see dynamodb_tables.md)
- [ ] **CalibrationResults** table (see dynamodb_tables.md)

### ECR Repositories

- [ ] Create repositories:
  ```bash
  aws ecr create-repository --repository-name socratic-runner
  aws ecr create-repository --repository-name socratic-judge
  aws ecr create-repository --repository-name socratic-canary
  ```

- [ ] Authenticate Docker:
  ```bash
  aws ecr get-login-password --region us-east-1 | \
    docker login --username AWS --password-stdin ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com
  ```

---

## Phase 3: Build & Push Containers (20 minutes)

### Runner Container

- [ ] Build:
  ```bash
  cd aws-benchmark-system/runners/
  docker build -t socratic-runner:v1.0 .
  ```

- [ ] Tag & push:
  ```bash
  docker tag socratic-runner:v1.0 ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/socratic-runner:v1.0
  docker push ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/socratic-runner:v1.0
  ```

### Judge Container

- [ ] Build:
  ```bash
  cd aws-benchmark-system/judges/
  docker build -t socratic-judge:v1.0 .
  ```

- [ ] Tag & push:
  ```bash
  docker tag socratic-judge:v1.0 ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/socratic-judge:v1.0
  docker push ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/socratic-judge:v1.0
  ```

---

## Phase 4: Lambda Functions (15 minutes)

Package and deploy Lambda functions (if not using CDK):

- [ ] **FetchConfig**: Reads manifest from S3
- [ ] **GenerateRuns**: Creates run matrix
- [ ] **HeuristicFilter**: Pre-filters turns
- [ ] **Aggregator**: Computes summaries
- [ ] **Alerts**: Checks thresholds
- [ ] **MetricsPublisher**: Publishes CloudWatch EMF

**Recommended**: Use CDK for Lambda deployment (auto-bundles dependencies)

---

## Phase 5: Batch Job Definitions (10 minutes)

- [ ] Create Fargate compute environment:
  ```bash
  aws batch create-compute-environment \
    --compute-environment-name socratic-fargate \
    --type MANAGED \
    --compute-resources type=FARGATE,maxvCpus=256,subnets=[...],securityGroupIds=[...]
  ```

- [ ] Create job queues:
  ```bash
  aws batch create-job-queue \
    --job-queue-name socratic-runner-queue \
    --priority 100 \
    --compute-environment-order order=1,computeEnvironment=socratic-fargate

  aws batch create-job-queue \
    --job-queue-name socratic-judge-queue \
    --priority 50 \
    --compute-environment-order order=1,computeEnvironment=socratic-fargate
  ```

- [ ] Register job definitions:
  ```bash
  aws batch register-job-definition \
    --job-definition-name socratic-runner \
    --type container \
    --platform-capabilities FARGATE \
    --container-properties '{
      "image": "ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/socratic-runner:v1.0",
      "resourceRequirements": [
        {"type":"VCPU","value":"1"},
        {"type":"MEMORY","value":"2048"}
      ],
      "executionRoleArn": "arn:aws:iam::ACCOUNT_ID:role/BatchRunnerRole",
      "jobRoleArn": "arn:aws:iam::ACCOUNT_ID:role/BatchRunnerRole"
    }'
  ```

- [ ] **socratic-judge** job definition (similar)

---

## Phase 6: Step Functions (10 minutes)

- [ ] Create state machine:
  ```bash
  aws stepfunctions create-state-machine \
    --name SocraticBenchmarkOrchestrator \
    --definition file://infrastructure/step_functions.json \
    --role-arn arn:aws:iam::ACCOUNT_ID:role/StepFunctionsOrchestratorRole
  ```

- [ ] Test execution (manual trigger):
  ```bash
  aws stepfunctions start-execution \
    --state-machine-arn arn:aws:states:us-east-1:ACCOUNT_ID:stateMachine:SocraticBenchmarkOrchestrator \
    --name test-$(date +%s)
  ```

---

## Phase 7: Upload Configs (10 minutes)

- [ ] **Models**:
  ```bash
  aws s3 cp config/models.json s3://socratic-bench/config/
  ```

- [ ] **Seeds** (with hash):
  ```bash
  HASH=$(sha256sum config/seeds/seeds-20251105.json | cut -d' ' -f1 | head -c8)
  aws s3 cp config/seeds/seeds-20251105.json \
    s3://socratic-bench/config/seeds/seeds-20251105@sha256_${HASH}.json
  ```

- [ ] **Rubrics** (with hash):
  ```bash
  HASH=$(sha256sum config/rubrics/rubric-1.1.json | cut -d' ' -f1 | head -c8)
  aws s3 cp config/rubrics/rubric-1.1.json \
    s3://socratic-bench/config/rubrics/rubric-1.1@sha256_${HASH}.json
  ```

- [ ] **System prompts** (with hash)
- [ ] **Judge prompts** (with hash)
- [ ] **Phases config** (with hash)

- [ ] Create manifest:
  ```bash
  python3 scripts/create_manifest.py --output s3://socratic-bench/manifests/
  ```

---

## Phase 8: Observability (15 minutes)

### CloudWatch

- [ ] Create log groups:
  ```bash
  aws logs create-log-group --log-group-name /aws/batch/socratic-runner
  aws logs create-log-group --log-group-name /aws/batch/socratic-judge
  aws logs create-log-group --log-group-name /aws/lambda/SocraticAggregator
  ```

- [ ] Create metric filters (for EMF)

### SNS

- [ ] Create topic:
  ```bash
  aws sns create-topic --name SocraticBenchmarkAlerts
  ```

- [ ] Subscribe email:
  ```bash
  aws sns subscribe \
    --topic-arn arn:aws:sns:us-east-1:ACCOUNT_ID:topic/SocraticBenchmarkAlerts \
    --protocol email \
    --notification-endpoint your-email@example.com
  ```

- [ ] Confirm subscription (check email)

### Athena

- [ ] Create database:
  ```sql
  CREATE DATABASE socratic_bench;
  ```

- [ ] Create external table (see Glue section below)

### Glue

- [ ] Create Glue database:
  ```bash
  aws glue create-database --database-input Name=socratic_bench
  ```

- [ ] Create Glue table for turns (see `infrastructure/glue_tables.sql`)

### QuickSight

- [ ] Create Athena data source
- [ ] Import curated Parquet dataset
- [ ] Create dashboards:
  - [ ] Half-life trend (line chart)
  - [ ] Compliance rate by phase (stacked bar)
  - [ ] Violation mix (pie chart)
  - [ ] CSD radar (radar chart)

---

## Phase 9: EventBridge Cron (5 minutes)

- [ ] Create rule:
  ```bash
  aws events put-rule \
    --name SocraticWeeklyCron \
    --schedule-expression "cron(0 3 ? * MON *)" \
    --description "Trigger Socratic benchmark every Monday 3 AM UTC"
  ```

- [ ] Add target (Step Functions):
  ```bash
  aws events put-targets \
    --rule SocraticWeeklyCron \
    --targets "Id"="1","Arn"="arn:aws:states:us-east-1:ACCOUNT_ID:stateMachine:SocraticBenchmarkOrchestrator","RoleArn"="arn:aws:iam::ACCOUNT_ID:role/EventBridgeStepFunctionsRole"
  ```

- [ ] Verify:
  ```bash
  aws events describe-rule --name SocraticWeeklyCron
  ```

---

## Phase 10: First Run (Manual Test) (2-4 hours)

- [ ] Trigger execution:
  ```bash
  aws stepfunctions start-execution \
    --state-machine-arn arn:aws:states:us-east-1:ACCOUNT_ID:stateMachine:SocraticBenchmarkOrchestrator \
    --name "first-run-$(date +%s)"
  ```

- [ ] Monitor execution:
  ```bash
  # Get execution ARN from previous command
  aws stepfunctions describe-execution --execution-arn <EXECUTION_ARN>
  ```

- [ ] Watch logs:
  ```bash
  aws logs tail /aws/batch/socratic-runner --follow
  ```

- [ ] Check S3 for outputs:
  ```bash
  aws s3 ls s3://socratic-bench/raw/ --recursive
  ```

- [ ] Verify DynamoDB:
  ```bash
  aws dynamodb scan --table-name SocraticBench-Runs --max-items 5
  ```

---

## Phase 11: Validation (30 minutes)

- [ ] **Data Integrity**:
  - [ ] Spot-check 5 random turns in S3
  - [ ] Verify judge scores are populated (not all null)
  - [ ] Check heuristic vs. judge disagreement rate (<15%)

- [ ] **Metrics**:
  - [ ] CloudWatch: `socratic.half_life_turn` appears
  - [ ] CloudWatch: `socratic.compliance_rate` appears

- [ ] **Athena Queries**:
  ```sql
  -- Count total turns
  SELECT COUNT(*) FROM socratic_bench.turns WHERE dt = '2025-11-05';

  -- Average half-life by model
  SELECT model, AVG(half_life_turn) FROM socratic_bench.runs GROUP BY model;
  ```

- [ ] **QuickSight Dashboard**:
  - [ ] Refresh dataset
  - [ ] Verify charts render
  - [ ] Drill down into specific run

---

## Phase 12: Post-Deployment (Ongoing)

- [ ] **Documentation**:
  - [ ] Update DEPLOYMENT_CHECKLIST.md with actual ARNs/names
  - [ ] Document any deviations from planned architecture
  - [ ] Create runbook for common operations

- [ ] **Monitoring**:
  - [ ] Set up CloudWatch alarms (half-life, compliance, cost)
  - [ ] Test SNS alerts (trigger manually)
  - [ ] Add Slack integration (optional)

- [ ] **Cost Tracking**:
  - [ ] Enable AWS Cost Explorer
  - [ ] Tag all resources with `Project=SocraticBenchmark`
  - [ ] Set budget alert ($100/month)

- [ ] **Calibration**:
  - [ ] Create golden set (200-500 items)
  - [ ] Hand-label with 2-3 experts
  - [ ] Upload to `s3://socratic-bench/calibration/golden_sets/`
  - [ ] Run first canary

---

## Troubleshooting

### "Execution failed at FetchConfig"

**Check**: S3 config files exist and are valid JSON

**Fix**: Upload missing configs

### "Batch job timed out"

**Check**: CloudWatch logs for Batch task

**Likely cause**: Bedrock throttling or model API error

**Fix**: Add retry logic or increase job timeout

### "DynamoDB PutItem failed: AccessDenied"

**Check**: IAM role attached to Lambda/Batch has DynamoDB write permissions

**Fix**: Update IAM policy (see `infrastructure/iam_policies.json`)

---

## Success Criteria

- [ ] Weekly cron triggers Step Functions automatically
- [ ] All Batch jobs complete within 4 hours
- [ ] S3 contains complete JSONL for all runs
- [ ] DynamoDB contains summaries for all runs
- [ ] QuickSight dashboard shows trends
- [ ] SNS alerts trigger on regression
- [ ] Cost <$40/week

---

**Deployment Time**: ~3 hours (manual) OR ~1 hour (CDK)

**Recommended**: Use AWS CDK for automated deployment (see `cdk/` directory)

---

**Status Tracking**:

- Start Date: __________
- Completion Date: __________
- Deployed By: __________
- Environment: us-east-1
- Version: v1.0-MVP
