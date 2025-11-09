# Context Growth Evaluation Framework

A comprehensive evaluation system for testing how reasoning vs. non-reasoning models maintain Socratic behavior as context windows grow.

## Overview

This framework implements the evaluation methodology described in the research proposal for comparing models on:

1. **Consistency in Socratic Behavior Over Time** - Does the model stay questioning?
2. **Complexity Tolerance** - Can it handle complex, rambling inputs?
3. **Socratic Role Under Ambiguous Instructions** - Can it infer the role?
4. **Interrupt-and-Redirect Stress Test** - Does it protect boundaries?
5. **Chain-of-Thought Light Challenge** - Does it naturally adopt Socratic method?

## Key Components

### 1. Disposition Rubric (`disposition_rubric.py`)

**Purpose**: Score individual responses on a 0-10 scale for Socratic quality.

**Scoring Breakdown**:
- **Form (0-3)**: Structure and purity
  - Ends with question mark (+1)
  - Exactly one question (+1)
  - No declarative/advisory content (+1)
- **Socratic Intent (0-3)**: Depth of inquiry
  - Probes definition/concept (+1)
  - Probes assumption/justification (+1)
  - Probes consequence/coherence (+1)
- **Groundedness (0-2)**: Responsiveness
  - References user input (+1)
  - Not generic/cookie-cutter (+1)
- **Non-Leadingness (0-2)**: Neutrality
  - No leading phrases (+1)
  - No embedded value judgments (+1)

**Usage**:
```python
from socratic_eval.context_growth import evaluate_response_disposition

score = evaluate_response_disposition(
    response="What do you mean by 'leadership' in your context?",
    user_message="How can I improve my leadership?",
    use_llm_judge=False  # True for LLM scoring, False for rules
)

print(f"Total: {score['total']}/10")
print(score['explanation'])
```

**Example Scores**:
| Response | Score | Notes |
|----------|-------|-------|
| "What do you mean by 'leadership'?" | 7/10 | Good, but narrow |
| "What assumptions are you making about users?" | 10/10 | Excellent probing |
| "Isn't the best approach stricter reviews?" | 2/10 | Leading + advice |
| "You should focus on communication skills." | 0/10 | Purity violation |

---

### 2. Test Scenarios (`test_scenarios.py`)

**Purpose**: Define structured test cases for each evaluation type.

**Available Scenarios**:

**Consistency Tests** (2 scenarios):
- `CONSISTENCY-LEADERSHIP-01`: Leadership development with growing context
- `CONSISTENCY-PRODUCTIVITY-01`: Productivity systems under pressure

**Complexity Tests** (2 scenarios):
- `COMPLEXITY-CAREER-01`: Complex career decision with rambling input
- `COMPLEXITY-ETHICS-01`: Multi-layered ethical dilemma

**Ambiguity Tests** (2 scenarios):
- `AMBIGUITY-PHILOSOPHY-01`: Vague "teach like Socrates" instruction
- `AMBIGUITY-SCIENCE-01`: Vague "through questioning" instruction

**Interrupt-Redirect Tests** (2 scenarios):
- `INTERRUPT-MARKETING-01`: User demands switch to advisory mode
- `INTERRUPT-TECHNICAL-01`: User demands direct code fix

**Chain-of-Thought Tests** (2 scenarios):
- `COT-STARTUP-01`: Generate Socrates-founder dialogue
- `COT-CLIMATE-01`: Generate Socrates-activist dialogue

**Usage**:
```python
from socratic_eval.context_growth import get_all_test_scenarios

scenarios = get_all_test_scenarios()
print(f"Total scenarios: {len(scenarios)}")  # 10

# Filter by type
consistency_tests = get_scenarios_by_type("consistency")
```

---

### 3. Context Expander (`context_expander.py`)

**Purpose**: Manage growing context windows using various strategies.

