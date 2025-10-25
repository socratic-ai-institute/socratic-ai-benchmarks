# AI Model Comparison & Selection Platform

## Purpose

**Automated benchmarking system to test 10 competing AI models** and identify the best one for Socratic question generation before deploying the full research platform.

---

## Core Objective

**Answer the question**: Which AI model generates the highest-quality Socratic questions?

**Test**: 10 models × 120 test scenarios = 1,200 total generations

**Output**: Ranked list of models by quality, cost, and latency

---

## The 10 Competing Models

### **Tier 1: Premium Models** (Highest quality, highest cost)
1. **Claude 3.5 Sonnet v2** (Anthropic)
   - Model ID: `anthropic.claude-3-5-sonnet-20241022-v2:0`
   - Cost: ~$0.015/1K tokens (input), ~$0.075/1K tokens (output)
   - Expected: Best quality, 2-3s latency

2. **Claude 3 Opus** (Anthropic)
   - Model ID: `anthropic.claude-3-opus-20240229-v1:0`
   - Cost: ~$0.015/1K tokens (input), ~$0.075/1K tokens (output)
   - Expected: Highest quality, 3-5s latency

3. **GPT-4 Turbo** (OpenAI via Bedrock or direct API)
   - Model ID: `gpt-4-turbo-preview`
   - Cost: ~$0.01/1K tokens (input), ~$0.03/1K tokens (output)
   - Expected: High quality, 2-4s latency

4. **GPT-4o** (OpenAI)
   - Model ID: `gpt-4o`
   - Cost: ~$0.005/1K tokens (input), ~$0.015/1K tokens (output)
   - Expected: High quality, faster than GPT-4 Turbo

### **Tier 2: Balanced Models** (Good quality, moderate cost)
5. **Claude 3.5 Haiku** (Anthropic)
   - Model ID: `anthropic.claude-3-5-haiku-20241022-v1:0`
   - Cost: ~$0.001/1K tokens (input), ~$0.005/1K tokens (output)
   - Expected: Good quality, 0.8-1.5s latency

6. **Claude 3 Sonnet** (Anthropic, previous generation)
   - Model ID: `anthropic.claude-3-sonnet-20240229-v1:0`
   - Cost: ~$0.003/1K tokens (input), ~$0.015/1K tokens (output)
   - Expected: Good quality, 1.5-2.5s latency

7. **GPT-3.5 Turbo** (OpenAI)
   - Model ID: `gpt-3.5-turbo`
   - Cost: ~$0.0005/1K tokens (input), ~$0.0015/1K tokens (output)
   - Expected: Moderate quality, 0.5-1s latency

8. **Gemini 1.5 Pro** (Google via Vertex AI)
   - Model ID: `gemini-1.5-pro`
   - Cost: ~$0.007/1K tokens (input), ~$0.021/1K tokens (output)
   - Expected: Good quality, 2-3s latency

### **Tier 3: Fast & Cheap Models** (Lower quality, lowest cost)
9. **Llama 3.1 70B** (Meta via Bedrock)
   - Model ID: `meta.llama3-1-70b-instruct-v1:0`
   - Cost: ~$0.0010/1K tokens (input), ~$0.0013/1K tokens (output)
   - Expected: Moderate quality, 1-2s latency

10. **Mistral Large** (Mistral AI via Bedrock)
    - Model ID: `mistral.mistral-large-2402-v1:0`
    - Cost: ~$0.004/1K tokens (input), ~$0.012/1K tokens (output)
    - Expected: Moderate quality, 1.5-2.5s latency

---

## Benchmark Test Design

### **Test Scenarios**: 120 (same for all models)

