# Dashboard Visualization Proposal

## Current Data Available

### DynamoDB Structure
```
RUN#{run_id}#META -> Run metadata (model_id, scenario_id, created_at, status)
RUN#{run_id}#TURN#{index} -> Turn data (tokens, latency, has_question)
RUN#{run_id}#JUDGE#{index} -> Judge scores (overall_score, has_question, is_open_ended)
RUN#{run_id}#SUMMARY -> Aggregated metrics
WEEK#{YYYY-WW}#MODEL#{model_id} -> Weekly aggregates by model
MANIFEST#{manifest_id}#META -> Test configuration snapshots
```

### S3 Structure
```
raw/runs/{run_id}/turn_{index}.json -> Full turn bundle (student, AI response, timestamps)
raw/runs/{run_id}/judge_{index}.json -> Judge rationale and detailed scores
curated/runs/{run_id}.json -> Aggregated run summary with all metrics
curated/weekly/{YYYY-WW}/{model_id}.json -> Weekly model performance
```

### Available Metrics Per Run
- `overall_score` (0-10): Mean judge score across all turns
- `compliance_rate` (0-1): % of turns scoring >= 3.0
- `half_life`: First turn where score drops below 3.0
- `violation_rate` (0-1): % turns without question marks
- `open_ended_rate` (0-1): % turns with open-ended questions
- `turn_count`: Number of turns in dialogue
- `total_input_tokens`: Total input tokens consumed
- `total_output_tokens`: Total output tokens consumed
- `latency_ms` per turn: Response time
- `created_at`: ISO timestamp

---

## Proposed Visualizations

### 1. ⭐ TIME-SERIES: Model Performance Over Time (PRIORITY)

