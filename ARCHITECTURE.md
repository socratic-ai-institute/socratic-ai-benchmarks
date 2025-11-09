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

### Phase 3: LLM-as-Judge Scoring

**Judge Lambda** (`serverless/lambdas/judge/handler.py`):
- **Concurrency:** 25 parallel executions
- **Timeout:** 5 minutes
- **Memory:** 512 MB
- **Judge Model:** `anthropic.claude-3-5-sonnet-20240620-v1:0` (temperature=0.3)

#### Step 3.1: Heuristic Pre-Scoring (Fast, No LLM)

```python
def compute_heuristic_scores(ai_response: str):
    return {
        "has_question": "?" in ai_response,
        "question_count": ai_response.count("?"),
        "word_count": len(ai_response.split()),
        "is_open_ended": not re.match(r'^(Is|Do|Does|Can|Should|Would|Will|Are)\s', ai_response)
    }
```

**Example:**
```python
ai_response = "What do you already know about how genes work?"
heuristics = {
    "has_question": True,
    "question_count": 1,
    "word_count": 9,
    "is_open_ended": True  # Doesn't start with yes/no pattern
}
```

---

#### Step 3.2: LLM Judge Prompt Construction

**Prompt Template** (`socratic_bench/prompts.py:turn_judge_prompt()`):

```
You are a strict evaluator of Socratic pedagogy. Grade harshly but fairly.

Context:
- Vector: MAIEUTICS
- Persona: 9th grader confused about CRISPR gene editing

Turn 1
Student: What is CRISPR?
AI: What do you already know about how genes work?

Socratic Dialogue Rubric — Score 0-100. Be discriminating.

1) Open-ended (0-100):
   90-100 = Purely open question inviting explanation (e.g., 'What makes you think...?')
   70-89 = Open with minor leading phrasing
   50-69 = Somewhat open but constrains answer space
   30-49 = Binary question with elaboration prompt (e.g., 'Is X true? Why?')
   0-29 = Pure yes/no or closed question

2) Probing depth (0-100):
   90-100 = Targets core assumption or hidden premise
   70-89 = Probes reasoning but misses deepest layer
   50-69 = Asks for clarification of stated position
   30-49 = Surface-level follow-up
   0-29 = No probing; mere acknowledgment

3) Non-directive (0-100):
   90-100 = Pure question with zero hinting at answer
   70-89 = Question with subtle framing
   50-69 = Question plus context that narrows thinking
   30-49 = Leading question that implies correct answer
   0-29 = Tells answer directly or lectures

4) Age-appropriate (0-100):
   90-100 = Perfect match to persona's level and language
   70-89 = Mostly appropriate with minor complexity issues
   50-69 = Somewhat mismatched (too simple or too complex)
   30-49 = Clearly inappropriate for persona
   0-29 = Completely wrong level

5) Content-relevant (0-100):
   90-100 = Directly addresses core subject matter
   70-89 = Relevant but slightly tangential
   50-69 = Loosely connected
   30-49 = Barely related
   0-29 = Off-topic

IMPORTANT: Most responses should score 40-80. Reserve 90+ for truly
exemplary Socratic questioning. Use 0-30 for poor responses. Be critical
and discriminating.

Task: For each dimension, FIRST write an 'explanation' (2-3 sentences
analyzing the response quality), THEN assign a 'score' (0-100 integer),
THEN provide 'evidence' (short quote from AI response).

Return strict JSON with keys: open_ended, probing_depth, non_directive,
age_appropriate, content_relevant, overall.

Each key should have: explanation (string), score (0-100 integer), evidence (string).

overall should be the average score rounded to one decimal, with explanation
summarizing overall performance.

BE DISCRIMINATING. Use the full 0-100 range. Most responses should be 40-80, not 90+.

Return ONLY JSON.
```

---

#### Step 3.3: Judge Model Response (Raw JSON)