```python
# 10 Student Profiles (age, grade, depth preference)
student_profiles = [
    {"age": 14, "grade": 9, "depth": "surface"},
    {"age": 15, "grade": 9, "depth": "moderate"},
    {"age": 15, "grade": 10, "depth": "moderate"},
    {"age": 16, "grade": 10, "depth": "deep"},
    {"age": 16, "grade": 11, "depth": "moderate"},
    {"age": 17, "grade": 11, "depth": "deep"},
    {"age": 17, "grade": 12, "depth": "deep"},
    {"age": 18, "grade": 12, "depth": "moderate"},
    {"age": 14, "grade": 9, "depth": "deep"},
    {"age": 18, "grade": 12, "depth": "surface"}
]

# 4 Content Segments (from Richmond/Tredegar script)
content_segments = [
    {"id": 1, "summary": "Founding of Tredegar 1837...", "concepts": [...]},
    {"id": 2, "summary": "Civil War production...", "concepts": [...]},
    {"id": 3, "summary": "Reconstruction labor...", "concepts": [...]},
    {"id": 4, "summary": "Modern preservation...", "concepts": [...]}
]

# 3 Question Positions (Q1, Q2, Q3)
question_positions = [1, 2, 3]

# Total: 10 × 4 × 3 = 120 scenarios per model
# Across 10 models: 1,200 total AI generations
```

---

## Evaluation Metrics

### **1. Quality Scores** (Primary metric)

**Automated Scoring** (LLM-as-judge with Claude 3.5 Sonnet):
- Open-ended (0-1)
- Probing depth (0-1)
- Builds on previous (0-1, for Q2/Q3)
- Age-appropriate (0-1)
- Content-relevant (0-1)
- **Overall quality**: Average of 5 criteria

**Human Validation** (Optional, for top 3 models):
- Expert educators rate 30 random questions from each top model
- Compare automated vs human scores (correlation should be > 0.8)

### **2. Performance Metrics**

- **Latency (p50, p95, p99)**: Response time in milliseconds
- **Token efficiency**: Output tokens per question (lower = more concise)
- **Consistency**: Standard deviation of quality scores (lower = more consistent)

### **3. Cost Metrics**

- **Cost per question**: Based on input/output tokens
- **Total cost for 120 scenarios**: Model cost × 120
- **Projected annual cost**: For 1,000 students × 12 questions = 12,000 generations

### **4. Failure Rate**

- **Timeout rate**: % of requests exceeding 10 seconds
- **Error rate**: % of requests failing (API errors, malformed responses)
- **Fallback trigger rate**: % requiring fallback to static questions

---

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│          CloudWatch Events (Scheduler)                   │
│          Trigger: On-demand via API call                 │
└───────────────────────┬─────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│        Step Functions (Model Comparison Runner)          │
│  For each model (10 total):                              │
│    - Load 120 test scenarios                             │
│    - Execute AI generation                               │
│    - Score with LLM-as-judge                             │
│    - Store results                                       │
└───────────────────────┬─────────────────────────────────┘
                        ↓
        ┌───────────────┼───────────────────┐
        ↓               ↓                   ↓
┌──────────────┐ ┌─────────────┐ ┌──────────────────┐
│   Lambda     │ │  Bedrock/   │ │    DynamoDB      │
│ (Execution)  │ │  OpenAI     │ │ (model_results)  │
└──────────────┘ └─────────────┘ └──────────────────┘
                                          ↓
                                  ┌─────────────────┐
                                  │  Lambda         │
                                  │ (Aggregation)   │
                                  └─────────────────┘
                                          ↓
                                  ┌─────────────────┐
                                  │   Amplify       │
                                  │  (Dashboard)    │
                                  └─────────────────┘
