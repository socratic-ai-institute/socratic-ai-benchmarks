# API Debugging Skill

## Description
Diagnose and fix Lambda API endpoint issues, data transformation problems, and DynamoDB access patterns.

## When to Use
- API returns unexpected data or formatting
- Endpoint returns 500 errors
- Data transformations are incorrect (e.g., score scaling)
- DynamoDB queries return empty results
- New endpoints need testing

## Quick Diagnosis

### 1. Check API Status
```bash
# Test endpoint
curl https://wcyf23uxxe.execute-api.us-east-1.amazonaws.com/prod/api/latest-rankings

# Test with jq for parsing
curl -s https://wcyf23uxxe.execute-api.us-east-1.amazonaws.com/prod/api/latest-rankings | jq '.rankings | length'
```

### 2. Check Lambda Logs
```bash
# List recent invocations
aws logs tail /aws/lambda/SocraticBenchStack-ApiHandlerLambda --profile mvp --follow

# Search for errors
aws logs filter-log-events \
  --log-group-name /aws/lambda/SocraticBenchStack-ApiHandlerLambda \
  --filter-pattern "ERROR" \
  --profile mvp
```

### 3. Test Individual Endpoints
```bash
# Model comparison
curl https://wcyf23uxxe.execute-api.us-east-1.amazonaws.com/prod/api/model-comparison | jq '.models | length'

# Timeseries
curl https://wcyf23uxxe.execute-api.us-east-1.amazonaws.com/prod/api/timeseries | jq '.series | length'

# Detailed results
curl https://wcyf23uxxe.execute-api.us-east-1.amazonaws.com/prod/api/detailed-results | jq '.results | length'

# Cost analysis
curl https://wcyf23uxxe.execute-api.us-east-1.amazonaws.com/prod/api/cost-analysis | jq '.scatter_data | length'
```

## Common Issues and Fixes

### Empty Results
**Symptom**: Endpoints return 0 items
**Root Cause**: DynamoDB scan/query returns no items
**Debug**:
```bash
# Check if data exists
aws dynamodb scan --table-name socratic_core \
  --filter-expression "begins_with(PK, :prefix)" \
  --expression-attribute-values '{":prefix":{"S":"WEEK#"}}' \
  --profile mvp | jq '.Items | length'
```

**Fix**:
- Verify benchmark has run: check if latest WEEK# items exist
- Check SUMMARY items exist for current week
- Verify model_id field is populated

### Wrong Score Scale
**Symptom**: Scores show 0-1 instead of 0-10, or 0-1000 instead of 0-10
**Root Cause**: Missing or duplicate scale conversion
**Fix in `serverless/lambdas/api/handler.py`**:
```python
# Line 263 (get_timeseries): MUST multiply by 10
mean_score = float(item.get("mean_score", 0)) * 10

# Line 318 (get_latest_rankings): MUST multiply by 10
"mean_score": float(item.get("mean_score", 0)) * 10

# In get_detailed_results: MUST multiply by 10 for all scores
directionally_socratic = float(scores.get("directionally_socratic", 0)) * 10
```

### Missing Fields in Response
**Symptom**: API returns incomplete objects
**Root Cause**: Field not included in response dict
**Debug**:
```python
# Add temporary logging
print(f"DEBUG: Item before transform: {item}")
return_obj = { "field": item.get("field") }
print(f"DEBUG: Response object: {return_obj}")
```

**Fix**:
- Ensure all required fields are extracted from DynamoDB items
- Use `.get()` with defaults to prevent KeyError
- Verify field names match between DynamoDB and response dict

## Deployment Workflow

### 1. Make Code Changes
Edit `serverless/lambdas/api/handler.py`

### 2. Test Locally (if possible)
```bash
# Check syntax
python -m py_compile serverless/lambdas/api/handler.py

# Check imports
python -c "import sys; sys.path.insert(0, 'serverless/lib'); from socratic_bench import *"
```

### 3. Deploy
```bash
cd serverless/infra
cdk deploy --profile mvp --require-approval never
```

### 4. Test Endpoints
```bash
# Wait 10 seconds for CloudFormation updates
sleep 10

# Test all endpoints
for endpoint in model-comparison timeseries latest-rankings detailed-results cost-analysis; do
  echo "Testing: $endpoint"
  curl -s https://wcyf23uxxe.execute-api.us-east-1.amazonaws.com/prod/api/$endpoint | jq '.status // .error // "OK"'
done
```

### 5. Check Logs
```bash
aws logs tail /aws/lambda/SocraticBenchStack-ApiHandlerLambda --profile mvp --follow
```

## Success Criteria
- Endpoint returns 200 status
- Response contains expected fields
- Data is properly formatted
- No errors in CloudWatch logs
- Results match database content

## Critical API Routes
| Route | Method | Purpose | Response Format |
|-------|--------|---------|-----------------|
| `/api/model-comparison` | GET | Top models by metric | `{models: [{model_id, conciseness, ends_with_question, directionally_socratic}], winner: {...}}` |
| `/api/timeseries` | GET | Score trends over time | `{weeks: [...], series: [{model_id, data: [{week, score}]}]}` |
| `/api/latest-rankings` | GET | Current week rankings | `{week, rankings: [{model_id, mean_score, mean_compliance, run_count}]}` |
| `/api/detailed-results` | GET | All individual results | `{results: [{test_type, scenario, model, overall, ...}]}` |
| `/api/cost-analysis` | GET | Cost vs performance | `{scatter_data: [{model_id, cost_per_run, avg_score, run_count, provider}]}` |

## Related Files
- `serverless/lambdas/api/handler.py` - All endpoint implementations
- `serverless/lib/socratic_bench/` - Supporting modules (models.py, google_client.py, etc.)
- `serverless/infra/stack.py` - Lambda configuration and environment variables