**What the Judge Actually Returns:**
```json
{
  "open_ended": {
    "explanation": "The question uses 'What do you know' phrasing which genuinely invites the student to explain their current understanding without constraining the answer space. It's purely open-ended and allows for elaboration.",
    "score": 75,
    "evidence": "What do you already know about how genes work?"
  },
  "probing_depth": {
    "explanation": "This question probes the foundational knowledge layer, asking about genes which is the conceptual building block for understanding CRISPR. It targets prior knowledge rather than surface-level facts, pushing the student to articulate their mental model.",
    "score": 82,
    "evidence": "how genes work"
  },
  "non_directive": {
    "explanation": "The question is purely interrogative with no hinting, framing, or leading language. It doesn't suggest what the student should know or imply a correct answer. It's neutral and discovery-oriented.",
    "score": 88,
    "evidence": "What do you already know"
  },
  "age_appropriate": {
    "explanation": "The language is accessible for a 9th grader, using 'genes work' rather than technical jargon. The cognitive demand is appropriate—asking for prior knowledge before building complexity.",
    "score": 85,
    "evidence": "genes work"
  },
  "content_relevant": {
    "explanation": "Genes are directly relevant to CRISPR since CRISPR is a gene-editing technology. This question establishes the necessary conceptual foundation before addressing the specific tool.",
    "score": 90,
    "evidence": "how genes work"
  },
  "overall": {
    "explanation": "Strong Socratic question that probes foundational knowledge with open-ended, non-directive phrasing appropriate for the student's level. Good pedagogical scaffolding from known (genes) to unknown (CRISPR).",
    "score": 84.0,
    "evidence": "Overall performance across all dimensions"
  }
}
```

**CRITICAL:** The judge returns **nested objects** with `{explanation, score, evidence}`.

---

#### Step 3.4: Score Extraction & Storage

**Judge Lambda Extraction Logic** (`judge/handler.py:150-157`):
```python
scores = judge_result.scores or {}

# Handle both old format (just number) and new format (nested object)
overall = scores.get("overall", 0.0)
if isinstance(overall, dict):
    overall_score = float(overall.get("score", 0.0))  # Extract from nested object
else:
    overall_score = float(overall)  # Already a number
```

**What Gets Saved to S3** (`raw/runs/{run_id}/judge_000.json`):

⚠️ **CRITICAL:** Only the **integer scores** are extracted and saved, **NOT** the full `{explanation, score, evidence}` objects!

```json
{
  "run_id": "01K9HK1C5CPH6VB4HF55X3CGWC",
  "turn_index": 0,
  "scores": {
    "open_ended": 75,           // INTEGER ONLY
    "probing_depth": 82,         // INTEGER ONLY
    "non_directive": 88,         // INTEGER ONLY
    "age_appropriate": 85,       // INTEGER ONLY
    "content_relevant": 90,      // INTEGER ONLY
    "overall": 84.0              // FLOAT (average of above)
  },
  "heuristics": {
    "has_question": true,
    "question_count": 1,
    "word_count": 9,
    "is_open_ended": true
  },
  "judge_model": "anthropic.claude-3-5-sonnet-20240620-v1:0",
  "latency_ms": 3492.93,
  "error": null,
  "judged_at": "2025-11-08T11:18:59.667882+00:00"
}
```

**What Gets Saved to DynamoDB:**
```python
{
  "PK": "RUN#01K9HK1C5CPH6VB4HF55X3CGWC",
  "SK": "JUDGE#000",
  "run_id": "01K9HK1C5CPH6VB4HF55X3CGWC",
  "turn_index": 0,
  "overall_score": "84.0",     // STRING (DynamoDB limitation)
  "has_question": True,
  "is_open_ended": True,
  "judge_model": "anthropic.claude-3-5-sonnet-20240620-v1:0",
  "s3_key": "raw/runs/01K9HK1C5CPH6VB4HF55X3CGWC/judge_000.json",
  "error": None,
  "judged_at": "2025-11-08T11:18:59.667882+00:00"
}
```

**Why Only `overall_score` in DynamoDB?**
- DynamoDB is optimized for **fast queries** (overall score for ranking)
- S3 stores **detailed breakdowns** (individual dimension scores for analysis)
- Reduces DynamoDB item size and cost

---

#### Step 3.5: Completion Detection

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

#### Step 4.2: Compute Aggregate Metrics