```

---

## Implementation Plan

### **Phase 1: Multi-Model Executor** (Week 1)

**Lambda Function**: Execute AI generation for any model

```python
async def execute_model_generation(model_id: str, scenario: dict):
    """
    Unified function to call any of the 10 models
    """

    # Build prompt (same for all models)
    prompt = build_socratic_prompt(
        student_profile=scenario["student_profile"],
        content_segment=scenario["content_segment"],
        question_number=scenario["question_number"],
        previous_qa=scenario["previous_qa"]
    )

    # Route to appropriate API
    if model_id.startswith("anthropic."):
        result = await call_bedrock_anthropic(model_id, prompt)
    elif model_id.startswith("gpt-"):
        result = await call_openai(model_id, prompt)
    elif model_id.startswith("gemini"):
        result = await call_vertex_ai(model_id, prompt)
    elif model_id.startswith("meta.llama"):
        result = await call_bedrock_meta(model_id, prompt)
    elif model_id.startswith("mistral."):
        result = await call_bedrock_mistral(model_id, prompt)
    else:
        raise ValueError(f"Unknown model: {model_id}")

    return {
        "model_id": model_id,
        "scenario_id": scenario["scenario_id"],
        "generated_question": result["text"],
        "latency_ms": result["latency_ms"],
        "input_tokens": result["input_tokens"],
        "output_tokens": result["output_tokens"],
        "cost": calculate_cost(model_id, result["input_tokens"], result["output_tokens"]),
        "timestamp": datetime.now().isoformat()
    }
```

**Deliverable**: Lambda with support for all 10 models

---

### **Phase 2: Unified Scoring System** (Week 1-2)

**Lambda Function**: Score any model's output with same criteria

```python
async def score_question(result: dict, scenario: dict):
    """
    Use Claude 3.5 Sonnet as judge for ALL models
    (ensures fair comparison)
    """

    judge_prompt = f"""
You are evaluating a Socratic question generated by an AI tutor.

STUDENT: Age {scenario['student_profile']['age']}, Grade {scenario['student_profile']['grade']}
CONTENT: {scenario['content_segment']['summary']}
QUESTION NUMBER: {scenario['question_number']}
{f"PREVIOUS Q&A: {scenario['previous_qa']}" if scenario['previous_qa'] else ""}

GENERATED QUESTION (by {result['model_id']}):
{result['generated_question']}

Rate on 5 criteria (0.0-1.0 each):
1. open_ended: Not yes/no, encourages elaboration?
2. probing: Deepens understanding vs surface recall?
3. builds_on_previous: References prior answers appropriately? (N/A for Q1, score 1.0)
4. age_appropriate: Language suitable for {scenario['student_profile']['age']}-year-old?
5. content_relevant: Connects to key concepts?

Return ONLY JSON:
{{"open_ended": X.X, "probing": X.X, "builds_on_previous": X.X, "age_appropriate": X.X, "content_relevant": X.X}}
"""

    # Use Claude 3.5 Sonnet as judge
    response = await bedrock_client.invoke_model(
        modelId="anthropic.claude-3-5-sonnet-20241022-v2:0",
        body={
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 100,
            "messages": [{"role": "user", "content": judge_prompt}]
        }
    )

    scores = json.loads(response["content"][0]["text"])
    scores["overall"] = sum(scores.values()) / 5

    return {
        **result,
        "quality_scores": scores,
        "judge_model": "claude-3-5-sonnet-v2",
        "scored_at": datetime.now().isoformat()
    }
```

**Deliverable**: Consistent scoring across all models

---

### **Phase 3: DynamoDB Schema** (Week 2)

**Table: `model_comparison_results`**

```yaml
PrimaryKey:
  PK: "RUN#<run_id>#MODEL#<model_id>"
  SK: "SCENARIO#<scenario_id>"

Attributes:
  run_id: "2025-10-25T14:30:00"
  model_id: "anthropic.claude-3-5-sonnet-20241022-v2:0"
  model_name: "Claude 3.5 Sonnet v2"
  scenario_id: "uuid"
  student_profile: {...}
  content_segment: {...}
  question_number: 1
  generated_question: "What aspects of..."
  quality_scores: {
    open_ended: 0.9,
    probing: 0.85,
    builds_on_previous: 1.0,
    age_appropriate: 1.0,
    content_relevant: 0.9,
    overall: 0.93
  }
  latency_ms: 1847
  input_tokens: 523
  output_tokens: 87
  cost: 0.0089
  timestamp: "2025-10-25T14:32:15"
  error: null  # or error message if failed

