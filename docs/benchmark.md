# Socratic Disposition Benchmark (SDB)

This document defines the **Socratic Disposition Benchmark (SDB)** — the primary evaluation metric for Phase 1.

---

## Overview

The SDB measures how well LLMs generate Socratic questions that:
- Follow proper **form** (structure and format)
- Have intellectual **substance** (depth of inquiry)
- Maintain **purity** (non-leading, neutral)

Each turn in a dialogue is scored on a **0–10 scale**, broken down into three sub-dimensions.

---

## Scoring Rubric

### Overall Score: 0–10

**Composition**:
- **Form**: 0–3 points
- **Substance**: 0–3 points
- **Purity**: 0–4 points

**Total**: Form + Substance + Purity = 0–10

---

## Sub-Dimensions

### 1. Form (0–3 points)

**What it measures**: Structural adherence to Socratic dialogue conventions.

| Score | Criteria |
|-------|----------|
| **3** | Ends with exactly one question, no advice or statements |
| **2** | Ends with a question but includes minor advice or extra questions |
| **1** | Contains a question but embedded in advice or multiple questions |
| **0** | No question, or question is rhetorical/closed |

**Examples**:

| Response | Score | Rationale |
|----------|-------|-----------|
| "What aspects of your career feel most misaligned with your values?" | 3 | Single question, no advice |
| "That's interesting. What do you mean by 'fulfilling'?" | 2 | Question present but includes statement |
| "Have you considered consulting? What about freelancing?" | 1 | Multiple questions |
| "You should try reflecting on your core values first." | 0 | No question |

---

### 2. Substance (0–3 points)

**What it measures**: Depth of intellectual probing — does the question explore definitions, assumptions, evidence, implications, or alternatives?

| Score | Criteria |
|-------|----------|
| **3** | Probes definition, assumption, evidence, implication, or alternative perspective |
| **2** | Explores surface-level reasoning or clarification |
| **1** | Asks for basic information or facts |
| **0** | No intellectual depth (e.g., yes/no question, small talk) |

**Dimensions of substance**:
- **Definition**: "What do you mean by 'fulfilling'?"
- **Assumption**: "What are you assuming about career success?"
- **Evidence**: "What leads you to believe that?"
- **Implication**: "If that's true, what would it mean for your decision?"
- **Alternative**: "What other perspectives might challenge that view?"

**Examples**:

| Response | Score | Rationale |
|----------|-------|-----------|
| "What assumptions are you making about what constitutes a meaningful career?" | 3 | Probes assumptions |
| "Can you tell me more about why you feel that way?" | 2 | Surface-level exploration |
| "What's your current job title?" | 1 | Basic fact-gathering |
| "Do you like your job?" | 0 | Yes/no question, no depth |

---

### 3. Purity (0–4 points)

**What it measures**: Neutrality and absence of leading, biased, or presumptive language.

| Score | Criteria |
|-------|----------|
| **4** | Completely neutral, no embedded answers or leading language |
| **3** | Mostly neutral with minimal leading (e.g., slight presupposition) |
| **2** | Moderately leading or contains embedded assumptions |
| **1** | Highly leading or suggests a specific answer |
| **0** | Directly states an answer or prescribes a solution |

**Red flags** (reduce purity):
- Embedded answers: "Don't you think...?"
- Loaded terms: "misguided", "clearly", "obviously"
- Presuppositions: "When did you realize...?" (assumes realization occurred)
- Leading: "Wouldn't it be better to...?"

**Examples**:

| Response | Score | Rationale |
|----------|-------|-----------|
| "What factors are you weighing in this decision?" | 4 | Completely neutral |
| "What aspects of your career feel misaligned?" | 3 | "misaligned" slightly leading |
| "Don't you think you should prioritize work-life balance?" | 2 | Embedded suggestion |
| "Isn't it obvious that passion matters more than salary?" | 1 | Highly leading |
| "You need to focus on your strengths first." | 0 | Direct prescription |

---

## Aggregate Metrics

### Overall Score

**Definition**: Mean score across all turns in a dialogue.

**Formula**:
```
overall_score = (sum of all turn scores) / n_turns
```

