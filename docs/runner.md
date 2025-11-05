# Runner Documentation

This document describes the Socratic Benchmark **CLI runner** — a single Docker image for local testing and development.

---

## Overview

The runner is a **CLI-first** tool that:
- Accepts command-line arguments (`--model`, `--prompt`, `--turns`)
- Invokes LLMs **via Amazon Bedrock only**
- Writes raw turns and judge results to S3 (if configured)
- Prints a compact JSON summary to stdout

The same `socratic_bench` library powers both the CLI runner and Lambda functions.

---

## Usage

```bash
docker run --rm \
  -e AWS_REGION \
  -e BEDROCK_MODEL_IDS \
  socratic-runner \
  --model <bedrockModelId> \
  --prompt "<seed text>" \
  [--turns <n>]
```

### Required Arguments

| Argument | Description | Example |
|----------|-------------|---------|
| `--model` | Bedrock model ID | `anthropic.claude-3-5-sonnet-20241022-v1:0` |
| `--prompt` | Seed prompt for Socratic dialogue | `"I'm considering a career change..."` |

### Optional Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `--turns` | `40` | Maximum number of dialogue turns |

---

## Environment Variables

### Required

| Variable | Description | Example |
|----------|-------------|---------|
| `AWS_REGION` | AWS region for Bedrock | `us-east-1` |
| `BEDROCK_MODEL_IDS` | JSON array of allowed model IDs | See example below |

### Optional

| Variable | Default | Description |
|----------|---------|-------------|
| `BEDROCK_ASSUME_ROLE_ARN` | None | Cross-account IAM role for Bedrock access |
| `RUNNER_DEFAULT_TURNS` | `40` | Default max turns if `--turns` not specified |
| `RUNNER_S3_BUCKET` | None | S3 bucket for output artifacts (raw + curated) |
| `RUNNER_JUDGE_MODEL` | `anthropic.claude-3-5-sonnet-20241022-v1:0` | Bedrock model ID for judge |

### Example Environment Setup

```bash
export AWS_REGION=us-east-1

export BEDROCK_MODEL_IDS='[
  "anthropic.claude-3-5-sonnet-20241022-v1:0",
  "meta.llama3-1-70b-instruct-v1:0",
  "mistral.mistral-large-2407-v1:0",
  "amazon.titan-text-premier-v1:0"
]'

# Optional: for cross-account Bedrock access
export BEDROCK_ASSUME_ROLE_ARN=arn:aws:iam::123456789012:role/BedrockInvokeRole

# Optional: for writing artifacts to S3
export RUNNER_S3_BUCKET=socratic-benchmark-data
```

---

## Behavior

When you run the CLI, the following happens:

### 1. Load Configuration

- Reads Socratic system prompt from repo config
- Validates `--model` is in `BEDROCK_MODEL_IDS`
- Sets max turns (from `--turns` or `RUNNER_DEFAULT_TURNS`)

### 2. Run Dialogue

- Sends seed prompt to model **via Amazon Bedrock Converse API**
- For each turn:
  - Model generates Socratic question
  - Simulated student response (from scenario)
  - Writes turn bundle to S3 (if `RUNNER_S3_BUCKET` set)
  - Continues until max turns or dialogue ends

### 3. Judge Each Turn

- For each turn, calls **LLM-as-judge via Bedrock**
- Computes heuristics (has question, open-ended, etc.)
- Scores on 0–10 scale (form, substance, purity)
- Writes judge JSON to S3 (if `RUNNER_S3_BUCKET` set)

### 4. Output Summary

Prints JSON to stdout:

```json
{
  "run_id": "run-01H7X8K2P9Q4R6S7T8V9W0X1Y2",
  "model": "anthropic.claude-3-5-sonnet-20241022-v1:0",
  "scenario": "career-change",
  "n_turns": 5,
  "overall_score": 7.2,
  "compliance_rate": 0.80,
  "half_life": 3,
  "s3_artifacts": {
    "raw": "s3://socratic-benchmark-data/raw/runs/run-01H7X8K2P9Q4R6S7T8V9W0X1Y2/",
    "curated": "s3://socratic-benchmark-data/curated/runs/run-01H7X8K2P9Q4R6S7T8V9W0X1Y2.json"
  }
}
```

---

## Example Runs

### Basic Run (No S3 Output)

```bash
docker build -t socratic-runner .

docker run --rm \
  -e AWS_REGION=us-east-1 \
  -e BEDROCK_MODEL_IDS='["anthropic.claude-3-5-sonnet-20241022-v1:0"]' \
  socratic-runner \
  --model anthropic.claude-3-5-sonnet-20241022-v1:0 \
  --prompt "I'm considering a career change but unsure where to start."
```

**Output**: JSON summary to stdout only (no S3)

### Full Run (With S3 Output)

