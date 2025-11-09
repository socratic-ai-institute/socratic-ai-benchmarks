# AWS Operations Skill

## Description
Monitor and troubleshoot the deployed Socratic AI Benchmarks platform on AWS.

## When to Use
- Debugging Lambda failures
- Monitoring benchmark runs
- Investigating performance issues
- Checking costs

## Key AWS Resources

### Stack Information
- **Stack Name**: SocraticBenchStack
- **Region**: us-east-1
- **Account**: 984906149037

### Lambda Functions
1. **Planner**: Orchestrates weekly runs (Monday 3am UTC)
2. **Runner**: Executes dialogue tests (25 parallel)
3. **Judge**: Scores dialogue turns (25 parallel)
4. **Curator**: Aggregates results
5. **API**: Serves dashboard data

### DynamoDB Table
- **Name**: socratic_core
- **Access Patterns**:
  - Get run metadata: `PK=RUN#{run_id}, SK=META`
  - Get all turns: `PK=RUN#{run_id}, SK starts with TURN#`
  - Get weekly data: `PK starts with WEEK#{week}#`

### S3 Bucket
- **Name**: socratic-bench-data-984906149037
- **Structure**:
  - `raw/runs/{run_id}/` - Turn and judge data
  - `curated/runs/` - Aggregated results
  - `manifests/` - Test configurations
  - `artifacts/` - Config files

### SQS Queues
1. **dialogue-jobs**: Planner → Runner
2. **judge-jobs**: Runner → Judge

## Common Operations

### Check Lambda Logs
```bash
# Get latest log stream for Runner Lambda
aws logs tail /aws/lambda/SocraticBenchStack-RunnerLambda --follow

# Search for errors
aws logs filter-pattern /aws/lambda/SocraticBenchStack-RunnerLambda \
  --filter-pattern "ERROR" --since 1h
```

### Query DynamoDB
```bash
# Get run summary
aws dynamodb get-item \
  --table-name socratic_core \
  --key '{"PK": {"S": "RUN#{run_id}"}, "SK": {"S": "SUMMARY"}}'

# Query all runs for a model
aws dynamodb query \
  --table-name socratic_core \
  --index-name GSI1 \
  --key-condition-expression "GSI1PK = :model" \
  --expression-attribute-values '{":model": {"S": "MODEL#anthropic.claude-sonnet-4-5-20250929-v1:0"}}'
```

### Check S3 Objects
```bash
# List recent runs
aws s3 ls s3://socratic-bench-data-984906149037/raw/runs/ \
  --recursive --human-readable | tail -20

# Get turn data
aws s3 cp s3://socratic-bench-data-984906149037/raw/runs/{run_id}/turn_000.json -
```

### Monitor Queue Depth
```bash
# Check dialogue queue
aws sqs get-queue-attributes \
  --queue-url {dialogue_queue_url} \
  --attribute-names ApproximateNumberOfMessages

# Check DLQ for failed messages
aws sqs get-queue-attributes \
  --queue-url {dialogue_queue_dlq_url} \
  --attribute-names ApproximateNumberOfMessages
```

## Troubleshooting Guide

### Lambda Timeouts
1. Check CloudWatch Logs for timeout errors
2. Verify Bedrock model availability
3. Check if concurrent execution limit is hit
4. Review Lambda timeout configuration (should be 15min for Runner)

### Missing Data
1. Check if Planner Lambda executed successfully
2. Verify SQS messages were sent
3. Check for throttling errors in Bedrock
4. Review DLQ for failed messages

### High Costs
1. Check Bedrock usage in Cost Explorer
2. Review number of dialogue runs
3. Verify concurrency settings
4. Check for retry loops

## Monitoring Dashboard
- **Live Dashboard**: https://d3ic7ds776p9cq.cloudfront.net
- **CloudWatch Dashboards**: AWS Console → CloudWatch → Dashboards
- **Cost Explorer**: AWS Console → Billing → Cost Explorer

## Related Documentation
- `ARCHITECTURE.md` - Detailed system architecture
- `docs/architecture.md` - Component deep dive
- `serverless/README.md` - Deployment guide