**Example**:
- Turn 0: 8.5
- Turn 1: 7.0
- Turn 2: 6.5
- Turn 3: 5.0
- Turn 4: 4.0

**Overall Score**: (8.5 + 7.0 + 6.5 + 5.0 + 4.0) / 5 = **6.2**

---

### Compliance Rate

**Definition**: Percentage of turns scoring ≥ 3.0 (threshold for "acceptable" Socratic question).

**Formula**:
```
compliance_rate = (count of turns with score ≥ 3.0) / n_turns
```

**Example** (from above):
- Turns ≥ 3.0: Turn 0 (8.5), Turn 1 (7.0), Turn 2 (6.5), Turn 3 (5.0), Turn 4 (4.0)
- All 5 turns ≥ 3.0

**Compliance Rate**: 5 / 5 = **100%** (1.0)

**Threshold note**: 3.0 represents a "minimally acceptable" Socratic question (1 point in each dimension).

---

### Half-Life

**Definition**: The turn number at which the score first drops below 8.0.

**Purpose**: Measures how quickly the model degrades into advice-giving or loses Socratic discipline.

**Formula**:
```
half_life = first turn index where score < 8.0
```

**Example** (from above):
- Turn 0: 8.5 (≥ 8.0)
- Turn 1: 7.0 (< 8.0) ← **half-life = 1**

**Interpretation**:
- **Higher half-life** = Model maintains Socratic discipline longer
- **Lower half-life** = Model quickly degrades into advice

**Special cases**:
- If all turns score ≥ 8.0: half-life = n_turns
- If first turn scores < 8.0: half-life = 0

---

### Violation Rates

**Definition**: Percentage of turns failing each sub-dimension (scoring 0 points).

**Formula**:
```
form_violation_rate = (count of turns with form = 0) / n_turns
substance_violation_rate = (count of turns with substance = 0) / n_turns
purity_violation_rate = (count of turns with purity = 0) / n_turns
```

**Example**:
- Turn 0: form=3, substance=3, purity=2.5
- Turn 1: form=2, substance=3, purity=2
- Turn 2: form=1, substance=2, purity=1
- Turn 3: form=0, substance=1, purity=2 ← form violation
- Turn 4: form=0, substance=0, purity=0 ← all violations

**Violation Rates**:
- Form: 2 / 5 = **40%**
- Substance: 1 / 5 = **20%**
- Purity: 1 / 5 = **20%**

**Interpretation**:
- **High form violations**: Model gives advice or statements instead of questions
- **High substance violations**: Model asks shallow or yes/no questions
- **High purity violations**: Model uses leading or prescriptive language

---

## Judging Process

### Two-Stage Judging

**Stage 1: Heuristics** (pre-filter)
- Check if response ends with `?`
- Count number of questions
- Detect advice keywords ("should", "try", "recommend")
- Detect leading phrases ("don't you think", "isn't it")

**Stage 2: LLM-as-Judge** (via Bedrock)
- Trusted model: **Claude 3.5 Sonnet v2** (`anthropic.claude-3-5-sonnet-20241022-v1:0`)
- Evaluates form, substance, purity
- Provides rationale for each score
- Outputs JSON with scores + evidence

**Example judge output**:

```json
{
  "overall_score": 8.5,
  "form": 3,
  "substance": 3,
  "purity": 2.5,
  "heuristics": {
    "has_question": true,
    "question_count": 1,
    "open_ended": true,
    "has_advice": false,
    "is_leading": false
  },
  "rationale": {
    "form": "Ends with a single question, no advice given.",
    "substance": "Probes values and assumptions about career alignment.",
    "purity": "Slightly leading with 'misaligned', but mostly neutral."
  }
}
```

### Judge Prompt (High-Level)

```
You are evaluating a Socratic question on three dimensions:

1. Form (0–3): Does it end with exactly one question, no advice?
2. Substance (0–3): Does it probe definition, assumption, evidence, implication, or alternative?
3. Purity (0–4): Is it neutral, non-leading, free of embedded answers?

Score each dimension and provide a brief rationale.
```

---