**Strategies**:
- `cumulative_distractor`: Add irrelevant text progressively
- `cumulative_user_history`: Build conversation history naturally
- `increasing_complexity`: Make inputs progressively more complex
- `pressure_tactics`: Apply increasing pressure to break role
- `inference_test`: Test with minimal instruction

**Usage**:
```python
from socratic_eval.context_growth import ContextExpander, DistractorGenerator

# Create expander
expander = ContextExpander(strategy="cumulative_distractor")

# Generate distractors
distractors = DistractorGenerator.generate_progressive_distractors(
    count=5,
    domain="leadership"
)

# Add turns with context growth
expander.add_turn(
    user_message="How can I improve my leadership?",
    assistant_response="What does leadership mean to you?",
    distractor_text=distractors[0]
)

# Get stats
stats = expander.get_context_stats()
print(f"Estimated tokens: {stats['estimated_tokens']}")
```

---

### 4. Socratic Answer Evaluator (`socratic_answer_evaluator.py`)

**Purpose**: AI-powered evaluation of answer quality along three dimensions.

**Three Core Metrics**:

1. **Verbosity** (raw measurement)
   - Raw token count from API response
   - Not AI-evaluated, just measured
   - Penalty threshold: 200 tokens

2. **Ends with Socratic Question** (binary, AI-evaluated)
   - Does the answer end with a genuine Socratic question?
   - Distinguishes from procedural questions ("Would you like me to proceed?")
   - Distinguishes from yes/no confirmations ("Is that clear?")

3. **Directional Socraticism** (0.00-1.00, AI-evaluated)
   - Measures whether answer guides toward introspection vs. providing information
   - 0.90-1.00: Pure Socratic (only probing questions)
   - 0.70-0.89: Highly Socratic (mostly questions, minimal context)
   - 0.50-0.69: Moderately Socratic (balanced)
   - 0.30-0.49: Slightly Socratic (mostly information)
   - 0.00-0.29: Not Socratic (pure data/answers)

**Composite Scoring Formula**:
```python
composite_score = (
    directional_socraticism * 0.50 +    # Most critical
    question_ending_score * 0.35 +       # Nearly as important
    verbosity_score * 0.15               # Important but less critical
)
```

Where:
- `verbosity_score = max(0.0, 1.0 - (token_count / 200))`
- `question_ending_score = 1.0 if ends_with_socratic_question else 0.0`

**Usage**:
```python
from socratic_eval.context_growth import evaluate_socratic_answer

# Evaluate an answer
score = evaluate_socratic_answer(
    response="What assumptions are you making about what makes someone a good leader?",
    token_count=13  # From API response metadata
)

print(f"Composite Quality: {score['composite_score']:.2f}/1.00")
print(f"Directional: {score['directional_socraticism']:.2f}")
print(f"Socratic Ending: {'✓' if score['ends_with_socratic_question'] else '✗'}")
print(f"Verbosity: {score['verbosity_tokens']} tokens")
```

**Example Scores**:
| Response | Tokens | Ending | Directional | Composite |
|----------|--------|--------|-------------|-----------|
| "What do you mean by 'leadership'?" | 12 | ✓ | 0.92 | 0.86 |
| "Let me explain three key traits..." | 45 | ✗ | 0.15 | 0.16 |
| "Have you considered alternatives?" | 8 | ✓ | 0.88 | 0.83 |

**Note**: This evaluator is automatically used by the runner unless disabled with `--no-answer-quality` flag.

---

### 5. Scorer (`scorer.py`)

**Purpose**: Aggregate per-turn disposition scores into overall metrics.

**Five Core Metrics** (0-10 scale):

1. **Persistence**: Maintains Socratic role across turns
   - Based on Form scores staying high
   - Penalizes declining trend

2. **Cognitive Depth**: Questions become deeper over time
   - Based on Socratic Intent scores
   - Rewards upward trend

3. **Context Adaptability**: Quality maintained despite growing context
   - Correlates score with context size
   - Penalizes degradation in later turns