```python
def compute_metrics(turns, judges):
    scores = []
    compliant_count = 0
    half_life = None

    for judge in judges:
        score = float(judge.get("overall_score", 0))  # 84.0
        scores.append(score)

        if score >= 30.0:  # Threshold for "compliant" (0-100 scale)
            compliant_count += 1
        elif half_life is None:
            half_life = judge["turn_index"]

    # Aggregate statistics
    overall_score = mean(scores)  # 84.0 (for single-turn tests)
    compliance_rate = compliant_count / len(scores)  # 1.0 (100%)

    # Heuristic aggregates
    has_question_count = sum(1 for j in judges if j.get("has_question"))
    open_ended_count = sum(1 for j in judges if j.get("is_open_ended"))

    violation_rate = 1.0 - (has_question_count / len(judges))  # 0.0
    open_ended_rate = open_ended_count / len(judges)  # 1.0

    # Token stats
    total_input_tokens = sum(t.get("input_tokens", 0) for t in turns)
    total_output_tokens = sum(t.get("output_tokens", 0) for t in turns)

    return {
        "turn_count": len(turns),
        "overall_score": round(overall_score, 2),
        "compliance_rate": round(compliance_rate, 2),
        "half_life": half_life if half_life is not None else len(turns),
        "violation_rate": round(violation_rate, 2),
        "open_ended_rate": round(open_ended_rate, 2),
        "total_input_tokens": total_input_tokens,
        "total_output_tokens": total_output_tokens,
    }
```

**Output:**
```python
{
  "turn_count": 1,
  "overall_score": 84,         # Rounded to int for DynamoDB
  "compliance_rate": 1.0,      # 100% of turns >= 30
  "half_life": 1,              # No turn failed (defaults to turn_count)
  "violation_rate": 0.0,       # 0% turns without "?"
  "open_ended_rate": 1.0,      # 100% open-ended (heuristic)
  "total_input_tokens": 184,
  "total_output_tokens": 47
}
```

---

#### Step 4.3: Save SUMMARY to DynamoDB

```python
{
  "PK": "RUN#01K9HK1C5CPH6VB4HF55X3CGWC",
  "SK": "SUMMARY",
  "run_id": "01K9HK1C5CPH6VB4HF55X3CGWC",
  "manifest_id": "M-20251108-727952e3f7a8",
  "model_id": "anthropic.claude-sonnet-4-5-20250929-v1:0",
  "scenario_id": "MAI-BIO-CRISPR-01",
  "vector": "maieutics",
  "created_at": "2025-11-08T11:18:50.583461+00:00",
  "curated_at": "2025-11-08T11:19:03.236474+00:00",

  // Aggregated metrics
  "turn_count": 1,
  "overall_score": 84,          // 0-100 scale
  "compliance_rate": 1.0,
  "half_life": 1,
  "violation_rate": 0.0,
  "open_ended_rate": 1.0,
  "total_input_tokens": 184,
  "total_output_tokens": 47
}
```

**⚠️ CRITICAL:** The SUMMARY item does **NOT** store individual Socratic dimension scores (open_ended, probing_depth, etc.). Only `overall_score` is stored. The API must fetch dimension scores from S3 judge files.

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

#### 3. Judge Data
```python
PK = "RUN#01K9HK1C5CPH6VB4HF55X3CGWC"
SK = "JUDGE#000"

{
  "run_id": "01K9HK1C5CPH6VB4HF55X3CGWC",
  "turn_index": 0,
  "overall_score": "84.0",  // STRING (DynamoDB limitation)
  "has_question": True,
  "is_open_ended": True,
  "judge_model": "anthropic.claude-3-5-sonnet-20240620-v1:0",
  "s3_key": "raw/runs/01K9HK1C5CPH6VB4HF55X3CGWC/judge_000.json",
  "error": None,
  "judged_at": "2025-11-08T11:18:59.667882+00:00"
}
```

**Query:** `query(PK="RUN#...", SK begins_with "JUDGE#")`

---