## File Paths for Results

### S3 Storage

**Raw turns**:
```
s3://{bucket}/raw/runs/{run_id}/turn_000.json
s3://{bucket}/raw/runs/{run_id}/turn_001.json
...
```

**Judge results**:
```
s3://{bucket}/raw/runs/{run_id}/judge_000.json
s3://{bucket}/raw/runs/{run_id}/judge_001.json
...
```

**Curated summary**:
```
s3://{bucket}/curated/runs/{run_id}.json
```

**Weekly aggregate**:
```
s3://{bucket}/curated/weekly/{week}/{model}.json
```

### DynamoDB Items

**Run metadata**:
```
PK: RUN#{run_id}
SK: META
```

**Turn pointer**:
```
PK: RUN#{run_id}
SK: TURN#000
```

**Judge scores**:
```
PK: RUN#{run_id}
SK: JUDGE#000
```

**Run summary**:
```
PK: RUN#{run_id}
SK: SUMMARY
```

**Weekly summary**:
```
PK: WEEK#2025-W45#MODEL#anthropic.claude-3-5-sonnet-20241022-v1:0
SK: SUMMARY
```

---

## Weekly Rollups

### DynamoDB Weekly Summary

**PK**: `WEEK#{yyyy-Www}#MODEL#{model_id}`
**SK**: `SUMMARY`

**Attributes**:
```json
{
  "week": "2025-W45",
  "model": "anthropic.claude-3-5-sonnet-20241022-v1:0",
  "n_runs": 12,
  "n_turns": 60,
  "mean_overall_score": 6.8,
  "mean_compliance_rate": 0.85,
  "mean_half_life": 8.2,
  "mean_form": 2.3,
  "mean_substance": 2.4,
  "mean_purity": 2.1,
  "violation_rates": {
    "form": 0.15,
    "substance": 0.10,
    "purity": 0.25
  }
}
```

### S3 Weekly Summary

**Path**: `s3://{bucket}/curated/weekly/{week}/{model}.json`

**Format**: Same as DynamoDB, with additional metadata:

```json
{
  "week": "2025-W45",
  "model": "anthropic.claude-3-5-sonnet-20241022-v1:0",
  "model_label": "Claude 3.5 Sonnet (extended thinking)",
  "runs": [
    "run-01H7X...",
    "run-01H7Y...",
    ...
  ],
  "metrics": { ... }
}
```

---

## Athena / QuickSight (Optional)

For advanced analytics, you can query S3 data with Athena:

**Create external table**:

```sql
CREATE EXTERNAL TABLE socratic_runs (
  run_id STRING,
  model STRING,
  scenario STRING,
  n_turns INT,
  overall_score DOUBLE,
  compliance_rate DOUBLE,
  half_life INT
)
STORED AS JSON
LOCATION 's3://socratic-benchmark-data/curated/runs/';
```

**Example queries**:

```sql
-- Mean score by model
SELECT model, AVG(overall_score) as mean_score
FROM socratic_runs
GROUP BY model
ORDER BY mean_score DESC;

-- Compliance rate distribution
SELECT
  CASE
    WHEN compliance_rate >= 0.9 THEN 'Excellent'
    WHEN compliance_rate >= 0.7 THEN 'Good'
    ELSE 'Needs improvement'
  END as category,
  COUNT(*) as count
FROM socratic_runs
GROUP BY category;
```

**QuickSight**: Connect to Athena and create dashboards with:
- Model comparison table
- Sparklines for weekly trends
- Violation rate heatmaps

---

## CSD Scoring (Future)

**Conversation-level Socratic Disposition (CSD)** is **out of scope** for Phase 1.

Future phases may add:
- Multi-turn coherence scoring
- Student engagement tracking
- Topic depth progression
- Conversational flow analysis

---

## Related Documentation

- **[README.md](../README.md)** – Overview and quickstart
- **[docs/architecture.md](architecture.md)** – System architecture
- **[docs/runner.md](runner.md)** – Docker CLI usage
- **[docs/bedrock.md](bedrock.md)** – Bedrock routing

---

*Last Updated: 2025-11-05*
