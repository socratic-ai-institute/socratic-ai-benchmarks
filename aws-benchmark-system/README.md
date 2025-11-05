# AWS Socratic Benchmark System

**Automated, weekly, cloud-native Socratic AI benchmarking platform**

---

## Overview

This system runs a **weekly, fully automated benchmark** to evaluate AI models on their ability to maintain Socratic teaching behavior over long conversations with increasing context windows.

### Key Features

- **Autonomous**: Weekly cron (EventBridge), no human in the loop
- **Reproducible**: Content-addressed configs (SHA256), immutable manifests
- **Explainable**: Every score links to exact turns, rubric, and judge rationale
- **Comparable**: Same seeds/temps/contexts across models and weeks
- **Cost-efficient**: 30-50% judge workload reduction via heuristic filtering
- **Observable**: CloudWatch metrics, SNS alerts, QuickSight dashboards

### Metrics

1. **Socratic Disposition (SD)**: Per-turn quality (Form, Substance, Purity)
2. **Socratic Half-life**: First turn where 3-turn MA drops below threshold
3. **Conversation-level Socratic Dynamism (CSD)**: 8-dimensional long-context evaluation

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    EventBridge (Weekly Cron)                     │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                Step Functions: BenchmarkOrchestrator             │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐     │
│  │ Fetch    │→  │ Generate │→  │ Dialogue │→  │  Judge   │     │
│  │ Config   │   │   Runs   │   │  (Batch) │   │ (Batch)  │     │
│  └──────────┘   └──────────┘   └──────────┘   └──────────┘     │
│                                       │              │           │
│                                       ▼              ▼           │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐     │
│  │ Aggregate│←  │ Heuristic│   │  Canary  │   │  Alerts  │     │
│  │          │   │  Filter  │   │          │   │          │     │
│  └──────────┘   └──────────┘   └──────────┘   └──────────┘     │
└─────────────────────────────────────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        ▼                    ▼                    ▼
  ┌──────────┐         ┌──────────┐        ┌──────────┐
  │    S3    │         │ DynamoDB │        │CloudWatch│
  │ (Source) │         │  (Index) │        │  + SNS   │
  └──────────┘         └──────────┘        └──────────┘
        │                    │
        └─────────┬──────────┘
                  ▼
        ┌───────────────────┐
        │ Athena + QuickSight│
        └───────────────────┘
```

### Components

| Component | Type | Purpose |
|-----------|------|---------|
| **EventBridge** | Scheduler | Weekly cron (Monday 3 AM UTC) |
| **Step Functions** | Orchestrator | 7-state workflow (see `infrastructure/step_functions.json`) |
| **Batch (Fargate)** | Compute | Dialogue runner + judge (parallel) |
| **S3** | Storage | Source-of-truth (JSONL, Parquet) |
| **DynamoDB** | Index | Hot queries (runs, weekly summaries) |
| **Athena** | Analytics | SQL over S3 |
| **QuickSight** | Dashboards | Trends, violations, CSD radar |
| **CloudWatch** | Observability | EMF metrics + logs |
| **SNS** | Alerts | Regressions, canary drift |

---

## Repository Structure

```
aws-benchmark-system/
├── DESIGN_DECISIONS.md       # Architecture decisions (MUST READ)
│
├── schemas/
│   ├── models.py              # Pydantic data models (Turn, RunSummary, etc.)
│   └── requirements.txt
│
├── infrastructure/
│   ├── s3_layout.md           # Bucket structure + partitioning
│   ├── iam_policies.json      # Least-privilege IAM roles
│   ├── dynamodb_tables.md     # Table schemas + access patterns
│   └── step_functions.json    # Orchestrator state machine
│
├── runners/
│   ├── dialogue_runner.py     # Batch task: simulate dialogue
│   └── Dockerfile             # Container for runner
│
├── judges/
│   ├── judge_runner.py        # Batch task: score turns
│   └── Dockerfile             # Container for judge
│
├── lambdas/
│   ├── fetch_config/          # Load manifest from S3
│   ├── generate_runs/         # Create run matrix
│   ├── heuristic_filter/      # Pre-filter for judge
│   ├── aggregator/            # Compute summaries
│   ├── alerts/                # Check thresholds + SNS
│   └── metrics_publisher/     # Publish CloudWatch EMF
│
├── cdk/
│   ├── app.py                 # CDK entry point
│   ├── stacks/
│   │   ├── storage_stack.py   # S3 + DynamoDB
│   │   ├── compute_stack.py   # Batch job definitions
│   │   ├── orchestration_stack.py  # Step Functions + EventBridge
│   │   └── observability_stack.py  # CloudWatch + SNS + QuickSight
│   └── cdk.json
│
├── config/
│   ├── models.json            # Model registry
│   ├── seeds/                 # Seed scenarios
│   ├── rubrics/               # Scoring rubrics
│   ├── prompts/               # System/judge prompts
│   └── phases/                # P0-P3 configurations
│
└── README.md                  # This file
```

---

## Quick Start (Deployment)

### Prerequisites

- AWS Account with permissions for: S3, DynamoDB, Batch, Step Functions, Lambda, EventBridge, Bedrock
- AWS CLI configured (`aws-cli/2.x`)
- AWS CDK installed (`npm install -g aws-cdk`)
- Python 3.12+
- Docker (for building Batch containers)
- Bedrock model access (Claude, Llama, Mistral)

### Step 1: Bootstrap CDK

```bash
cd aws-benchmark-system/cdk
npm install
cdk bootstrap aws://ACCOUNT-ID/us-east-1
```

### Step 2: Deploy Infrastructure

```bash
# Deploy all stacks
cdk deploy --all

