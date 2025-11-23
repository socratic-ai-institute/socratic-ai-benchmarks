# Model Configuration and Testing Skill

## Description
Add new AI models to the benchmark suite, configure their parameters, run test invocations, and verify integration.

## When to Use
- Adding a new model (e.g., Gemini 3 Pro)
- Testing a new provider integration
- Updating model costs or configurations
- Running one-time test for new model
- Fixing model invocation issues

## Quick Start: Add New Model

### 1. Update Model Configuration
Edit `serverless/config-24-models.json`:

```json
{
  "model_id": "google.gemini-3-pro-preview",
  "name": "Gemini 3 Pro Preview",
  "cost_per_1k_input": 0.00015,
  "cost_per_1k_output": 0.0006,
  "expected_score": 6.2
}
```

**Required fields**:
- `model_id`: Provider.model-name format (e.g., `google.gemini-3-pro-preview`, `bedrock.claude-3-sonnet`)
- `name`: Human-readable name for dashboard
- `cost_per_1k_input`: Cost per 1000 input tokens
- `cost_per_1k_output`: Cost per 1000 output tokens
- `expected_score`: Estimated 0-10 score (for display)

### 2. Create Client Module (if new provider)
Example: `serverless/lib/socratic_bench/google_client.py`

```python
from dataclasses import dataclass
from google import genai

@dataclass
class GoogleModelConfig:
    model_id: str
    api_key: str

class GoogleClient:
    def __init__(self, config: GoogleModelConfig):
        self.config = config
        genai.configure(api_key=config.api_key)
        self.client = genai.Client()

    def invoke(self, prompt: str) -> dict:
        response = self.client.models.generate_content(
            model=self.config.model_id,
            contents=[{"role": "user", "parts": [{"text": prompt}]}],
            config=GenerateContentConfig(temperature=1.0)
        )
        return {
            "text": response.text,
            "latency_ms": 0,  # Calculate if available
            "input_tokens": 0,
            "output_tokens": len(response.text.split())
        }
```

### 3. Add Provider Routing in models.py
Edit `serverless/lib/socratic_bench/models.py`:

```python
if provider == "google":
    from socratic_bench.google_client import GoogleClient, GoogleModelConfig
    config = GoogleModelConfig(
        model_id=model_id.replace("google.", ""),
        api_key=os.environ.get("GOOGLE_API_KEY", "")
    )
    client = GoogleClient(config)
    return client.invoke(prompt)
```

### 4. Add Environment Variables
Edit `serverless/infra/stack.py`:

```python
google_api_key = self.node.try_get_context("google_api_key") or \
                 os.environ.get("GOOGLE_API_KEY", "")
if google_api_key:
    common_env["GOOGLE_API_KEY"] = google_api_key
```

### 5. Update Requirements
Edit `serverless/lib/requirements.txt`:

```
google-genai>=0.3.0
```

## Running Tests

### 1. Test Model Invocation Directly
```python
import sys
sys.path.insert(0, 'serverless/lib')

from socratic_bench.models import invoke_model

result = invoke_model(
    model_id="google.gemini-3-pro-preview",
    prompt="What is the capital of France?",
    scenario_id="test"
)
print(f"Response: {result['text']}")
print(f"Tokens: {result.get('output_tokens', 0)}")
```

### 2. Test Full Pipeline (one-time run)
```bash
cd /Users/williamprior/Development/GitHub/socratic-ai-benchmarks

# Trigger lambda with test event
aws lambda invoke \
  --function-name SocraticBenchStack-RunBenchmarkLambda \
  --payload '{"model_id": "google.gemini-3-pro-preview", "mode": "single"}' \
  --profile mvp \
  /tmp/response.json

# Check result
cat /tmp/response.json | jq '.'
```

### 3. Check DynamoDB for Results
```bash
# Scan for new model results
aws dynamodb query \
  --table-name socratic_core \
  --key-condition-expression "begins_with(PK, :prefix)" \
  --expression-attribute-values '{":prefix":{"S":"RUN#google.gemini"}}' \
  --profile mvp | jq '.Items | length'
```

### 4. Verify in Dashboard
- Deploy changes: `cd serverless/infra && cdk deploy --profile mvp --require-approval never`
- Visit dashboard: https://d3ic7ds776p9cq.cloudfront.net/research.html
- Check "Latest Model Rankings" chart for new model

## Configuration Reference

### Provider Format
| Provider | Prefix | Example |
|----------|--------|---------|
| Anthropic (Bedrock) | bedrock. | bedrock.claude-3-sonnet-20240229-v1:0 |
| AWS (Bedrock) | bedrock. | bedrock.us.amazon.nova-pro-v1:0 |
| Meta (Bedrock) | bedrock. | bedrock.us.meta.llama3-70b-instruct-v1:0 |
| Google | google. | google.gemini-3-pro-preview |

### Cost Estimation
```python
# Calculate cost per run
input_tokens = 500  # typical prompt
output_tokens = 200  # typical response

input_cost = (input_tokens / 1000) * cost_per_1k_input
output_cost = (output_tokens / 1000) * cost_per_1k_output
total_cost = input_cost + output_cost
```

## Debugging Integration Issues

### Model Not Invoked
**Check**:
1. Model ID exists in config file
2. Provider is routed in `models.py`
3. API key is set in environment
4. Model exists in provider's API

```bash
# Test Google API directly
export GOOGLE_API_KEY="your-key"
python3 << 'EOF'
from google import genai
genai.configure(api_key="your-key")
response = genai.Client().models.generate_content(
    model="gemini-3-pro-preview",
    contents=[{"role": "user", "parts": [{"text": "Hi"}]}]
)
print(response.text)
EOF
```

### Authentication Fails
```bash
# Verify API key
echo $GOOGLE_API_KEY

# Check Bedrock access (if using AWS models)
aws bedrock list-foundation-models --profile mvp --region us-east-1 | jq '.modelSummaries | length'
```

### Results Not Appearing
```bash
# Check Lambda logs
aws logs tail /aws/lambda/SocraticBenchStack-RunBenchmarkLambda --profile mvp --follow

# Check for errors
aws logs filter-log-events \
  --log-group-name /aws/lambda/SocraticBenchStack-RunBenchmarkLambda \
  --filter-pattern "ERROR" \
  --profile mvp
```

## Related Files
- `serverless/config-24-models.json` - Model definitions
- `serverless/lib/socratic_bench/models.py` - Provider routing
- `serverless/infra/stack.py` - Lambda environment variables
- `serverless/lambdas/benchmark/handler.py` - Benchmark runner
- `serverless/lib/requirements.txt` - Dependencies
