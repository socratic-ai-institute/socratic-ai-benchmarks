# Gemini 3.0 Pro Integration Notes

## Status
- **Configuration**: ✅ Complete (added to model list)
- **One-time test**: ✅ Enqueued (SQS message sent)
- **Recurring runs**: ✅ Ready (will run on next Monday 3am UTC)
- **Actual execution**: ⏳ Pending (requires Bedrock support or Vertex AI integration)

## What Was Done

### 1. Configuration Updates
- Added `google.gemini-3-0-pro-v1:0` to model roster
- Updated S3 config: `s3://socratic-bench-data-984906149037/artifacts/config.json`
- Updated repo config: `serverless/config-24-models.json`
- Total models: 24 → 25

### 2. One-Time Test Run
- Enqueued to: `socratic-dialogue-jobs` SQS queue
- Message ID: `9ced4830-5aab-4262-9a3e-f14ffaf0a4f3`
- Scenario: `EL-ETH-UTIL-DEON-01`
- Expected behavior: Runner lambda will attempt to invoke but fail (Bedrock limitation)

### 3. Future Weekly Runs
Starting Monday, November 25, 2025 at 3:00 AM UTC, Gemini will be included in:
- 75 total jobs (25 models × 3 scenarios)
- 3 Gemini jobs per week

## Implementation Path

### To Fully Enable (Choose One):

#### Path A: Bedrock Availability (Lowest Effort)
1. Wait for AWS to add Gemini models to Bedrock
2. No code changes needed
3. Tests will pass through once available
4. Timeline: Unknown (depends on AWS/Google partnership)

#### Path B: Vertex AI Integration (Recommended)
1. Set up Google Cloud service account
2. Add credentials to Lambda environment variables
3. Modify runner lambda:
   - Detect `provider == "google"`
   - Use `google-cloud-aiplatform` SDK instead of boto3
   - Call Vertex AI endpoint instead of Bedrock
4. Handle provider-specific API differences

#### Path C: Direct Google API
Similar to Path B but uses public Google API endpoint (simpler but may have rate limits)

## Files Modified
- `serverless/config-24-models.json` - Model configuration
- `serverless/ui/index.html` - Homepage methodology (separate change)
- S3: `artifacts/config.json` - Production configuration

## Testing
Once implementation is chosen, verify:
1. Runner lambda can authenticate to Google service
2. Model inference works end-to-end
3. Judge receives response and scores correctly
4. Results appear in dashboard

## Notes
- Gemini model ID follows Bedrock naming convention for future compatibility
- Cost estimates are from Google's public pricing as of Nov 2025
- Expected score is conservative estimate pending actual benchmarking
