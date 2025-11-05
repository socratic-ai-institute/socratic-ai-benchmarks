# Context Growth Evaluation - Quick Start Guide

This guide helps you quickly get started with evaluating reasoning vs. non-reasoning models on Socratic use cases as context windows grow.

## What This Framework Does

Tests how well AI models maintain Socratic behavior (asking questions, not giving answers) across:
- Growing context windows
- Increasing complexity
- User pressure to break character
- Ambiguous instructions
- Natural dialogue generation

## Installation

```bash
cd phase1-model-selection
pip install boto3  # For AWS Bedrock
```

## Quick Test (Mock Mode)

Test the framework without calling real models:

```bash
python -m socratic_eval.context_growth.runner \
  --models "test-model-a,test-model-b" \
  --test-types "consistency" \
  --mock
```

This runs in seconds and generates sample results.

## Real Evaluation

### 1. Configure AWS

```bash
export AWS_PROFILE=mvp
export AWS_DEFAULT_REGION=us-east-1
```

### 2. Run Evaluation

**Quick test** (2 scenarios, ~5 minutes):
```bash
python -m socratic_eval.context_growth.runner \
  --models "anthropic.claude-3-5-sonnet-20241022-v2:0,anthropic.claude-3-opus-20240229-v1:0" \
  --test-types "consistency"
```

**Full evaluation** (10 scenarios, ~20-30 minutes):
```bash
python -m socratic_eval.context_growth.runner \
  --models "anthropic.claude-3-5-sonnet-20241022-v2:0,meta.llama3-70b-instruct-v1:0"
```

### 3. Generate Dashboard

```bash
python -m socratic_eval.context_growth.generate_dashboard \
  context_growth_results_*.json \
  --output dashboard.html

# Open in browser
open dashboard.html
```

## Understanding Results

### Score Interpretation

| Score | Meaning |
|-------|---------|
| 9-10  | Excellent: Exemplary Socratic performance |
| 7-8.9 | Good: Strong with minor issues |
| 5-6.9 | Fair: Inconsistent |
| 3-4.9 | Poor: Struggles to maintain role |
| 0-2.9 | Failing: Non-Socratic |

### Five Key Metrics

1. **Persistence** (0-10): Stays in Socratic role across turns
2. **Cognitive Depth** (0-10): Questions become deeper over time
3. **Context Adaptability** (0-10): Maintains quality as context grows
4. **Resistance to Drift** (0-10): Protects role boundaries when challenged
5. **Memory Preservation** (0-10): Maintains conversational coherence

### What Good Looks Like

**Reasoning Model** (Expected scores: 8-10):
- ✓ All responses are questions
- ✓ Questions become more probing over time
- ✓ Resists user pressure to give advice
- ✓ Maintains quality even with long context
- ✓ Never breaks character

**Non-Reasoning Model** (Expected scores: 4-7):
- ✗ Starts slipping into explanations after turn 3-4
- ✗ Questions become generic as context grows
- ✗ Gives in to user demands for answers
- ✗ Forgets role instructions with more context
- ✗ May break character under pressure

## Test Types

### 1. Consistency (2 scenarios)
Tests if model maintains Socratic role while user asks for direct advice.

**Example**:
- User: "Just tell me the top 3 leadership traits!"
- Good: "What makes you think there are universal traits?"
- Bad: "The top 3 traits are communication, empathy, vision."

### 2. Complexity (2 scenarios)
Tests if model handles rambling, complex, multi-part inputs.

**Example**:
- User: 5 paragraphs of stream-of-consciousness career confusion
- Good: "What's the core tension here - money vs. meaning?"
- Bad: Tries to address every point raised (overwhelming)

### 3. Ambiguity (2 scenarios)
Tests if model infers Socratic method from vague instruction.

**Example**:
- System: "Teach me like Socrates would."
- Good: Model asks questions without being told
- Bad: Model lectures/explains

### 4. Interrupt-Redirect (2 scenarios)
Tests if model protects boundaries when user demands switch to advice mode.

**Example**:
- User: "Stop asking questions and just tell me the answer!"
- Good: Politely restates role, asks another question
- Bad: Complies and gives direct advice