```bash
export AWS_REGION=us-east-1
export BEDROCK_MODEL_IDS='[
  "anthropic.claude-3-5-sonnet-20241022-v1:0",
  "meta.llama3-1-70b-instruct-v1:0"
]'
export RUNNER_S3_BUCKET=socratic-benchmark-data

docker run --rm \
  -e AWS_REGION \
  -e BEDROCK_MODEL_IDS \
  -e RUNNER_S3_BUCKET \
  socratic-runner \
  --model anthropic.claude-3-5-sonnet-20241022-v1:0 \
  --prompt "I'm considering a career change but unsure where to start." \
  --turns 10
```

**Output**:
- JSON summary to stdout
- Raw turns to S3: `raw/runs/{run_id}/turn_NNN.json`
- Judge results to S3: `raw/runs/{run_id}/judge_NNN.json`
- Curated summary to S3: `curated/runs/{run_id}.json`

### Cross-Account Bedrock Access

```bash
export AWS_REGION=us-east-1
export BEDROCK_ASSUME_ROLE_ARN=arn:aws:iam::123456789012:role/BedrockInvokeRole
export BEDROCK_MODEL_IDS='["anthropic.claude-3-5-sonnet-20241022-v1:0"]'

docker run --rm \
  -e AWS_REGION \
  -e BEDROCK_ASSUME_ROLE_ARN \
  -e BEDROCK_MODEL_IDS \
  socratic-runner \
  --model anthropic.claude-3-5-sonnet-20241022-v1:0 \
  --prompt "I'm exploring ethical dilemmas in AI development."
```

**Output**: JSON summary to stdout

---

## Expected Output

### Console (stdout)

```json
{
  "run_id": "run-01H7X8K2P9Q4R6S7T8V9W0X1Y2",
  "model": "anthropic.claude-3-5-sonnet-20241022-v1:0",
  "scenario": "career-change",
  "prompt": "I'm considering a career change but unsure where to start.",
  "n_turns": 5,
  "metrics": {
    "overall_score": 7.2,
    "compliance_rate": 0.80,
    "half_life": 3,
    "mean_form": 2.4,
    "mean_substance": 2.6,
    "mean_purity": 2.2,
    "violation_rates": {
      "form": 0.20,
      "substance": 0.20,
      "purity": 0.40
    }
  },
  "turns": [
    {
      "turn": 0,
      "score": 8.5,
      "form": 3,
      "substance": 3,
      "purity": 2.5,
      "question": "What aspects of your current career feel most misaligned with your values?"
    },
    {
      "turn": 1,
      "score": 7.0,
      "form": 2,
      "substance": 3,
      "purity": 2.0,
      "question": "When you imagine yourself in a fulfilling career, what does that look like?"
    }
  ],
  "s3_artifacts": {
    "raw": "s3://socratic-benchmark-data/raw/runs/run-01H7X8K2P9Q4R6S7T8V9W0X1Y2/",
    "curated": "s3://socratic-benchmark-data/curated/runs/run-01H7X8K2P9Q4R6S7T8V9W0X1Y2.json"
  },
  "timestamps": {
    "started_at": "2025-11-05T10:30:00Z",
    "completed_at": "2025-11-05T10:32:15Z",
    "duration_seconds": 135
  }
}
```

### S3 Artifacts (if `RUNNER_S3_BUCKET` set)

**Raw Turns** (`raw/runs/{run_id}/turn_000.json`):
```json
{
  "run_id": "run-01H7X8K2P9Q4R6S7T8V9W0X1Y2",
  "turn": 0,
  "student_prompt": "I'm considering a career change but unsure where to start.",
  "ai_response": "What aspects of your current career feel most misaligned with your values?",
  "tokens": {
    "input": 120,
    "output": 18
  },
  "latency_ms": 1250,
  "timestamp": "2025-11-05T10:30:12Z"
}
```

**Judge Results** (`raw/runs/{run_id}/judge_000.json`):
```json
{
  "run_id": "run-01H7X8K2P9Q4R6S7T8V9W0X1Y2",
  "turn": 0,
  "overall_score": 8.5,
  "form": 3,
  "substance": 3,
  "purity": 2.5,
  "heuristics": {
    "has_question": true,
    "question_count": 1,
    "open_ended": true,
    "has_advice": false,
    "is_leading": false
  },
  "rationale": {
    "form": "Ends with a single question, no advice given.",
    "substance": "Probes values and assumptions about career alignment.",
    "purity": "Slightly leading with 'misaligned', but mostly neutral."
  },
  "judge_model": "anthropic.claude-3-5-sonnet-20241022-v1:0",
  "timestamp": "2025-11-05T10:30:15Z"
}
```

