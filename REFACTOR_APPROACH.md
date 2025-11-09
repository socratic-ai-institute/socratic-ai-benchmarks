# Wholesale Refactor Approach: New Vectors + Dimensions

## Goal
Replace current vectors and dimensions with your new definitions while minimizing breakage and maintaining data integrity.

---

## Pre-Refactor: Context Collection Phase

**BEFORE touching any code, I need from you:**

### 1. New Vectors (Scenario Types)
- [ ] How many vectors? (currently 3: elenchus, maieutics, aporia)
- [ ] What are they called?
- [ ] What does each vector test? (1-sentence description each)

### 2. New Dimensions (Scoring Criteria)
- [ ] How many dimensions? (currently 5)
- [ ] What are they called?
- [ ] What does each measure? (with 0-100 rubric if you have it)
- [ ] Overall score = average? Or weighted?

### 3. New Scenarios
- [ ] How many scenarios total?
- [ ] Which vector does each belong to?
- [ ] Provide: scenario_id, student utterance, persona for each
- [ ] OR: just give me the list and I'll structure them

### 4. Backwards Compatibility Requirements
- [ ] Do old test runs need to remain queryable?
- [ ] Can we archive old data and start fresh?
- [ ] Do we need a migration path?

---

## Proposed Refactor Approach: 5-Phase Safe Batches

### **Phase 1: Schema Design (No Code Changes)**
**Duration:** 30 minutes  
**Risk:** Zero

**Tasks:**
1. Document new vector definitions in SCENARIOS.md format
2. Document new dimension rubrics with 0-100 scoring bands
3. Create mapping: old dimensions → new dimensions (if overlap exists)
4. Design new S3 judge file schema
5. Get your approval before proceeding

**Deliverables:**
- `NEW_VECTORS.md` - Complete vector definitions
- `NEW_DIMENSIONS.md` - Complete rubric for each dimension
- `MIGRATION_PLAN.md` - Batch-by-batch execution plan

**Verification:** You review and approve before Phase 2

---

### **Phase 2: Judge Layer Update (Core Scoring Logic)**
**Duration:** 1 hour  
**Risk:** Medium (affects all future scores)

**Files to change:**
```
serverless/lib/socratic_bench/prompts.py
  - turn_judge_prompt() - Update rubric with new dimensions
  
serverless/lib/socratic_bench/judge.py
  - parse_judge_response() - Parse new dimension names from LLM
  
serverless/lambdas/judge/handler.py
  - Save new dimension scores to S3
```

**Batch Acceptance Criteria:**
- [ ] Judge Lambda can be invoked with test scenario
- [ ] Returns new dimension scores in expected format
- [ ] S3 judge file has correct schema
- [ ] No errors in CloudWatch logs

**Rollback:** Revert 3 files, redeploy judge Lambda

**Test BEFORE proceeding to Phase 3:**
```bash
# Invoke judge Lambda with test turn
aws lambda invoke --function-name JudgeFunction --payload '{...}' /tmp/test.json
cat /tmp/test.json | jq '.scores'  # Should show new dimensions
```

---

### **Phase 3: Scenario Definitions (Test Content)**
**Duration:** 45 minutes  
**Risk:** Low (just data)

**Files to change:**
```
serverless/lib/socratic_bench/scenarios.py
  - Replace get_elenchus_scenarios() or add new vector functions
  - Update get_scenario_by_id() to return new scenarios
  
artifacts/config.json (S3)
  - Update scenario IDs to match new scenarios
```

**Batch Acceptance Criteria:**
- [ ] All new scenario IDs defined
- [ ] Each has: id, vector, persona, prompt, num_turns
- [ ] config.json references valid scenario IDs
- [ ] Python import test passes

**Rollback:** Restore old scenarios.py, update config.json

**Test BEFORE Phase 4:**
```python
from socratic_bench.scenarios import get_scenario_by_id
scenario = get_scenario_by_id("YOUR-NEW-SCENARIO-01")
assert scenario["vector"] == "your_new_vector"
```

---

### **Phase 4: Runner + Planner (Orchestration)**
**Duration:** 30 minutes  
**Risk:** Low (just references)

**Files to change:**
```
serverless/lambdas/runner/handler.py
  - Update vector-specific prompt construction (if needed)
  - No changes if prompts are generic
  
serverless/lambdas/planner/handler.py
  - No changes needed (just loads scenarios from config)
```

**Batch Acceptance Criteria:**
- [ ] Planner creates jobs with new scenario IDs
- [ ] Runner loads new scenarios correctly
- [ ] Prompts constructed properly for new vectors

**Rollback:** Revert runner/handler.py

**Test BEFORE Phase 5:**
```bash
# Invoke planner to create manifest
aws lambda invoke --function-name PlannerFunction --payload '{}' /tmp/plan.json

# Check one runner job manually
aws sqs receive-message --queue-url $QUEUE_URL
```

---

### **Phase 5: API + UI (Display Layer)**
**Duration:** 1 hour  
**Risk:** Low (just presentation)

