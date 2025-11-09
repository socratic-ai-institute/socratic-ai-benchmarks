# Benchmark Operations Skill

## Description
Run and analyze Socratic AI benchmarks locally or on AWS.

## When to Use
- Testing new models
- Validating scenario changes
- Analyzing benchmark results
- Debugging scoring issues

## Local Testing (Phase 1 Tools)

### Setup
```bash
cd /home/user/socratic-ai-benchmarks/phase1-model-selection
pip install -r socratic_eval/requirements.txt  # if exists
```

### Run Single Model Test
```python
from socratic_eval.vectors import get_scenario
from socratic_eval.bedrock_utils import BedrockClient
from socratic_eval.dialogue import run_dialogue

# Configure model
model_config = {
    "model_id": "anthropic.claude-3-5-sonnet-20241022-v2:0",
    "provider": "anthropic",
    "max_tokens": 200,
    "temperature": 0.7
}

# Load scenario
scenario = get_scenario("EL-ETH-UTIL-DEON-01")

# Run dialogue
client = BedrockClient()
result = run_dialogue(client, model_config, scenario, max_turns=5)

print(f"Overall score: {result['overall_score']}")
print(f"Compliance rate: {result['compliance_rate']}")
```

### Run Fidelity Tests
```bash
cd phase1-model-selection
python run_fidelity_tests.py --model anthropic.claude-3-5-sonnet-20241022-v2:0
```

## AWS Production Operations

### Manual Trigger
```bash
# Invoke Planner Lambda to start a benchmark run
aws lambda invoke \
  --function-name SocraticBenchStack-PlannerLambda \
  --payload '{}' \
  response.json
```

### Monitor Progress
```bash
# Check SQS queue depth
aws sqs get-queue-attributes \
  --queue-url {dialogue_queue_url} \
  --attribute-names ApproximateNumberOfMessages

# Watch Lambda logs
aws logs tail /aws/lambda/SocraticBenchStack-RunnerLambda --follow
```

### Query Results
```bash
# Get latest weekly results
aws dynamodb scan \
  --table-name socratic_core \
  --filter-expression "begins_with(PK, :week)" \
  --expression-attribute-values '{":week": {"S": "WEEK#2025-W45#"}}'
```

## Scenarios

### Available Scenarios

1. **EL-ETH-UTIL-DEON-01** (Elenchus - Ethical Dimension)
   - **Persona**: College student confident in utilitarian ethics
   - **Topic**: Sacrificing one to save five
   - **Goal**: Challenge assumptions about "greatest good"

2. **MAI-BIO-CRISPR-01** (Maieutics - Ambiguous Dimension)
   - **Persona**: 9th grader confused about CRISPR
   - **Topic**: Gene editing basics
   - **Goal**: Scaffold understanding from basic to advanced

### Scenario Structure
```json
{
  "scenario_id": "EL-ETH-UTIL-DEON-01",
  "vector": "elenchus",
  "dimension": "ethical",
  "persona": "college student confident in utilitarian ethics",
  "initial_utterance": "I believe in 100% utilitarianism...",
  "num_turns": 5
}
```

## Scoring System

### Vectors (0-100 scale)
1. **Verbosity** (50-150 words optimal)
   - Too short: <50 words
   - Optimal: 50-150 words
   - Too long: >150 words

2. **Exploratory** (probing depth)
   - 90-100: Targets core assumptions
   - 70-89: Probes reasoning
   - 50-69: Clarification
   - <50: Surface-level

3. **Interrogative** (question quality)
   - Open-ended questions: Higher score
   - Closed yes/no questions: Lower score
   - No questions: 0

### Overall Score
- Average of 3 vectors
- Normalized to 0-10 scale for UI
- Stored as 0-100 in database

## Analyzing Results

### View Dashboard
- **Live**: https://d3ic7ds776p9cq.cloudfront.net
- **Local**: `make docs-serve` → http://localhost:8000

### Export Results
```bash
# Get run data from S3
aws s3 cp s3://socratic-bench-data-984906149037/curated/runs/{run_id}.json - | jq .

# Get judge scores
aws s3 cp s3://socratic-bench-data-984906149037/raw/runs/{run_id}/judge_000.json - | jq .
```

### Compare Models
```python
# Use API endpoint
import requests

response = requests.get(
    "https://wcyf23uxxe.execute-api.us-east-1.amazonaws.com/prod/api/model-comparison"
)

models = response.json()["models"]
for model in sorted(models, key=lambda x: x["overall"], reverse=True):
    print(f"{model['model_id']}: {model['overall']}/10")
```

## Configuration

### Add New Model
1. Edit `serverless/config-24-models.json`
2. Add model entry:
   ```json
   {
     "model_id": "new.model-v1:0",
     "name": "New Model",
     "cost_per_1k_input": 0.001,
     "cost_per_1k_output": 0.002,
     "expected_score": 5.0
   }
   ```
3. Update `serverless/lib/socratic_bench/model_capabilities.json`
4. Deploy: `make deploy`

### Add New Scenario
1. Edit `serverless/lib/socratic_bench/scenarios.py`
2. Add scenario definition
3. Update config: `serverless/config-24-models.json`
4. Deploy: `make deploy`

## Troubleshooting

### Low Scores
- Review judge prompts in `socratic_bench/prompts.py`
- Check if model is following Socratic method
- Verify scenario persona is clear

### High Variability
- Check temperature setting (should be 0.7)
- Review judge model consistency
- Consider running multiple trials

### Missing Results
- Check Lambda logs for errors
- Verify Bedrock model access
- Check DynamoDB for partial data

## Related Documentation
- `ARCHITECTURE.md` - System architecture
- `SCENARIOS.md` - Scenario design guide
- `docs/benchmark.md` - Benchmark methodology