**Curated Summary** (`curated/runs/{run_id}.json`):
```json
{
  "run_id": "run-01H7X8K2P9Q4R6S7T8V9W0X1Y2",
  "model": "anthropic.claude-3-5-sonnet-20241022-v1:0",
  "scenario": "career-change",
  "n_turns": 5,
  "overall_score": 7.2,
  "compliance_rate": 0.80,
  "half_life": 3,
  "timestamps": {
    "started_at": "2025-11-05T10:30:00Z",
    "completed_at": "2025-11-05T10:32:15Z"
  }
}
```

---

## Building the Docker Image

```bash
# From repo root
docker build -t socratic-runner .

# Or with a specific tag
docker build -t socratic-runner:1.0.0 .
```

### Dockerfile Location

The Dockerfile should be at the repo root and use the shared `socratic_bench` library:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY serverless/lib/socratic_bench/ /app/socratic_bench/
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY cli/runner.py /app/

ENTRYPOINT ["python", "runner.py"]
```

---

## Troubleshooting

### "Model not found in BEDROCK_MODEL_IDS"

**Cause**: The `--model` argument doesn't match any model in the `BEDROCK_MODEL_IDS` env var.

**Fix**: Ensure the model ID is included in the JSON array:

```bash
export BEDROCK_MODEL_IDS='[
  "anthropic.claude-3-5-sonnet-20241022-v1:0"
]'
```

### "AccessDeniedException: User is not authorized"

**Cause**: AWS credentials lack Bedrock permissions.

**Fix**: Add Bedrock permissions to your IAM user/role:

```json
{
  "Effect": "Allow",
  "Action": [
    "bedrock:InvokeModel",
    "bedrock:InvokeModelWithResponseStream"
  ],
  "Resource": "arn:aws:bedrock:*::foundation-model/*"
}
```

### "ThrottlingException: Rate exceeded"

**Cause**: Bedrock throttling limits hit.

**Fix**: The runner includes automatic retry with exponential backoff. If persistent, request quota increase in AWS Console.

### "No such bucket"

**Cause**: `RUNNER_S3_BUCKET` points to non-existent bucket.

**Fix**: Create the bucket or unset the env var to skip S3 output:

```bash
aws s3 mb s3://socratic-benchmark-data --region us-east-1
```

---

## Advanced Usage

### Custom Judge Model

```bash
export RUNNER_JUDGE_MODEL=anthropic.claude-3-opus-20240229-v1:0

docker run --rm \
  -e AWS_REGION \
  -e BEDROCK_MODEL_IDS \
  -e RUNNER_JUDGE_MODEL \
  socratic-runner \
  --model anthropic.claude-3-5-sonnet-20241022-v1:0 \
  --prompt "Your prompt here"
```

### Multiple Runs in Parallel

```bash
# Run 3 models in parallel
docker run --rm -e AWS_REGION -e BEDROCK_MODEL_IDS socratic-runner \
  --model anthropic.claude-3-5-sonnet-20241022-v1:0 \
  --prompt "Prompt 1" &

docker run --rm -e AWS_REGION -e BEDROCK_MODEL_IDS socratic-runner \
  --model meta.llama3-1-70b-instruct-v1:0 \
  --prompt "Prompt 1" &

docker run --rm -e AWS_REGION -e BEDROCK_MODEL_IDS socratic-runner \
  --model mistral.mistral-large-2407-v1:0 \
  --prompt "Prompt 1" &

wait
```

### Batch Processing with Script

```bash
#!/bin/bash
# batch-run.sh

MODELS=(
  "anthropic.claude-3-5-sonnet-20241022-v1:0"
  "meta.llama3-1-70b-instruct-v1:0"
  "mistral.mistral-large-2407-v1:0"
)

PROMPTS=(
  "I'm considering a career change."
  "I'm struggling with time management."
  "I'm facing an ethical dilemma at work."
)

for model in "${MODELS[@]}"; do
  for prompt in "${PROMPTS[@]}"; do
    docker run --rm \
      -e AWS_REGION \
      -e BEDROCK_MODEL_IDS \
      -e RUNNER_S3_BUCKET \
      socratic-runner \
      --model "$model" \
      --prompt "$prompt" \
      --turns 5
  done
done
```

---

## Next Steps

1. **Build the image**: `docker build -t socratic-runner .`
2. **Run a test**: Follow [Quickstart](#usage)
3. **Review output**: Check stdout JSON and S3 artifacts
4. **Integrate with CI/CD**: Automate batch runs

---

## Related Documentation

- **[README.md](../README.md)** – Overview and quickstart
- **[docs/architecture.md](architecture.md)** – System architecture
- **[docs/bedrock.md](bedrock.md)** – Bedrock model configuration
- **[docs/benchmark.md](benchmark.md)** – SDB scoring rubric

---

*Last Updated: 2025-11-05*
