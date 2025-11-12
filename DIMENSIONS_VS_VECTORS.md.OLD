# Dimensions vs Vectors - Complete Explanation

## Quick Answer

**Dimensions (5)** = **HOW WE SCORE** each AI response  
**Vectors (3)** = **WHAT SCENARIO TYPE** we test (the pedagogical approach)

---

## The 5 Dimensions (Scoring Criteria)

Every AI response is scored on these 5 independent criteria:

| Dimension | What It Measures | Scale |
|-----------|------------------|-------|
| `open_ended` | Question invites explanation vs yes/no | 0-100 |
| `probing_depth` | Targets core assumptions vs surface | 0-100 |
| `non_directive` | Pure questioning vs lecturing | 0-100 |
| `age_appropriate` | Matches persona's grade level | 0-100 |
| `content_relevant` | Stays on-topic vs tangent | 0-100 |

**Overall Score** = Average of the 5 dimensions

**Example Judge Output:**
```json
{
  "open_ended": 82,      // Pretty open question
  "probing_depth": 78,    // Good depth
  "non_directive": 85,    // Mostly questioning
  "age_appropriate": 76,  // Decent match to student level
  "content_relevant": 90, // Very on-topic
  "overall": 82.2         // Average
}
```

---

## The 3 Vectors (Scenario Types)

Each test scenario uses ONE of three Socratic teaching techniques:

### 1. Elenchus (Refutation/Contradiction)
**Goal:** Surface contradictions in student's beliefs using their own logic

**Example Scenario:** `EL-ETH-UTIL-DEON-01`
- **Student says:** "I believe in 100% utilitarianism AND that harvesting organs without consent is morally required."
- **AI should:** Ask questions exposing the contradiction between max utility and individual rights
- **AI should NOT:** Lecture about deontology vs consequentialism

**Tested Skill:** Can the AI use questioning to reveal logical inconsistencies?

---

### 2. Maieutics (Scaffolding/Discovery)
**Goal:** Guide student from correct foundation to deeper understanding

**Example Scenario:** `MAI-BIO-CRISPR-01`
- **Student says:** "I know Cas9 cuts DNA like scissors, but how does it know WHERE to cut?"
- **AI should:** Ask questions that guide toward gRNA and PAM concepts
- **AI should NOT:** Explain guide RNA mechanism directly

**Tested Skill:** Can the AI scaffold learning through stepwise questions?

---

### 3. Aporia (Puzzlement/Deconstruction)
**Goal:** Expose misconception, create productive confusion, rebuild understanding

**Example Scenario:** `APO-PHY-HEAT-TEMP-01` (not in current 2-scenario config)
- **Student misconception:** "Metal spoons get hotter so they transfer more heat"
- **AI should:** Ask questions that reveal the heat≠temperature confusion
- **AI should NOT:** Correct the misconception directly

**Tested Skill:** Can the AI deconstruct faulty mental models through questioning?

---

## Why Your Rankings Are Inconsistent

### Problem: Only 2 Scenarios Per Model

Current test configuration:
```json
{
  "scenarios": [
    "EL-ETH-UTIL-DEON-01",  // Elenchus (refutation)
    "MAI-BIO-CRISPR-01"      // Maieutics (scaffolding)
  ]
}
```

Each model gets scored on:
- 1 elenchus scenario → 5 dimension scores
- 1 maieutics scenario → 5 dimension scores
- **Overall = mean of 2 runs**

### Why This Causes Variance

**1. Vector-specific Performance**

Models perform differently on different vectors:

```
Model: Claude 3.5 Haiku
  EL-ETH-UTIL-DEON-01 (elenchus): 82/100
  MAI-BIO-CRISPR-01 (maieutics):  82.2/100
  → Overall: 82.1/100 (8.21/10)

Model: Claude 3.5 Sonnet  
  EL-ETH-UTIL-DEON-01 (elenchus): 82/100
  MAI-BIO-CRISPR-01 (maieutics):  74/100
  → Overall: 78/100 (7.8/10)
```

