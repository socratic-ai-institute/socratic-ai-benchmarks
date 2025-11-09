# Serverless Lambda Functions

**Event-driven microservices for automated Socratic AI benchmarking**

This directory contains all AWS Lambda function handlers for the Socratic Benchmarking Platform. Together, these functions form a completely automated pipeline that runs weekly benchmark tests against 24+ AI models.

## 🏗️ Architecture Overview

```
┌─────────────────────┐
│ EventBridge (Cron)  │
│  Monday 3am UTC     │
└──────────┬──────────┘
           │ triggers
           ▼
┌─────────────────────┐
│  Planner Lambda     │ ────► Creates manifest
│  (planner/)         │ ────► Enqueues 48 jobs
└──────────┬──────────┘
           │ SQS: dialogue-jobs
           ▼
┌─────────────────────┐
│  Runner Lambda      │ ────► Runs dialogues
│  (runner/)          │ ────► Saves turns to S3
│  25 parallel        │ ────► Enqueues judge jobs
└──────────┬──────────┘
           │ SQS: judge-jobs
           ▼
┌─────────────────────┐
│  Judge Lambda       │ ────► Scores turns
│  (judge/)           │ ────► Writes to DynamoDB
│  10 parallel        │ ────► Emits run.judged event
└──────────┬──────────┘
           │ EventBridge: run.judged
           ▼
┌─────────────────────┐
│  Curator Lambda     │ ────► Aggregates results
│  (curator/)         │ ────► Materializes JSON
│                     │ ────► Updates weekly stats
└─────────────────────┘

           │ HTTP requests from UI
           ▼
┌─────────────────────┐
│  API Lambda         │ ────► Serves data
│  (api/)             │ ────► Read-only
└─────────────────────┘
```

## 📁 Lambda Functions

### 1. Planner Lambda (`planner/`)

**Trigger**: EventBridge cron (weekly, Monday 3am UTC)
**Purpose**: Orchestrate weekly benchmark runs
**Outputs**: SQS dialogue-jobs queue

**Flow**:
1. Load active config from S3 (models, scenarios, parameters)
2. Generate deterministic manifest ID (content hash)
3. Save manifest to S3 + DynamoDB
4. Create run jobs (one per model × scenario combination)
5. Enqueue jobs to dialogue-jobs queue (batched, idempotent)

**Key Features**:
- **Idempotent**: Same config = same manifest ID, won't duplicate
- **Deterministic**: Uses content hash for reproducibility
- **Scalable**: Batches SQS sends (10 messages per API call)

**Configuration**:
- Models: From `artifacts/config.json` (24 models)
- Scenarios: From `artifacts/config.json` (8 scenarios)
- Result: 24 × 8 = 192 dialogue jobs (but typically 2 scenarios per model = 48 jobs)

**Example Job**:
```json
{
  "run_id": "01HEQJ5KZM8RTYQXJWD6H4TV6C",
  "manifest_id": "M-20251109-a1b2c3d4e5f6",
  "model_id": "anthropic.claude-3-5-sonnet-20241022-v2:0",
  "provider": "anthropic",
  "scenario_id": "EL-ETH-UTIL-DEON-01",
  "max_turns": 5
}
```

---

### 2. Runner Lambda (`runner/`)

**Trigger**: SQS dialogue-jobs queue
**Purpose**: Execute Socratic dialogues
**Outputs**: S3 turns, DynamoDB TURN items, SQS judge-jobs

**Flow**:
1. Receive job from SQS (run_id, model, scenario, params)
2. Load scenario definition
3. Create RUN item in DynamoDB (status: "running")
4. Run dialogue using `socratic_bench.run_dialogue()`
5. For each turn:
   - Save turn bundle to S3 (`raw/runs/{run_id}/turn_{N}.json`)
   - Write TURN item to DynamoDB
   - Enqueue judge job to SQS
6. Update RUN status to "completed"

**Key Features**:
- **Token Tracking**: Records input/output tokens for cost analysis
- **Latency Measurement**: Tracks API call latency
- **Error Handling**: Updates RUN status to "failed" on errors
- **Parallel Execution**: Up to 25 concurrent Lambda instances

**Concurrency**:
- Reserved concurrency: 25
- Typical execution time: 10-20 seconds
- Memory: 512 MB

