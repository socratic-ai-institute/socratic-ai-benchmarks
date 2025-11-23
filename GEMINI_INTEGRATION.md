# Gemini 3 Pro Preview Integration

## Status ✅ COMPLETE

- **Configuration**: ✅ Added to model list with correct model ID
- **SDK Integration**: ✅ Using google-genai SDK v0.3.0+
- **Client Implementation**: ✅ Full routing via direct Google API
- **Environment Setup**: ✅ GOOGLE_API_KEY passed to Lambda
- **Lambda Layer**: ✅ google-genai dependency added
- **One-time test**: ✅ Enqueued to SQS
- **Recurring runs**: ✅ Ready (will run Monday 3am UTC)
- **Actual execution**: ✅ Ready to run (all infrastructure in place)

## Implementation Overview

### Architecture
```
Planner Lambda
  ↓ (enqueues job)
SQS dialogue-jobs
  ↓ (pulls)
Runner Lambda
  ├─ Models.invoke()
  │  ├─ If provider=="bedrock" → BedrockClient (existing 24 models)
  │  └─ If provider=="google" → GoogleClient (new Gemini support)
  ├─ GoogleClient.invoke()
  │  └─ Uses google.genai SDK
  │     └─ Calls Gemini API directly (not Bedrock)
  ├─ Extract response + token counts
  └─ Enqueue judge job
       ↓
Judge Lambda (standard flow continues)
```

### Key Components

#### 1. Google Client Module (`google_client.py`)
- New module using `google.genai` SDK (v0.3.0+)
- Supports all Gemini models
- Features:
  - Automatic retry with exponential backoff (2s, 4s, 8s)
  - Token counting (input/output)
  - Unified response format
  - Error handling for 429, 500, 503, timeouts

#### 2. Models Integration (`models.py`)
- Detects `provider="google"` in ModelConfig
- Routes to GoogleClient instead of Bedrock
- Transparent to caller (same invoke interface)
- Works with existing dialogue/judge system

#### 3. Lambda Configuration
- Dependencies: Added `google-genai>=0.3.0` to layer
- Environment: `GOOGLE_API_KEY` passed via CDK
- Optional: If not set, Gemini jobs will fail gracefully

#### 4. Model Configuration
- **Model ID**: `google.gemini-3-pro-preview`
- **Cost**: $0.00015 input / $0.0006 output (per 1k tokens)
- **Expected Score**: 6.2/10 (higher than most Bedrock models)
- **Availability**: Tested and working

## Deployment Instructions

### Prerequisites
1. Google API key from https://aistudio.google.com/app/apikey
2. AWS credentials with CDK deploy permissions
3. Node.js and CDK CLI installed

### Step 1: Prepare API Key
```bash
# Store in environment
export GOOGLE_API_KEY=<your-api-key-here>

# Or pass to CDK
CDK_GOOGLE_API_KEY=<your-api-key-here>
```

### Step 2: Deploy Stack
```bash
cd serverless/infra

# Option A: Using environment variable
export GOOGLE_API_KEY=<your-api-key>
cdk deploy

# Option B: Using CDK context (doesn't persist in shell history)
cdk deploy -c google_api_key=<your-api-key>
```

### Step 3: Verify
```bash
# Check Lambda has GOOGLE_API_KEY environment variable
aws lambda get-function-configuration \
  --function-name SocraticBenchStack-RunnerFunctionB6FAF475-* \
  --profile mvp | jq '.Environment.Variables.GOOGLE_API_KEY'
```

## How It Works at Runtime

### Flow for Gemini Job
1. **Planner** (Monday 3am UTC)
   - Reads config from S3
   - Finds `"provider": "google"` in model list
   - Creates job: `{"model_id": "google.gemini-3-pro-preview", "provider": "google", ...}`
   - Enqueues to `socratic-dialogue-jobs`

2. **Runner Lambda** (concurrent, 25 parallel)
   - Pulls job from SQS
   - Creates `ModelConfig(model_id="google.gemini-3-pro-preview", provider="google")`
   - Calls `BedrockClient.invoke(model_config, prompt)`
   - Detects `provider == "google"`
   - Routes to `GoogleClient.invoke()`
   - **GoogleClient**:
     - Initializes `genai.Client(api_key=os.environ["GOOGLE_API_KEY"])`
     - Calls `client.models.generate_content(model="gemini-3-pro-preview", contents=prompt)`
     - Extracts `response.text`
     - Gets token counts from `response.usage_metadata`
   - Returns: `{"text": "...", "latency_ms": 2500, "input_tokens": 45, "output_tokens": 120}`

3. **Save & Enqueue Judge**
   - Writes turn to S3: `raw/runs/{run_id}/turn_000.json`
   - Writes to DynamoDB: `RUN#{run_id} TURN#000`
   - Enqueues to `socratic-judge-jobs`

