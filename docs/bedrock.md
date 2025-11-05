# Bedrock Routing Documentation

This document describes how **all LLM requests** in the Socratic Benchmark system are routed through **Amazon Bedrock**.

---

## Core Principle

**All requests go through Amazon Bedrock. No direct provider SDKs are used.**

This applies to:
- Dialogue generation (Runner Lambda / CLI)
- Turn scoring (Judge Lambda)
- Any future LLM operations

---

## Model Registry

The following models are supported via Bedrock for Phase 1:

```yaml
models:
  - id: anthropic.claude-3-5-sonnet-20241022-v1:0
    label: "Claude 3.5 Sonnet (extended thinking)"
    provider: Anthropic
    use_cases:
      - dialogue
      - judge
    notes: "Recommended for both dialogue and judging"

  - id: anthropic.claude-3-opus-20240229-v1:0
    label: "Claude 3 Opus"
    provider: Anthropic
    use_cases:
      - dialogue
      - judge
    notes: "Highest quality, slower and more expensive"

  - id: anthropic.claude-3-5-haiku-20241022-v1:0
    label: "Claude 3.5 Haiku"
    provider: Anthropic
    use_cases:
      - dialogue
    notes: "Fast and affordable, suitable for high-volume runs"

  - id: meta.llama3-1-70b-instruct-v1:0
    label: "Llama 3.1 70B Instruct"
    provider: Meta
    use_cases:
      - dialogue
    notes: "Open-source alternative, good quality"

  - id: meta.llama3-1-8b-instruct-v1:0
    label: "Llama 3.1 8B Instruct"
    provider: Meta
    use_cases:
      - dialogue
    notes: "Ultra-cheap baseline, lower quality"

  - id: mistral.mistral-large-2407-v1:0
    label: "Mistral Large 24.07"
    provider: Mistral AI
    use_cases:
      - dialogue
    notes: "Non-Anthropic alternative"

  - id: amazon.titan-text-premier-v1:0
    label: "Titan Text Premier"
    provider: Amazon
    use_cases:
      - dialogue
    notes: "AWS native model"
```

### How to Add/Remove Models

**To add a model:**

1. Ensure the model is available in your AWS region via Bedrock
2. Request model access in AWS Console (Bedrock → Model access)
3. Add the model ID to the `BEDROCK_MODEL_IDS` environment variable
4. Test with CLI: `docker run ... --model <new-model-id> ...`

**To remove a model:**

1. Remove the model ID from `BEDROCK_MODEL_IDS`
2. Existing runs with that model remain in DynamoDB/S3

**Example**:

```bash
export BEDROCK_MODEL_IDS='[
  "anthropic.claude-3-5-sonnet-20241022-v1:0",
  "meta.llama3-1-70b-instruct-v1:0",
  "mistral.mistral-large-2407-v1:0",
  "amazon.titan-text-premier-v1:0"
]'
```

---

## API Calls

We use two Bedrock APIs:

### 1. Converse API (Dialogue Generation)

**Used by**: Runner Lambda / CLI

**Endpoint**: `bedrock-runtime:Converse`

**Purpose**: Multi-turn dialogue generation

**Example Request** (via boto3):

```python
import boto3

bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')

response = bedrock.converse(
    modelId='anthropic.claude-3-5-sonnet-20241022-v1:0',
    messages=[
        {
            'role': 'user',
            'content': [{'text': 'I am considering a career change.'}]
        }
    ],
    system=[
        {'text': 'You are a Socratic tutor. Ask probing questions...'}
    ],
    inferenceConfig={
        'maxTokens': 512,
        'temperature': 0.7
    }
)

ai_message = response['output']['message']['content'][0]['text']
```

**Benefits**:
- Model-agnostic interface
- Built-in streaming support
- Handles message history automatically

### 2. InvokeModel API (Judge Scoring)

**Used by**: Judge Lambda

**Endpoint**: `bedrock-runtime:InvokeModel`

**Purpose**: Single-turn scoring requests

**Example Request** (via boto3):

```python
import boto3
import json

bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')

prompt = {
    "anthropic_version": "bedrock-2023-05-31",
    "max_tokens": 1024,
    "system": "You are a judge evaluating Socratic questions...",
    "messages": [
        {
            "role": "user",
            "content": "Score this question: 'What aspects of your career feel misaligned?'"
        }
    ]
}

response = bedrock.invoke_model(
    modelId='anthropic.claude-3-5-sonnet-20241022-v1:0',
    body=json.dumps(prompt)
)

result = json.loads(response['body'].read())
score = result['content'][0]['text']
```