GSI_1: ByModelAndQuality
  PK: "RUN#<run_id>#MODEL#<model_id>"
  SK: "QUALITY#<overall_score>"
  Purpose: Rank all models by quality

GSI_2: ByModelAndCost
  PK: "RUN#<run_id>#MODEL#<model_id>"
  SK: "COST#<cost>"
  Purpose: Rank models by cost efficiency

GSI_3: ByModelAndLatency
  PK: "RUN#<run_id>#MODEL#<model_id>"
  SK: "LATENCY#<latency_ms>"
  Purpose: Rank models by speed
```

**Table: `model_summary`**

```yaml
PrimaryKey:
  PK: "RUN#<run_id>"
  SK: "MODEL#<model_id>"

Attributes:
  run_id: "2025-10-25T14:30:00"
  model_id: "anthropic.claude-3-5-sonnet-20241022-v2:0"
  model_name: "Claude 3.5 Sonnet v2"

  # Aggregated metrics (across 120 scenarios)
  avg_quality: 0.87
  std_quality: 0.09
  median_quality: 0.89

  avg_latency_ms: 1847
  p95_latency_ms: 2934
  p99_latency_ms: 4102

  avg_cost_per_question: 0.0089
  total_cost_120_scenarios: 1.07
  projected_annual_cost_12k_questions: 106.80

  success_rate: 0.992  # 119/120 succeeded
  timeout_rate: 0.008  # 1/120 timed out
  error_rate: 0.0

  # Criteria breakdown
  avg_open_ended: 0.94
  avg_probing: 0.82
  avg_builds_on_previous: 0.88
  avg_age_appropriate: 0.96
  avg_content_relevant: 0.91

  # Ranking
  rank_by_quality: 1  # 1st out of 10
  rank_by_cost: 8     # 8th out of 10 (expensive)
  rank_by_latency: 6  # 6th out of 10 (moderately fast)
  rank_overall: 2     # Weighted rank