# Or deploy individually:
cdk deploy SocraticStorageStack
cdk deploy SocraticComputeStack
cdk deploy SocraticOrchestrationStack
cdk deploy SocraticObservabilityStack
```

**Deployment time**: ~15 minutes

### Step 3: Upload Configs to S3

```bash
# Upload model registry
aws s3 cp config/models.json s3://socratic-bench/config/

# Upload seeds (with content hash)
HASH=$(sha256sum config/seeds/seeds-20251105.json | cut -d' ' -f1 | head -c8)
aws s3 cp config/seeds/seeds-20251105.json \
  s3://socratic-bench/config/seeds/seeds-20251105@sha256_${HASH}.json

# Repeat for rubrics, prompts, phases...
```

### Step 4: Trigger First Run (Manual)

```bash
# Start Step Functions execution
aws stepfunctions start-execution \
  --state-machine-arn arn:aws:states:us-east-1:ACCOUNT-ID:stateMachine:SocraticBenchmarkOrchestrator \
  --name "manual-test-$(date +%s)" \
  --input '{}'
```

**Expected duration**: 2-4 hours (for full matrix)

### Step 5: View Results

**DynamoDB** (hot queries):
```bash
aws dynamodb query \
  --table-name SocraticBench-Runs \
  --index-name HalfLifeIndex \
  --key-condition-expression "week = :week" \
  --expression-attribute-values '{":week":{"S":"2025-W45"}}'
