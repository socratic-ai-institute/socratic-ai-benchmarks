# Socratic AI Benchmarking Data Layer Schema
**DynamoDB + S3 Serverless Architecture**

## Design Philosophy

**Simple, Simple, Simple**
- Primary store: DynamoDB (on-demand, pay-per-use)
- Cold artifacts: S3 for raw turns/logs/judge JSONL
- IDs: ULIDs for all rows; SHA-256 for immutable artifacts
- Immutability: artifacts append-only; runs/turns write-once; summaries upsert

**Why DynamoDB over PostgreSQL?**
- Zero cost when idle (perfect for periodic benchmarking)
- Auto-scaling for burst workloads
- Serverless fits Lambda-based architecture
- Simple single-table design for this use case

---

## Entities (Normalized, Minimal)

### Reference / Immutable

```
prompt       — system/judge text blobs (immutable; hash-keyed)
rubric       — JSON rubric definition (immutable; hash-keyed)
seed         — Socratic test scenarios (immutable; hash-keyed)
model        — catalog of tested models (mutable: display name, tags)
```

### Execution Graph

```
run_manifest — frozen combo of model list, seeds, prompts/rubric (immutable; hash-keyed)
run          — one model × seed × vector execution (write-once)
turn         — single tutor question + student response (write-once)
```

### Judging / Scoring

```
judge_result   — per turn (4 dimensions + overall; S3 for full rationale)
run_summary    — aggregates per run (avg scores across turns)
vector_summary — aggregates per vector (Elenchus/Maieutics/Aporia)
model_summary  — aggregates per model (overall profile)
```

---

## DynamoDB Single Table Design

**Table Name**: `SocraticBenchmarks`

**Primary Key**:
- `PK` (Partition Key): Entity identifier
- `SK` (Sort Key): Entity type or timestamp

**Global Secondary Indexes**:

### GSI1: Query by Model
- `GSI1PK`: `MODEL#<model_id>`
- `GSI1SK`: `<timestamp>`
- Purpose: Get all runs for a specific model

### GSI2: Query by Vector
- `GSI2PK`: `VECTOR#<elenchus|maieutics|aporia>`
- `GSI2SK`: `<timestamp>`
- Purpose: Compare models across specific Socratic vectors

### GSI3: Query by Manifest
- `GSI3PK`: `MANIFEST#<manifest_id>`
- `GSI3SK`: `<timestamp>`
- Purpose: Reproducibility - get all runs from a specific benchmark batch

---

## Entity Schemas

### 1. Prompt (Immutable)

**Keys**:
```
PK: PROMPT#<ulid>
SK: METADATA
```

**Attributes**:
```json
{
  "PK": "PROMPT#01HW1234567890ABCDEFGHIJK",
  "SK": "METADATA",
  "entity_type": "prompt",
  "sha256": "abc123...def456",
  "kind": "socratic_tutor",  // or "judge"
  "title": "Non-directive Socratic Tutor (Age 16-18)",
  "body": "You are a Socratic tutor. Your role is to...",
  "created_at": "2025-10-25T12:00:00Z"
}
```

---

### 2. Rubric (Immutable)

**Keys**:
```
PK: RUBRIC#<ulid>
SK: METADATA
```

**Attributes**:
```json
{
  "PK": "RUBRIC#01HW2234567890ABCDEFGHIJK",
  "SK": "METADATA",
  "entity_type": "rubric",
  "sha256": "def456...ghi789",
  "title": "ASE Rubric (Aporia-Scaffolding-Elenchus)",
  "body": {
    "dimensions": [
      {
        "name": "pedagogical_stance",
        "description": "Questions vs lectures",
        "scale": "1-5"
      },
      {
        "name": "conceptual_fidelity",
        "description": "Targets right concept/flaw",
        "scale": "1-5"
      },
      {
        "name": "persona_adaptation",
        "description": "Age-appropriate pacing",
        "scale": "1-5"
      },
      {
        "name": "dialectical_progress",
        "description": "Achieves vector goal",
        "scale": "1-5"
      }
    ],
    "overall": "average of 4 dimensions"
  },
  "created_at": "2025-10-25T12:00:00Z"
}
```

---

### 3. Seed (Scenario - Immutable)

