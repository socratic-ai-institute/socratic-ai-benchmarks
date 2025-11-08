# Dashboard Visualization Implementation Plan

## ⚠️ COMPLEXITY CHECK: Is This Too Complicated?

### Current Situation
- ✅ We have a working dashboard at https://d3ic7ds776p9cq.cloudfront.net
- ✅ Infrastructure is deployed and operational
- ⚠️ BUT: No actual run data yet (models aren't all working)
- ⚠️ We're building visualizations for data we don't have yet

### Reality Check Questions

**Q1: Do we have data to visualize?**
- Current: Maybe 1-2 successful runs (out of 48 attempted)
- Time-series needs: Multiple weeks of data (we have 0 weeks)
- **PROBLEM**: Building time-series before we have time-series data

**Q2: Should we fix the pipeline first?**
- 20+ models failing (need inference profiles)
- Amazon Nova/Cohere not supported (need provider code)
- **RISK**: Building dashboards for broken pipeline

**Q3: Can we show empty states gracefully?**
- Yes, we can show "No data yet" messages
- Charts can render with sample/mock data
- **SOLUTION**: Build with mock data, swap in real data later

### Decision: Simplified Approach

**PHASE 1: Get Data Flowing (PRIORITY)**
1. Fix the model support issues first
2. Get one complete weekly run
3. Validate data is being stored correctly

**PHASE 2: Basic Visualizations (SIMPLIFIED)**
1. Simple bar chart: Latest scores per model
2. Simple table: Raw metrics (what we have now)
3. Status indicator: Last run timestamp

**PHASE 3: Advanced Visualizations (FUTURE)**
1. Time-series (after 3+ weeks of data)
2. Heatmaps (after enough runs)
3. Interactive explorers

---

## SIMPLIFIED PLAN (Recommended)

### What We'll Build NOW

**1. Current Snapshot Dashboard** (Easy, works with 1 run)
```
┌─────────────────────────────────────────────────┐
│ Last Updated: 2025-11-05 17:40 UTC             │
│ Total Models: 24 | Successful Runs: 8          │
├─────────────────────────────────────────────────┤
│ TOP PERFORMERS (Latest Run)                     │
│ ┌─────────────────────────────────────────────┐ │
│ │ Claude Sonnet 4.5        ████████ 6.84/10   │ │
│ │ Llama 4 Maverick         ███████  6.63/10   │ │
│ │ Llama 4 Scout            ██████   6.37/10   │ │
│ │ ...                                          │ │
│ └─────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────┤
│ COST BREAKDOWN (Latest Run)                     │
│ Total Cost: $2.45 | Avg per Model: $0.10       │
│ ┌─────────────────────────────────────────────┐ │
│ │ [Pie Chart: Cost by Provider]               │ │
│ │ Anthropic: 45% | Meta: 30% | Others: 25%    │ │
│ └─────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────┤
│ QUICK STATS                                     │
│ • Models tested: 24                             │
│ • Total turns: 120 (5 per model)               │
│ • Avg score: 5.2/10                            │
│ • Best scenario: Utilitarianism (5.8/10)       │
└─────────────────────────────────────────────────┘
```

**Why This is Better:**
- ✅ Works with current data (even just 1 run)
- ✅ Simple: bar charts + tables (no complex D3.js)
- ✅ Fast to build: 2-3 hours vs 2-3 days
- ✅ Still valuable: shows key insights
- ✅ No backend changes needed (use existing data)

**2. Data Status Page** (Critical for transparency)
```
┌─────────────────────────────────────────────────┐
│ SYSTEM STATUS                                   │
├─────────────────────────────────────────────────┤
│ Last Run: 2025-11-05 17:40 UTC ✅              │
│ Next Scheduled: 2025-11-11 03:00 UTC           │
│                                                 │
│ MODEL STATUS:                                   │
│ ✅ Working (8):  Claude 3 Sonnet, Mistral...   │
│ ⚠️  Partial (12): Need inference profiles       │
│ ❌ Failed (4):   Need provider support          │
│                                                 │
│ [View detailed logs] [Trigger manual run]      │
└─────────────────────────────────────────────────┘
```

**Why This is Critical:**
- Shows what's actually working
- Sets expectations (24 models configured, 8 working)
- Helps debug (links to logs)

---

## DETAILED IMPLEMENTATION PLAN (Simplified)

### Step 1: Audit Current Data (30 minutes)

**Task**: Check what data actually exists in DynamoDB/S3

```bash
# Query DynamoDB for any SUMMARY items
aws dynamodb scan \
  --table-name socratic_core \
  --filter-expression "begins_with(SK, :sk)" \
  --expression-attribute-values '{":sk":{"S":"SUMMARY"}}' \
  --profile mvp

# Check S3 for curated runs
aws s3 ls s3://socratic-bench-data-984906149037/curated/runs/ --profile mvp
```

**Outcomes**:
- [ ] Count: How many successful runs do we have?
- [ ] Structure: Does data match expected schema?
- [ ] Quality: Are scores/metrics present?

**Decision Point**: 
- If 0 runs: Build mock data dashboard
- If 1-5 runs: Build snapshot dashboard
- If 10+ runs: Consider time-series

---

### Step 2: Create Simple API Endpoint (1 hour)

**File**: `serverless/lambdas/api/handler.py`

Add ONE new endpoint:

```python
def get_latest_snapshot(event, context):
    """
    GET /api/snapshot
    
    Returns:
    {
        "last_run_time": "2025-11-05T17:40:00Z",
        "total_runs": 48,
        "successful_runs": 8,
        "models": [
            {
                "model_id": "anthropic.claude-sonnet-4-5",
                "name": "Claude Sonnet 4.5",
                "score": 6.84,
                "cost": 0.15,
                "status": "success"
            },
            ...
        ]
    }
    """
    # Query DynamoDB for all SUMMARY items
    # Sort by score
    # Return top 10 + stats
```

**Complexity**: LOW
- Single DynamoDB scan (we have < 100 items)
- Basic aggregation (sum, average)
- JSON response (already working)

**Test**:
```bash
curl https://wcyf23uxxe.execute-api.us-east-1.amazonaws.com/prod/api/snapshot
```

---

### Step 3: Update Dashboard HTML (2 hours)

**File**: `serverless/ui/index.html`

**Current**: Static HTML with placeholder data  
**New**: Fetch from API, render charts

**Changes**:
1. Add Chart.js library (CDN, no build step)
2. Fetch `/api/snapshot` on page load
3. Render 3 simple charts:
   - Bar chart: Model scores
   - Pie chart: Cost by provider
   - Table: Top 10 models

**Code Sketch**:
```html
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script>
async function loadData() {
    const response = await fetch('/api/snapshot');
    const data = await response.json();
    
    // Bar chart: scores
    new Chart(document.getElementById('scoresChart'), {
        type: 'bar',
        data: {
            labels: data.models.map(m => m.name),
            datasets: [{
                label: 'Score',
                data: data.models.map(m => m.score)
            }]
        }
    });
    
    // Pie chart: costs
    // Table: models
}

loadData();
</script>
```

**Complexity**: LOW
- Chart.js is beginner-friendly
- No React/Vue/complex framework
- Just vanilla JS + Chart.js

---

### Step 4: Add Status Indicators (30 minutes)

Show system health:
```html
<div class="status">
    <div class="metric">
        <span class="label">Last Run:</span>
        <span class="value" id="lastRun">Loading...</span>
    </div>
    <div class="metric">
        <span class="label">Models Working:</span>
        <span class="value" id="modelsWorking">8 / 24</span>
    </div>
</div>
```

**Complexity**: TRIVIAL
- Just display numbers from API
- Color code: green = good, yellow = partial, red = broken

---

### Step 5: Deploy (15 minutes)

```bash
cd serverless/infra
cdk deploy --profile mvp

# Upload updated dashboard
aws s3 sync ../ui/ s3://socratic-bench-ui-984906149037/ --profile mvp --delete

# Invalidate CloudFront
aws cloudfront create-invalidation --distribution-id E3NCWVQEJKM7NC --paths "/*" --profile mvp
```

**Complexity**: ZERO
- Same process we used before
- Known to work

---

## FULL vs SIMPLIFIED COMPARISON

### FULL PLAN (Original Proposal)
**Time**: 2-3 days  
**Complexity**: HIGH  
**Risks**:
- Need to modify curator Lambda (weekly aggregates)
- Redeploy infrastructure
- Complex D3.js/ApexCharts code
- Multiple new API endpoints
- Testing with mock data (real data doesn't exist yet)

**Pros**:
- Beautiful, feature-rich dashboard
- Time-series tracking ready

**Cons**:
- Overkill for current state (no data yet)
- High risk of bugs
- Long development time

### SIMPLIFIED PLAN (Recommended)
**Time**: 4 hours  
**Complexity**: LOW  
**Risks**: Minimal (uses existing patterns)

**Pros**:
- ✅ Works with current data state
- ✅ Fast to implement
- ✅ Easy to debug
- ✅ Can add time-series LATER when we have data
- ✅ Shows what's actually working vs broken

**Cons**:
- Less fancy
- No time-series (yet)

---

## RECOMMENDATION: Two-Phase Approach

### PHASE 1: NOW (This Week)
**Goal**: Show current system state

**Build**:
1. ✅ Simple snapshot dashboard (bar charts, tables)
2. ✅ Status indicators (what's working)
3. ✅ One API endpoint (/api/snapshot)
4. ✅ Cost breakdown

**Time**: 4 hours  
**Value**: HIGH (shows progress, sets expectations)

### PHASE 2: LATER (After Pipeline is Fixed)
**Goal**: Track trends over time

**Build**:
1. Fix model support (inference profiles, providers)
2. Run for 3-4 weeks to collect data
3. Add weekly aggregates to curator
4. Build time-series chart
5. Add heatmap, radar charts

**Time**: 1-2 days  
**Value**: HIGH (after we have data to visualize)

---

## FINAL COMPLEXITY CHECK

### What We're Actually Building (Phase 1)

**Backend Changes**: 
- 1 new function in api/handler.py (~50 lines)
- 0 infrastructure changes
- 0 database schema changes

**Frontend Changes**:
- Add Chart.js CDN link (1 line)
- Add fetch() call (~10 lines)
- Add 2 charts (bar + pie, ~40 lines total)
- Update HTML structure (~30 lines)

**Total New Code**: ~130 lines  
**Complexity**: LOW  
**Deployment Risk**: LOW (no infra changes)

### Can This Go Wrong?

**Potential Issues**:
1. ❌ No data in DynamoDB
   - **Solution**: Show "No runs yet" message
   
2. ❌ API endpoint errors
   - **Solution**: Try-catch, return empty array
   
3. ❌ Chart.js fails to render
   - **Solution**: Fall back to table view

4. ❌ CloudFront caching issues
   - **Solution**: Invalidate cache (known process)

**Worst Case**: Dashboard shows "No data yet" → Same as now

**Best Case**: Dashboard shows 8 working models with scores → Much better than now

---

## DECISION TREE

```
Do we have 10+ weeks of data?
├─ YES → Build time-series (original plan)
└─ NO → 
    └─ Do we have ANY successful runs?
        ├─ YES (1-10 runs) → Build snapshot dashboard ✅ (RECOMMENDED)
        └─ NO (0 runs) → 
            └─ Fix pipeline first, then build dashboard
```

**Current State**: We have ~8 successful runs (out of 48)  
**Recommendation**: Build snapshot dashboard ✅

---

## WHAT I'LL BUILD (Pending Your Approval)

### Deliverables

1. **API Endpoint**: `GET /api/snapshot`
   - Returns latest run summary
   - All models, scores, costs, status
   
2. **Dashboard Updates**:
   - Bar chart: Model scores (sorted)
   - Pie chart: Cost by provider
   - Status cards: Last run time, success rate
   - Table: Top 10 models with details

3. **Deployment**:
   - Update Lambda
   - Upload new UI
   - Invalidate CloudFront cache

### NOT Building (Yet)

- ❌ Time-series (need more data first)
- ❌ Heatmaps (complex, can add later)
- ❌ Radar charts (nice-to-have)
- ❌ Weekly aggregates in curator (not needed yet)

### Timeline

- **Hour 1**: Audit data, create API endpoint
- **Hour 2**: Build charts in HTML
- **Hour 3**: Add status indicators, polish
- **Hour 4**: Deploy, test, debug

**Total**: 4 hours of focused work

---

## QUESTIONS FOR YOU

1. **Approve simplified plan?** (Snapshot dashboard vs full time-series)
2. **Should we fix pipeline FIRST** before building dashboards?
3. **Want me to start NOW** or wait until pipeline is working?

**My Strong Recommendation**: 
- Build simplified snapshot dashboard NOW (4 hours)
- Shows progress, looks good
- Add time-series LATER when we have 3+ weeks of data

**What do you think?**