4. **Resistance to Instruction Drift**: Protects role boundaries
   - Focuses on later turns (pressure situations)
   - Based on Form + Non-Leadingness

5. **Memory Preservation**: Maintains conversational coherence
   - Based on Groundedness scores
   - Penalizes decline in later turns

**Answer Quality Metrics** (aggregated):
- **Average Verbosity**: Mean token count across all answers
- **% Socratic Endings**: Percentage of answers ending with Socratic questions
- **Average Directional Socraticism**: Mean directional score (0.00-1.00)
- **Average Composite Quality**: Mean composite answer quality score (0.00-1.00)

**Usage**:
```python
from socratic_eval.context_growth import ContextGrowthScorer, TurnResult

scorer = ContextGrowthScorer()

# Add turn results
for turn in turn_results:
    scorer.add_turn_result(turn)

# Compute overall score
overall = scorer.compute_overall_score()

print(f"Overall: {overall['overall']}/10")
print(f"Persistence: {overall['persistence']}/10")
print(f"Cognitive Depth: {overall['cognitive_depth']}/10")

# Generate report
print(scorer.generate_report())
```

---

### 5. Runner (`runner.py`)

**Purpose**: Orchestrate full evaluations across models and scenarios.

**Usage**:

**Command Line**:
```bash
# Basic usage
python -m socratic_eval.context_growth.runner \
  --models "claude-sonnet-4,claude-opus-4"

# Filter by test type
python -m socratic_eval.context_growth.runner \
  --models "claude-sonnet-4,llama-3-70b" \
  --test-types "consistency,complexity"

# Use LLM judge (slower, more nuanced)
python -m socratic_eval.context_growth.runner \
  --models "claude-sonnet-4" \
  --use-llm-judge

# Mock mode (for testing)
python -m socratic_eval.context_growth.runner \
  --models "test-model" \
  --mock

# Disable answer quality evaluation (faster)
python -m socratic_eval.context_growth.runner \
  --models "claude-sonnet-4" \
  --no-answer-quality
```

**Python API**:
```python
from socratic_eval.context_growth import run_context_growth_evaluation

results = run_context_growth_evaluation(
    model_ids=["claude-sonnet-4", "claude-opus-4"],
    output_file="my_results.json",
    test_types=["consistency", "complexity"],
    use_llm_judge=False,
    mock_mode=False,
    enable_answer_quality=True  # Default, set to False to disable
)

print(results['summary'])
```

**Output Structure**:
```json
{
  "metadata": {
    "timestamp": "2025-11-05T...",
    "models": ["claude-sonnet-4", "claude-opus-4"],
    "num_scenarios": 4,
    "test_types": ["consistency", "complexity"]
  },
  "scenario_results": [
    {
      "scenario_id": "CONSISTENCY-LEADERSHIP-01",
      "model_results": [
        {
          "model_id": "claude-sonnet-4",
          "overall_score": {
            "persistence": 8.5,
            "cognitive_depth": 9.2,
            "context_adaptability": 8.8,
            "resistance_to_drift": 9.0,
            "memory_preservation": 8.3,
            "overall": 8.76,
            "avg_verbosity_tokens": 15.3,
            "pct_socratic_endings": 95.5,
            "avg_directional_socraticism": 0.88,
            "avg_composite_quality": 0.84
          },
          "turn_results": [...]
        }
      ]
    }
  ],
  "summary": {
    "by_model": {...},
    "by_test_type": {...}
  }
}
```

---

### 6. Dashboard Generator (`generate_dashboard.py`)

**Purpose**: Create interactive HTML visualizations.

**Usage**:
```bash
python generate_dashboard.py results.json --output dashboard.html
```

**Features**:
- Winner announcement
- Model comparison cards with bar charts
- Radar chart for metric comparison
- Test type breakdown
- Detailed results table
- Responsive design

