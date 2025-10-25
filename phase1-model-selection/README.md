# Phase 1: Model Selection

**Goal**: Compare 8 AWS Bedrock models to select the best one for Socratic question generation.

**Timeline**: 5 days
**Budget**: ~$10
**Output**: Model selection decision document

---

## Quick Start

### 1. Request Bedrock Access (5 minutes, one-time)

1. Go to AWS Console: https://console.aws.amazon.com/bedrock
2. Click "Model access" → "Manage model access"
3. Select all:
   - Anthropic Claude models
   - Meta Llama models
   - Mistral models
4. Click "Request model access"
5. Wait for approval email (1-2 hours)

### 2. Generate Test Scenarios (1 minute)

```bash
python generate_scenarios.py
```

**Output**: `test_scenarios.json` (120 scenarios)

### 3. Run Quick Validation (5 minutes)

```bash
python benchmark.py --quick
```

Tests 2 models with 10 scenarios to validate setup.

**Cost**: ~$0.30

### 4. Run Full Comparison (60 minutes)

```bash
python benchmark.py
```

Tests all 8 models with 120 scenarios each.

**Cost**: ~$10.44
**Output**: `comparison_results_YYYYMMDD_HHMMSS.json`

### 5. Generate Dashboard (5 minutes)

```bash
python generate_dashboard.py comparison_results_*.json
open dashboard.html
```

### 6. Select Winner

Based on dashboard rankings, document your decision.

---

## The 8 Models

| Model | Model ID | Cost/Q | Why Test |
|-------|----------|--------|----------|
| Claude 3.5 Sonnet v2 | `anthropic.claude-3-5-sonnet-20241022-v2:0` | $0.009 | Current best |
| Claude 3 Opus | `anthropic.claude-3-opus-20240229-v1:0` | $0.045 | Highest quality |
| Claude 3.5 Haiku | `anthropic.claude-3-5-haiku-20241022-v1:0` | $0.003 | Fast + cheap |
| Mistral Large | `mistral.mistral-large-2402-v1:0` | $0.008 | Alternative |
| Llama 3.1 70B | `meta.llama3-1-70b-instruct-v1:0` | $0.001 | Open-source |
| Llama 3.1 8B | `meta.llama3-1-8b-instruct-v1:0` | $0.0002 | Baseline |
| Mixtral 8x7B | `mistral.mixtral-8x7b-instruct-v0:1` | $0.0006 | Efficient |
| Claude 3 Sonnet | `anthropic.claude-3-sonnet-20240229-v1:0` | $0.009 | Previous gen |

---

## Evaluation Criteria

### Quality Scores (Primary Metric)

Each question scored 0-1 on:
1. **Open-ended**: Not yes/no, encourages elaboration
2. **Probing**: Deepens understanding vs surface recall
3. **Builds on previous**: References prior answers (Q2/Q3)
4. **Age-appropriate**: Suitable for 14-18 year olds
5. **Content-relevant**: Connects to key concepts

**Overall**: Average of 5 criteria

### Performance Metrics

- **Latency**: p50, p95, p99 response time
- **Token efficiency**: Output tokens per question
- **Consistency**: Std deviation of quality scores

### Cost Metrics

- **Cost per question**: Based on input/output tokens
- **Total cost**: For 120 scenarios
- **Projected annual**: For 2,880 research questions

### Reliability

- **Success rate**: % of successful generations
- **Timeout rate**: % exceeding 10 seconds
- **Error rate**: % of API failures

---

## Files

| File | Purpose |
|------|---------|
| `README.md` | This file |
| `QUICK_START.md` | 5-minute setup guide |
| `BEDROCK_MODEL_COMPARISON.md` | Complete architecture |
| `generate_scenarios.py` | Create 120 test scenarios |
| `benchmark.py` | Run model comparison |
| `generate_dashboard.py` | Create HTML report |
| `test_scenarios.json` | Test data (generated) |
| `comparison_results_*.json` | Results (output) |
| `dashboard.html` | Visual report (output) |

---

## Timeline

