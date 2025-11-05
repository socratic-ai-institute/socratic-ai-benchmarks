# Serverless Socratic AI Benchmarking - Implementation Summary

Complete serverless MVP implementation for weekly Socratic AI model benchmarking.

## 📦 What Was Built

A dead-simple, all-Lambda, serverless architecture that:
- Runs weekly automated benchmarks
- Tests multiple models in parallel
- Scores with LLM-as-judge
- Stores results in DynamoDB + S3
- Serves data via API + web dashboard
- Costs ~$2/week (~$8/month)

## 🏗️ Architecture

```
EventBridge (weekly cron)
    ↓
Planner Lambda
    ↓
SQS dialogue-jobs
    ↓
Runner Lambda (parallel, max 25 concurrent)
    ↓
SQS judge-jobs
    ↓
Judge Lambda (parallel, max 25 concurrent)
    ↓
EventBridge run.judged event
    ↓
Curator Lambda
    ↓
DynamoDB + S3 (curated JSON)
    ↓
API Gateway + Read Lambda
    ↓
Static UI (S3 + CloudFront)
```

## 📂 Directory Structure

```
serverless/
├── README.md                    # Full architecture documentation
├── DEPLOYMENT_GUIDE.md          # Step-by-step deployment
├── QUICK_START.md               # 5-minute quick start
│
├── lib/                         # Shared socratic_bench library
│   └── socratic_bench/
│       ├── __init__.py
│       ├── models.py            # Bedrock client wrapper
│       ├── scenarios.py         # Test scenarios
│       ├── prompts.py           # Prompt templates
│       ├── dialogue.py          # Dialogue runner
│       └── judge.py             # LLM-as-judge
│
├── lambdas/                     # Lambda function handlers
│   ├── planner/                 # Orchestrator
│   ├── runner/                  # Dialogue executor
│   ├── judge/                   # Turn scorer
│   ├── curator/                 # Results aggregator
│   └── api/                     # Read API
│
├── infra/                       # AWS CDK infrastructure
│   ├── app.py                   # CDK app entry point
│   ├── stack.py                 # Complete stack definition
│   └── cdk.json                 # CDK configuration
│
├── ui/                          # Static web dashboard
│   ├── index.html
│   ├── styles.css
│   ├── app.js
│   └── error.html
│
└── scripts/                     # Deployment helpers
    ├── deploy.sh                # Full deployment
    ├── upload-config.sh         # Upload config to S3
    ├── test-run.sh              # Manual test run
    └── check-queues.sh          # Monitor SQS queues
```

## 🚀 Key Features

### 1. CLI-First, Lambda-Second

The `socratic_bench` library is used by **both** CLI and Lambda:

```python
# Same code path for local testing and production
from socratic_bench import run_dialogue, judge_turn

result = run_dialogue(scenario, model_config, max_turns=5)
```

### 2. SQS Fan-Out (Not Step Functions)

- **Cheaper**: Free tier covers 1M requests/month
- **Simpler**: No state machine JSON
- **Durable**: Built-in retries + DLQ
- **Throttled**: Reserved concurrency limits

### 3. Single-Table DynamoDB

```
PK                          SK          Type
─────────────────────────────────────────────────────
MANIFEST#M-20251105-abc123  META        Manifest
RUN#01H7X...                META        Run metadata
RUN#01H7X...                TURN#000    Turn pointer
RUN#01H7X...                JUDGE#000   Judge scores
RUN#01H7X...                SUMMARY     Aggregated
WEEK#2025-W45#MODEL#claude  SUMMARY     Weekly stats
```

**GSI1**: Query by model
**GSI2**: Query by manifest

### 4. Two-Tier Storage

**S3 Raw** (raw/runs/{run_id}/):
- Complete turn bundles
- Full judge rationale
- Archived to Glacier after 90 days

**S3 Curated** (curated/):
- Compact JSON summaries
- Stays hot forever
- Powers UI and Athena

### 5. Idempotent Operations

- Planner uses deterministic manifest IDs (content hash)
- Runner/Judge check for existing data before writing
- Curator safely handles duplicate events

## 💰 Cost Breakdown

**Weekly run** (2 models × 6 scenarios = 12 runs × 5 turns = 60 turns):

| Component | Cost/Week | Cost/Month |
|-----------|-----------|------------|
| Lambda (Compute) | $0.92 | $3.68 |
| Bedrock (Dialogue) | $0.50 | $2.00 |
| Bedrock (Judge) | $0.30 | $1.20 |
| DynamoDB | $0.03 | $0.10 |
| S3 + CloudFront | $0.05 | $0.20 |
| **Total** | **~$2** | **~$8** |

Idle cost (no runs): **~$0.35/month** (DynamoDB + S3 storage only)

## 🔧 Core Components

### Planner Lambda

**Trigger**: EventBridge weekly cron
**Function**: Orchestrate benchmark runs

1. Read config from S3
2. Generate deterministic manifest
3. Enqueue dialogue jobs (one per model × scenario)
4. Idempotent (manifest_id prevents duplicates)

### Runner Lambda

**Trigger**: SQS dialogue-jobs
**Function**: Execute Socratic dialogues

1. Load scenario + model config
2. Call `run_dialogue()` (shared library)
3. For each turn:
   - Write turn bundle to S3
   - Write TURN item to DynamoDB
   - Enqueue judge job
4. Mark RUN completed

**Concurrency**: Max 25 parallel

### Judge Lambda

**Trigger**: SQS judge-jobs
**Function**: Score dialogue turns