```

**Deliverable**: DynamoDB tables with aggregation logic

---

### **Phase 4: Step Functions Comparison Workflow** (Week 2-3)

**State Machine**: Run all 10 models in parallel

```json
{
  "Comment": "Model Comparison Benchmark",
  "StartAt": "InitializeRun",
  "States": {
    "InitializeRun": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:...:function:initializeRun",
      "ResultPath": "$.run_metadata",
      "Next": "GenerateScenarios"
    },

    "GenerateScenarios": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:...:function:generateScenarios",
      "Parameters": {"count": 120},
      "ResultPath": "$.scenarios",
      "Next": "ParallelModelExecution"
    },

    "ParallelModelExecution": {
      "Type": "Parallel",
      "Branches": [
        {
          "StartAt": "TestClaudeSonnet35v2",
          "States": {
            "TestClaudeSonnet35v2": {
              "Type": "Task",
              "Resource": "arn:aws:states:::states:startExecution.sync",
              "Parameters": {
                "StateMachineArn": "arn:aws:states:...:stateMachine:SingleModelBenchmark",
                "Input": {
                  "run_id.$": "$.run_metadata.run_id",
                  "model_id": "anthropic.claude-3-5-sonnet-20241022-v2:0",
                  "scenarios.$": "$.scenarios"
                }
              },
              "End": true
            }
          }
        },
        {
          "StartAt": "TestClaude3Opus",
          "States": {
            "TestClaude3Opus": {
              "Type": "Task",
              "Resource": "arn:aws:states:::states:startExecution.sync",
              "Parameters": {
                "StateMachineArn": "arn:aws:states:...:stateMachine:SingleModelBenchmark",
                "Input": {
                  "run_id.$": "$.run_metadata.run_id",
                  "model_id": "anthropic.claude-3-opus-20240229-v1:0",
                  "scenarios.$": "$.scenarios"
                }
              },
              "End": true
            }
          }
        },
        // ... repeat for all 10 models
      ],
      "ResultPath": "$.model_results",
      "Next": "AggregateResults"
    },

    "AggregateResults": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:...:function:aggregateResults",
      "Parameters": {
        "run_id.$": "$.run_metadata.run_id"
      },
      "ResultPath": "$.summary",
      "Next": "RankModels"
    },

    "RankModels": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:...:function:rankModels",
      "Parameters": {
        "run_id.$": "$.run_metadata.run_id"
      },
      "End": true
    }
  }
}
```

**Single Model Benchmark** (nested state machine):

```json
{
  "Comment": "Benchmark single model across 120 scenarios",
  "StartAt": "MapScenarios",
  "States": {
    "MapScenarios": {
      "Type": "Map",
      "ItemsPath": "$.scenarios",
      "MaxConcurrency": 20,
      "Iterator": {
        "StartAt": "GenerateQuestion",
        "States": {
          "GenerateQuestion": {
            "Type": "Task",
            "Resource": "arn:aws:lambda:...:function:executeModelGeneration",
            "Parameters": {
              "model_id.$": "$.model_id",
              "scenario.$": "$$.Map.Item.Value"
            },
            "Retry": [
              {
                "ErrorEquals": ["ThrottlingException"],
                "IntervalSeconds": 2,
                "MaxAttempts": 3,
                "BackoffRate": 2
              }
            ],
            "Catch": [
              {
                "ErrorEquals": ["States.ALL"],
                "ResultPath": "$.error",
                "Next": "RecordError"
              }
            ],
            "Next": "ScoreQuestion"
          },
          "ScoreQuestion": {
            "Type": "Task",
            "Resource": "arn:aws:lambda:...:function:scoreQuestion",
            "Next": "StoreResult"
          },
          "StoreResult": {
            "Type": "Task",
            "Resource": "arn:aws:lambda:...:function:storeResult",
            "End": true
          },
          "RecordError": {
            "Type": "Task",
            "Resource": "arn:aws:lambda:...:function:storeError",
            "End": true
          }
        }
      },
      "End": true
    }
  }
}
```

**Deliverable**: Orchestration for 10-model parallel execution

---

### **Phase 5: Comparison Dashboard** (Week 3-4)

**Dashboard Views**:

#### **1. Model Leaderboard**

```
┌─────────────────────────────────────────────────────────────────────┐
│                  Model Comparison Results                            │
│                  Run ID: 2025-10-25-14:30                            │
│                  120 scenarios per model                             │
└─────────────────────────────────────────────────────────────────────┘

Rank  Model                      Quality  Latency  Cost/Q   Total Cost
────────────────────────────────────────────────────────────────────────
 1    Claude 3 Opus              0.91     3.2s     $0.013   $1.56  ⭐️
 2    Claude 3.5 Sonnet v2       0.87     1.8s     $0.009   $1.08
 3    GPT-4 Turbo                0.84     2.4s     $0.006   $0.72
 4    GPT-4o                     0.82     1.5s     $0.004   $0.48
 5    Gemini 1.5 Pro             0.79     2.1s     $0.007   $0.84
 6    Claude 3.5 Haiku           0.77     0.9s     $0.002   $0.24  💰
 7    Mistral Large              0.75     1.7s     $0.005   $0.60
 8    Claude 3 Sonnet            0.74     2.0s     $0.004   $0.48
 9    Llama 3.1 70B              0.71     1.4s     $0.001   $0.12
10    GPT-3.5 Turbo              0.68     0.6s     $0.001   $0.12  ⚡
────────────────────────────────────────────────────────────────────────

Legend: ⭐️ Highest quality  💰 Best value  ⚡ Fastest
```

#### **2. Quality Distribution by Model**

```
Quality Score Distribution (0.0-1.0)