**Keys**:
```
PK: SEED#<ulid>
SK: METADATA
```

**Attributes**:
```json
{
  "PK": "SEED#01HW3334567890ABCDEFGHIJK",
  "SK": "METADATA",
  "entity_type": "seed",
  "sha256": "ghi789...jkl012",
  "vector": "elenchus",  // or "maieutics" or "aporia"
  "title": "Free Speech Contradiction",
  "scenario": {
    "persona": "Age 17, debate team, opinionated",
    "student_statement": "I believe all speech should be allowed with no exceptions. But people who say hurtful things should be arrested.",
    "goal": "Expose contradiction between absolute free speech and punishing speech",
    "key_conflict": "Cannot have both unlimited speech AND legal consequences for speech"
  },
  "created_at": "2025-10-25T12:00:00Z"
}
```

---

### 4. Model (Mutable Catalog)

**Keys**:
```
PK: MODEL#<model_id>
SK: METADATA
```

**Attributes**:
```json
{
  "PK": "MODEL#claude-3-5-sonnet-20241022",
  "SK": "METADATA",
  "entity_type": "model",
  "provider": "anthropic",
  "name": "Claude 3.5 Sonnet v2",
  "bedrock_model_id": "anthropic.claude-3-5-sonnet-20241022-v2:0",
  "tags": ["reasoning", "high-quality"],
  "active": true,
  "created_at": "2025-10-25T12:00:00Z"
}
```

---

### 5. Run Manifest (Immutable)

**Keys**:
```
PK: MANIFEST#<ulid>
SK: METADATA
```

**GSI Keys**:
```
GSI3PK: MANIFEST#<ulid>
GSI3SK: <timestamp>
```

**Attributes**:
```json
{
  "PK": "MANIFEST#01HW4444567890ABCDEFGHIJK",
  "SK": "METADATA",
  "GSI3PK": "MANIFEST#01HW4444567890ABCDEFGHIJK",
  "GSI3SK": "2025-10-25T12:00:00Z",

  "entity_type": "manifest",
  "sha256": "jkl012...mno345",
  "manifest": {
    "prompt_id": "PROMPT#01HW1234567890ABCDEFGHIJK",
    "rubric_id": "RUBRIC#01HW2234567890ABCDEFGHIJK",
    "judge_prompt_id": "PROMPT#01HW1111111111ABCDEFGHIJK",
    "seed_set": [
      {"id": "SEED#01HW3334567890ABCDEFGHIJK", "vector": "elenchus"},
      {"id": "SEED#01HW3335678901BCDEFGHIJKL", "vector": "maieutics"},
      {"id": "SEED#01HW3336789012CDEFGHIJKLM", "vector": "aporia"}
    ],
    "model_set": [
      {"id": "MODEL#claude-3-5-sonnet-20241022", "temperature": 0.7},
      {"id": "MODEL#claude-3-opus-20240229", "temperature": 0.7}
    ]
  },
  "created_at": "2025-10-25T12:00:00Z"
}
```

---

### 6. Run (One Model × Seed × Vector)

**Keys**:
```
PK: RUN#<ulid>
SK: METADATA
```

**GSI Keys**:
```
GSI1PK: MODEL#<model_id>
GSI1SK: <timestamp>
GSI2PK: VECTOR#<vector_name>
GSI2SK: <timestamp>
GSI3PK: MANIFEST#<manifest_id>
GSI3SK: <timestamp>
```

**Attributes**:
```json
{
  "PK": "RUN#01HW5555567890ABCDEFGHIJK",
  "SK": "METADATA",
  "GSI1PK": "MODEL#claude-3-5-sonnet-20241022",
  "GSI1SK": "2025-10-25T12:05:00Z",
  "GSI2PK": "VECTOR#elenchus",
  "GSI2SK": "2025-10-25T12:05:00Z",
  "GSI3PK": "MANIFEST#01HW4444567890ABCDEFGHIJK",
  "GSI3SK": "2025-10-25T12:05:00Z",

  "entity_type": "run",
  "manifest_id": "MANIFEST#01HW4444567890ABCDEFGHIJK",
  "model_id": "MODEL#claude-3-5-sonnet-20241022",
  "seed_id": "SEED#01HW3334567890ABCDEFGHIJK",
  "vector": "elenchus",
  "temperature": 0.7,

  "started_at": "2025-10-25T12:05:00Z",
  "ended_at": "2025-10-25T12:05:45Z",
  "status": "completed",  // running, completed, failed

  "cost_prompt_tokens": 1250,
  "cost_completion_tokens": 180,
  "cost_usd": 0.0089,

  "turns_completed": 3,
  "avg_generation_time_ms": 920
}
```