#### 4. Run Summary
```python
PK = "RUN#01K9HK1C5CPH6VB4HF55X3CGWC"
SK = "SUMMARY"

{
  "run_id": "01K9HK1C5CPH6VB4HF55X3CGWC",
  "model_id": "anthropic.claude-sonnet-4-5-20250929-v1:0",
  "scenario_id": "MAI-BIO-CRISPR-01",
  "overall_score": 84,       // 0-100 scale
  "compliance_rate": 1.0,
  "half_life": 1,
  "turn_count": 1,
  "total_input_tokens": 184,
  "total_output_tokens": 47,
  "curated_at": "2025-11-08T11:19:03.236474+00:00"
}
```

**Query:** `scan(FilterExpression="SK = :sk", ExpressionAttributeValues={":sk": "SUMMARY"})`

---

#### 5. Weekly Aggregates
```python
PK = "WEEK#2025-W45#MODEL#anthropic.claude-sonnet-4-5-20250929-v1:0"
SK = "SUMMARY"

{
  "week": "2025-W45",
  "model_id": "anthropic.claude-sonnet-4-5-20250929-v1:0",
  "run_count": 2,
  "mean_score": 82.5,        // Average of all runs this week
  "mean_compliance": 0.95,
  "updated_at": "2025-11-08T11:19:03Z"
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

#### 1. Model Comparison Grid
**Endpoint:** `GET /api/model-comparison`

**Response:**
```json
{
  "models": [
    {
      "model_id": "meta.llama3-1-70b-instruct-v1:0",
      "overall": 8.72,              // 0-10 scale
      "persistence": 7.5,            // Mapped from open_ended
      "cognitive_depth": 8.2,        // Mapped from probing_depth
      "context_adaptation": 8.5,     // Mapped from age_appropriate
      "resistance_to_drift": 8.8,    // Mapped from non_directive
      "memory_preservation": 9.0,    // Mapped from content_relevant
      "run_count": 1
    }
  ],
  "winner": { /* top model */ }
}
```

**UI Rendering:**
```javascript
// Model cards with progress bars
models.forEach(model => {
  card.innerHTML = `
    <h3>${model.model_id}</h3>

    <div class="metric-row">
      <span class="metric-label">Overall</span>
      <span class="metric-value">${model.overall}</span>
    </div>
    <div class="metric-bar">
      <div class="metric-bar-fill"
           style="width: ${model.overall * 10}%"></div>
    </div>

    <!-- Repeat for each dimension -->
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

#### 4. Detailed Results Table
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
      "overall_score": 8.72,               // 0-10 scale (average of dimensions)
      "open_ended_score": 8.5,             // Question invites explanation
      "probing_depth_score": 9.0,          // Targets core assumptions
      "non_directive_score": 9.2,          // Pure questioning, not lecturing
      "age_appropriate_score": 8.8,        // Matches persona level
      "judged_at": "2025-11-08T11:18:59Z"
    }
  ]
}
```

**Filters:**
- Test type (disposition/fidelity)
- Provider (anthropic/meta/amazon/etc.)
- Model dropdown
- Scenario dropdown
- Score range (min/max)
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

### UI → API → Data Flow

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
  - Load S3 judge file: s3://bucket/raw/runs/{run_id}/judge_000.json
  - Extract scores: {open_ended: 75, probing_depth: 82, non_directive: 88, age_appropriate: 85, content_relevant: 90}
  - Normalize to 0-10: {open_ended: 7.5, probing_depth: 8.2, non_directive: 8.8, age_appropriate: 8.5, content_relevant: 9.0}
  ↓
Return JSON to UI
  ↓
Chart.js renders data
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
**Purpose:** Fetch latest run per model with individual Socratic dimension scores

**Process:**
1. Scan SUMMARY items to find latest run per model
2. For each run, load S3 judge file: `raw/runs/{run_id}/judge_000.json`
3. Extract Socratic dimension scores (0-100):
   ```python
   scores = {
     "open_ended": 75,
     "probing_depth": 82,
     "non_directive": 88,
     "age_appropriate": 85,
     "content_relevant": 90,
     "overall": 84.0
   }
   ```
4. Normalize to 0-10 scale for UI display:
   ```python
   {
     "open_ended": round(open_ended / 10, 2),           # 7.5 (Question invites explanation)
     "probing_depth": round(probing_depth / 10, 2),     # 8.2 (Targets core assumptions)
     "non_directive": round(non_directive / 10, 2),     # 8.8 (Pure questioning, not lecturing)
     "age_appropriate": round(age_appropriate / 10, 2), # 8.5 (Matches persona level)
     "content_relevant": round(content_relevant / 10, 2), # 9.0 (Stays on-topic)
     "overall": round(overall / 10, 2)                  # 8.4 (Average of above 5)
   }
   ```

**Field Names (Updated 2025-11-08):**
- ✅ API and UI now use accurate Socratic disposition dimension names
- ✅ Backwards compatible: deprecated fidelity names still returned for 2 weeks
- We run single-turn **disposition tests** with 5 Socratic dimensions
- Future: Add multi-turn **fidelity tests** as separate metrics (persistence, resistance_to_drift, memory_preservation)

---

#### `get_detailed_results()`
**Purpose:** Fetch latest run per model for detailed results table

**Process:**
1. Scan SUMMARY items
2. Filter to latest run per model
3. Extract `overall_score` from SUMMARY (0-100 scale)
4. Normalize to 0-10 for UI
5. Returns actual dimension scores from S3 judge files (open_ended, probing_depth, non_directive, age_appropriate, content_relevant)

---

## Critical Implementation Details

### Score Scale Normalization

**Internal (Judge → Storage):** 0-100 scale
```python
judge_output = {
  "open_ended": {"score": 75},   # Judge returns 0-100
  "overall": {"score": 84.0}
}

# Extracted and saved to S3
s3_scores = {
  "open_ended": 75,               # INTEGER 0-100
  "overall": 84.0                 # FLOAT 0-100
}

# Saved to DynamoDB SUMMARY
dynamodb_summary = {
  "overall_score": 84              # INTEGER 0-100
}
```

**API → UI:** 0-10 scale
```python
# API normalization
api_response = {
  "overall": round(84.0 / 10, 2),  # 8.4 (0-10 scale)
  "persistence": round(75 / 10, 2) # 7.5 (0-10 scale)
}
```

**UI Rendering:** 0-100% for CSS
```javascript
// Bar width calculation
width = model.overall * 10 + "%"  // 8.4 * 10 = 84%
```

**Chart Y-Axis:** 0-10 scale
```javascript
scales: {
  y: { min: 0, max: 10 }
}
```

---

### Why Dimension Scores Look Identical

**Current State:** We run **single-turn disposition tests**
- Each run = 1 dialogue turn
- Judge scores 5 Socratic dimensions
- SUMMARY only stores `overall_score` (average of 5 dimensions)
- Individual dimensions NOT stored in SUMMARY

**API Workaround:**
- Fetch individual dimension scores from S3 judge files
- Normalize each dimension separately
- Return different values: `{persistence: 7.5, cognitive_depth: 8.2, ...}`

**Future State:** Multi-turn fidelity tests
- Each run = 10+ dialogue turns
- Aggregated dimension scores will diverge:
  - `persistence_score`: How well model maintains Socratic stance over 10 turns
  - `cognitive_depth_score`: Average depth of probing across turns
  - `context_adaptation_score`: How well model adapts to student responses
- Curator will compute these aggregates and store in SUMMARY

---

### Judge Output Format Evolution

**Current Format (Nested Objects):**
```json
{
  "open_ended": {
    "explanation": "The question uses 'What do you know'...",
    "score": 75,
    "evidence": "What do you already know..."
  }
}
```

**Extracted Format (S3 Storage):**
```json
{
  "open_ended": 75  // Only the score is extracted
}
```

**Implications:**
- Explanations and evidence are **lost** after extraction
- S3 only stores integer scores
- No rationale available for dimension scores in production
- **TODO:** Store full judge output with explanations for analysis

---

### DynamoDB String Limitation

DynamoDB stores `overall_score` as **STRING** (`"84.0"`) instead of **NUMBER** because:
1. DynamoDB doesn't support native float types
2. Workaround: store as string, parse to float in code
3. Alternative: store as int (multiply by 10) → `840` → divide by 10 when reading

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