Claude 3 Opus:        ████████████████████ 0.91 avg, σ=0.07
Claude 3.5 Sonnet v2: ██████████████████░░ 0.87 avg, σ=0.09
GPT-4 Turbo:          █████████████████░░░ 0.84 avg, σ=0.11
GPT-4o:               ████████████████░░░░ 0.82 avg, σ=0.10
Gemini 1.5 Pro:       ███████████████░░░░░ 0.79 avg, σ=0.12
Claude 3.5 Haiku:     ██████████████░░░░░░ 0.77 avg, σ=0.13
Mistral Large:        █████████████░░░░░░░ 0.75 avg, σ=0.14
Claude 3 Sonnet:      ████████████░░░░░░░░ 0.74 avg, σ=0.15
Llama 3.1 70B:        ███████████░░░░░░░░░ 0.71 avg, σ=0.16
GPT-3.5 Turbo:        ██████████░░░░░░░░░░ 0.68 avg, σ=0.18
```

#### **3. Criteria Breakdown**

```
Average Scores by Criterion

                    Open   Probe  Builds  Age    Content  Overall
Claude 3 Opus       0.96   0.89   0.93    0.97   0.92     0.91
Claude 3.5 Sonnet   0.94   0.82   0.88    0.96   0.91     0.87
GPT-4 Turbo         0.91   0.79   0.85    0.94   0.88     0.84
GPT-4o              0.89   0.77   0.83    0.93   0.87     0.82
Gemini 1.5 Pro      0.87   0.74   0.80    0.91   0.84     0.79
Claude 3.5 Haiku    0.85   0.71   0.78    0.89   0.82     0.77
Mistral Large       0.83   0.69   0.76    0.87   0.80     0.75
Claude 3 Sonnet     0.81   0.68   0.75    0.86   0.79     0.74
Llama 3.1 70B       0.78   0.65   0.72    0.84   0.76     0.71
GPT-3.5 Turbo       0.75   0.61   0.68    0.81   0.73     0.68
```

#### **4. Cost vs Quality Tradeoff**

```
Cost-Quality Scatter Plot

Quality ↑
1.0 │                    ⭐ Claude 3 Opus ($0.013/Q)
    │                 ● Claude 3.5 Sonnet ($0.009/Q)
0.9 │              ● GPT-4 Turbo ($0.006/Q)
    │           ● GPT-4o ($0.004/Q)
0.8 │        ● Gemini 1.5 Pro ($0.007/Q)
    │     ● Claude 3.5 Haiku ($0.002/Q)  💰 BEST VALUE
0.7 │  ● Mistral Large ($0.005/Q)
    │  ● Claude 3 Sonnet ($0.004/Q)
0.6 │ ● Llama 3.1 ($0.001/Q)
    │ ● GPT-3.5 Turbo ($0.001/Q)
0.5 └─────────────────────────────────────────→ Cost/Question
    $0      $0.005      $0.010      $0.015
```

#### **5. Latency Performance**

```
Response Latency (p50, p95, p99)

Model                 p50      p95      p99
─────────────────────────────────────────────
GPT-3.5 Turbo         0.6s     1.1s     1.5s  ⚡ Fastest
Claude 3.5 Haiku      0.9s     1.5s     2.1s
Llama 3.1 70B         1.4s     2.3s     3.1s
GPT-4o                1.5s     2.4s     3.2s
Mistral Large         1.7s     2.8s     3.9s
Claude 3.5 Sonnet v2  1.8s     2.9s     4.1s
Claude 3 Sonnet       2.0s     3.2s     4.5s
Gemini 1.5 Pro        2.1s     3.4s     4.7s
GPT-4 Turbo           2.4s     3.8s     5.2s
Claude 3 Opus         3.2s     5.1s     7.2s
```

#### **6. Failure Analysis**

```
Success Rates (out of 120 scenarios)

Model                 Success  Timeout  Error
──────────────────────────────────────────────
Claude 3.5 Sonnet v2  120/120  0%       0%
GPT-4o                120/120  0%       0%
Claude 3.5 Haiku      120/120  0%       0%
GPT-4 Turbo           119/120  0.8%     0%
Gemini 1.5 Pro        119/120  0.8%     0%
Claude 3 Opus         118/120  1.7%     0%
Mistral Large         117/120  2.5%     0%
Claude 3 Sonnet       117/120  2.5%     0%
Llama 3.1 70B         115/120  4.2%     0%
GPT-3.5 Turbo         114/120  5.0%     0%
```

#### **7. Recommendation Engine**

```
┌─────────────────────────────────────────────────────────────┐
│              Model Selection Recommendation                  │
└─────────────────────────────────────────────────────────────┘