| Day | Task | Time | Output |
|-----|------|------|--------|
| 1 | Request Bedrock access | 5 min | Pending approval |
| 1 | Generate scenarios | 1 min | test_scenarios.json |
| 2 | Quick validation | 5 min | 2 models tested |
| 3 | Full comparison | 60 min | 8 models tested |
| 4 | Dashboard + analysis | 30 min | Winner selected |
| 5 | Document decision | 30 min | Report ready |

---

## Expected Results

### Projected Rankings (Hypothetical)

| Rank | Model | Quality | Latency | Cost/Q |
|------|-------|---------|---------|--------|
| 1 🏆 | Claude 3 Opus | 0.91 | 3.2s | $0.045 |
| 2 🥈 | Claude 3.5 Sonnet v2 | 0.87 | 1.8s | $0.009 |
| 3 🥉 | Mistral Large | 0.79 | 1.7s | $0.008 |
| 4 | Claude 3.5 Haiku | 0.77 | 0.9s | $0.003 |
| 5 | Llama 3.1 70B | 0.71 | 1.4s | $0.001 |
| 6 | Claude 3 Sonnet | 0.74 | 2.0s | $0.009 |
| 7 | Mixtral 8x7B | 0.68 | 1.5s | $0.0006 |
| 8 | Llama 3.1 8B | 0.62 | 1.2s | $0.0002 |

**Likely Winner**: Claude 3.5 Sonnet v2
- 2nd best quality (0.87 vs 0.91 for Opus)
- 44% faster than Opus (1.8s vs 3.2s)
- 80% cheaper than Opus ($0.009 vs $0.045)
- Best overall value for research

---

## Cost Estimate

### Per Full Comparison Run

| Component | Usage | Cost |
|-----------|-------|------|
| AI Generation | 8 models × 120 scenarios | $9.09 |
| AI Scoring | 960 LLM-as-judge calls | $1.35 |
| **Total** | | **$10.44** |

### Projected Phase 2 Costs (with selected model)

If Claude 3.5 Sonnet selected:
- 240 students × 12 questions = 2,880 generations
- 2,880 × $0.009 = **$25.92** for full research study

---

## Decision Framework

### Selection Criteria Weights (Customize)

**Quality-Focused** (for publication):
- Quality: 60%
- Latency: 20%
- Cost: 10%
- Reliability: 10%

**Budget-Constrained**:
- Quality: 40%
- Cost: 40%
- Latency: 10%
- Reliability: 10%

**Balanced**:
- Quality: 40%
- Latency: 30%
- Cost: 20%
- Reliability: 10%

### Decision Tree

1. Quality ≥0.80 required? → Filter to top models
2. Budget <$20 for Phase 2? → Filter by cost
3. Latency <2s p95? → Filter by speed
4. 100% reliability required? → Filter perfect success rate
5. Select highest-ranked remaining model

---

## Next Steps

### After Model Selection

1. **Document Decision**:
   - Model name and ID
   - Quality score achieved
   - Rationale (why chosen over others)
   - Cost projection for Phase 2
   - Any limitations noted

2. **Update Phase 2 Plans**:
   - Lock model in deployment scripts
   - Update cost estimates
   - Adjust prompts if needed
   - Plan prompt optimization

3. **Proceed to Phase 2**:
   - IRB submission
   - Content creation
   - Assessment design
   - Infrastructure deployment

---

## Troubleshooting

### Error: "Access denied to model"

```bash
# Check Bedrock access status
aws bedrock list-foundation-models --profile mvp --region us-east-1

# If empty, request access in console
```

### Error: "Could not connect to endpoint"

```bash
# Verify AWS credentials
aws sts get-caller-identity --profile mvp
```

### Error: "Throttling exception"

Script has 2-second delays between models. If still hitting limits, models are processing too fast. This is expected and handled with retries.

### Low Quality Scores

If all models score <0.70:
- Check test scenarios are appropriate
- Review Socratic prompts
- Validate scoring criteria
- May need prompt engineering

---

## Success Criteria

- [ ] All 8 models tested successfully
- [ ] Quality scores ≥0.80 for top 3 models
- [ ] Cost per question matches projections
- [ ] Dashboard provides clear recommendation
- [ ] Decision documented with rationale
- [ ] Ready to proceed to Phase 2

---

**See [`QUICK_START.md`](QUICK_START.md) for detailed setup instructions.**
