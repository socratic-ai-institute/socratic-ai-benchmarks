# Socratic Benchmark Terminology Documentation

## Current State Analysis (2025-11-08)

### The Problem: Two Conflicting Naming Systems

We have a **terminology mismatch** between what we measure and what we display:

**Backend (Judge & S3):**
- Measures: **Socratic Consistency Dimensions** (single-turn quality)
- Storage: `open_ended`, `probing_depth`, `non_directive`, `age_appropriate`, `content_relevant`
- Scale: 0-100

**Frontend (UI & API Response):**
- Displays: **Fidelity Test Terminology** (multi-turn persistence - NOT IMPLEMENTED)
- Labels: `persistence`, `cognitive_depth`, `context_adaptation`, `resistance_to_drift`, `memory_preservation`
- Scale: 0-10

### Why This Happened

1. **Phase 1 (Design):** UI was designed for future multi-turn fidelity tests
2. **Phase 2 (MVP):** We implemented single-turn consistency tests
3. **Phase 3 (Workaround):** API maps Socratic names → Fidelity names to fit existing UI

### The Actual Mapping (Live in Production)

```python
# In serverless/lambdas/api/handler.py lines 418-434

# From S3 judge_000.json (0-100 scale):
open_ended = scores.get("open_ended")         # Pure question vs yes/no
probing_depth = scores.get("probing_depth")   # Targets assumptions
non_directive = scores.get("non_directive")   # Questions vs lectures
age_appropriate = scores.get("age_appropriate") # Matches persona level
content_relevant = scores.get("content_relevant") # On-topic vs tangent

# Mapped to UI labels (0-10 scale):
"persistence": open_ended / 10              # MISLEADING NAME
"cognitive_depth": probing_depth / 10       # CORRECT NAME
"context_adaptation": age_appropriate / 10  # SOMEWHAT CORRECT
"resistance_to_drift": non_directive / 10   # MISLEADING NAME
"memory_preservation": content_relevant / 10 # MISLEADING NAME
```

### What Each Dimension ACTUALLY Measures

| Storage Name | UI Name | What It Measures | Scale | Accurate? |
|--------------|---------|------------------|-------|-----------|
| `open_ended` | `persistence` | Does question invite explanation vs yes/no? | 0-100 → 0-10 | ❌ Wrong name |
| `probing_depth` | `cognitive_depth` | Does question target core assumptions? | 0-100 → 0-10 | ✅ Good name |
| `non_directive` | `resistance_to_drift` | Pure questioning vs lecturing/telling? | 0-100 → 0-10 | ⚠️ Confusing |
| `age_appropriate` | `context_adaptation` | Language matches persona level? | 0-100 → 0-10 | ⚠️ Confusing |
| `content_relevant` | `memory_preservation` | Stays on-topic vs goes off-topic? | 0-100 → 0-10 | ❌ Wrong name |

### Why Names Are Misleading

**"Persistence"** (UI) vs `open_ended` (actual):
- ❌ UI suggests: "Does the model persist in Socratic behavior over multiple turns?"
- ✅ Actual: "Is the question open-ended rather than yes/no?"
- **Mismatch severity:** HIGH

**"Resistance to Drift"** (UI) vs `non_directive` (actual):
- ❌ UI suggests: "Does the model resist drifting into lecturing over time?"
- ✅ Actual: "Is the question non-directive vs leading/telling?"
- **Mismatch severity:** MEDIUM

**"Memory Preservation"** (UI) vs `content_relevant` (actual):
- ❌ UI suggests: "Does the model remember earlier conversation context?"
- ✅ Actual: "Does the question stay relevant to the topic?"
- **Mismatch severity:** HIGH

---

## What We Actually Have Deployed

### Test Type: **Socratic Consistency** (Single-Turn)

**Judge:** `anthropic.claude-3-5-sonnet-20240620-v1:0` (temperature=0.3)

**Rubric:** From `serverless/lib/socratic_bench/prompts.py:turn_judge_prompt()`

**Dimensions (0-100 each):**

1. **Open-ended**
   - 90-100: Purely open question ("What makes you think...?")
   - 70-89: Open with minor leading
   - 50-69: Somewhat open but constrains answers
   - 30-49: Binary question with elaboration prompt
   - 0-29: Pure yes/no or closed question

2. **Probing depth**
   - 90-100: Targets core assumption or hidden premise
   - 70-89: Probes reasoning but misses deepest layer
   - 50-69: Asks for clarification of stated position
   - 30-49: Surface-level follow-up
   - 0-29: No probing; mere acknowledgment

3. **Non-directive**
   - 90-100: Pure question with zero hinting
   - 70-89: Question with subtle framing
   - 50-69: Question plus narrowing context
   - 30-49: Leading question implying answer
   - 0-29: Tells answer directly or lectures