**Data Source**: Query DynamoDB GSI1 (MODEL#{model_id}) or S3 curated/weekly/

**X-Axis**: Time (weekly manifests)  
**Y-Axis**: Overall Score (0-10)  
**Series**: One line per model (24 lines)

**Features**:
- Line chart with dots at each data point
- Hoverable tooltips showing exact score + date
- Legend with model names (toggleable to show/hide models)
- Highlight top 3 performers with bolder lines
- Show trend arrows (↑↓) for each model

**Data Requirements**: 
- Query all RUN#SUMMARY items grouped by model_id and created_at
- Or use WEEK#{date}#MODEL#{id} aggregates if available
- **Need to add**: Store manifest_id or week_id in SUMMARY for time grouping

**Query Logic**:
```python
# GSI1 query
for model_id in all_models:
    runs = table.query(
        IndexName='GSI1',
        KeyConditionExpression='GSI1PK = :pk',
        ExpressionAttributeValues={':pk': f'MODEL#{model_id}'}
    )
    # Group by week, calculate weekly average
```

---

### 2. 📊 SCORE DISTRIBUTION: Violin Plot

**What**: Show the distribution of scores for each model

**X-Axis**: Model names (24 models)  
**Y-Axis**: Score (0-10)  
**Visualization**: Violin plot or box-and-whisker

**Why This Matters**:
- Reveals consistency vs variability
- Some models might average 6/10 but range 2-9 (unreliable)
- Others might average 6/10 but range 5-7 (consistent)

**Features**:
- Show median, quartiles, min/max
- Color by performance tier (red < 4, yellow 4-6, green > 6)
- Click to see individual runs

**Data**: All RUN#SUMMARY items, group by model_id

---

### 3. 🎯 COMPLIANCE HEATMAP: Turn-by-Turn Performance

**What**: Heatmap showing score degradation across turns

**X-Axis**: Turn number (1-5)  
**Y-Axis**: Model names (24 models)  
**Color**: Average score at that turn (red=low, green=high)

**Why This Matters**:
- Shows which models "give up" Socratic method after N turns
- Reveals the "half-life" pattern visually
- Identifies models that improve or degrade over conversation

**Example**:
```
Model          Turn1  Turn2  Turn3  Turn4  Turn5
Claude 4.5     [8.2]  [7.9]  [7.5]  [7.1]  [6.8]  ← Gradual decline
Llama 3.3      [6.5]  [6.3]  [3.1]  [2.9]  [2.7]  ← Sudden drop at T3
```

**Features**:
- Click cell to see example responses from that turn
- Show average + count of runs per cell
- Highlight "cliff" patterns (sudden drops)

**Data**: Query all JUDGE items, group by (model_id, turn_index)

---

### 4. 💰 COST-EFFECTIVENESS SCATTER: Score vs Cost

**What**: Scatter plot showing value for money

**X-Axis**: Cost per dialogue ($ calculated from tokens)  
**Y-Axis**: Overall Score (0-10)  
**Bubble Size**: Number of runs (larger = more data)  
**Color**: Model provider (Anthropic=blue, Meta=orange, etc.)

**Why This Matters**:
- Find the "sweet spot" models (high score, low cost)
- Identify overpriced models (high cost, low score)
- Compare providers

**Quadrants**:
- **Top-Left** (low cost, high score): ⭐ BEST VALUE
- **Top-Right** (high cost, high score): Premium performers
- **Bottom-Left** (low cost, low score): You get what you pay for
- **Bottom-Right** (high cost, low score): ❌ AVOID

**Features**:
- Hover shows model name + exact cost + score
- Draw trend line (correlation between cost and performance)
- Filter by provider

**Data**: Calculate cost from `total_input_tokens + total_output_tokens` using pricing table

---

### 5. 📈 METRIC RADAR: Multi-Dimensional Performance

**What**: Radar/Spider chart for top 5 models across 6 dimensions

**Dimensions** (0-10 normalized):
1. Overall Score
2. Compliance Rate (× 10)
3. Open-Ended Rate (× 10)
4. Half-Life (inverted: 5 turns = 10, 1 turn = 2)
5. Speed (inverted latency: fast = 10, slow = 0)
6. Token Efficiency (inverse of tokens per turn)

**Why This Matters**:
- Shows strengths/weaknesses beyond just score
- Model A might score 7/10 but be 3x faster
- Model B might score 6/10 but ask better open-ended questions

**Features**:
- Overlay 2-3 models for comparison
- Click dimension to sort all models by that metric
- Color-coded by provider

**Data**: Aggregate all metrics from RUN#SUMMARY

---

### 6. 🔍 TURN EXPLORER: Interactive Dialogue Viewer

**What**: Dropdown to select a run, then show turn-by-turn conversation

**Layout**:
```
[Model: Claude 4.5] [Scenario: Utilitarianism] [Score: 7.2/10]

Turn 1 | Score: 8.5/10 | 245ms
Student: "I believe in 100% utilitarianism..."
AI: "When you say 'greatest good,' how are you measuring..." ✅
Judge: Strong open-ended question, directly probes assumption

Turn 2 | Score: 7.8/10 | 189ms
Student: "Well, by happiness..."
AI: "And if someone's happiness conflicts with..." ✅
Judge: Good follow-up, maintains Socratic stance
```

**Features**:
- Color-code turns by score (green=high, red=low)
- Show judge rationale on hover
- Link to raw S3 JSON for developers
- "Share this conversation" button (copy link)

**Data**: Load from S3 `raw/runs/{run_id}/` bundle

---

## Data Layer Changes Needed

### For Time-Series Graph

**Option 1**: Query existing data
```python
# Pros: No schema changes
# Cons: Slower, requires aggregation in Lambda
runs = scan_all_summary_items()
group_by_week_and_model(runs)
```

**Option 2**: Add weekly aggregate table (RECOMMENDED)
```python
# Add to curator.py
def update_weekly_aggregate(run_meta, summary):
    week_id = get_iso_week(summary['created_at'])  # "2025-W45"
    model_id = run_meta['model_id']
    
    # Update or create WEEK#{week}#MODEL#{model}
    table.update_item(
        Key={'PK': f'WEEK#{week_id}', 'SK': f'MODEL#{model_id}'},
        UpdateExpression='SET #scores = list_append(if_not_exists(#scores, :empty), :new_score)',
        ExpressionAttributeNames={'#scores': 'scores'},
        ExpressionAttributeValues={
            ':empty': [],
            ':new_score': [summary['overall_score']]
        }
    )
```

**Recommended**: Option 2 (add weekly aggregates)

---

## Implementation Priority

1. **TIME-SERIES** (requested) - Add weekly aggregates, build line chart
2. **SCORE DISTRIBUTION** (easy win) - Uses existing data, high value
3. **COMPLIANCE HEATMAP** (unique insight) - Shows turn degradation visually
4. **COST-EFFECTIVENESS** (business value) - Helps choose models
5. **METRIC RADAR** (advanced) - Multi-dimensional comparison
6. **TURN EXPLORER** (deep dive) - For detailed analysis

---

## Technical Implementation

### Frontend (HTML/JS)
- Use **Chart.js** or **D3.js** for visualizations
- **ApexCharts** for time-series (beautiful, interactive)
- Responsive design (works on mobile)
- Dark mode support

### Backend (API Lambda)
- Add new endpoints:
  - `GET /api/timeseries?model_id=...` → Weekly scores
  - `GET /api/distribution` → All scores grouped by model
  - `GET /api/heatmap` → Turn-by-turn matrix
  - `GET /api/cost-analysis` → Cost + performance data
  - `GET /api/run/{run_id}` → Full dialogue details

### Data Fetching
- Cache frequently accessed data (weekly aggregates)
- Use DynamoDB GSI for efficient queries
- Fall back to S3 for detailed views

---

## Mock-Up Wireframe

```
┌─────────────────────────────────────────────────────────────┐
│  SOCRATIC AI BENCHMARKING DASHBOARD                         │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  [TIME-SERIES CHART - Model Performance Over Time]           │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ 10 ┤                        ╭─ Claude 4.5              │  │
│  │  9 ┤                    ╭───╯                          │  │
│  │  8 ┤         ╭──────────╯                              │  │
│  │  7 ┤    ╭────╯                                         │  │
│  │  6 ┤────╯    ╰──── Llama 3.3                           │  │
│  │  5 ┤                                                    │  │
│  │  4 ┼─────────────────────────────────────────────────  │  │
│  │    Week1  Week2  Week3  Week4  Week5  Week6           │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                               │
├─────────────────────┬─────────────────────┬──────────────────┤
│ [SCORE DISTRIBUTION]│ [COMPLIANCE HEATMAP]│ [COST vs SCORE]  │
│  Violin Plot        │  Turn Degradation   │  Scatter Plot    │
├─────────────────────┴─────────────────────┴──────────────────┤
│ [METRIC RADAR - Top 5 Models]                                │
├───────────────────────────────────────────────────────────────┤
│ [TURN EXPLORER - Interactive Dialogue Viewer]                │
└───────────────────────────────────────────────────────────────┘
```

---

## Next Steps

1. **Review & Approve**: Which visualizations to implement?
2. **Data Schema**: Confirm weekly aggregate structure
3. **Prototype**: Build time-series first (most requested)
4. **Iterate**: Add remaining charts based on priority

---

**Questions for Approval**:

1. Time-series: Should we show all 24 models at once or group by provider?
2. Should we add filters (date range, scenario type, provider)?
3. Do you want downloadable data (CSV export)?
4. Should charts update live when new runs complete?
5. Priority order: Which 3 charts should we build first?