---

### 7. Turn (Single Question-Answer Exchange)

**Keys**:
```
PK: RUN#<run_id>
SK: TURN#<turn_index>
```

**Attributes**:
```json
{
  "PK": "RUN#01HW5555567890ABCDEFGHIJK",
  "SK": "TURN#001",

  "entity_type": "turn",
  "run_id": "RUN#01HW5555567890ABCDEFGHIJK",
  "turn_index": 1,

  "question": {
    "text": "Looking at what you just said about free speech, what does 'no exceptions' mean to you?",
    "generated_at": "2025-10-25T12:05:15Z",
    "generation_time_ms": 850,
    "prompt_tokens": 450,
    "completion_tokens": 42,
    "temperature": 0.7
  },

  "answer": {
    "text": "It means everyone should be able to say whatever they want without any punishment.",
    "received_at": "2025-10-25T12:05:30Z",
    "response_time_seconds": 15,
    "word_count": 14
  },

  "s3_path": "s3://socratic-bench/raw/dt=2025-10-25/run_01HW555/turn_001.json",
  "created_at": "2025-10-25T12:05:15Z"
}
```

---

### 8. Judge Result (Per-Turn Evaluation)

**Keys**:
```
PK: RUN#<run_id>
SK: JUDGE#<turn_index>
```

**Attributes**:
```json
{
  "PK": "RUN#01HW5555567890ABCDEFGHIJK",
  "SK": "JUDGE#001",

  "entity_type": "judge_result",
  "run_id": "RUN#01HW5555567890ABCDEFGHIJK",
  "turn_index": 1,

  "score": 4.2,
  "subscores": {
    "pedagogical_stance": 4,
    "conceptual_fidelity": 5,
    "persona_adaptation": 4,
    "dialectical_progress": 4
  },

  "violations": [],  // e.g., ["lecturing", "off-topic"]

  "rationale_excerpt": "Strong question that probes the meaning of 'no exceptions' without lecturing. Age-appropriate framing.",
  "s3_path": "s3://socratic-bench/raw/dt=2025-10-25/run_01HW555/turn_001_judge.json",

  "judge_metadata": {
    "model": "claude-3-5-sonnet-20241022",
    "generation_time_ms": 1200,
    "prompt_tokens": 680,
    "completion_tokens": 95
  },

  "created_at": "2025-10-25T12:05:35Z"
}
```

---

### 9. Run Summary (Aggregated Scores)

**Keys**:
```
PK: RUN#<run_id>
SK: SUMMARY
```

**Attributes**:
```json
{
  "PK": "RUN#01HW5555567890ABCDEFGHIJK",
  "SK": "SUMMARY",

  "entity_type": "run_summary",
  "run_id": "RUN#01HW5555567890ABCDEFGHIJK",

  "overall_score": 4.3,
  "dimension_averages": {
    "pedagogical_stance": 4.2,
    "conceptual_fidelity": 4.7,
    "persona_adaptation": 4.1,
    "dialectical_progress": 4.2
  },

  "turns_evaluated": 3,
  "violations_count": 0,

  "score_distribution": {
    "min": 4.0,
    "max": 4.5,
    "p50": 4.3,
    "stddev": 0.21
  },

  "updated_at": "2025-10-25T12:06:00Z"
}
```

---

### 10. Vector Summary (Elenchus/Maieutics/Aporia Aggregates)

**Keys**:
```
PK: MANIFEST#<manifest_id>
SK: VECTOR_SUMMARY#<vector_name>
```