```

**Athena** (analytics):
```sql
SELECT model, AVG(half_life_turn) as avg_half_life
FROM socratic_bench.runs
WHERE dt >= '2025-10-01'
GROUP BY model
ORDER BY avg_half_life DESC;
```

**QuickSight**: Navigate to dashboard (deployed by CDK)

---

## Core Concepts

### Phases (Context Window Tests)

| Phase | Tokens | Turns | Noise | Pressure Tactics |
|-------|--------|-------|-------|------------------|
| **P0** | 2K | 10 | None | None |
| **P1** | 8K | 15 | Mild | "Just tell me" |
| **P2** | 32K | 20 | Medium | Sidebars + "Give tips" |
| **P3** | 128K+ | 40 | Heavy | Explicit "Switch mode" |

### Socratic Disposition (SD) Score

**Per-turn evaluation** (0-10 scale):

```
SD = 0.2 × Form + 0.3 × Substance + 0.5 × Purity
```

- **Form**: Question structure (open-ended, single, grammatical)
- **Substance**: Pedagogical value (probes depth, builds on prior)
- **Purity**: Non-directive (no advice, no leading)

### Socratic Half-life

**First turn where 3-turn moving average drops below 8.0**

- Lower is worse (model degrades quickly)
- Typical range: 10-30 turns
- Metric: `socratic.half_life_turn` (CloudWatch)

### Conversation-level Socratic Dynamism (CSD)

**8-dimensional long-context evaluation**:

1. **CR** (Context Responsiveness): Semantic similarity to last user turn
2. **ST** (Salience Tracking): References important prior facts
3. **RHD** (Red-Herring Discipline): Avoids planted decoys
4. **AP** (Adaptive Probing): Question type matches dialogue state
5. **NVT** (Novelty vs. Template): Avoids canned questions
6. **TC** (Thread Continuity): Maintains coherent inquiry chains
7. **CH** (Contradiction Handling): Detects user contradictions
8. **MA** (Meta-Adaptation): Timely check-ins

**Formula**:
```
CSD = 0.20×CR + 0.20×ST + 0.15×RHD + 0.15×AP + 0.10×NVT + 0.10×TC + 0.05×CH + 0.05×MA
```

**Gating**: If SD < 7, cap CSD at SD (purity first)

---

## Judge Design (Two-Stage)

### Stage 1: Heuristic Filter (Fast)

**Rule-based checks** (~10ms/turn):

- Question mark count (form)
- Directive phrases: "you should", "try", "consider" (purity)
- Length + question words (substance)

**Output**: `HeuristicResult` with confidence (0-1)

**Bypass judge if**: confidence > 0.8 → **30-50% cost reduction**

### Stage 2: LLM Judge (Slow)

**Model**: Claude 3 Opus (or strongest available)

**Input**:
- Last N user turns (context)
- Assistant turn
- Rubric definitions

**Output**: `JudgeResult` (JSON with scores + rationale)

**Disagreement check**: If |judge - heuristic| > 2 → alert + optional secondary judge

### Calibration (Weekly Canary)

- **Golden set**: 200-500 hand-labeled items (2-3 expert consensus)
- **Run judge on golden set** every week
- **Alert if**: avg deviation > 5%
- **Purpose**: Detect judge drift before contamination

---

## Metrics & Alerts

### CloudWatch EMF Metrics

**Namespace**: `SocraticBenchmark`

| Metric | Dimensions | Threshold |
|--------|------------|-----------|
| `half_life_turn` | model, week | Alert if drop >20% WoW |
| `compliance_rate` | model, phase | Alert if drop >10 pts |
| `judge_latency_p95` | - | Alert if >5s |
| `cost_per_run_usd` | model | Budget cap: >$2/run |

### SNS Alerts

**Topic**: `SocraticBenchmarkAlerts`

**Triggers**:
- Half-life regression >20% WoW
- Compliance drop >10 pts
- Judge-heuristic disagreement >15%
- Canary deviation >5%

**Destinations**: Slack, email, PagerDuty (optional)

---

## Cost Estimates

### Weekly Run (7,200 turns)

| Service | Usage | Cost/Week | Cost/Year |
|---------|-------|-----------|-----------|
| **Bedrock** (dialogue) | 3.24M tokens | $19 | $988 |
| **Bedrock** (judge) | ~2M tokens @ 60% | $8 | $416 |
| **Batch/Fargate** | 2 hrs compute | $2 | $104 |
| **S3** | 50 GB storage | $0.20 | $10 |
| **DynamoDB** | 30K writes/month | $0.05 | $0.60 |
| **Athena** | 50 GB scans/month | $0.25 | $3 |
| **CloudWatch** | Logs + metrics | $1 | $12 |
| **QuickSight** | 1 author | $3 | $36 |
| **TOTAL** | | **~$33/week** | **~$1,720/year** |

**Cost per model tested**: $6.60/week (for 5 models)

---

## Access Patterns & Queries

### DynamoDB (Fast Queries)

**"Worst-performing runs this week"**:
```python
dynamodb.query(
    TableName='SocraticBench-Runs',
    IndexName='HalfLifeIndex',
    KeyConditionExpression='week = :week',
    ScanIndexForward=True,  # Ascending (earliest half-life)
    Limit=10
)
```

**"Model trend over 12 weeks"**:
```python
dynamodb.query(
    TableName='SocraticBench-Runs',
    IndexName='ModelWeekIndex',
    KeyConditionExpression='model = :model AND dt >= :start_date'
)
```

### Athena (Analytics)

**"Violation mix by model"**:
```sql
SELECT model, violation, COUNT(*) as count
FROM socratic_bench.turns
CROSS JOIN UNNEST(violations) AS t(violation)
WHERE dt = '2025-11-05'
GROUP BY model, violation;
```

**"CSD subscores (radar chart)"**:
```sql
SELECT model,
       AVG(csd_subscores.CR) as avg_CR,
       AVG(csd_subscores.ST) as avg_ST,
       AVG(csd_subscores.RHD) as avg_RHD,
       AVG(csd_subscores.AP) as avg_AP