Claude 3.5 Sonnet is **worse at maieutics** than haiku, so its overall rank drops.

**2. Temperature = 0.7 (Non-Deterministic)**

Models generate different responses on each run:
- Run 1: Might ask "What makes you think...?" → Score: 85
- Run 2: Might ask "Why do you believe...?" → Score: 82

**3. Small Sample Size**

With only 2 scenarios:
- **High variance:** One bad scenario tanks overall score
- **No statistical confidence:** 2 data points can't capture true capability
- **Rankings swing wildly:** A few points difference changes rank dramatically

**4. Dimension Scores Vary by Vector**

Example: `open_ended` score depends on scenario type:
- Elenchus scenarios often trigger leading questions (lower open_ended)
- Maieutics scenarios often elicit pure open questions (higher open_ended)

---

## Example: Why Rankings Change Between Runs

### Run 1 (Your First Test)
```
1. Claude Sonnet 4.5: 6.84/10
2. Llama 4 Maverick: 6.63/10
3. Llama 4 Scout: 6.37/10
```

### Run 2 (After Data Wipe)
```
1. OpenAI GPT-OSS 120B: 8.43/10
2. Llama 3.3 70B: 8.40/10
3. AI21 Jamba: 8.35/10
```

**Why the drastic change?**

1. **Different model responses** (temperature=0.7 randomness)
2. **Judging variance** (same response might score 82 or 85 depending on judge interpretation)
3. **Small sample magnifies differences** (2 scenarios = 50% weight each)

---

## How to Reduce Inconsistency

### Option 1: Add More Scenarios (Recommended)
```json
{
  "scenarios": [
    "EL-ETH-UTIL-DEON-01",     // Elenchus - Ethics
    "EL-CIV-FREE-HARM-01",     // Elenchus - Civics
    "MAI-BIO-CRISPR-01",       // Maieutics - Biology
    "MAI-ECO-INFL-01",         // Maieutics - Economics
    "APO-PHY-HEAT-TEMP-01",    // Aporia - Physics
    "APO-BIO-EVOL-LAM-01"      // Aporia - Biology
  ]
}
```

**Result:** 6 scenarios × 24 models = 144 runs (better statistical confidence)

### Option 2: Run Multiple Times Per Scenario
```json
{
  "runs_per_scenario": 3  // Run each scenario 3x, take median
}
```

**Result:** 2 scenarios × 3 runs × 24 models = 144 runs (averages out randomness)

### Option 3: Lower Temperature
```json
{
  "temperature": 0.3  // More deterministic responses
}
```

**Result:** Reduces response variance, but may make models less "natural"

### Option 4: Use All 9 Available Scenarios
```
Current: 2 scenarios (EL×1, MAI×1, APO×0)
Available: 9 scenarios (EL×2, MAI×2, APO×4)
```

**Result:** 9 scenarios × 24 models = 216 runs (~3x better confidence)

---

## Current State Summary

**What you're testing:**
- 2 scenarios only (1 elenchus, 1 maieutics)
- Temperature 0.7 (some randomness)
- Single run per scenario

**Why rankings change:**
- Small sample size (2 data points per model)
- Models excel at different vectors
- Non-deterministic responses
- Judge scoring has ~±3 point variance

**To get stable rankings:**
- Add at least 3-4 more scenarios
- OR run each scenario 3x and take median
- OR both (9 scenarios × 3 runs = high confidence)

---

## Current Test Configuration

From `s3://socratic-bench-data-984906149037/artifacts/config.json`:

```json
{
  "models": 24,
  "scenarios": 2,
  "scenario_ids": [
    "EL-ETH-UTIL-DEON-01",  // Elenchus (refutation)
    "MAI-BIO-CRISPR-01"      // Maieutics (scaffolding)
  ],
  "temperature": 0.7,
  "max_tokens": 500
}
```

**Missing vectors:** Aporia (misconception deconstruction) - 0 scenarios tested

---

## End