**S3 Turn Bundle Format**:
```json
{
  "run_id": "01HEQJ5KZM8RTYQXJWD6H4TV6C",
  "turn_index": 0,
  "scenario_id": "EL-ETH-UTIL-DEON-01",
  "dimension": "elenchus",
  "persona": "I am an 11th-grade student in an ethics class.",
  "student": "I believe in 100% utilitarianism...",
  "ai": "When you say 'greatest good,' how do you measure that?",
  "latency_ms": 2347.5,
  "input_tokens": 287,
  "output_tokens": 45,
  "timestamp": "2025-11-09T14:23:45.123Z"
}
```

---

### 3. Judge Lambda (`judge/`)

**Trigger**: SQS judge-jobs queue
**Purpose**: Score dialogue turns using vector-based system
**Outputs**: S3 judge results, DynamoDB JUDGE items, EventBridge run.judged events

**Flow**:
1. Receive job from SQS (run_id, turn_index)
2. Load turn bundle from S3
3. Compute heuristic scores (fast pre-scoring)
4. Compute vector scores using `socratic_bench.compute_vector_scores()`:
   - **Verbosity**: 0.00-1.00 (optimal length 50-150 tokens)
   - **Exploratory**: 0.00-1.00 (probing depth & conceptual questioning)
   - **Interrogative**: 0.00-1.00 (question-asking behavior)
   - **Overall**: Average of 3 vectors
5. Save judge result to S3 + DynamoDB
6. Check if all turns judged → emit run.judged event

**Scoring System**:

| Vector | Formula | Ideal Score |
|--------|---------|-------------|
| **Verbosity** | Optimal range: 50-150 tokens | 1.00 (in range) |
| **Exploratory** | Cognitive verbs + conceptual words | 0.70-1.00 |
| **Interrogative** | Question count + open-ended check | 1.00 (single open Q) |
| **Overall** | Average of 3 vectors | 0.70-0.90 (good Socratic) |

**Key Features**:
- **Fast Heuristics**: No LLM needed for basic metrics
- **Vector Scoring**: Unified 0-1 scale (replaced old 0-100 scale)
- **Event Emission**: Triggers curator when all turns judged
- **Parallel Execution**: Up to 10 concurrent instances

**S3 Judge Result Format**:
```json
{
  "run_id": "01HEQJ5KZM8RTYQXJWD6H4TV6C",
  "turn_index": 0,
  "scores": {
    "verbosity": 0.85,
    "exploratory": 0.72,
    "interrogative": 1.00,
    "overall": 0.86
  },
  "heuristics": {
    "has_question": true,
    "question_count": 1,
    "word_count": 15,
    "is_open_ended": true
  },
  "judge_model": "vector-scoring-v1",
  "latency_ms": 0.5,
  "error": null,
  "judged_at": "2025-11-09T14:23:46.234Z"
}
```

---

### 4. Curator Lambda (`curator/`)

**Trigger**: EventBridge run.judged event
**Purpose**: Aggregate and materialize results
**Outputs**: S3 curated JSON, DynamoDB SUMMARY items

**Flow**:
1. Load RUN metadata
2. Load all TURN and JUDGE items for run_id
3. Compute aggregate metrics:
   - **Overall score**: Mean of all turn scores
   - **Compliance rate**: % turns with score ≥ 0.5
   - **Half-life**: First turn where score drops below 0.5
   - **Violation rate**: % turns without questions
   - **Open-ended rate**: % turns with open-ended questions