FROM socratic_bench.turns
WHERE dt >= '2025-11-01' AND phase = 'P2'
GROUP BY model;
```

---

## Security & Compliance

### IAM (Least Privilege)

- **Batch Runner**: Read config/, write raw/
- **Judge**: Read raw/, write scores/
- **Aggregator**: Read all, write curated/ + DynamoDB
- **Developer**: Read-only + deploy (no data writes)

See: `infrastructure/iam_policies.json`

### Encryption

- **S3**: SSE-S3 (AES-256) mandatory
- **DynamoDB**: AWS-managed encryption
- **In-transit**: TLS 1.2+ only

### Bucket Policy

- **Deny** unencrypted uploads
- **Deny** insecure transport (HTTP)

### Audit

- **CloudTrail**: All S3/DynamoDB writes logged
- **Versioning**: Enabled for config/ and calibration/
- **Backup**: Weekly DynamoDB snapshots (1-year retention)

---

## Operational Playbook

### Manual Trigger (Ad-hoc Run)

```bash
aws stepfunctions start-execution \
  --state-machine-arn $(aws stepfunctions list-state-machines --query "stateMachines[?name=='SocraticBenchmarkOrchestrator'].stateMachineArn" --output text) \
  --name "adhoc-$(date +%s)"
```

### View Execution Status

```bash
EXECUTION_ARN=$(aws stepfunctions list-executions \
  --state-machine-arn <STATE_MACHINE_ARN> \
  --max-results 1 --query "executions[0].executionArn" --output text)

aws stepfunctions describe-execution --execution-arn $EXECUTION_ARN
```

### Inspect Turn Details

```bash
# Download JSONL
aws s3 cp s3://socratic-bench/raw/dt=2025-11-05/model=claude-3.5-sonnet/phase=P2/<RUN_ID>.jsonl - | jq .

# Query specific turn
jq 'select(.turn == 10)' <RUN_ID>.jsonl
```

### Check Canary Results

```bash
aws dynamodb get-item \
  --table-name SocraticBench-CalibrationResults \
  --key '{"golden_set_version":{"S":"golden_set_v1"},"dt":{"S":"2025-11-05"}}'
```

### Re-run Failed Execution

```bash
# Get failed execution input
INPUT=$(aws stepfunctions describe-execution --execution-arn $EXECUTION_ARN --query "input" --output text)

# Retry
aws stepfunctions start-execution \
  --state-machine-arn <STATE_MACHINE_ARN> \
  --name "retry-$(date +%s)" \
  --input "$INPUT"
```

---

## Development

### Local Testing (Runner)

```bash
cd runners/

# Set env vars
export RUN_ID=$(python3 -c "from ulid import ULID; print(str(ULID()))")
export MANIFEST_ID="manifest_20251105_test1234"
export MODEL_ID="anthropic.claude-3-5-sonnet-20241022-v2:0"
export SEED_ID="APO-BIO-EVOL-LAM-01"
export PHASE="P0"
export TEMPERATURE="0.3"
export MAX_TURNS="10"
export S3_BUCKET="socratic-bench"
export DT="2025-11-05T00:00:00Z"

# Run
python3 dialogue_runner.py
```

### Local Testing (Judge)

```bash
cd judges/

export RUN_ID="<RUN_ID_FROM_ABOVE>"
export S3_BUCKET="socratic-bench"
export JUDGE_MODEL="anthropic.claude-3-opus-20240229-v1:0"

python3 judge_runner.py
```

### Build Containers

```bash
# Runner
cd runners/
docker build -t socratic-runner:latest .
docker tag socratic-runner:latest ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/socratic-runner:latest
docker push ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/socratic-runner:latest

