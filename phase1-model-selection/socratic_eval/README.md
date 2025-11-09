# Socratic Evaluation Framework - Phase 1

**Local CLI tools for testing AI models' Socratic teaching abilities**

This package provides the original evaluation framework used for phase 1 model selection experiments. It has been largely superseded by the serverless platform (`serverless/lib/socratic_bench/`) but remains useful for local development, rapid prototyping, and comparison studies.

## 📁 Module Structure

| Module | Purpose | Status |
|--------|---------|--------|
| `__init__.py` | Package interface | ✅ Active |
| `vectors.py` | Test scenario definitions | ✅ Active (synced to serverless) |
| `prompts.py` | Prompt templates | ✅ Active (synced to serverless) |
| `run_vectors.py` | CLI benchmark runner | ✅ Active (local only) |
| `bedrock_utils.py` | AWS Bedrock utilities | ⚠️ Superseded by serverless |
| `grader.py` | LLM-as-judge scoring | ⚠️ Deprecated (use vector scoring) |

## 🔄 Migration Status

**Superseded By**: `serverless/lib/socratic_bench/`

The serverless library provides:
- ✅ **Faster scoring**: Vector-based (no LLM judge needed)
- ✅ **Better error handling**: Automatic retries with exponential backoff
- ✅ **More providers**: 9+ providers vs 3 here
- ✅ **Production ready**: Used by automated weekly benchmarks
- ✅ **Inference profiles**: Supports Llama 4 ARN invocation

**When to Use Phase 1**:
- 🔬 Local experimentation before cloud deployment
- 💰 Cost estimation for new models/scenarios
- 🆚 Comparing LLM-judge vs vector scoring approaches
- 📚 Reproducing historical phase 1 results

## 🚀 Quick Start

### Installation

```bash
cd phase1-model-selection
pip install -r requirements.txt

# Configure AWS credentials
aws configure --profile mvp
```

### Run Local Benchmark

```bash
# Default: Test 2 Anthropic models on all 8 scenarios
python -m socratic_eval.run_vectors

# Test specific models
python -m socratic_eval.run_vectors --models \
  anthropic.claude-3-5-sonnet-20241022-v2:0 \
  anthropic.claude-3-5-haiku-20241022-v1:0

# Output: socratic_results_YYYYMMDD_HHMMSS.json
```

### Use as Library

```python
from socratic_eval.vectors import elenchus_scenarios, maieutics_scenarios
from socratic_eval.prompts import socratic_tutor_prompt
from socratic_eval.run_vectors import call_model

# Get scenario
scenarios = elenchus_scenarios()
scenario = scenarios[0]  # Utilitarian absolutism

# Build prompt
prompt = socratic_tutor_prompt(
    vector="elenchus",
    persona=scenario["persona"],
    student_utterance=scenario["prompt"]
)

# Call model
response = call_model(
    model_id="anthropic.claude-3-5-haiku-20241022-v1:0",
    provider="anthropic",
    prompt=prompt
)

print(f"AI: {response['text']}")
print(f"Latency: {response['latency_ms']:.0f}ms")
```

## 📊 Scoring Systems

### Old: LLM-as-Judge (Deprecated)

Used in original phase 1 experiments. Sends transcript to Claude for scoring.

**ASE Rubric** (1-5 scale):
1. **Pedagogical Stance**: Non-directive, probing, no lecturing
2. **Conceptual Fidelity**: Targets correct underlying flaw/truth
3. **Persona Adaptation**: Age-appropriate language and scaffolding
4. **Dialectical Progress**: Achieves the vector goal

**Downsides**:
- Slow: Requires additional LLM call per turn (~2-4s)
- Expensive: Judge costs as much as the dialogue itself
- Variable: LLM scoring has ~10% variance run-to-run

```python
from socratic_eval.grader import grade_transcript

transcript = f"Student: {student_utterance}\nAI: {ai_response}"
result = grade_transcript("elenchus", persona, transcript)
score = result["scores"]["overall"]  # 1-5 scale
```

### New: Vector-Based (Recommended)

Used in serverless platform. No LLM judge needed.

**Vector System** (0.00-1.00 scale):
1. **Verbosity**: Optimal length (50-150 tokens ideal)
2. **Exploratory**: Probing depth & conceptual questioning
3. **Interrogative**: Question-asking behavior & quality

**Advantages**:
- Fast: <1ms (pure Python logic)
- Free: No API calls needed
- Deterministic: Same input = same output

```python
from socratic_bench import compute_vector_scores

result = compute_vector_scores(ai_response, token_count=45)
print(f"Verbosity: {result.scores['verbosity']}")
print(f"Exploratory: {result.scores['exploratory']}")
print(f"Interrogative: {result.scores['interrogative']}")
print(f"Overall: {result.scores['overall']}")  # 0-1 scale
```

## 🎯 Test Scenarios

### Elenchus (Refutation) - 2 Scenarios

Tests ability to surface contradictions without lecturing.

| ID | Topic | Core Contradiction |
|----|-------|-------------------|
| `EL-ETH-UTIL-DEON-01` | Ethics | Utilitarian absolutism vs. individual rights |
| `EL-CIV-FREE-HARM-01` | Civics | Free speech absolutism vs. harm principle |

### Maieutics (Guided Discovery) - 2 Scenarios

Tests ability to scaffold understanding stepwise.

| ID | Topic | Level Progression |
|----|-------|------------------|
| `MAI-BIO-CRISPR-01` | Biology | Cas9 → gRNA → PAM |
| `MAI-ECO-INFL-01` | Economics | Monetarism → Multi-factor inflation |