**Benefits**:
- Lower latency for single requests
- Full control over request format
- Used with trusted judge model (Claude 3.5 Sonnet v2)

---

## Permissions

### IAM Policy for Bedrock Access

**Minimum permissions** for CLI and Lambda:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": [
        "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-5-sonnet-20241022-v1:0",
        "arn:aws:bedrock:us-east-1::foundation-model/meta.llama3-1-70b-instruct-v1:0",
        "arn:aws:bedrock:us-east-1::foundation-model/mistral.mistral-large-2407-v1:0",
        "arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-text-premier-v1:0"
      ]
    }
  ]
}
```

**Note**: Replace `us-east-1` with your region.

### Cross-Account Access (Optional)

If Bedrock access is in a different AWS account, use `BEDROCK_ASSUME_ROLE_ARN`:

```bash
export BEDROCK_ASSUME_ROLE_ARN=arn:aws:iam::123456789012:role/BedrockInvokeRole
```

**Trust policy** for the role (in the Bedrock account):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::987654321098:root"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

**Permissions policy** for the role:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": "arn:aws:bedrock:*::foundation-model/*"
    }
  ]
}
```

### SSM Parameter Store (Not Used for Bedrock)

**Important**: Bedrock uses IAM-based authentication only. No API keys or secrets are needed.

If you're using SSM for other secrets (e.g., API keys for future integrations), add:

```json
{
  "Effect": "Allow",
  "Action": [
    "ssm:GetParameter",
    "ssm:GetParameters"
  ],
  "Resource": "arn:aws:ssm:us-east-1:123456789012:parameter/socratic-bench/*"
}
```

---

## Regions

### Primary Region

**Default**: `us-east-1` (US East - N. Virginia)

**Reason**: Widest model availability and lowest latency for most models

### Supported Regions

The following regions have broad Bedrock model support:

- `us-east-1` (N. Virginia) — **Recommended**
- `us-west-2` (Oregon)
- `eu-west-1` (Ireland)
- `ap-southeast-1` (Singapore)

**Check model availability**:

```bash
aws bedrock list-foundation-models \
  --region us-east-1 \
  --query 'modelSummaries[?contains(modelId, `anthropic`)]'
```

### Fallback Region (Future)

Phase 1 uses a single region. Future phases may implement multi-region fallback:

```python
REGIONS = ['us-east-1', 'us-west-2']

for region in REGIONS:
    try:
        bedrock = boto3.client('bedrock-runtime', region_name=region)
        response = bedrock.converse(...)
        break
    except Exception as e:
        continue
```

---

## Retry and Throttling

### Exponential Backoff

All Bedrock calls include retry logic with exponential backoff:

```python
import time
from botocore.exceptions import ClientError

def invoke_bedrock_with_retry(bedrock_client, **kwargs):
    retries = 4
    backoff = [2, 4, 8, 16]  # seconds

    for attempt in range(retries):
        try:
            response = bedrock_client.converse(**kwargs)
            return response
        except ClientError as e:
            if e.response['Error']['Code'] == 'ThrottlingException':
                if attempt < retries - 1:
                    time.sleep(backoff[attempt])
                    continue
            raise

    raise Exception("Max retries exceeded")
```

### Throttling Limits

**Default Bedrock quotas** (per region):

| Model | Requests/min | Tokens/min |
|-------|--------------|------------|
| Claude 3.5 Sonnet | 200 | 300,000 |
| Claude 3 Opus | 50 | 100,000 |
| Claude 3.5 Haiku | 500 | 500,000 |
| Llama 3.1 70B | 200 | 300,000 |
| Mistral Large | 200 | 300,000 |

**To request quota increase**:
1. AWS Console → Service Quotas
2. Search "Bedrock"
3. Request increase for specific model

---

## Cost Estimation

**Pricing** (as of 2025-11, us-east-1):

| Model | Input (per 1M tokens) | Output (per 1M tokens) |
|-------|-----------------------|------------------------|
| Claude 3.5 Sonnet | $3.00 | $15.00 |
| Claude 3 Opus | $15.00 | $75.00 |
| Claude 3.5 Haiku | $0.80 | $4.00 |
| Llama 3.1 70B | $0.99 | $0.99 |
| Mistral Large | $2.00 | $6.00 |
| Titan Text Premier | $0.50 | $1.50 |

**Example weekly run** (2 models × 6 scenarios × 5 turns):

- **Dialogue**: 12 runs × 5 turns × 200 tokens = 12,000 tokens → $0.18
- **Judge**: 60 judgments × 500 tokens = 30,000 tokens → $0.45

**Total**: ~$0.63/week for dialogue + judge

---