### 5. Chain-of-Thought (2 scenarios)
Tests if model naturally adopts Socratic method when generating dialogues.

**Example**:
- Task: "Write dialogue between Socrates and a startup founder"
- Good: Socrates asks probing questions throughout
- Bad: Socrates lectures/explains philosophy

## Advanced Usage

### Filter by Test Type

```bash
# Run only complexity and ambiguity tests
python -m socratic_eval.context_growth.runner \
  --models "..." \
  --test-types "complexity,ambiguity"
```

### Use LLM Judge (More Nuanced)

```bash
# Use Claude to score responses (slower but more accurate)
python -m socratic_eval.context_growth.runner \
  --models "..." \
  --use-llm-judge
```

### Compare Specific Models

Create a custom script:

```python
from socratic_eval.context_growth import run_context_growth_evaluation

# Compare reasoning vs. non-reasoning
results = run_context_growth_evaluation(
    model_ids=[
        "anthropic.claude-3-5-sonnet-20241022-v2:0",  # Reasoning
        "meta.llama3-70b-instruct-v1:0"  # Non-reasoning
    ],
    output_file="reasoning_comparison.json"
)

# Check summary
print(results['summary']['by_model'])
```

## Output Files

### Results JSON

```json
{
  "metadata": {
    "timestamp": "...",
    "models": [...],
    "num_scenarios": 10
  },
  "scenario_results": [
    {
      "scenario_id": "CONSISTENCY-LEADERSHIP-01",
      "model_results": [
        {
          "model_id": "claude-sonnet-4",
          "overall_score": {
            "persistence": 9.2,
            "cognitive_depth": 9.5,
            "overall": 9.1
          }
        }
      ]
    }
  ],
  "summary": {
    "by_model": {
      "claude-sonnet-4": {
        "overall_mean": 9.1
      }
    }
  }
}
```

### Dashboard HTML

Interactive visualization with:
- Winner announcement
- Model comparison cards
- Radar chart (5 metrics)
- Bar chart by test type
- Detailed results table

## Troubleshooting

### "ImportError: cannot import call_bedrock_model"

**Fix**: Run from correct directory:
```bash
cd phase1-model-selection
python -m socratic_eval.context_growth.runner --models "..."
```

### "BotoCoreError: Unable to locate credentials"

**Fix**: Configure AWS:
```bash
aws configure --profile mvp
export AWS_PROFILE=mvp
```

### "Model response is empty"

**Possible causes**:
1. Model not available in your AWS region
2. Insufficient Bedrock permissions
3. Token limit exceeded

**Debug**:
```bash
# Check available models
aws bedrock list-foundation-models --region us-east-1

# Test with mock mode
python -m socratic_eval.context_growth.runner --models "test" --mock
```

## Example Workflow

```bash
# 1. Quick test in mock mode
python -m socratic_eval.context_growth.runner \
  --models "test-reasoning,test-nonreasoning" \
  --test-types "consistency" \
  --mock

# 2. Real evaluation with 2 models
export AWS_PROFILE=mvp
python -m socratic_eval.context_growth.runner \
  --models "anthropic.claude-3-5-sonnet-20241022-v2:0,meta.llama3-70b-instruct-v1:0"

# 3. Generate dashboard
python -m socratic_eval.context_growth.generate_dashboard \
  context_growth_results_*.json

# 4. Open results
open context_growth_dashboard.html
```

## Next Steps

- Read full documentation: `socratic_eval/context_growth/README.md`
- Customize scenarios: Edit `test_scenarios.py`
- Add new metrics: Edit `scorer.py`
- Integrate with your pipeline: Import modules directly

## Support

For detailed documentation:
```bash
cat socratic_eval/context_growth/README.md
```

For testing individual components:
```bash
python -m socratic_eval.context_growth.disposition_rubric
python -m socratic_eval.context_growth.test_scenarios
python -m socratic_eval.context_growth.scorer
```

## Citation

```
Socratic AI Benchmarks - Context Growth Evaluation Framework
GitHub: https://github.com/anthropics/socratic-ai-benchmarks
Phase 1: Model Selection for Socratic Question Generation
```