**Files to change:**
```
serverless/lambdas/api/handler.py
  - get_model_comparison() - Extract new dimension names from S3
  - get_detailed_results() - Return new dimension field names
  
serverless/ui/research.html
  - Update radar chart labels (line 412)
  - Update model card labels (lines 675-712)
  - Update table headers (lines 369-371)
  - Update JavaScript field references (lines 753-755)
  
serverless/ui/methodology.html
  - Update dimension definitions
  - Update vector descriptions
```

**Batch Acceptance Criteria:**
- [ ] API returns new dimension names
- [ ] Charts render with new labels
- [ ] Table shows new columns
- [ ] No JavaScript errors in browser console

**Rollback:** Revert 3 files, redeploy

**Test BEFORE declaring done:**
```bash
# API test
curl .../api/model-comparison | jq '.models[0]'

# UI test
# Open browser, check:
# - Radar chart has new dimension labels
# - Model cards show new dimensions
# - Table headers match new dimensions
```

---

### **Phase 6: Documentation + Cleanup**
**Duration:** 30 minutes  
**Risk:** Zero

**Files to update:**
```
ARCHITECTURE.md - Update dimension definitions and vector descriptions
SCENARIOS.md - Replace with new scenario catalog
TERMINOLOGY_DOCUMENTATION.md - Update or archive
methodology.html - Already updated in Phase 5
```

**Archive old data (optional):**
- Export current DynamoDB to CSV
- Save old judge files to archive/ prefix in S3
- Clear tables for fresh start

---

## Execution Strategy

### Option A: Incremental Deploy (Safer)
Deploy each phase separately:
```
Phase 1 → Review → Phase 2 → Deploy → Test → Phase 3 → Deploy → Test → etc.
```

**Pros:** Catch issues early, easy rollback  
**Cons:** 5 separate deployments, takes longer

### Option B: All-at-Once Deploy (Faster)
Make all code changes, test locally, deploy once:
```
Phase 1 → Phase 2-5 (all changes) → Deploy → Test everything
```

**Pros:** One deployment, faster  
**Cons:** If something breaks, harder to isolate

**My recommendation: Option A for safety**

---

## Risk Mitigation

### Before Starting
1. **Backup current state:**
   ```bash
   # Export all DynamoDB data
   aws dynamodb scan --table-name socratic_core > backup_$(date +%s).json
   
   # Save current code snapshot
   git tag refactor-pre-vectors-$(date +%s)
   ```

2. **Create test manifest** with 1 model, 1 scenario for validation

3. **Set up monitoring:**
   - CloudWatch Logs filtered for "Error"
   - Lambda metrics dashboard

### During Refactor
- Syntax check every file before committing
- Test each Lambda independently before integration test
- Keep deprecated field names for 2 weeks (backwards compatibility)

### Rollback Plan
Each phase has explicit rollback:
```bash
# Revert Phase N
git checkout HEAD~1 -- serverless/lambdas/judge/handler.py
cd serverless/infra && cdk deploy

# Or full rollback
git revert HEAD
git push
cd serverless/infra && cdk deploy
```

---

## Critical Dependencies Map

```
Dimension Names Flow:
Judge Prompt (defines dimensions)
  ↓
Judge Lambda (extracts from LLM response)
  ↓
S3 judge_000.json (stores dimension scores)
  ↓
API Lambda (reads S3, normalizes to 0-10)
  ↓
UI (displays dimension labels)

Vector Names Flow:
Scenarios.py (defines vector types)
  ↓
config.json (scenario selection)
  ↓
Planner Lambda (creates jobs)
  ↓
Runner Lambda (loads scenario, constructs prompt)
  ↓
DynamoDB SUMMARY (stores vector type)
```

**Order matters:** Must update in sequence (Judge → Storage → API → UI)

---

## What I Need From You Now

**Before I touch ANY code:**

1. **New Vector Names** - e.g., ["scaffolding", "challenging", "clarifying"]
2. **New Dimension Names** - e.g., ["question_quality", "depth", "neutrality", ...]
3. **How many scenarios** - e.g., "6 scenarios total, 2 per vector"
4. **Scoring rubric** - Do you have specific 0-100 rubrics for each dimension? Or should I draft based on your definitions?

**Once you provide these, I'll:**
1. Create complete schema docs for your review
2. Show you exact file changes (batched)
3. Execute phases 2-6 sequentially with tests between each
4. Document everything

**Time estimate:** 3-4 hours total with testing, assuming clear requirements

---

## Alternative: Minimal Change Approach

If you want to **keep current architecture but add scenarios:**

**Much simpler:**
1. Just add 4-7 new scenarios to scenarios.py
2. Update config.json with new IDs
3. Deploy
4. Run tests
5. Done in 30 minutes

**Would this solve your variance problem?** (More scenarios = more stable rankings)

---

## My Recommendation

**Start simple:** Add 4 more scenarios (6 total) to current system → test stability

**If that's not enough:** Do full refactor with new vectors/dimensions

**What do you think?**