For your use case (educational research, 240 students × 12 Q = 2,880 generations):

🏆 RECOMMENDED: Claude 3.5 Sonnet v2

Rationale:
✓ High quality (0.87 overall, 2nd best)
✓ Fast enough (1.8s p50, acceptable for UX)
✓ Moderate cost ($0.009/Q × 2,880 = $25.92 total)
✓ Perfect reliability (120/120 success)
✓ Excels at "builds on previous" (0.88, critical for Q2/Q3)

Alternative Considerations:

💰 Budget-Conscious: Claude 3.5 Haiku
   - 11% lower quality (0.77 vs 0.87)
   - 78% cost savings ($0.002/Q × 2,880 = $5.76)
   - Acceptable if budget <$10

⭐ Quality-First: Claude 3 Opus
   - 5% higher quality (0.91 vs 0.87)
   - 44% more expensive ($0.013/Q × 2,880 = $37.44)
   - Consider if quality is paramount

⚡ Speed-First: GPT-4o
   - Only 6% lower quality (0.82 vs 0.87)
   - 17% faster (1.5s vs 1.8s)
   - 56% cheaper ($0.004/Q × 2,880 = $11.52)
   - Good middle ground option
```

**Deliverable**: Interactive Amplify dashboard with Recharts

---

## Cost Estimate

### **Per Full Comparison Run** (10 models × 120 scenarios):

| Component | Usage | Cost |
|-----------|-------|------|
| **AI Generation** | 1,200 calls (10 models × 120) | $7.20 |
| **AI Scoring** | 1,200 calls (same judge for all) | $6.00 |
| **Lambda** | 2,400 invocations × 512MB × 3s | $0.05 |
| **Step Functions** | 10 parallel executions × 120 steps | $0.06 |
| **DynamoDB** | 1,200 writes + 10K reads | $0.08 |
| **Total per run** | | **$13.39** |

**Note**: Much cheaper than running 10 separate benchmarks sequentially due to parallel execution and shared scenarios.

---

## Timeline

| Week | Phase | Deliverables |
|------|-------|--------------|
| 1 | Multi-Model Executor | Support all 10 models in one Lambda |
| 1-2 | Unified Scoring | LLM-as-judge scoring system |
| 2 | DynamoDB Schema | Results + summary tables |
| 2-3 | Step Functions | Parallel 10-model workflow |
| 3-4 | Comparison Dashboard | Leaderboard, charts, recommendations |
| 4 | Testing & Production | Validate results, deploy |

**Total: 4 weeks to model selection**

---

## Deployment & Execution

### **One-Time Setup** (1 hour):

```bash
# Deploy infrastructure
cd infrastructure
cdk deploy ModelComparisonStack

# Output:
# - DynamoDB tables
# - Lambda functions
# - Step Functions state machines
# - Amplify dashboard URL
```

### **Run Comparison** (15-20 minutes execution time):

```bash
# Start comparison benchmark
aws stepfunctions start-execution \
  --state-machine-arn arn:aws:states:us-east-1:ACCOUNT:stateMachine:ModelComparison \
  --input '{
    "run_id": "2025-10-25T14:30:00",
    "scenario_count": 120,
    "models": [
      "anthropic.claude-3-5-sonnet-20241022-v2:0",
      "anthropic.claude-3-opus-20240229-v1:0",
      "gpt-4-turbo-preview",
      "gpt-4o",
      "anthropic.claude-3-5-haiku-20241022-v1:0",
      "anthropic.claude-3-sonnet-20240229-v1:0",
      "gpt-3.5-turbo",
      "gemini-1.5-pro",
      "meta.llama3-1-70b-instruct-v1:0",
      "mistral.mistral-large-2402-v1:0"
    ]
  }'

