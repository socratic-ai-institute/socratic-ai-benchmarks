# Chart Debugging Skill

## Description
Diagnose and fix chart rendering issues, data scaling problems, and visualization bugs.

## When to Use
- Charts display incorrect data or scaling
- Models missing from rankings/timeseries visualizations
- Chart labels, colors, or axes are wrong
- Score values don't match expected ranges

## Quick Diagnosis

### 1. Identify the Issue
```bash
# Open browser DevTools (F12) and check:
# - Console for JavaScript errors
# - Network tab to inspect API responses
# - Elements tab to check chart canvas sizing
```

### 2. Check API Response Format
```bash
# Test timeseries endpoint
curl https://wcyf23uxxe.execute-api.us-east-1.amazonaws.com/prod/api/timeseries | jq '.series[0]'

# Test rankings endpoint
curl https://wcyf23uxxe.execute-api.us-east-1.amazonaws.com/prod/api/latest-rankings | jq '.rankings[0]'
```

### 3. Verify Score Scaling
Key rule: **API returns 0-10 scale** (not 0-1)
- Check `serverless/lambdas/api/handler.py` lines 263, 318-319: should multiply by 10
- Check `serverless/ui/research.html` chart code: should NOT multiply by 10 again
- Chart.js options: `max: 10.0` for both axes

### 4. Common Fixes

#### Double Scaling (0-1000 instead of 0-10)
```javascript
// WRONG: API returns 0-10, chart multiplies by 100
data: series.data.map(d => d.score * 100)

// CORRECT: Use API value directly
data: series.data.map(d => d.score)
```

#### Missing Models in Bar Charts
Check `.chart-container` height in `research.html`:
```css
.chart-container {
    position: relative;
    height: 800px;  /* Increase if needed for more bars */
    margin-bottom: 40px;
}
```

#### Y-Axis Not Showing Full Range
Verify Chart.js options have correct scale:
```javascript
scales: {
    x: {
        min: 0,
        max: 10.0,
        title: { display: true, text: 'Mean Score' }
    }
}
```

## Testing Workflow

### Before Fix
1. Take screenshot of broken chart
2. Open DevTools Network tab
3. Copy API response to text file for comparison

### After Fix
1. Deploy UI: `cd serverless/infra && cdk deploy --profile mvp --require-approval never`
2. Hard refresh browser: Cmd+Shift+R
3. Compare new chart with before screenshot
4. Verify all models appear
5. Verify data points align with expected ranges

## Success Criteria
- All expected models visible in chart
- Data points within 0-10 range
- No JavaScript errors in console
- Chart renders responsive on different screen sizes
- Legend displays correctly

## Score Scaling Reference

| Layer | Scale | Example |
|-------|-------|---------|
| Judge Output (LLM) | 0-1 | 0.91 |
| DynamoDB Storage | 0-1 | 0.91 |
| API Response | 0-10 | 9.1 |
| Chart.js Render | 0-10 | 9.1 |
| UI Bar Width | % | 91% |

## Related Files
- `serverless/ui/research.html` - Chart rendering code (lines 415-681)
- `serverless/lambdas/api/handler.py` - Score conversion (lines 260-330)
- `serverless/ui/styles.css` - Chart container styles (line 169)