**Attributes**:
```json
{
  "PK": "MANIFEST#01HW4444567890ABCDEFGHIJK",
  "SK": "VECTOR_SUMMARY#elenchus",

  "entity_type": "vector_summary",
  "manifest_id": "MANIFEST#01HW4444567890ABCDEFGHIJK",
  "vector": "elenchus",

  "model_scores": {
    "MODEL#claude-3-5-sonnet-20241022": {
      "overall": 4.3,
      "pedagogical_stance": 4.2,
      "conceptual_fidelity": 4.7,
      "persona_adaptation": 4.1,
      "dialectical_progress": 4.2,
      "runs_count": 5
    },
    "MODEL#claude-3-opus-20240229": {
      "overall": 4.1,
      "pedagogical_stance": 4.0,
      "conceptual_fidelity": 4.5,
      "persona_adaptation": 3.9,
      "dialectical_progress": 4.0,
      "runs_count": 5
    }
  },

  "updated_at": "2025-10-25T12:30:00Z"
}
```

---

### 11. Model Summary (Overall Profile)

**Keys**:
```
PK: MANIFEST#<manifest_id>
SK: MODEL_SUMMARY#<model_id>
```

**Attributes**:
```json
{
  "PK": "MANIFEST#01HW4444567890ABCDEFGHIJK",
  "SK": "MODEL_SUMMARY#claude-3-5-sonnet-20241022",

  "entity_type": "model_summary",
  "manifest_id": "MANIFEST#01HW4444567890ABCDEFGHIJK",
  "model_id": "MODEL#claude-3-5-sonnet-20241022",

  "overall_score": 4.25,

  "vector_breakdown": {
    "elenchus": {
      "score": 4.3,
      "runs": 5,
      "rank": 1
    },
    "maieutics": {
      "score": 4.2,
      "runs": 5,
      "rank": 1
    },
    "aporia": {
      "score": 4.25,
      "runs": 5,
      "rank": 2
    }
  },

  "dimension_averages": {
    "pedagogical_stance": 4.1,
    "conceptual_fidelity": 4.6,
    "persona_adaptation": 4.0,
    "dialectical_progress": 4.2
  },

  "performance_metrics": {
    "avg_generation_time_ms": 920,
    "total_cost_usd": 0.134,
    "total_turns": 45
  },

  "updated_at": "2025-10-25T12:30:00Z"
}
```

---

## S3 Layout (Simple, Deterministic)

```
s3://socratic-bench/
  raw/                                # write-once artifacts from runs
    dt=YYYY-MM-DD/
      run_<ulid>/
        turn_001.json                 # full question + answer + metadata
        turn_001_judge.json           # full judge rationale + scores
        turn_002.json
        turn_002_judge.json
        turn_003.json
        turn_003_judge.json

  manifests/
    manifest_<sha256>.json            # reproducibility record

  artifacts/
    prompts/<prompt_id>.txt
    rubrics/<rubric_id>.json
    seeds/<seed_id>.json

  curated/
    runs/<run_id>.json                # flattened run summary
    vectors/<vector_name>_<manifest_id>.json
    models/<model_id>_<manifest_id>.json
```

---

## Immutability Rules

**Append-only** (identity = SHA-256 of body):
- `prompt`, `rubric`, `seed`, `run_manifest`

**Write-once** (no updates after creation):
- `run`, `turn`, `judge_result`

**Upsert** (idempotent recompute):
- `run_summary`, `vector_summary`, `model_summary`

---

## Minimal CRUD Contract

### Planner Lambda
1. Create `run_manifest` (idempotent on SHA-256)
2. For each model × seed: enqueue message to `dialogue-jobs` SQS

### Dialogue Runner Lambda
1. Create `run` (idempotent on unique key)
2. For each turn (3 questions typical):
   - Generate question (call Bedrock)
   - Simulate student answer (call Bedrock with persona)
   - Upload `raw/.../turn_NNN.json` to S3
   - Insert `turn` row with S3 pointer
3. Update `run.status = 'completed'`
4. Enqueue 3 messages to `judge-jobs` (one per turn)

### Judge Runner Lambda
1. Load turn from S3
2. Call judge model (Bedrock) with rubric
3. Upload `turn_NNN_judge.json` to S3
4. Insert `judge_result` row
5. When all turns judged: publish event to `curation-events`

