# Quick Start Guide - Bedrock Model Comparison

## 5-Minute Setup

### Step 1: AWS Bedrock Access (One-time, 5 minutes)

Your AWS credentials are already set up with the `mvp` profile.

**Request Bedrock model access**:

1. Go to AWS Console: https://console.aws.amazon.com/bedrock
2. Click "Model access" in left sidebar
3. Click "Manage model access"
4. Select these models:
   - ✅ All Anthropic Claude models (3.5 Sonnet, Opus, Haiku, etc.)
   - ✅ All Meta Llama models (3.1 405B, 70B, 8B)
   - ✅ All Mistral models (Large, Mixtral 8x7B)
5. Click "Request model access"
6. Wait 1-2 hours for approval (you'll get email)

**Check approval status**:
```bash
aws bedrock list-foundation-models --profile mvp --region us-east-1 \
  | grep -A 5 "claude-3-5-sonnet"
```

---

### Step 2: Install Dependencies (2 minutes)

```bash
cd /Users/williamprior/Development/GitHub/socratic-ai-benchmarks

# Install boto3 if not already installed
pip install boto3

# Or use conda
# conda install boto3
```

---

### Step 3: Generate Test Scenarios (1 minute)

```bash
python generate_scenarios.py
```

**Output**: `test_scenarios.json` (120 scenarios, ~50 KB)

---

### Step 4: Run Quick Validation Test (5 minutes)

Test 2 models with 10 scenarios to validate setup:

```bash
python benchmark.py --quick
```

**What it does**:
- Tests Claude 3.5 Sonnet v2 and Haiku
- 10 scenarios each = 20 API calls
- Scores quality with LLM-as-judge
- ~2-3 minutes to complete

**Expected output**:
```
🚀 BEDROCK MODEL COMPARISON BENCHMARK
======================================================================
AWS Profile: mvp
Region: us-east-1

📊 Loading test scenarios...
✅ Loaded 10 test scenarios
✅ Testing 2 models

🤖 Testing Claude 3.5 Sonnet v2 (anthropic.claude-3-5-sonnet-20241022-v2:0)
   ✓ Progress: 10/10 | Avg Quality: 0.876
   ✅ Complete: 10/10 successful | Avg Quality: 0.876 | Avg Latency: 1847ms

🤖 Testing Claude 3.5 Haiku (anthropic.claude-3-5-haiku-20241022-v1:0)
   ✓ Progress: 10/10 | Avg Quality: 0.743
   ✅ Complete: 10/10 successful | Avg Quality: 0.743 | Avg Latency: 892ms

======================================================================
✅ COMPARISON COMPLETE
======================================================================
Results saved to: comparison_results_20251025_143000.json

📊 MODEL COMPARISON SUMMARY
==================================================================================
Rank   Model                               Quality    Latency      Success
----------------------------------------------------------------------------------
1 🏆   Claude 3.5 Sonnet v2                0.876      1847ms       100%
2 🥈   Claude 3.5 Haiku                    0.743      892ms        100%

Next step: Run generate_dashboard.py to create visual report
```

**Cost**: ~$0.30 (20 generations + 20 scoring calls)

---

### Step 5: Run Full Comparison (Optional, 45-60 minutes)

If quick test succeeded, run full comparison:

```bash
python benchmark.py
```

**What it does**:
- Tests all 8 Bedrock models
- 120 scenarios each = 960 total generations
- LLM-as-judge scoring for all
- ~45-60 minutes to complete (models run sequentially)

**Cost**: ~$10.44

**Output**: `comparison_results_YYYYMMDD_HHMMSS.json`

---

## Troubleshooting

### Error: "Could not connect to endpoint"
```bash
# Check AWS credentials
aws sts get-caller-identity --profile mvp

# Should return your AWS account info
```

### Error: "Access denied to model"
```bash
# Check Bedrock model access status
aws bedrock list-foundation-models --profile mvp --region us-east-1

# If no models listed, go request access in console
```

### Error: "Throttling exception"
```bash
# Too many requests too fast
# The script has 2-second delays between models
# If still hitting limits, add longer delays
```

### Error: "test_scenarios.json not found"
```bash
# Run scenario generator first
python generate_scenarios.py
```

---

## Next Steps

### After Quick Test Succeeds:

1. **Run full comparison** (8 models × 120 scenarios)
2. **Generate dashboard** (coming next)
3. **Analyze results** and select winning model
4. **Document decision** for research paper

### After Full Comparison Completes:

```bash
# Generate HTML dashboard
python generate_dashboard.py comparison_results_20251025_143000.json

# Open in browser
open dashboard.html
```

---

## File Structure

```
socratic-ai-benchmarks/
├── generate_scenarios.py       # Generate test scenarios
├── test_scenarios.json         # 120 test scenarios (output)
├── benchmark.py                # Run model comparison
├── comparison_results_*.json   # Results (output)
├── generate_dashboard.py       # Create HTML dashboard (next)
├── dashboard.html              # Visual report (output)
└── QUICK_START.md             # This file
```

---

## Expected Timeline

| Day | Task | Time | Output |
|-----|------|------|--------|
| **Today** | Request Bedrock access | 5 min | Email confirmation |
| **Today** | Install dependencies | 2 min | boto3 installed |
| **Today** | Generate scenarios | 1 min | test_scenarios.json |
| **Today** | Quick test (2 models) | 5 min | Validation complete ✅ |
| **Tomorrow** | Full comparison (8 models) | 60 min | comparison_results.json |
| **Tomorrow** | Generate dashboard | 5 min | dashboard.html |
| **Tomorrow** | Analyze & select winner | 30 min | Decision documented |

**Total: ~2 hours of active work over 2 days**

---

## Pro Tips

### Speed Up Testing
```bash
# Test fewer scenarios while debugging
python benchmark.py --scenarios 20  # 8 models × 20 = 160 calls (~15 min)

# Test fewer models
python benchmark.py --models 3      # Top 3 models × 120 = 360 calls (~20 min)

# Combine both
python benchmark.py --models 3 --scenarios 20  # 3 × 20 = 60 calls (~5 min)
```

### Resume Failed Run
If benchmark crashes midway:
- Results are saved per model
- Re-run with `--models` to skip completed ones
- Manually merge JSON files

### Cost Monitoring
```bash
# Check Bedrock pricing
# https://aws.amazon.com/bedrock/pricing/

# Estimate cost before running
# Claude 3.5 Sonnet: ~$0.009/question × 120 = $1.08
# Claude 3 Opus: ~$0.045/question × 120 = $5.40
# Total for 8 models: ~$10.44
```

---

## Support

**Issues? Questions?**

1. Check this guide first
2. Review error messages carefully
3. Verify Bedrock access is approved
4. Confirm AWS credentials work: `aws sts get-caller-identity --profile mvp`

**Ready to start?**

```bash
# Step 1: Generate scenarios
python generate_scenarios.py

# Step 2: Run quick test
python benchmark.py --quick

# If successful, you're ready for full comparison! 🚀
```
