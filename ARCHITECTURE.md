# Socratic AI Benchmarking Platform - Complete Architecture

**Last Updated:** 2025-11-08
**Version:** 1.0
**Author:** William Prior

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Data Flow Architecture](#data-flow-architecture)
3. [Grading System Deep Dive](#grading-system-deep-dive)
4. [Data Layer](#data-layer)
5. [Compute Layer](#compute-layer)
6. [Frontend Layer](#frontend-layer)
7. [API Layer](#api-layer)
8. [Critical Implementation Details](#critical-implementation-details)
9. [Access Patterns & Queries](#access-patterns--queries)
10. [Cost & Performance](#cost--performance)

---

## System Overview

The Socratic AI Benchmarking Platform is a **serverless, event-driven system** that evaluates AI models on their ability to practice the Socratic Method—asking probing questions instead of lecturing.

### Key Metrics

- **Models Tested:** 25 AWS Bedrock models
- **Test Frequency:** Weekly (Monday 3am UTC)
- **Concurrent Workers:** 25 parallel Lambda executions
- **Monthly Cost:** ~$22
- **Score Scale:** 0-100 internally, normalized to 0-10 for UI
- **Storage:** DynamoDB + S3 (hot data <90 days, archived to Glacier)

### Architecture Pattern

**Event-Driven Orchestration** with asynchronous message queues:
```
EventBridge (cron) → Planner → SQS → Runner (25x parallel) → SQS → Judge (25x parallel)
                                                                       ↓
                                                              EventBridge (run.judged)
                                                                       ↓
                                                                   Curator
                                                                       ↓
                                                              DynamoDB + S3
                                                                       ↓
                                                              API Gateway → Read Lambda
                                                                       ↓
                                                              CloudFront → Static UI
```

---

## Data Flow Architecture

### Phase 1: Planning & Orchestration

**Trigger:** EventBridge cron rule (Monday 3am UTC)

**Planner Lambda** (`serverless/lambdas/planner/handler.py`):
1. Loads test manifest from S3 (`artifacts/manifest.json`)
2. Generates unique `manifest_id` with timestamp
3. Creates cartesian product: 25 models × 2 scenarios = 50 jobs
4. Sends 50 messages to `socratic-dialogue-jobs` SQS queue
5. Writes manifest to S3 for audit trail

**Output:**
```json
{
  "manifest_id": "M-20251108-727952e3f7a8",
  "run_id": "01K9HK1C5CPH6VB4HF55X3CGWC",
  "model_id": "anthropic.claude-sonnet-4-5-20250929-v1:0",
  "scenario_id": "MAI-BIO-CRISPR-01"
}
```

---

### Phase 2: Test Execution

**Runner Lambda** (`serverless/lambdas/runner/handler.py`):
- **Concurrency:** 25 parallel executions
- **Timeout:** 15 minutes
- **Memory:** 1024 MB
- **Triggered by:** SQS `dialogue-jobs` queue

**Process:**
1. **Load Scenario** from DynamoDB or S3:
   ```json
   {
     "scenario_id": "MAI-BIO-CRISPR-01",
     "vector": "maieutics",
     "persona": "9th grader confused about CRISPR gene editing",
     "initial_utterance": "What is CRISPR?",
     "num_turns": 1
   }
   ```

2. **Construct Socratic Tutor Prompt** (`socratic_bench/prompts.py:socratic_tutor_prompt()`):
   ```
   You are a Socratic facilitator. Ask only open-ended, probing questions.
   Do not lecture. Do not provide answers. Use the student's own words to
   surface assumptions. Keep language age-appropriate and concise.

   Vector: MAIEUTICS
   Objective: Scaffold from the student's correct Level-1 understanding to
   deeper levels by asking stepwise questions. Avoid information dumps;
   introduce one idea per question.

   Persona: 9th grader confused about CRISPR gene editing
   Student: What is CRISPR?

   Your response: Ask 1-2 Socratic questions only (no explanations, no answers).
   ```

3. **Invoke Test Model** via AWS Bedrock:
   - Model: `anthropic.claude-sonnet-4-5-20250929-v1:0`
   - Max tokens: 300
   - Temperature: 0.7
   - Captures: response text, input/output tokens, latency

4. **Save Turn Bundle** to S3 (`raw/runs/{run_id}/turn_000.json`):
   ```json
   {
     "run_id": "01K9HK1C5CPH6VB4HF55X3CGWC",
     "turn_index": 0,
     "vector": "maieutics",
     "persona": "9th grader confused about CRISPR gene editing",
     "student": "What is CRISPR?",
     "ai": "What do you already know about how genes work?",
     "input_tokens": 184,
     "output_tokens": 47,
     "latency_ms": 1523.4,
     "timestamp": "2025-11-08T11:18:57Z"
   }
   ```

5. **Write TURN Item** to DynamoDB:
   ```python
   {
     "PK": "RUN#01K9HK1C5CPH6VB4HF55X3CGWC",
     "SK": "TURN#000",
     "run_id": "01K9HK1C5CPH6VB4HF55X3CGWC",
     "turn_index": 0,
     "s3_key": "raw/runs/01K9HK1C5CPH6VB4HF55X3CGWC/turn_000.json",
     "input_tokens": 184,
     "output_tokens": 47,
     "latency_ms": 1523.4,
     "word_count": 28,
     "has_question": True
   }
   ```

6. **Send Judge Job** to SQS `judge-jobs` queue:
   ```json
   {
     "run_id": "01K9HK1C5CPH6VB4HF55X3CGWC",
     "turn_index": 0
   }
   ```

---

### Phase 3: V2 LLM-as-Judge Scoring

**Judge Lambda** (`serverless/lambdas/judge/handler.py`):
- **Concurrency:** 25 parallel executions
- **Timeout:** 5 minutes
- **Memory:** 512 MB
- **Judge Model:** `anthropic.claude-3-5-sonnet-20240620-v1:0` (temperature=0.3)

**V2 Judge System (Current):** Rule-based + LLM hybrid scoring that produces 3 metrics:

#### Step 3.1: Token Count Extraction

```python
def compute_token_count(ai_response: str) -> int:
    # Count actual tokens using Bedrock tokenizer
    return bedrock_tokenizer.count_tokens(ai_response)
```

**Example:**
```python
ai_response = "What do you already know about how genes work?"
token_count = 11  # Measured via tokenizer
```

---

#### Step 3.2: Socratic Question Detection

**Rule:** Response must end with a question mark

```python
def ends_with_socratic_question(ai_response: str) -> bool:
    return ai_response.strip().endswith("?")
```

**Example:**
```python
ai_response = "What do you already know about how genes work?"
ends_with_question = True  # Ends with "?"
```

---

#### Step 3.3: LLM Judge for Directional Alignment

**Prompt Template** (`socratic_bench/prompts.py:v2_judge_prompt()`):

```
You are evaluating whether an AI tutor's response aligns with the Socratic method.

Context:
- Vector: MAIEUTICS
- Persona: 9th grader confused about CRISPR gene editing

Turn 1
Student: What is CRISPR?
AI: What do you already know about how genes work?

Task: Evaluate whether the AI's response is directionally Socratic (asking probing questions
to surface student reasoning) versus directive (lecturing or providing answers).

Score 0.0 to 1.0:
- 1.0 = Pure Socratic questioning (no lecture, no answers)
- 0.7-0.9 = Mostly Socratic with minor directive elements
- 0.4-0.6 = Mixed questioning and telling
- 0.1-0.3 = Mostly directive with minor questions
- 0.0 = Pure lecture, no questions

Return ONLY a JSON object: {"directionally_socratic": 0.85, "explanation": "..."}
```

---

#### Step 3.4: V2 Judge Response

**What the V2 Judge Returns:**
```json
{
  "token_count": 11,
  "ends_with_socratic_question": true,
  "directionally_socratic": 0.85,
  "explanation": "Response asks a probing question about foundational knowledge (genes) without providing any direct answers or explanations. Pure Socratic technique."
}
```

**CRITICAL:** V2 judge returns **3 flat metrics**, not nested dimension objects.

---

#### Step 3.5: V2 Metric Storage

**What Gets Saved to S3** (`raw/runs/{run_id}/judge_000.json`):

```json
{
  "run_id": "01K9HK1C5CPH6VB4HF55X3CGWC",
  "turn_index": 0,
  "token_count": 11,
  "ends_with_socratic_question": true,
  "directionally_socratic": 0.85,
  "explanation": "Response asks a probing question about foundational knowledge...",
  "judge_model": "anthropic.claude-3-5-sonnet-20240620-v1:0",
  "latency_ms": 2847.32,
  "error": null,
  "judged_at": "2025-11-12T14:28:59.667882+00:00"
}
```

**What Gets Saved to DynamoDB:**
```python
{
  "PK": "RUN#01K9HK1C5CPH6VB4HF55X3CGWC",
  "SK": "JUDGE#000",
  "run_id": "01K9HK1C5CPH6VB4HF55X3CGWC",
  "turn_index": 0,
  "token_count": 11,
  "ends_with_socratic_question": True,
  "directionally_socratic": 0.85,
  "judge_model": "anthropic.claude-3-5-sonnet-20240620-v1:0",
  "s3_key": "raw/runs/01K9HK1C5CPH6VB4HF55X3CGWC/judge_000.json",
  "error": None,
  "judged_at": "2025-11-12T14:28:59.667882+00:00"
}
```

**V2 Metrics (3 Core Dimensions):**
- `token_count`: Response verbosity (raw token count)
- `ends_with_socratic_question`: Boolean (must end with "?")
- `directionally_socratic`: 0.0-1.0 scale (pure Socratic vs directive)

---

#### Step 3.6: Completion Detection

After saving each JUDGE item, the Lambda checks:
```python
def check_all_turns_judged(run_id: str) -> bool:
    items = table.query(PK=f"RUN#{run_id}")

    turn_count = count(items where SK starts with "TURN#")
    judge_count = count(items where SK starts with "JUDGE#")

    return turn_count > 0 and turn_count == judge_count
```

If all turns are judged, emit **EventBridge event**:
```json
{
  "source": "socratic-bench.judge",
  "detail-type": "run.judged",
  "detail": {
    "run_id": "01K9HK1C5CPH6VB4HF55X3CGWC"
  }
}
```

---

### Phase 4: Aggregation & Curation

**Curator Lambda** (`serverless/lambdas/curator/handler.py`):
- **Trigger:** EventBridge `run.judged` event
- **Timeout:** 5 minutes
- **Memory:** 512 MB

#### Step 4.1: Load Run Data

```python
# Load metadata
run_meta = table.get_item(PK=f"RUN#{run_id}", SK="META")

# Load all turns and judges
turns = table.query(PK=f"RUN#{run_id}", SK begins with "TURN#")
judges = table.query(PK=f"RUN#{run_id}", SK begins with "JUDGE#")
```

---

#### Step 4.2: Compute V2 Aggregate Metrics

```python
def compute_v2_metrics(turns, judges):
    # Token aggregates
    token_counts = [j.get("token_count", 0) for j in judges]
    avg_tokens = mean(token_counts)

    # Question compliance
    ends_with_question_count = sum(1 for j in judges if j.get("ends_with_socratic_question"))
    question_rate = ends_with_question_count / len(judges)

    # Directional Socratic alignment
    socratic_scores = [j.get("directionally_socratic", 0.0) for j in judges]
    avg_socratic = mean(socratic_scores)

    # Token stats from turns
    total_input_tokens = sum(t.get("input_tokens", 0) for t in turns)
    total_output_tokens = sum(t.get("output_tokens", 0) for t in turns)

    return {
        "turn_count": len(turns),
        "avg_token_count": round(avg_tokens, 2),
        "question_compliance_rate": round(question_rate, 2),
        "avg_directionally_socratic": round(avg_socratic, 2),
        "total_input_tokens": total_input_tokens,
        "total_output_tokens": total_output_tokens,
    }
```

**Output:**
```python
{
  "turn_count": 1,
  "avg_token_count": 11,                      # Average tokens per response
  "question_compliance_rate": 1.0,            # 100% of turns end with "?"
  "avg_directionally_socratic": 0.85,         # Average 0-1 Socratic score
  "total_input_tokens": 184,
  "total_output_tokens": 47
}
```

---

#### Step 4.3: Save V2 SUMMARY to DynamoDB

```python
{
  "PK": "RUN#01K9HK1C5CPH6VB4HF55X3CGWC",
  "SK": "SUMMARY",
  "run_id": "01K9HK1C5CPH6VB4HF55X3CGWC",
  "manifest_id": "M-20251112-89ef6931b55b",
  "model_id": "anthropic.claude-sonnet-4-5-20250929-v1:0",
  "scenario_id": "MAI-BIO-CRISPR-01",
  "vector": "maieutics",
  "created_at": "2025-11-12T14:28:50.583461+00:00",
  "curated_at": "2025-11-12T14:29:03.236474+00:00",

  // V2 Aggregated metrics
  "turn_count": 1,
  "avg_token_count": 11,                      // Average tokens per response
  "question_compliance_rate": 1.0,            // 100% of turns end with "?"
  "avg_directionally_socratic": 0.85,         // Average 0-1 Socratic score
  "total_input_tokens": 184,
  "total_output_tokens": 47
}
```

**⚠️ CRITICAL:** The V2 SUMMARY stores 3 aggregate metrics derived from per-turn judge data. For per-turn granular data, the API must fetch S3 judge files.

---

#### Step 4.4: Materialize Curated JSON to S3

**Path:** `curated/runs/{run_id}.json`

Contains full run summary with all turns and judges for offline analysis.

---

#### Step 4.5: Update Weekly Aggregate

```python
week = datetime.now().strftime("%Y-W%V")  # "2025-W45"

{
  "PK": f"WEEK#{week}#MODEL#{model_id}",
  "SK": "SUMMARY",
  "week": week,
  "model_id": model_id,
  "run_count": 1,
  "mean_score": 84.0,
  "mean_compliance": 1.0,
  "updated_at": "2025-11-08T11:19:03Z"
}
```

---

## Data Layer

### DynamoDB Table: `socratic_core`

**Design Pattern:** Single Table Design with GSIs

**Primary Key:**
- **PK (Partition Key):** Composite identifier
- **SK (Sort Key):** Item type + identifier

**Global Secondary Indexes:**
- **GSI1:** Query by model (`GSI1PK=MODEL#{model_id}`, `GSI1SK=RUN#{run_id}`)
- **GSI2:** Query by manifest (`GSI2PK=MANIFEST#{manifest_id}`, `GSI2SK=RUN#{run_id}`)

**Billing:** Pay-per-request (no reserved capacity)

---

### Access Patterns

#### 1. Run Metadata
```python
PK = "RUN#01K9HK1C5CPH6VB4HF55X3CGWC"
SK = "META"

{
  "run_id": "01K9HK1C5CPH6VB4HF55X3CGWC",
  "manifest_id": "M-20251108-727952e3f7a8",
  "model_id": "anthropic.claude-sonnet-4-5-20250929-v1:0",
  "scenario_id": "MAI-BIO-CRISPR-01",
  "vector": "maieutics",
  "status": "completed",
  "turn_count": 1,
  "created_at": "2025-11-08T11:18:50.583461+00:00",
  "updated_at": "2025-11-08T11:18:59.069000+00:00",

  // GSI keys
  "GSI1PK": "MODEL#anthropic.claude-sonnet-4-5-20250929-v1:0",
  "GSI1SK": "RUN#01K9HK1C5CPH6VB4HF55X3CGWC",
  "GSI2PK": "MANIFEST#M-20251108-727952e3f7a8",
  "GSI2SK": "RUN#01K9HK1C5CPH6VB4HF55X3CGWC"
}
```

**Query:** `get_item(PK="RUN#...", SK="META")`

---

#### 2. Turn Data
```python
PK = "RUN#01K9HK1C5CPH6VB4HF55X3CGWC"
SK = "TURN#000"  // Zero-padded 3 digits

{
  "run_id": "01K9HK1C5CPH6VB4HF55X3CGWC",
  "turn_index": 0,
  "s3_key": "raw/runs/01K9HK1C5CPH6VB4HF55X3CGWC/turn_000.json",
  "input_tokens": 184,
  "output_tokens": 47,
  "latency_ms": 1523.4,
  "word_count": 9,
  "has_question": True
}
```

**Query:** `query(PK="RUN#...", SK begins_with "TURN#")`

---

#### 3. V2 Judge Data
```python
PK = "RUN#01K9HK1C5CPH6VB4HF55X3CGWC"
SK = "JUDGE#000"

{
  "run_id": "01K9HK1C5CPH6VB4HF55X3CGWC",
  "turn_index": 0,
  "token_count": 11,
  "ends_with_socratic_question": True,
  "directionally_socratic": 0.85,
  "judge_model": "anthropic.claude-3-5-sonnet-20240620-v1:0",
  "s3_key": "raw/runs/01K9HK1C5CPH6VB4HF55X3CGWC/judge_000.json",
  "error": None,
  "judged_at": "2025-11-12T14:28:59.667882+00:00"
}
```

**Query:** `query(PK="RUN#...", SK begins_with "JUDGE#")`

---

#### 4. V2 Run Summary
```python
PK = "RUN#01K9HK1C5CPH6VB4HF55X3CGWC"
SK = "SUMMARY"

{
  "run_id": "01K9HK1C5CPH6VB4HF55X3CGWC",
  "model_id": "anthropic.claude-sonnet-4-5-20250929-v1:0",
  "scenario_id": "MAI-BIO-CRISPR-01",
  "avg_token_count": 11,
  "question_compliance_rate": 1.0,
  "avg_directionally_socratic": 0.85,
  "turn_count": 1,
  "total_input_tokens": 184,
  "total_output_tokens": 47,
  "curated_at": "2025-11-12T14:29:03.236474+00:00"
}
```

**Query:** `scan(FilterExpression="SK = :sk", ExpressionAttributeValues={":sk": "SUMMARY"})`

---

#### 5. V2 Weekly Aggregates
```python
PK = "WEEK#2025-W46#MODEL#anthropic.claude-sonnet-4-5-20250929-v1:0"
SK = "SUMMARY"

{
  "week": "2025-W46",
  "model_id": "anthropic.claude-sonnet-4-5-20250929-v1:0",
  "run_count": 2,
  "mean_token_count": 11.5,
  "mean_question_compliance": 0.95,
  "mean_directionally_socratic": 0.82,
  "updated_at": "2025-11-12T14:29:03Z"
}
```

**Query:** `scan(FilterExpression="begins_with(PK, :prefix) AND SK = :sk")`

---

### S3 Bucket: `socratic-bench-data-{account_id}`

**Structure:**
```
s3://socratic-bench-data-984906149037/
├── raw/
│   └── runs/
│       └── {run_id}/
│           ├── turn_000.json        # Full turn bundle
│           ├── turn_001.json
│           ├── judge_000.json       # Judge scores + heuristics
│           └── judge_001.json
│
├── curated/
│   └── runs/
│       └── {run_id}.json            # Aggregated run summary
│
├── manifests/
│   └── {manifest_id}.json           # Test manifest
│
└── artifacts/
    ├── manifest.json                # Current test config
    └── scenarios/
        └── MAI-BIO-CRISPR-01.json   # Scenario definitions
```

**Lifecycle:**
- **Raw data** → Glacier after 90 days
- **Curated data** → Retained indefinitely
- **Manifests** → Retained for audit

---

## Compute Layer

### Lambda Functions

| Function | Trigger | Concurrency | Timeout | Memory | Purpose |
|----------|---------|-------------|---------|--------|---------|
| **Planner** | EventBridge cron | 1 | 5 min | 512 MB | Orchestrates weekly test runs |
| **Runner** | SQS `dialogue-jobs` | 25 | 15 min | 1024 MB | Executes Socratic dialogues |
| **Judge** | SQS `judge-jobs` | 25 | 5 min | 512 MB | Scores dialogue turns |
| **Curator** | EventBridge `run.judged` | 1 | 5 min | 512 MB | Aggregates results |
| **Read API** | API Gateway | Auto | 30 sec | 256 MB | Serves UI data |

**Shared Layer:** `SocraticLibLayer` (Python 3.12)
- `socratic_bench/`: Core library
  - `models.py`: Bedrock client
  - `prompts.py`: Tutor & judge prompts
  - `judge.py`: Judge logic
  - `__init__.py`: Exports

---

### SQS Queues

#### `socratic-dialogue-jobs`
- **Purpose:** Planner → Runner
- **Visibility Timeout:** 15 minutes
- **Max Receive Count:** 3 (then DLQ)
- **Message Format:**
  ```json
  {
    "run_id": "01K9HK...",
    "model_id": "anthropic.claude-sonnet-4-5...",
    "scenario_id": "MAI-BIO-CRISPR-01"
  }
  ```

#### `socratic-judge-jobs`
- **Purpose:** Runner → Judge
- **Visibility Timeout:** 5 minutes
- **Max Receive Count:** 3 (then DLQ)
- **Message Format:**
  ```json
  {
    "run_id": "01K9HK...",
    "turn_index": 0
  }
  ```

---

### EventBridge

**Event Bus:** `socratic-bench`

**Rules:**
1. **Weekly Trigger:** `cron(0 3 * * MON)` → Planner Lambda
2. **Run Judged:** `detail-type="run.judged"` → Curator Lambda

**Event Format:**
```json
{
  "source": "socratic-bench.judge",
  "detail-type": "run.judged",
  "detail": {
    "run_id": "01K9HK1C5CPH6VB4HF55X3CGWC"
  },
  "event-bus": "socratic-bench"
}
```

---

## Frontend Layer

### Static Website (CloudFront + S3)

**URL:** `https://d3ic7ds776p9cq.cloudfront.net`

**Files:**
- `index.html`: Landing page with project overview
- `research.html`: Interactive dashboard with charts

**CDN:** CloudFront distribution
- **Origin:** S3 bucket `socratic-ui-{account_id}`
- **Cache:** 1 hour TTL
- **Compression:** Enabled (gzip)

---

### Research Dashboard (`research.html`)

**Libraries:**
- **Chart.js:** Radar charts, bar charts, line charts, scatter plots

**API Endpoint:** `https://wcyf23uxxe.execute-api.us-east-1.amazonaws.com/prod`

**Data Sources:**

#### 1. V2 Model Comparison Grid
**Endpoint:** `GET /api/model-comparison`

**Response:**
```json
{
  "models": [
    {
      "model_id": "meta.llama3-1-70b-instruct-v1:0",
      "overall": 8.5,                       // 0-10 scale (composite score)
      "conciseness": 7.5,                   // Inverted: lower tokens = better
      "ends_with_question": 9.2,            // % of turns ending with "?"
      "directionally_socratic": 8.4,        // 0-1 scale converted to 0-10
      "run_count": 1
    }
  ],
  "winner": { /* top model */ }
}
```

**V2 Metrics (3 Core Dimensions):**
- `conciseness` (0-10): Response verbosity scoring (inverted: shorter = better, capped at ~100 tokens)
- `ends_with_question` (0-10): % of turns ending with "?" (0-100% normalized to 0-10)
- `directionally_socratic` (0-10): 0-1 Socratic alignment score × 10

**UI Rendering:**
```javascript
// Model cards with progress bars
models.forEach(model => {
  card.innerHTML = `
    <h3>${model.model_id}</h3>

    <div class="metric-row">
      <span class="metric-label">Conciseness</span>
      <span class="metric-value">${model.conciseness}</span>
    </div>
    <div class="metric-bar">
      <div class="metric-bar-fill"
           style="width: ${model.conciseness * 10}%"></div>
    </div>

    <!-- Repeat for ends_with_question and directionally_socratic -->
  `;
});
```

**CRITICAL:** Bar width uses `* 10` to convert 0-10 scale to 0-100% CSS width.

---

#### 2. Time-Series Chart
**Endpoint:** `GET /api/timeseries`

**Response:**
```json
{
  "weeks": ["2025-W45", "2025-W46", ...],
  "series": [
    {
      "model_id": "anthropic.claude-sonnet-4-5...",
      "data": [
        {"week": "2025-W45", "score": 8.4},
        {"week": "2025-W46", "score": null}
      ]
    }
  ]
}
```

**Chart Config:**
```javascript
{
  type: 'line',
  options: {
    scales: {
      y: { min: 0, max: 10 }  // Expects 0-10 scale
    }
  }
}
```

---

#### 3. Latest Rankings
**Endpoint:** `GET /api/latest-rankings`

**Response:**
```json
{
  "week": "2025-W45",
  "rankings": [
    {
      "model_id": "anthropic.claude-sonnet-4-5...",
      "mean_score": 8.4,     // 0-10 scale
      "mean_compliance": 1.0,
      "run_count": 2
    }
  ]
}
```

**Chart:** Horizontal bar chart sorted by `mean_score` descending.

---

#### 4. V2 Detailed Results Table
**Endpoint:** `GET /api/detailed-results`

**Response:**
```json
{
  "total": 25,
  "results": [
    {
      "run_id": "01K9HK...",
      "model_id": "meta.llama3-1-70b-instruct-v1:0",
      "scenario_name": "MAI-BIO-CRISPR-01",
      "test_type": "disposition",
      "overall_score": 8.4,                // 0-10 scale (composite)
      "token_count": 11,                   // Average tokens per response
      "ends_with_socratic_question": true, // Boolean
      "directionally_socratic": 0.85,      // 0-1 scale
      "judged_at": "2025-11-12T14:28:59Z"
    }
  ]
}
```

**Filters:**
- Test type (disposition/fidelity)
- Provider (anthropic/meta/amazon/etc.)
- Model dropdown
- Scenario dropdown
- Verbosity range (token count)
- Text search

---

#### 5. Cost Analysis Scatter Plot
**Endpoint:** `GET /api/cost-analysis`

**Response:**
```json
{
  "scatter_data": [
    {
      "model_id": "anthropic.claude-sonnet-4-5...",
      "avg_score": 8.4,         // 0-10 scale
      "cost_per_run": 0.0012,   // USD
      "run_count": 2,
      "provider": "anthropic"
    }
  ]
}
```

**Chart:** Bubble scatter (x=cost, y=score, size=run_count)

---

### UI → API → Data Flow (V2)

```
User loads research.html
  ↓
JavaScript fetch() to API Gateway
  ↓
Lambda Read API handler
  ↓
DynamoDB scan(FilterExpression="SK = :sk", ExpressionAttributeValues={":sk": "SUMMARY"})
  ↓
For each SUMMARY item:
  - Load S3 judge files: s3://bucket/raw/runs/{run_id}/judge_*.json
  - Extract V2 metrics: {token_count: 11, ends_with_socratic_question: true, directionally_socratic: 0.85}
  - Normalize to 0-10: {conciseness: 7.5, ends_with_question: 9.2, directionally_socratic: 8.4}
  ↓
Return JSON to UI
  ↓
Chart.js renders data (3 metrics, not 5)
  - Bar widths: score * 10 (converts 0-10 to 0-100% CSS)
  - Y-axis: 0-10 scale
```

---

## API Layer

### API Gateway: `Socratic Bench API`

**Endpoint:** `https://wcyf23uxxe.execute-api.us-east-1.amazonaws.com/prod`

**Authentication:** API Key (simple MVP auth)
- Key ID: `0qwosllwel`
- Rate Limit: 100 req/sec
- Burst Limit: 200 req/sec

**CORS:** Enabled for all origins (public UI)

---

### Routes

| Method | Path | Description | Response Time |
|--------|------|-------------|---------------|
| `GET` | `/weekly?week=YYYY-WW` | Weekly aggregate data | ~200ms |
| `GET` | `/runs/{run_id}/summary` | Run summary (from S3) | ~300ms |
| `GET` | `/runs/{run_id}/turns` | Paginated turn headers | ~150ms |
| `GET` | `/api/timeseries` | 52-week performance trends | ~400ms |
| `GET` | `/api/latest-rankings` | Current week rankings | ~200ms |
| `GET` | `/api/cost-analysis` | Cost vs performance scatter | ~500ms |
| `GET` | `/api/model-comparison` | Latest run per model | ~600ms |
| `GET` | `/api/detailed-results` | Latest run per model (table) | ~400ms |

---

### Read Lambda Handler (`lambdas/api/handler.py`)

**Key Functions:**

#### `get_model_comparison()`
**Purpose:** Fetch latest run per model with V2 3-metric scores

**Process:**
1. Scan SUMMARY items to find latest run per model
2. For each run, load S3 judge files: `raw/runs/{run_id}/judge_*.json`
3. Extract V2 metrics and aggregate:
   ```python
   avg_tokens = mean([j["token_count"] for j in judges])
   question_rate = sum(j["ends_with_socratic_question"] for j in judges) / len(judges)
   avg_socratic = mean([j["directionally_socratic"] for j in judges])
   ```
4. Normalize to 0-10 scale for UI display:
   ```python
   {
     "conciseness": compute_conciseness_score(avg_tokens),     # 7.5 (inverted: shorter is better)
     "ends_with_question": round(question_rate * 10, 2),       # 9.2 (% ending with "?")
     "directionally_socratic": round(avg_socratic * 10, 2),    # 8.4 (0-1 scaled to 0-10)
     "overall": round((conciseness + ends_q + socratic) / 3, 2) # 8.3 (Average of 3 metrics)
   }
   ```

**V2 Metric Definitions:**
- **Conciseness**: Inverted token count (lower tokens = higher score, capped at ~100 tokens for ideal length)
- **Ends with Question**: % of response turns ending with "?" (0-100% → 0-10 scale)
- **Directionally Socratic**: LLM judgment of Socratic alignment (0.0-1.0 → 0-10 scale)

---

#### `get_detailed_results()`
**Purpose:** Fetch latest run per model for detailed results table with V2 metrics

**Process:**
1. Scan SUMMARY items
2. Filter to latest run per model
3. Load S3 judge files to extract V2 metrics (token_count, ends_with_socratic_question, directionally_socratic)
4. Normalize to 0-10 for UI display
5. Return table rows with V2 metrics only (conciseness, ends_with_question, directionally_socratic)

---

## Critical Implementation Details

### V2 Score Scale Normalization

**Judge Output (Raw):** Mixed scales
```python
judge_output = {
  "token_count": 11,                    # Integer (raw token count)
  "ends_with_socratic_question": True,  # Boolean
  "directionally_socratic": 0.85        # Float 0.0-1.0
}
```

**Storage (S3):** Same as above (no conversion)
```json
{
  "token_count": 11,
  "ends_with_socratic_question": true,
  "directionally_socratic": 0.85
}
```

**DynamoDB SUMMARY:** Aggregated V2 metrics
```python
{
  "avg_token_count": 11.0,
  "question_compliance_rate": 1.0,      # 0.0-1.0 → stored as decimal
  "avg_directionally_socratic": 0.85    # 0.0-1.0 → stored as decimal
}
```

**API → UI:** Normalized to 0-10 scale
```python
# API normalization
api_response = {
  "conciseness": 7.5,                   # Inverted token score, 0-10
  "ends_with_question": 10.0,           # question_rate * 10 (1.0 * 10 = 10.0)
  "directionally_socratic": 8.5         # avg_socratic * 10 (0.85 * 10 = 8.5)
}
```

**UI Rendering:** 0-100% for CSS
```javascript
// Bar width calculation
width = model.conciseness * 10 + "%"  // 7.5 * 10 = 75%
```

**Chart Y-Axis:** 0-10 scale
```javascript
scales: {
  y: { min: 0, max: 10 }
}
```

---

### V2 Metric Specifics

**Token Count Scoring:**
- Raw metric: actual token count from model output
- Scoring rule: Inverted (fewer tokens = higher score)
- Ideal range: ~40-100 tokens (clear, concise Socratic questions)
- Too terse (<40): Score reduced (incomplete explanation)
- Too verbose (>100): Score reduced (drifts into lecturing)

**Question Compliance:**
- Rule: Response MUST end with "?" to be considered Socratic
- Scoring: Binary (true/false) → aggregated as % compliance across turns
- Example: 9/10 turns end with "?" = 0.9 compliance = 9.0 on 0-10 scale

**Directionally Socratic:**
- LLM judgment: Is this question-based discovery or lecture?
- Scale: 0.0-1.0 (pure Socratic to pure directive)
- Aggregated: Mean across all turns, then converted to 0-10 scale

---

### Judge Output Format (V2)

**Current Format (Flat Metrics):**
```json
{
  "token_count": 11,
  "ends_with_socratic_question": true,
  "directionally_socratic": 0.85,
  "explanation": "Response asks a probing question without providing answers."
}
```

**Stored Format (S3 + DynamoDB):**
All 3 metrics preserved as-is. No dimension expansion needed.

---

## Access Patterns & Queries

### Common Queries

#### 1. Get All Runs for a Model
```python
response = table.query(
    IndexName="GSI1",
    KeyConditionExpression="GSI1PK = :pk",
    ExpressionAttributeValues={
        ":pk": "MODEL#anthropic.claude-sonnet-4-5-20250929-v1:0"
    }
)
```

#### 2. Get Latest Run for Each Model
```python
# Scan all SUMMARY items
response = table.scan(
    FilterExpression="SK = :sk",
    ExpressionAttributeValues={":sk": "SUMMARY"}
)

# Group by model_id, keep latest by created_at
model_to_latest = {}
for item in response["Items"]:
    model_id = item["model_id"]
    created_at = item["created_at"]

    if model_id not in model_to_latest or created_at > model_to_latest[model_id]["created_at"]:
        model_to_latest[model_id] = item
```

#### 3. Get Weekly Performance
```python
response = table.scan(
    FilterExpression="begins_with(PK, :prefix) AND SK = :sk",
    ExpressionAttributeValues={
        ":prefix": "WEEK#2025-W45#",
        ":sk": "SUMMARY"
    }
)
```

#### 4. Get All Turns and Judges for a Run
```python
# Single query gets everything
response = table.query(
    KeyConditionExpression="PK = :pk",
    ExpressionAttributeValues={
        ":pk": "RUN#01K9HK1C5CPH6VB4HF55X3CGWC"
    }
)

# Filter in code
meta = [item for item in items if item["SK"] == "META"][0]
turns = [item for item in items if item["SK"].startswith("TURN#")]
judges = [item for item in items if item["SK"].startswith("JUDGE#")]
summary = [item for item in items if item["SK"] == "SUMMARY"][0]
```

---

## Cost & Performance

### Monthly Cost Breakdown

| Service | Usage | Cost |
|---------|-------|------|
| **Lambda Invocations** | ~200 invocations/week | $0.10 |
| **Lambda Duration** | ~500 GB-seconds/week | $0.50 |
| **Bedrock (Runner)** | 50 invocations × $0.003/1K tokens | $5.00 |
| **Bedrock (Judge)** | 50 invocations × $0.003/1K tokens | $10.00 |
| **DynamoDB** | ~5K writes, 50K reads/month | $2.00 |
| **S3 Storage** | ~5 GB stored | $0.12 |
| **S3 Requests** | ~10K PUTs, 100K GETs | $0.20 |
| **API Gateway** | ~50K requests/month | $0.05 |
| **CloudFront** | ~100K requests + 5 GB transfer | $2.00 |
| **EventBridge** | ~200 events/month | $0.00 |
| **SQS** | ~200 messages/month | $0.00 |
| **Total** | | **~$22/month** |

---

### Performance Metrics

| Metric | Value | Notes |
|--------|-------|-------|
| **E2E Test Duration** | ~12 minutes | 50 jobs, 25 parallel workers |
| **Single Dialogue** | ~20 seconds | Model invocation + judge + save |
| **Judge Latency** | ~3.5 seconds | Claude 3.5 Sonnet judge call |
| **API P50** | ~200ms | DynamoDB scan + S3 reads |
| **API P99** | ~800ms | Cold start + multiple S3 reads |
| **UI Load Time** | ~2 seconds | 5 API calls + Chart.js render |

---

## Appendix

### Environment Variables (All Lambdas)

```python
TABLE_NAME = "socratic_core"
BUCKET_NAME = "socratic-bench-data-984906149037"
DIALOGUE_QUEUE_URL = "https://sqs.us-east-1.amazonaws.com/.../socratic-dialogue-jobs"
JUDGE_QUEUE_URL = "https://sqs.us-east-1.amazonaws.com/.../socratic-judge-jobs"
EVENT_BUS_NAME = "socratic-bench"
```

### IAM Permissions Summary

| Lambda | DynamoDB | S3 | SQS | Bedrock | EventBridge |
|--------|----------|-----|-----|---------|-------------|
| **Planner** | Read/Write | Read `artifacts/*`, Write `manifests/*` | Send to `dialogue-jobs` | - | - |
| **Runner** | Read/Write | Read `artifacts/*`, Write `raw/*` | Send to `judge-jobs` | InvokeModel | - |
| **Judge** | Read/Write | Write `raw/*` | - | InvokeModel | PutEvents |
| **Curator** | Read/Write | Read `raw/*`, Write `curated/*` | - | - | - |
| **Read API** | Read | Read `curated/*`, `raw/*` | - | - | - |

---

**End of Architecture Document**