### Curator Lambda
1. Read all `JUDGE#*` for a run
2. Compute `run_summary` (averages, distributions)
3. Upsert `RUN#<id>/SUMMARY`
4. Write `curated/runs/<id>.json` to S3
5. Update `vector_summary` and `model_summary`

---

## Access Patterns

### Pattern 1: Get All Runs for a Model
```python
response = dynamodb.query(
    TableName='SocraticBenchmarks',
    IndexName='GSI1',
    KeyConditionExpression='GSI1PK = :model',
    ExpressionAttributeValues={
        ':model': 'MODEL#claude-3-5-sonnet-20241022'
    }
)
```

### Pattern 2: Get All Runs for a Vector
```python
response = dynamodb.query(
    TableName='SocraticBenchmarks',
    IndexName='GSI2',
    KeyConditionExpression='GSI2PK = :vector',
    ExpressionAttributeValues={
        ':vector': 'VECTOR#elenchus'
    }
)
```

### Pattern 3: Get Complete Run Data (All Turns + Judges)
```python
response = dynamodb.query(
    TableName='SocraticBenchmarks',
    KeyConditionExpression='PK = :run',
    ExpressionAttributeValues={
        ':run': 'RUN#01HW5555567890ABCDEFGHIJK'
    }
)
# Returns: METADATA, TURN#001, TURN#002, TURN#003,
#          JUDGE#001, JUDGE#002, JUDGE#003, SUMMARY
```

### Pattern 4: Get Model Performance Summary
```python
response = dynamodb.get_item(
    TableName='SocraticBenchmarks',
    Key={
        'PK': 'MANIFEST#01HW4444567890ABCDEFGHIJK',
        'SK': 'MODEL_SUMMARY#claude-3-5-sonnet-20241022'
    }
)
```

---

## Cost Projection (Pay-Per-Use)

### Benchmark Run (8 models × 15 scenarios = 120 runs)

**DynamoDB Writes**:
- 1 manifest
- 120 runs
- 360 turns (3 per run)
- 360 judge results
- 120 run summaries
- 6 vector summaries (3 vectors × 2 model comparisons)
- 8 model summaries
- **Total**: ~975 writes × $1.25/M = **$0.0012**

**DynamoDB Reads** (dashboard queries):
- 100 queries × 10 items avg = 1,000 reads × $0.25/M = **$0.0003**

**S3 Storage**:
- 720 JSON files (turns + judges) × 2KB avg = 1.4MB
- First month: **$0.00003**

**Lambda Execution**:
- Planner: 1 invocation × 1s × 128MB = $0.000002
- Dialogue: 120 invocations × 30s × 512MB = $0.012
- Judge: 360 invocations × 10s × 256MB = $0.009
- Curator: 120 invocations × 2s × 256MB = $0.0006
- **Total**: **$0.022**

**Bedrock (Claude 3.5 Sonnet)**:
- Dialogue: 120 runs × 3 turns × (450 + 42 tokens) × $3/M = $0.177
- Judge: 360 evals × (680 + 95 tokens) × $3/M = $0.837
- **Total**: **$1.014**

**Grand Total per Benchmark Run**: **~$1.04** (Bedrock is 97% of cost)

**Monthly (4 benchmark runs)**: **~$4.16**

**With Prompt Caching** (60% reduction on Bedrock): **~$2.50/month**

---

## Why This Stays Simple

1. **Single DynamoDB table** - no complex joins, simple access patterns
2. **One S3 bucket** - deterministic paths, easy to navigate
3. **No Step Functions** - SQS + Lambda is simpler for this use case
4. **Pay-per-use** - $0 when idle, <$5/month when actively benchmarking
5. **Serverless** - no servers to manage, auto-scales

---

## What You Get

✅ **Reproducibility**: Every run manifest is content-addressed and immutable
✅ **Traceability**: Full audit trail from scenario → question → answer → judge score
✅ **Analytics**: Pre-computed summaries for models, vectors, and dimensions
✅ **Cost-effective**: Pay only when running benchmarks
✅ **Simple**: Single table, deterministic S3 paths, clear Lambda boundaries

---

**Next Steps**:
1. Review this schema - does it capture what you need?
2. Confirm S3 bucket naming and structure
3. Ready to generate CDK infrastructure code?