# Judge
cd judges/
docker build -t socratic-judge:latest .
docker tag socratic-judge:latest ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/socratic-judge:latest
docker push ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/socratic-judge:latest
```

---

## Troubleshooting

### Execution Failed at "ParallelDialogueRuns"

**Symptoms**: Some Batch jobs time out or fail

**Diagnosis**:
```bash
# Check Batch job logs
aws logs tail /aws/batch/socratic-runner --follow
```

**Common causes**:
- Model API throttling → add retry with backoff
- Container OOM → increase memory in job definition

**Fix**: Re-run with partial failure flag (orchestrator handles this)

### Judge Canary Triggered Alert

**Symptoms**: `alert_triggered=True` in CalibrationResults

**Diagnosis**:
```bash
# Download detailed canary results
aws s3 cp s3://socratic-bench/calibration/results/2025-11-05.json -

# Find items with high deviation
jq '.details[] | select(.deviation > 0.1)' 2025-11-05.json
```

**Possible causes**:
- Judge model updated (new version)
- Prompt drift (check judge prompt version)
- Golden set items ambiguous

**Fix**: Review high-deviation items; update golden set or judge prompt

### DynamoDB Write Throttling

**Symptoms**: `ProvisionedThroughputExceededException`

**Diagnosis**: Should not occur (on-demand billing)

**Fix**: Check CloudWatch for `ThrottledRequests` metric; increase provisioned capacity if needed (rare)

---

## Roadmap

### MVP (Weeks 1-2)

- [x] Design decisions locked
- [x] Pydantic schemas
- [x] S3 layout + IAM
- [x] DynamoDB tables
- [x] Step Functions orchestrator
- [x] Dialogue runner (stub)
- [x] Judge runner (stub)
- [ ] CDK deployment
- [ ] End-to-end test (P0 only, 2 models, 2 temps, 2 seeds, 10 turns)

### V1.0 (Weeks 3-4)

- [ ] Full P0-P3 matrix
- [ ] CSD feature extractors (8 dimensions)
- [ ] Secondary judge (tie-breaker)
- [ ] QuickSight dashboards
- [ ] Canary calibration
- [ ] SNS alerts
- [ ] Weekly cron enabled

### V1.1 (Month 2)

- [ ] Multi-turn Aporia tests (from existing eval framework)
- [ ] Cost optimization (spot instances for Batch)
- [ ] Advanced CSD: salience map, thread graph
- [ ] Parquet curated layer
- [ ] Historical trend analysis (12-week lookback)

---

## FAQ

**Q: Why Batch instead of Lambda?**
A: Dialogues can take 2-5 minutes (40 turns × 3s/turn). Lambda max is 15 min; Batch is unlimited.

**Q: Why S3 as source-of-truth instead of DynamoDB?**
A: Cost + analytics. DynamoDB costs $0.25/GB-month; S3 is $0.023. Athena requires S3.

**Q: Why heuristic filter before judge?**
A: 30-50% cost reduction. Many turns have obvious scores (all question marks, no directive language).

**Q: How to add a new model?**
A: Add to `config/models.json`, push to S3. Next weekly run picks it up automatically.

**Q: How to change rubric?**
A: Create new rubric file (new SHA256), update manifest. Old runs keep old rubric for comparison.

**Q: Why ULID instead of UUID?**
A: Time-sortable. DynamoDB range queries on run_id are faster.

**Q: Can I run multiple benchmarks in parallel?**
A: Yes. Use `execution_id` to isolate. Each run writes to unique S3 keys.

---

## Contributing

This is a research system. For contributions:

1. **Open an issue** describing the improvement
2. **Discuss design** (especially if changing data model)
3. **Submit PR** with:
   - Updated schemas (if applicable)
   - Updated CDK (if infrastructure change)
   - Integration test

**Code style**: Black, isort, mypy

---

## License

Research code. License TBD pending publication.

---

## Contact

**Project**: Socratic AI Institute
**AWS Account**: TBD
**Region**: us-east-1
**Support**: [Create GitHub issue](https://github.com/socratic-ai/benchmark-system/issues)

---

**Last Updated**: 2025-11-05
**Version**: 1.0-MVP
**Status**: Design complete, ready for CDK implementation