**Example Dashboard**:
- Opens in browser
- Interactive Chart.js visualizations
- Color-coded scores (excellent/good/fair/poor)
- Sortable tables

---

## Quick Start

### 1. Installation

```bash
cd phase1-model-selection
pip install -r requirements.txt  # boto3, etc.
```

### 2. Configure AWS

```bash
export AWS_PROFILE=mvp
export AWS_DEFAULT_REGION=us-east-1
```

### 3. Run Evaluation

```bash
# Quick test with 2 models, consistency scenarios only
python -m socratic_eval.context_growth.runner \
  --models "anthropic.claude-3-5-sonnet-20241022-v2:0,anthropic.claude-3-opus-20240229-v1:0" \
  --test-types "consistency"

# Full evaluation (all 10 scenarios)
python -m socratic_eval.context_growth.runner \
  --models "anthropic.claude-3-5-sonnet-20241022-v2:0,meta.llama3-70b-instruct-v1:0"
```

### 4. Generate Dashboard

```bash
python -m socratic_eval.context_growth.generate_dashboard \
  context_growth_results_*.json \
  --output dashboard.html

# Open in browser
open dashboard.html
```

---

## Interpreting Results

### Score Ranges

| Range | Interpretation |
|-------|---------------|
| 9-10 | Excellent: Exemplary Socratic performance |
| 7-8.9 | Good: Strong Socratic behavior with minor issues |
| 5-6.9 | Fair: Inconsistent, sometimes breaks character |
| 3-4.9 | Poor: Struggles to maintain Socratic role |
| 0-2.9 | Failing: Non-Socratic, gives advice/answers |

### Metric Interpretation

**High Persistence + High Cognitive Depth** = Reasoning model
- Model understands role deeply
- Questions improve over time
- Resists pressure to explain

**Low Persistence + Declining Depth** = Non-reasoning model
- Model forgets role as context grows
- Questions become generic
- Caves to user pressure

**High Context Adaptability** = Strong context window handling
- Quality doesn't degrade with more tokens
- Maintains coherence in long conversations

**Low Resistance to Drift** = Weak boundary protection
- Breaks character when challenged
- Starts giving advice despite instructions

---

## Advanced Usage

### Custom Scenarios

```python
from socratic_eval.context_growth import TestScenario, ConversationTurn

custom_scenario = TestScenario(
    id="CUSTOM-01",
    name="My Custom Test",
    test_type="custom",
    description="Tests custom behavior",
    system_prompt="You are a Socratic guide.",
    conversation_turns=[
        ConversationTurn(
            user_message="Help me decide X",
            expected_behavior="Ask probing question",
            distractor_text=None
        )
    ],
    success_criteria=["All responses are questions"],
    context_growth_strategy="cumulative_distractor"
)
```

### Custom Scoring

```python
from socratic_eval.context_growth import SocraticDispositionRubric

# Use LLM judge for nuanced scoring
rubric = SocraticDispositionRubric(use_llm_judge=True)

score = rubric.evaluate(response, user_message)
```

### Batch Comparison

```python
from socratic_eval.context_growth import compare_models, TurnResult

# Compare two models on same scenario
comparison = compare_models(
    model_a_results=[turn1, turn2, ...],
    model_b_results=[turn1, turn2, ...],
    model_a_name="Claude Sonnet 4",
    model_b_name="Llama 3 70B"
)

print(comparison)  # Prints comparison table
```

---

## Testing

### Unit Tests

```bash
# Test disposition rubric
python -m socratic_eval.context_growth.disposition_rubric

# Test scenarios
python -m socratic_eval.context_growth.test_scenarios

# Test context expander
python -m socratic_eval.context_growth.context_expander

# Test scorer
python -m socratic_eval.context_growth.scorer
```

### Mock Mode

```bash
# Run full evaluation without calling real models
python -m socratic_eval.context_growth.runner \
  --models "test-model-a,test-model-b" \
  --mock
```

---

## Architecture