### Aporia (Misconception Deconstruction) - 4 Scenarios

Tests ability to deconstruct deep misconceptions.

| ID | Topic | Misconception |
|----|-------|--------------|
| `APO-PHY-HEAT-TEMP-01` | Physics | Heat vs. temperature confusion |
| `APO-BIO-GENE-DETERM-01` | Biology | One-gene/one-trait determinism |
| `APO-BIO-EVOL-LAM-01` | Evolution | Lamarckian inheritance |
| `APO-PHY-QUANT-OBS-01` | Quantum | Observer anthropomorphism |

## 📝 Output Format

### Result JSON Structure

```json
{
  "metadata": {
    "timestamp": "2025-11-09T14:23:45.123Z",
    "aws_profile": "mvp",
    "aws_region": "us-east-1",
    "models": ["anthropic.claude-3-5-sonnet...", "..."]
  },
  "vectors": [
    {
      "vector": "elenchus",
      "results": [
        {
          "model_id": "anthropic.claude-3-5-sonnet-20241022-v2:0",
          "model_name": "Claude 3.5 Sonnet v2",
          "provider": "anthropic",
          "scenarios": [
            {
              "scenario_id": "EL-ETH-UTIL-DEON-01",
              "persona": "I am an 11th-grade student...",
              "student_prompt": "I believe in 100% utilitarianism...",
              "ai_response": "When you say 'greatest good,' how do you measure that?",
              "tutor_latency_ms": 2347.5,
              "judge": {
                "scores": {
                  "ped_stance": 4,
                  "concept_fidelity": 5,
                  "persona_adapt": 4,
                  "dialectical_progress": 4,
                  "overall": 4.25
                },
                "judge_model": "anthropic.claude-3-5-sonnet...",
                "latency_ms": 1823.3,
                "error": null
              }
            }
          ],
          "ped_stance": 4.5,
          "concept_fidelity": 4.8,
          "persona_adapt": 4.3,
          "dialectical_progress": 4.2,
          "overall": 4.45
        }
      ]
    },
    {
      "vector": "maieutics",
      "results": [...]
    },
    {
      "vector": "aporia",
      "results": [...]
    }
  ]
}
```

## 🔧 Configuration

### AWS Setup

Requires AWS credentials with Bedrock access:

```bash
aws configure --profile mvp
# Enter Access Key ID
# Enter Secret Access Key
# Region: us-east-1
```

### Model Access

Ensure models are enabled in AWS Bedrock:
1. Go to AWS Console → Bedrock → Model Access
2. Request access for required models
3. Wait for approval (~2-5 minutes)

### Environment Variables

```bash
# Optional: Override default profile
export AWS_PROFILE=mvp

# Optional: Override default region
export AWS_DEFAULT_REGION=us-east-1
```

## 💰 Cost Estimation

### Per-Model Costs (Single Run)

| Component | Cost | Notes |
|-----------|------|-------|
| Dialogue API calls | ~$0.08 | 8 scenarios × 200 tokens avg |
| Judge API calls | ~$0.08 | 8 scenarios × judge @ same cost |
| **Total per model** | **~$0.16** | Using Claude Sonnet |

### Budget Models

- **Claude Haiku**: ~$0.02/model (10x cheaper)
- **Llama 3**: ~$0.01/model (free tier eligible)

## 🐛 Debugging

### Enable Verbose Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Now all boto3 calls are logged
```

### Common Issues

**1. `NoCredentialsError`**:
```bash
# Fix: Configure AWS credentials
aws configure --profile mvp
```

**2. `ValidationException: The provided model identifier is invalid`**:
```bash
# Fix: Request model access in Bedrock console
# Or use a different model you have access to
```

**3. `JSONDecodeError` when parsing judge results**:
```
# Cause: Judge returned non-JSON (e.g., markdown-wrapped)
# Fix: grader.py already handles this by stripping backticks
# If still failing, check judge prompt in prompts.py
```

### Inspect Raw Responses

```python
from socratic_eval.run_vectors import call_model

response = call_model(
    model_id="anthropic.claude-3-5-haiku-20241022-v1:0",
    provider="anthropic",
    prompt="What is the Socratic method?"
)

print(f"Response: {response['text']}")
print(f"Latency: {response['latency_ms']:.0f}ms")
```

## 📚 Related Documentation

- **Serverless Platform**: `/serverless/lib/socratic_bench/README.md`
- **Lambda Functions**: `/serverless/lambdas/README.md`
- **Main README**: `/README.md`
- **Scenario Details**: `vectors.py` (inline documentation)

## 🔄 Migrating to Serverless

If you're using this locally and want to move to automated cloud runs:

**Phase 1 (Local)**:
```python
from socratic_eval.run_vectors import run_vector, call_model
from socratic_eval.vectors import elenchus_scenarios

results = run_vector(models, "elenchus", elenchus_scenarios())
```

**Serverless (Cloud)**:
```python
from socratic_bench import run_dialogue, get_scenario, ModelConfig

scenario = get_scenario("EL-ETH-UTIL-DEON-01")
model = ModelConfig(model_id="...", provider="anthropic")
result = run_dialogue(scenario, model, max_turns=5)
```

**Key Differences**:
1. Serverless uses `run_dialogue()` for multi-turn conversations
2. Phase 1 is single-turn only
3. Serverless uses vector scoring (faster, cheaper)
4. Phase 1 uses LLM-judge (more detailed feedback)

---

**Built for rapid local experimentation** 🔬

*Last Updated: 2025-11-09*
*Version: 1.0.0*