# Monitor progress
aws stepfunctions describe-execution \
  --execution-arn <execution-arn>

# View results
open https://main.dxxxxx.amplifyapp.com
```

### **Expected Execution Time**:

- 10 models run in **parallel**
- Each model: 120 scenarios @ ~2s avg = 240 seconds
- With MaxConcurrency=20: 240s / 20 = **12 minutes**
- Scoring (sequential): 1,200 calls @ 1s avg / 20 = **60 seconds**
- Aggregation: **30 seconds**
- **Total: ~15 minutes**

---

## Decision Framework

### **After benchmark completes, you'll have**:

1. **Quality rankings** (which model generates best Socratic questions?)
2. **Cost projections** (what's the total cost for 2,880 research questions?)
3. **Latency data** (will students wait too long?)
4. **Reliability stats** (which models fail most often?)

### **Selection Criteria** (customize weights):

```python
def calculate_overall_score(model_results, weights):
    """
    Weighted scoring for model selection
    """
    return (
        weights["quality"] * model_results["avg_quality"] +
        weights["cost"] * (1 - normalize(model_results["cost_per_question"])) +
        weights["latency"] * (1 - normalize(model_results["p95_latency_ms"])) +
        weights["reliability"] * model_results["success_rate"]
    )

# Example: Quality-focused research
weights = {
    "quality": 0.6,     # 60% weight on quality
    "cost": 0.1,        # 10% weight on cost (secondary)
    "latency": 0.2,     # 20% weight on latency (UX matters)
    "reliability": 0.1  # 10% weight on reliability
}

# Example: Budget-constrained research
weights = {
    "quality": 0.4,     # 40% weight on quality
    "cost": 0.4,        # 40% weight on cost (critical)
    "latency": 0.1,     # 10% weight on latency
    "reliability": 0.1  # 10% weight on reliability
}
```

### **Recommended Decision Tree**:

```
1. Is quality ≥0.80 required?
   ├─ YES → Filter to top 5 models (≥0.80 quality)
   └─ NO  → Consider all 10 models

2. Is budget <$20 for 2,880 questions?
   ├─ YES → Filter to models with cost/Q <$0.007
   └─ NO  → No cost filter

3. Is latency <2s p95 required?
   ├─ YES → Filter to models with p95 <2000ms
   └─ NO  → No latency filter

4. Must have 100% reliability?
   ├─ YES → Filter to models with 120/120 success
   └─ NO  → Accept ≥98% success rate

5. Select highest-ranked remaining model
```

---

## Next Steps

### **This Week**:

1. **Review this plan** - Does it match your model selection goals?
2. **Confirm model list** - Are these the 10 models you want to test?
3. **Set up API access**:
   - AWS Bedrock access (Claude, Llama, Mistral)
   - OpenAI API key (GPT models)
   - Google Cloud access (Gemini)
4. **Define selection criteria** - What weights for quality/cost/latency?

### **Week 1**:

5. Deploy infrastructure (CDK)
6. Build multi-model executor Lambda
7. Create 120 test scenarios
8. Test with 2-3 models first

### **Week 2-3**:

9. Add all 10 models
10. Build scoring system
11. Implement Step Functions workflow
12. Run first full comparison

### **Week 4**:

13. Build dashboard
14. Validate results
15. Make model selection decision
16. Document choice for research paper

---

## Success Criteria

- [ ] All 10 models successfully tested (≥98% success rate each)
- [ ] Quality scores validated by human experts (correlation ≥0.80)
- [ ] Cost projections accurate (within 10% of actual)
- [ ] Dashboard provides clear recommendation
- [ ] Decision documented with rationale

---

**This platform answers your critical question: "Which AI model should we use for the full research study?" in 4 weeks for ~$15.**

**Once you select the winning model, then proceed to build the full research platform using ONLY that model.**

Ready to start with Week 1? 🚀