## Monitoring

### CloudWatch Metrics

Bedrock does not expose native metrics to CloudWatch. We log custom metrics:

```python
import boto3

cloudwatch = boto3.client('cloudwatch')

cloudwatch.put_metric_data(
    Namespace='SocraticBench',
    MetricData=[
        {
            'MetricName': 'BedrockLatency',
            'Value': latency_ms,
            'Unit': 'Milliseconds',
            'Dimensions': [
                {'Name': 'ModelId', 'Value': model_id},
                {'Name': 'Operation', 'Value': 'Converse'}
            ]
        }
    ]
)
```

**Metrics tracked**:
- `BedrockLatency`: API call latency (ms)
- `BedrockTokens`: Tokens consumed (input + output)
- `BedrockErrors`: Error count by type
- `BedrockThrottles`: Throttling exception count

### Logs

All Bedrock calls are logged to CloudWatch Logs:

```
[INFO] Invoking Bedrock: model=anthropic.claude-3-5-sonnet-20241022-v1:0
[INFO] Bedrock response: latency=1250ms, tokens=120/18
[ERROR] Bedrock throttled: retrying in 2s
```

**Log group**: `/aws/lambda/SocraticBenchStack-RunnerFunction`

---

## Troubleshooting

### "ResourceNotFoundException: Could not find model"

**Cause**: Model not available in your region or account.

**Fix**:
1. Check model availability: `aws bedrock list-foundation-models --region us-east-1`
2. Request model access: AWS Console → Bedrock → Model access
3. Wait for approval (usually instant for Claude/Llama)

### "AccessDeniedException: User is not authorized"

**Cause**: IAM permissions missing.

**Fix**: Add `bedrock:InvokeModel` permission (see [Permissions](#permissions))

### "ThrottlingException: Rate exceeded"

**Cause**: Exceeded requests-per-minute quota.

**Fix**:
1. Retry logic (built-in)
2. Request quota increase (AWS Console → Service Quotas)
3. Reduce concurrency (Lambda reserved concurrency)

### "ValidationException: Invalid model input"

**Cause**: Request format incorrect for model.

**Fix**: Ensure you're using the correct API:
- **Converse API**: For multi-turn dialogues
- **InvokeModel API**: For single requests with model-specific format

---

## Best Practices

### 1. Use Converse API for Dialogues

**Why**: Model-agnostic, handles context automatically, easier to maintain.

```python
# ✅ Good: Converse API
response = bedrock.converse(
    modelId='anthropic.claude-3-5-sonnet-20241022-v1:0',
    messages=messages,
    system=system_prompt
)

# ❌ Bad: InvokeModel with custom format
response = bedrock.invoke_model(
    modelId='anthropic.claude-3-5-sonnet-20241022-v1:0',
    body=json.dumps({'messages': messages, ...})
)
```

### 2. Cache System Prompts

**Why**: Reduces token usage for repeated system prompts.

```python
# Future: Use Bedrock prompt caching
response = bedrock.converse(
    modelId='...',
    messages=[...],
    system=[{'text': socratic_prompt, 'cacheControl': {'type': 'ephemeral'}}]
)
```

### 3. Monitor Token Usage

**Why**: Track costs and optimize prompt length.

```python
response = bedrock.converse(...)
input_tokens = response['usage']['inputTokens']
output_tokens = response['usage']['outputTokens']

print(f"Tokens used: {input_tokens} input, {output_tokens} output")
```

### 4. Handle Streaming (Optional)

For real-time UIs (future):

```python
response = bedrock.converse_stream(
    modelId='...',
    messages=[...]
)

for event in response['stream']:
    if 'contentBlockDelta' in event:
        chunk = event['contentBlockDelta']['delta']['text']
        print(chunk, end='', flush=True)
```

---

## Security

### No API Keys Stored

**Important**: Bedrock uses IAM-based authentication. No API keys or secrets are stored.

### Audit Logging

Enable CloudTrail for Bedrock API calls:

```bash
aws cloudtrail create-trail \
  --name bedrock-audit \
  --s3-bucket-name my-audit-bucket

aws cloudtrail start-logging \
  --name bedrock-audit
```

**Events logged**:
- `InvokeModel`
- `InvokeModelWithResponseStream`
- `Converse`
- `ConverseStream`

---

## Related Documentation

- **[README.md](../README.md)** – Overview and quickstart
- **[docs/architecture.md](architecture.md)** – System architecture
- **[docs/runner.md](runner.md)** – Docker CLI usage
- **[docs/benchmark.md](benchmark.md)** – SDB scoring rubric

---

*Last Updated: 2025-11-05*
