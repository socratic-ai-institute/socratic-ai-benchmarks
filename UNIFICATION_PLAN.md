# Terminology Unification Plan

## Goal
Unify naming between backend (Socratic dimensions) and frontend (UI labels) **without breaking anything currently working**.

---

## Option A: Rename UI to Match Reality (RECOMMENDED)

**Change:** Update UI labels to accurately reflect what we measure (Socratic consistency dimensions)

**Impact:** Visual only - no API breaking changes

### Changes Required

#### 1. Update API Response Field Names
**File:** `serverless/lambdas/api/handler.py`

**Current mapping:**
```python
"persistence": round(open_ended / 10, 2)
"cognitive_depth": round(probing_depth / 10, 2)
"context_adaptation": round(age_appropriate / 10, 2)
"resistance_to_drift": round(non_directive / 10, 2)
"memory_preservation": round(content_relevant / 10, 2)
```

**New mapping (accurate names):**
```python
"open_ended": round(open_ended / 10, 2)
"probing_depth": round(probing_depth / 10, 2)  # Keep same
"non_directive": round(non_directive / 10, 2)
"age_appropriate": round(age_appropriate / 10, 2)
"content_relevant": round(content_relevant / 10, 2)
```

#### 2. Update UI Display Labels
**File:** `serverless/ui/research.html`

**Lines 665-712** (Model Comparison Cards):
```html
<!-- BEFORE -->
<span class="metric-label">Persistence</span>
<span class="metric-value">${model.persistence}</span>

<!-- AFTER -->
<span class="metric-label">Open-ended</span>
<span class="metric-value">${model.open_ended}</span>
```

**Lines 675-680, 683-688, 691-696, 699-704, 707-712:**
- "Persistence" → "Open-ended"
- "Cognitive Depth" → "Probing Depth" (keep similar)
- "Context Adaptability" → "Age-appropriate"
- "Resistance to Drift" → "Non-directive"
- "Memory Preservation" → "Content-relevant"

#### 3. Update Chart Labels
**Lines 412** (Radar chart labels):
```javascript
// BEFORE
"labels": ["Persistence", "Cognitive Depth", "Context Adaptability", "Resistance to Drift", "Memory Preservation"]

// AFTER
"labels": ["Open-ended", "Probing Depth", "Non-directive", "Age-appropriate", "Content-relevant"]
```

#### 4. Update Table Headers
**Lines 369-371** (Detailed Results table):
```html
<!-- BEFORE -->
<th>Persistence</th>
<th>Cognitive Depth</th>
<th>Context Adapt.</th>

<!-- AFTER -->
<th>Open-ended</th>
<th>Probing Depth</th>
<th>Age-appropriate</th>
```

**Lines 752-756** (Table body data mapping):
```javascript
// Update field references
result.open_ended_score  // was persistence_score
result.probing_depth_score  // unchanged
result.age_appropriate_score  // was context_adaptation_score
```

### Pros
- ✅ Accurate terminology
- ✅ Matches backend storage
- ✅ Aligns with documentation
- ✅ Makes future fidelity tests easier to add

### Cons
- ⚠️ Users must learn new terms
- ⚠️ Visual change (charts/tables relabel)

---

## Option B: Keep Current Names, Add Footnote

**Change:** Keep misleading names but add clear explanation in UI

**Impact:** No code changes, just add explanatory text

### Changes Required

Add disclaimer to `serverless/ui/research.html` at line 285:

```html
<div class="section">
    <h2 class="section-title">Model Comparison</h2>
    <div style="background: #fff3cd; border: 1px solid #ffc107; padding: 1rem; border-radius: 8px; margin-bottom: 1.5rem;">
        <strong>Note on Metrics:</strong> Current tests measure single-turn Socratic consistency.
        Dimension names below were designed for multi-turn fidelity tests (coming soon):
        <ul style="margin: 0.5rem 0 0 1.5rem; font-size: 0.9rem;">
            <li><strong>Persistence</strong> = Open-ended questioning</li>
            <li><strong>Cognitive Depth</strong> = Probing depth</li>
            <li><strong>Context Adaptation</strong> = Age-appropriate language</li>
            <li><strong>Resistance to Drift</strong> = Non-directive questioning</li>
            <li><strong>Memory Preservation</strong> = Content relevance</li>
        </ul>
    </div>
    <div id="model-comparison" class="model-comparison">
```

### Pros
- ✅ No breaking changes
- ✅ Quick to implement

### Cons
- ❌ Still misleading
- ❌ Adds UI clutter
- ❌ Doesn't fix the actual problem

---

## Option C: Hybrid Approach

**Change:** Use accurate names internally, but keep friendly labels with tooltips

**Impact:** Moderate code changes

### Implementation

1. API returns accurate field names (Option A)
2. UI displays user-friendly labels with tooltips explaining what they measure
3. Add "(Single-turn)" tag to overall page title

**Example:**
```html
<span class="metric-label">
    Open-ended 
    <span class="tooltip" title="Does the question invite explanation vs yes/no?">ⓘ</span>
</span>
```

### Pros
- ✅ Accurate API
- ✅ User-friendly labels
- ✅ Educational tooltips

### Cons
- ⚠️ More implementation work
- ⚠️ Need to design tooltip UI

---

## Recommended Path: **Option A**

### Why
1. **Accuracy:** Names reflect what we actually measure
2. **Simplicity:** Clean 1:1 mapping backend → frontend
3. **Future-proof:** When fidelity tests launch, we add NEW fields (no confusion)
4. **Documentation:** Aligns with SCENARIOS.md and ARCHITECTURE.md

### Migration Steps

**Phase 1: Backend (No Breaking Changes)**
1. Add NEW fields to API responses with accurate names
2. Keep OLD fields for backwards compatibility (deprecated)
3. Deploy API changes

**Phase 2: Frontend**
4. Update UI to read from NEW fields
5. Update all display labels
6. Deploy UI changes

**Phase 3: Cleanup**
7. Remove OLD deprecated fields from API (after 2 weeks)

---

## Implementation Checklist

### Step 1: API Update (Backwards Compatible)
- [ ] `serverless/lambdas/api/handler.py` - Add new fields alongside old ones
- [ ] Test `/api/model-comparison` returns both old & new fields
- [ ] Test `/api/detailed-results` returns both old & new fields
- [ ] Deploy API changes

### Step 2: UI Update
- [ ] `serverless/ui/research.html` - Update all labels
- [ ] Update radar chart labels
- [ ] Update table headers
- [ ] Update JavaScript field references
- [ ] Test charts render correctly
- [ ] Deploy UI changes

### Step 3: Documentation
- [ ] Update ARCHITECTURE.md with correct terminology
- [ ] Add TERMINOLOGY_DOCUMENTATION.md to repo
- [ ] Update API documentation
- [ ] Add migration notes

### Step 4: Cleanup (2 weeks later)
- [ ] Remove deprecated fields from API
- [ ] Final deployment

---

## Timeline

- **Week 1:** Implement backwards-compatible API changes
- **Week 2:** Update UI to use new fields
- **Week 3:** Monitor for issues
- **Week 4:** Remove deprecated fields

---

## Rollback Plan

If anything breaks:
1. Revert UI to read old fields (5 minute fix)
2. Keep both field sets in API indefinitely
3. No data loss - everything still works

---

## End of Plan