4. **Age-appropriate**
   - 90-100: Perfect match to persona level
   - 70-89: Mostly appropriate, minor issues
   - 50-69: Somewhat mismatched (too simple/complex)
   - 30-49: Clearly inappropriate
   - 0-29: Completely wrong level

5. **Content-relevant**
   - 90-100: Directly addresses core subject
   - 70-89: Relevant but slightly tangential
   - 50-69: Loosely connected
   - 30-49: Barely related
   - 0-29: Off-topic

**Overall Score:** Average of 5 dimensions

---

## Storage Locations

### S3: `raw/runs/{run_id}/judge_000.json`
```json
{
  "scores": {
    "open_ended": 75,
    "probing_depth": 82,
    "non_directive": 88,
    "age_appropriate": 85,
    "content_relevant": 90,
    "overall": 84.0
  }
}
```

### DynamoDB: `RUN#xxx` with `SK=SUMMARY`
```python
{
  "overall_score": "84",  # Only stores overall, not dimensions
  "run_id": "...",
  "model_id": "..."
}
```

### DynamoDB: `WEEK#2025-W45#MODEL#xxx` with `SK=SUMMARY`
```python
{
  "mean_score": "83.1",  # Aggregated across runs
  "run_count": 2
}
```

---

## What Fidelity Tests Would Actually Measure (Not Implemented)

If we implement fidelity tests (planned), they would measure:

**Persistence:** Maintains Socratic questioning across 3-5 turns even when tempted to answer
**Cognitive Depth:** Probes progressively deeper each turn
**Context Adaptation:** Adapts questions based on student's evolving understanding
**Resistance to Drift:** Resists pressure to break character ("Just tell me!")
**Memory Preservation:** References earlier conversation context accurately

**These are fundamentally different metrics** requiring multi-turn conversations and different evaluation criteria.

---

---

## RESOLUTION (2025-11-08)

### Implemented: Option A - Rename UI to Match Reality

**Changes Made:**

1. **API Response Fields (Backwards Compatible)**
   - Added accurate Socratic dimension names: `open_ended`, `probing_depth`, `non_directive`, `age_appropriate`, `content_relevant`
   - Kept deprecated fidelity names for 2 weeks: `persistence`, `cognitive_depth`, `context_adaptation`, `resistance_to_drift`, `memory_preservation`
   - Files: `serverless/lambdas/api/handler.py` (lines 430-442, 489-498)

2. **UI Display Labels**
   - Updated Model Comparison cards: "Persistence" → "Open-ended", etc.
   - Updated table headers: "Persistence" → "Open-ended", "Context Adapt." → "Age-appropriate"
   - Updated radar chart labels: All 5 dimensions now use accurate names
   - Updated JavaScript field references to use new names
   - File: `serverless/ui/research.html` (lines 369-371, 412, 675-712, 753-755)

3. **Documentation Updates**
   - ARCHITECTURE.md: Updated API response examples, removed TODO note
   - TERMINOLOGY_DOCUMENTATION.md: Added resolution section (this)
   - UNIFICATION_PLAN.md: Available for reference

### Current Mapping (ACCURATE)

```
Backend (S3)         →  API Response     →  UI Display
---------------         --------------       -----------
open_ended (0-100)  →  open_ended (0-10)  →  "Open-ended"  ✅
probing_depth       →  probing_depth      →  "Probing Depth" ✅
non_directive       →  non_directive      →  "Non-directive" ✅
age_appropriate     →  age_appropriate    →  "Age-appropriate" ✅
content_relevant    →  content_relevant   →  "Content-relevant" ✅
```

### Backwards Compatibility

**Deprecated fields (remove after 2025-11-22):**
- `persistence`, `cognitive_depth`, `context_adaptation`, `resistance_to_drift`, `memory_preservation`

**Migration path:** All old field references will continue working for 2 weeks, allowing gradual updates.

### Future: When Fidelity Tests Launch

Fidelity tests will ADD new dimensions, not replace existing ones:

```json
{
  // Consistency dimensions (single-turn quality)
  "open_ended": 7.5,
  "probing_depth": 8.2,
  "non_directive": 8.8,
  "age_appropriate": 8.5,
  "content_relevant": 9.0,

  // Fidelity dimensions (multi-turn persistence) - FUTURE
  "persistence": 8.1,           // Maintains Socratic behavior over 5 turns
  "cognitive_deepening": 7.8,   // Probes progressively deeper
  "context_memory": 9.2,        // References earlier conversation
  "drift_resistance": 8.5,      // Resists pressure to break character
  "adaptive_scaffolding": 8.3   // Adjusts to student's evolving understanding
}
```

No naming conflicts when both test types coexist.

---

## End of Documentation