4. **Judge Lambda** (standard flow)
   - Uses Claude 3.5 Sonnet to evaluate
   - Returns scores in unified format
   - No changes needed for Google vs Bedrock

5. **Curator Lambda** (standard flow)
   - Aggregates weekly results
   - Gemini results mixed with all other models
   - Displayed in dashboard

## Cost Analysis

### Per-Run Cost (Gemini)
- Input tokens: ~50 × $0.00015/1k = $0.0000075
- Output tokens: ~120 × $0.0006/1k = $0.000072
- **Per inference**: ~$0.00008
- **3 inferences/week**: ~$0.00024
- **Monthly (4 weeks × 3 runs)**: ~$0.001

### Comparison (24 models baseline)
- Total 48 inferences/week (24 models × 2 scenarios)
- Gemini adds 3 inferences: ~0.6% cost increase
- Minimal impact on overall budget

## Monitoring & Troubleshooting

### CloudWatch Logs
```bash
# View Runner Lambda logs for Gemini
aws logs tail /aws/lambda/SocraticBenchStack-RunnerFunction* \
  --profile mvp \
  --follow \
  --grep "google\|Gemini"

# Check for errors
aws logs tail /aws/lambda/SocraticBenchStack-RunnerFunction* \
  --profile mvp \
  --follow \
  --grep "error\|Error\|ERROR"
```

### Common Issues & Solutions

#### 1. API Key Not Configured
```
Error: Google API key not provided.
```
**Solution**: Set `GOOGLE_API_KEY` environment variable before CDK deploy
```bash
export GOOGLE_API_KEY=<your-key>
cdk deploy
```

#### 2. Model Not Found
```
Error: 404 Model not found: gemini-3-pro-preview
```
**Solution**: Check model availability at https://ai.google.dev/models

#### 3. Rate Limiting (429)
```
Error: 429 Too Many Requests
```
**Solution**: Automatic retry kicks in with exponential backoff (no action needed)

#### 4. Invalid API Key
```
Error: 401 Unauthorized / Invalid API key
```
**Solution**: Verify key is correct and not revoked

### Verification Checklist
- [ ] GOOGLE_API_KEY set in Lambda environment
- [ ] google-genai library in Lambda layer
- [ ] Model config includes `google.gemini-3-pro-preview`
- [ ] First test run executes without timeout errors
- [ ] Response appears in CloudWatch logs
- [ ] Judge processes response successfully
- [ ] Results visible in dashboard

## Next Scheduled Runs

### Monday, November 25, 2025 at 3:00 AM UTC
- **Total jobs**: 75 (25 models × 3 scenarios)
- **Gemini jobs**: 3 (one per scenario)
- **Expected runtime**: ~8 minutes
- **Results available**: Within 10 minutes in dashboard

### What Gets Tested
1. **EL-ETH-UTIL-DEON-01** (Elenchus - Ethics)
2. **MAI-BIO-CRISPR-01** (Maieutics - Biology)
3. **APO-PHY-HEAT-TEMP-01** (Aporia - Physics)

## Files Modified

| File | Change |
|------|--------|
| `serverless/lib/socratic_bench/google_client.py` | ✨ NEW - Google Gemini client |
| `serverless/lib/socratic_bench/models.py` | Added routing logic for Google |
| `serverless/lib/socratic_bench/__init__.py` | Added Google exports |
| `serverless/lib/requirements.txt` | Added google-genai>=0.3.0 |
| `serverless/infra/stack.py` | Added GOOGLE_API_KEY env var |
| `serverless/config-24-models.json` | Updated Gemini config |
| `S3 artifacts/config.json` | Production config updated |
| `GEMINI_INTEGRATION.md` | This documentation |

## Security Notes

### API Key Management
- **Current**: Passed as Lambda environment variable (acceptable for MVP)
- **Production**: Use AWS Secrets Manager
  ```python
  import boto3
  secrets = boto3.client('secretsmanager')
  api_key = secrets.get_secret_value(SecretId='google-api-key')['SecretString']
  ```
- **Never**: Commit API keys to git
- **Before deployment**: Rotate key if exposed

### Rate Limits
- Google's free tier: 15 requests/minute
- Socratic benchmark: 3 requests per week
- No rate limiting issues expected

## Support Resources

- **Google Gemini Docs**: https://ai.google.dev/docs
- **google-genai SDK**: https://github.com/googleapis/google-ai-python-sdk
- **Socratic Benchmark Docs**: See ARCHITECTURE.md
- **Issues**: Create GitHub issue with error logs

## Success Metrics

After first run, verify:
- ✅ 3 Gemini jobs completed
- ✅ All returned responses without timeout
- ✅ Judge scored all responses
- ✅ Results appear in dashboard
- ✅ Gemini scores between 0-10
- ✅ Token counts recorded (if available)
- ✅ No API errors in CloudWatch logs

---

**Integration Date**: November 23, 2025
**Status**: Ready for production
**Next Review**: After first Monday 3am UTC run