1. Load turn bundle from S3
2. Compute heuristics (has question, open-ended, etc.)
3. Call LLM-as-judge via `judge_turn()`
4. Write JUDGE item + full JSON to S3
5. If all turns judged → emit `run.judged` event

**Concurrency**: Max 25 parallel

### Curator Lambda

**Trigger**: EventBridge `run.judged` event
**Function**: Aggregate and materialize results

1. Load all TURNs + JUDGEs for run
2. Compute metrics:
   - Overall score (mean)
   - Compliance rate (% ≥ 3.0)
   - Half-life (first turn < 3.0)
   - Violation rates
3. Write RUN#SUMMARY to DynamoDB
4. Materialize `curated/runs/{run_id}.json`
5. Update weekly aggregate (WEEK#...)

### Read API Lambda

**Trigger**: API Gateway
**Function**: Serve data to UI

**Routes**:
- `GET /weekly?week=YYYY-WW` → Weekly stats
- `GET /runs/{run_id}/summary` → Run summary
- `GET /runs/{run_id}/turns` → Turn headers (paginated)

**Auth**: API key

## 🎨 Static UI

Single-page app (vanilla JS, no framework):

- **Weekly Dashboard**: Model performance table + sparklines
- **Run Details**: Turn-by-turn breakdown
- **Turn Viewer**: Full dialogue + judge scores

**Deployment**: S3 + CloudFront for HTTPS + CDN

## 📊 Data Model

### DynamoDB Items

**MANIFEST#META**: Frozen config snapshot
**RUN#META**: Model, scenario, status, timestamps
**RUN#TURN#NNN**: S3 pointer, token counts, latency
**RUN#JUDGE#NNN**: Overall score, heuristics, S3 pointer
**RUN#SUMMARY**: Aggregated metrics
**WEEK#YYYY-WW#MODEL#X#SUMMARY**: Weekly stats per model

### S3 Objects

**manifests/{id}.json**: Frozen manifest
**raw/runs/{run_id}/turn_NNN.json**: Full turn (student, AI, tokens)
**raw/runs/{run_id}/judge_NNN.json**: Full scores + evidence
**curated/runs/{run_id}.json**: Compact summary
**curated/weekly/{week}/{model}.json**: Weekly aggregate

## 🧪 Testing

### Manual Test Run

```bash
./scripts/test-run.sh
```

Invokes Planner → 12 dialogue jobs → 60 judge jobs → 12 curated results.

**Duration**: ~5-10 minutes (parallel execution)

### Watch Logs

```bash
aws logs tail /aws/lambda/SocraticBenchStack-RunnerFunction --follow
```

### Check Results

```bash
# Via API
curl -H "x-api-key: $API_KEY" "$API_URL/weekly"

# Via DynamoDB
aws dynamodb scan --table-name socratic_core --max-items 10

# Via S3
aws s3 ls s3://$BUCKET/curated/runs/
```

## 📈 Monitoring

**CloudWatch Logs**:
- `/aws/lambda/SocraticBenchStack-PlannerFunction`
- `/aws/lambda/SocraticBenchStack-RunnerFunction`
- `/aws/lambda/SocraticBenchStack-JudgeFunction`
- `/aws/lambda/SocraticBenchStack-CuratorFunction`

**SQS Metrics**:
- Approximate message count
- DLQ depth

**Lambda Metrics**:
- Invocations
- Errors
- Duration
- Throttles

## 🔐 Security

**IAM**: Least privilege per Lambda
**API**: API key required
**S3**: Private buckets, CloudFront OAI for UI
**Bedrock**: IAM role-based access (no API keys)

## 🎯 Next Steps

1. **Deploy**: `./scripts/deploy.sh`
2. **Test**: `./scripts/test-run.sh`
3. **Monitor**: CloudWatch dashboards
4. **Extend**:
   - Add more models
   - Add more scenarios
   - Enable CSD (Content-Specific Dimensions) scoring
   - Add Athena for analytics
   - Add SNS alerting

## 📚 Documentation

- **Full Architecture**: `serverless/README.md`
- **Deployment Guide**: `serverless/DEPLOYMENT_GUIDE.md`
- **Quick Start**: `serverless/QUICK_START.md`

## ✅ What's Locked In

✅ DynamoDB + S3 (no other data stores)
✅ SQS for fan-out (not Step Functions)
✅ Single trusted judge model (Claude 3.5 Sonnet v2)
✅ Per-turn SD scoring (required)
✅ Weekly cron (Monday 3 AM UTC)
✅ Idempotent operations
✅ CLI-first, Lambda-second code sharing

## 🚫 What's Not Included (MVP Scope)

❌ Multi-turn simulated student responses (single-turn only)
❌ CSD (Content-Specific Dimensions) scoring
❌ Secondary judge for validation
❌ Real-time student interaction
❌ Advanced analytics (Athena)
❌ SNS alerting
❌ CI/CD pipeline

These can be added incrementally without architecture changes.

## 🎉 Summary

A production-ready, cost-effective serverless platform for weekly Socratic AI benchmarking:

- **All Lambda**: No containers, no servers
- **Weekly automated**: EventBridge cron
- **Parallel execution**: SQS fan-out
- **Durable**: Retries + DLQs
- **Observable**: CloudWatch logs + metrics
- **Cheap**: ~$2/week
- **Extensible**: Add models/scenarios via config
- **Clean separation**: Shared library for CLI + Lambda

**Time to deploy**: 10 minutes
**Time to first result**: 5 minutes
**Ongoing cost**: ~$8/month

Ready to ship! 🚀