4. Save RUN#SUMMARY to DynamoDB
5. Materialize curated JSON to S3 (`curated/runs/{run_id}.json`)
6. Update weekly aggregate (WEEK#YYYY-WW#MODEL)
7. Materialize weekly JSON to S3

**Key Metrics**:

| Metric | Formula | Interpretation |
|--------|---------|----------------|
| **Overall Score** | Mean of turn scores | 0.70-0.90 = good Socratic |
| **Compliance Rate** | % turns ≥ 0.5 | 80-100% = consistent |
| **Half-Life** | Turn where score < 0.5 | Higher = better stamina |
| **Violation Rate** | % turns without `?` | Lower = more interrogative |

**Weekly Aggregation**:
- Tracks performance trends over time
- Groups by ISO week (YYYY-Www format)
- Enables time-series visualization

---

### 5. API Lambda (`api/`)

**Trigger**: HTTP requests from CloudFront
**Purpose**: Serve benchmark data to UI
**Outputs**: JSON responses

**Routes**:

| Endpoint | Method | Purpose | Response |
|----------|--------|---------|----------|
| `/weekly?week=YYYY-WW` | GET | Weekly aggregates | All models for week |
| `/runs/{run_id}/summary` | GET | Run details | Curated run JSON from S3 |
| `/runs/{run_id}/turns` | GET | Turn list (paginated) | Turn headers + signed S3 URLs |
| `/api/timeseries` | GET | 52-week time series | All models × 52 weeks |
| `/api/latest-rankings` | GET | Current week rankings | Models sorted by score |
| `/api/cost-analysis` | GET | Cost vs performance | Scatter plot data |
| `/api/model-comparison` | GET | Model comparison | Per-dimension vector scores |
| `/api/detailed-results` | GET | Latest run per model | Full vector breakdowns |

**Key Features**:
- **Read-only**: No mutations, safe for public access
- **CORS Enabled**: `Access-Control-Allow-Origin: *`
- **Signed URLs**: For S3 turn bundles (1-hour expiry)
- **Pagination**: Offset + limit for large result sets

**Example Response** (`/api/latest-rankings`):
```json
{
  "week": "2025-W45",
  "rankings": [
    {
      "model_id": "anthropic.claude-3-5-sonnet-20241022-v2:0",
      "mean_score": 0.86,
      "mean_compliance": 0.95,
      "run_count": 8
    },
    {
      "model_id": "meta.llama4-maverick-v1:0",
      "mean_score": 0.82,
      "mean_compliance": 0.88,
      "run_count": 8
    }
  ]
}
```

---

## 🗄️ Data Flow & Storage

### DynamoDB Schema

**Single Table Design**: `SocraticBenchTable`

| PK | SK | Type | Purpose |
|----|----|----|---------|
| `MANIFEST#{id}` | `META` | Config | Benchmark run manifest |
| `RUN#{id}` | `META` | Metadata | Run metadata & status |
| `RUN#{id}` | `TURN#{idx}` | Turn | Turn metadata (points to S3) |
| `RUN#{id}` | `JUDGE#{idx}` | Score | Judge scores |
| `RUN#{id}` | `SUMMARY` | Aggregate | Run-level metrics |
| `WEEK#{week}#MODEL#{id}` | `SUMMARY` | Aggregate | Weekly model performance |

**GSI Indexes**:
- GSI1: Query runs by model (`GSI1PK = MODEL#{id}`)
- GSI2: Query runs by manifest (`GSI2PK = MANIFEST#{id}`)

### S3 Bucket Layout

```
socratic-bench-bucket/
├── artifacts/
│   └── config.json              # Active benchmark configuration
├── manifests/
│   └── M-20251109-a1b2c3d4.json # Manifest snapshots
├── raw/
│   └── runs/
│       └── {run_id}/
│           ├── turn_000.json    # Full turn data
│           ├── turn_001.json
│           ├── judge_000.json   # Full judge rationale
│           └── judge_001.json
└── curated/
    ├── runs/
    │   └── {run_id}.json        # Aggregated run summary
    └── weekly/
        └── {week}/
            └── {model_id}.json  # Weekly model aggregate
```

---

## 📊 Execution Metrics

### Typical Weekly Run

| Stage | Duration | Cost |
|-------|----------|------|
| **Planning** | 5-10s | $0.001 |
| **Dialogue Execution** | 5-15 min | $4.50 (Bedrock API calls) |
| **Judging** | 30-60s | $0.10 (vector scoring, no LLM) |
| **Curation** | 10-20s | $0.02 |
| **Total** | ~15 min | **~$5.50/week** |

**Breakdown**:
- 48 dialogues × $0.09/dialogue = $4.32 (Bedrock)
- Lambda executions = $0.18
- S3 + DynamoDB = $0.50
- Data transfer = $0.50

### Concurrency & Parallelism

| Function | Reserved Concurrency | Batch Size | Throughput |
|----------|---------------------|------------|------------|
| Planner | 1 | N/A | 1 run/week |
| Runner | 25 | 1 | 25 dialogues/min |
| Judge | 10 | 1 | 10 judges/min |
| Curator | 3 | N/A | 3 runs/min |
| API | 10 | N/A | 100 req/s |

---

## 🔧 Configuration

### Environment Variables

All lambdas receive these environment variables (set by CDK):

```bash
TABLE_NAME=SocraticBenchTable        # DynamoDB table
BUCKET_NAME=socratic-bench-bucket    # S3 bucket
DIALOGUE_QUEUE_URL=https://...       # SQS dialogue-jobs queue
JUDGE_QUEUE_URL=https://...          # SQS judge-jobs queue
EVENT_BUS_NAME=default               # EventBridge bus
```

### IAM Permissions

Each Lambda has minimal required permissions:

**Planner**:
- `s3:GetObject` on `artifacts/config.json`
- `s3:PutObject` on `manifests/*`
- `dynamodb:PutItem` on manifest items
- `sqs:SendMessage` on dialogue-jobs queue

**Runner**:
- `bedrock:InvokeModel` on all models
- `s3:PutObject` on `raw/runs/*`
- `dynamodb:PutItem` on RUN and TURN items
- `dynamodb:UpdateItem` on RUN items
- `sqs:SendMessage` on judge-jobs queue

**Judge**:
- `s3:GetObject` on `raw/runs/*`
- `s3:PutObject` on `raw/runs/*` (judge results)
- `dynamodb:PutItem` on JUDGE items
- `dynamodb:Query` on RUN items
- `events:PutEvents` on EventBridge

**Curator**:
- `dynamodb:GetItem`, `Query`, `PutItem` on all items
- `s3:PutObject` on `curated/*`

**API**:
- `dynamodb:GetItem`, `Query`, `Scan` (read-only)
- `s3:GetObject` on all paths
- `s3:GeneratePresignedUrl`

---

## 🚀 Deployment

Lambdas are deployed via AWS CDK:

```bash
cd serverless
./DEPLOY.sh
```

**CDK Stack** (`infra/stack.py`):
- Creates Lambda functions with layers
- Configures SQS queues with DLQs
- Sets up EventBridge rules
- Creates IAM roles and policies
- Configures API Gateway + CloudFront

**Lambda Layers**:
- `socratic-bench-layer`: Core library (dialogue, judge, models, etc.)
- `dependencies-layer`: Python packages (boto3, etc.)

---

## 🐛 Debugging

### CloudWatch Logs

Each Lambda writes structured logs:

```python
print(f"Runner started: processing {len(event['Records'])} messages")
print(f"Run complete: {run_id}, {turn_count} turns")
```

**Log Groups**:
- `/aws/lambda/SocraticBenchStack-Planner...`
- `/aws/lambda/SocraticBenchStack-Runner...`
- `/aws/lambda/SocraticBenchStack-Judge...`
- `/aws/lambda/SocraticBenchStack-Curator...`
- `/aws/lambda/SocraticBenchStack-API...`

### Common Issues

**1. Runner Timeout**:
- **Symptom**: Dialogue runs fail after 5 minutes
- **Cause**: Slow model or network issues
- **Fix**: Increase timeout in `stack.py` (current: 300s)

**2. Judge Queue Backup**:
- **Symptom**: Judge jobs pile up in queue
- **Cause**: Not enough concurrency
- **Fix**: Increase reserved concurrency for judge (current: 10)

**3. DynamoDB Throttling**:
- **Symptom**: `ProvisionedThroughputExceededException`
- **Cause**: Too many concurrent writes
- **Fix**: Enable auto-scaling or increase provisioned capacity

**4. S3 Access Denied**:
- **Symptom**: `AccessDenied` when writing to S3
- **Cause**: Missing IAM permissions
- **Fix**: Check Lambda execution role in IAM

### Manual Testing

Test individual Lambdas:

```bash
# Test Planner (triggers full pipeline)
aws lambda invoke --function-name SocraticBenchStack-Planner response.json

# Test Runner with specific job
aws sqs send-message --queue-url $DIALOGUE_QUEUE_URL --message-body '{
  "run_id": "test-123",
  "model_id": "anthropic.claude-3-5-haiku-20241022-v1:0",
  "provider": "anthropic",
  "scenario_id": "EL-ETH-UTIL-DEON-01",
  "max_turns": 1
}'

# Test API endpoint
curl https://your-api-url.execute-api.us-east-1.amazonaws.com/weekly?week=2025-W45
```

---

## 📚 Additional Resources

- **Core Library**: `/serverless/lib/socratic_bench/README.md`
- **Infrastructure**: `/serverless/infra/README.md` (CDK stack details)
- **Main README**: `/README.md` (project overview)
- **Architecture**: `/ARCHITECTURE.md` (system design)

---

**Built to run weekly benchmarks at scale** ⚡

*Last Updated: 2025-11-09*
*Version: 2.0.0*