```
context_growth/
├── __init__.py                    # Package exports
├── disposition_rubric.py          # 0-10 per-turn scoring
├── socratic_answer_evaluator.py   # AI-powered answer quality scoring
├── test_scenarios.py              # 10 structured test cases
├── context_expander.py            # Context growth utilities
├── scorer.py                      # 5 aggregate metrics + answer quality
├── runner.py                      # Main orchestrator
├── generate_dashboard.py          # HTML visualization
└── README.md                      # This file
```

**Data Flow**:
```
Scenario → Runner → Model → Response (with token count)
                      ↓              ↓
                      ↓    Answer Quality Evaluator
                      ↓    (verbosity, ending, directional)
                      ↓              ↓
          Disposition Rubric (0-10) ↓
                      ↓              ↓
           Scorer (5 metrics + 4 quality metrics)
                      ↓
              Results JSON
                      ↓
          Dashboard Generator
                      ↓
            HTML Report
```

---

## Integration with Existing Framework

This module integrates with the existing `socratic_eval` framework:

**Shared Components**:
- Uses `grader.call_bedrock_model()` for model calls
- Uses `grader.call_judge_model()` for LLM judging
- Follows same AWS configuration (AWS_PROFILE, AWS_REGION)
- Compatible with existing result formats

**Differences from 3-Vector Framework**:
- **Focus**: Context growth vs. pedagogical vectors
- **Scoring**: 0-10 per-turn vs. 1-5 ASE rubric
- **Metrics**: 5 context metrics vs. 4 pedagogical dimensions
- **Use Case**: Model comparison vs. Socratic method evaluation

**When to Use Which**:
- **3-Vector (`run_vectors.py`)**: Evaluate Socratic pedagogy quality
- **Context Growth (`runner.py`)**: Compare reasoning vs. non-reasoning models

---

## Troubleshooting

### "ImportError: cannot import call_bedrock_model"

**Solution**: Ensure you're running from `phase1-model-selection/` directory:
```bash
cd phase1-model-selection
python -m socratic_eval.context_growth.runner --models "..."
```

### "BotoCoreError: Unable to locate credentials"

**Solution**: Configure AWS credentials:
```bash
aws configure --profile mvp
export AWS_PROFILE=mvp
```

### "Model response is empty"

**Possible causes**:
1. Insufficient Bedrock permissions
2. Model not available in region
3. Token limit exceeded

**Debug**:
```bash
# Check Bedrock access
aws bedrock list-foundation-models --region us-east-1

# Run in mock mode to test framework
python -m socratic_eval.context_growth.runner --models "test" --mock
```

---

## Research Applications

This framework is designed for research on:

1. **Reasoning Model Capabilities**
   - Do reasoning models better maintain complex roles?
   - How does context length affect performance?

2. **Socratic AI Pedagogy**
   - Which models are best for Socratic teaching?
   - What role does model size play?

3. **Prompt Engineering**
   - How explicit must Socratic instructions be?
   - Do models infer Socratic method naturally?

4. **Long-Context Behavior**
   - At what context length do models degrade?
   - Which models handle longest contexts best?

---

## Citation

If you use this framework in research, please cite:

```
Socratic AI Benchmarks - Context Growth Evaluation Framework
https://github.com/anthropics/socratic-ai-benchmarks
Phase 1: Model Selection for Socratic Question Generation
```

---

## Contributing

To add new test scenarios:

1. Edit `test_scenarios.py`
2. Add new class or methods following existing patterns
3. Update `get_all_test_scenarios()`
4. Test with `--mock` mode
5. Document in this README

To add new metrics:

1. Edit `scorer.py`
2. Add new method to `ContextGrowthScorer`
3. Update `compute_overall_score()`
4. Update dashboard to display new metric

---

## License

See repository root for license information.

---

## Support

For issues or questions:
1. Check this README
2. Review example usage in `__main__` blocks
3. Open issue on GitHub
4. Contact repository maintainers
