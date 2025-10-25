# Automated Socratic AI Benchmark Testing Platform

## Purpose

Automated system to test and benchmark Socratic AI question generation quality **WITHOUT** human students. Runs in AWS sandbox/playground environment with synthetic test scenarios.

---

## What This Platform Does

### **Core Function**: Automated Quality Testing

1. **Generate test scenarios** (student profiles + content segments)
2. **Execute Socratic AI generation** (via Bedrock/Claude)
3. **Score question quality** (automated metrics)
4. **Store results** (DynamoDB)
5. **Visualize benchmarks** (Amplify dashboard)

### **NOT Included** (Save for Full Research Platform Later)
- ❌ Real students
- ❌ Location verification (GPS, QR codes)
- ❌ Content delivery system (audio/video player)
- ❌ Comprehension assessments
- ❌ IRB compliance
- ❌ 24 experimental conditions

---

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│              CloudWatch Events (Scheduler)               │
│          Trigger: Every hour / Daily / On-demand         │
└───────────────────────┬─────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│           Step Functions (Test Orchestrator)             │
│   - Load test scenarios                                  │
│   - Execute AI generation                                │
│   - Score results                                        │
│   - Store to DynamoDB                                    │
└───────────────────────┬─────────────────────────────────┘
                        ↓
        ┌───────────────┼───────────────┐
        ↓               ↓               ↓
┌──────────────┐ ┌─────────────┐ ┌─────────────┐
│   Lambda     │ │   Bedrock   │ │  DynamoDB   │
│ (Scoring)    │ │  (Claude)   │ │  (Results)  │
└──────────────┘ └─────────────┘ └─────────────┘
                                        ↓
                                ┌─────────────┐
                                │   Amplify   │
                                │ (Dashboard) │
                                └─────────────┘
```

---

## Implementation Plan

### **Phase 1: Test Scenario Generator** (Week 1)

#### **What to Build**:
Lambda function that generates synthetic test cases

**Test Scenarios**:
```python
{
    "scenario_id": "uuid",
    "student_profile": {
        "age": 15,
        "grade": 10,
        "depth_preference": "moderate"
    },
    "content_segment": {
        "segment_id": 1,
        "summary": "Introduction to Tredegar Iron Works...",
        "key_concepts": ["industrial revolution", "Richmond's role"],
        "difficulty": "introductory"
    },
    "question_context": {
        "question_number": 1,  # Q1, Q2, or Q3
        "previous_qa": []  # For Q2/Q3, includes prior exchanges
    }
}
```

**Deliverable**: Lambda function `generateTestScenarios(count: int) → List[Scenario]`

**Test Data**:
- 10 student profiles (varied ages, preferences)
- 4 content segments (from Tredegar script)
- 3 question positions (Q1, Q2, Q3)
- Total: 10 × 4 × 3 = 120 test scenarios

---

### **Phase 2: AI Generation Executor** (Week 2)

#### **What to Build**:
Lambda function that calls Bedrock/Claude for each scenario

**Process**:
```python
async def execute_ai_generation(scenario):
    """
    For each scenario, generate Socratic question via Claude
    """
    prompt = build_socratic_prompt(
        student_profile=scenario["student_profile"],
        content_segment=scenario["content_segment"],
        question_number=scenario["question_context"]["question_number"],
        previous_qa=scenario["question_context"]["previous_qa"]
    )

    response = await bedrock_client.invoke_model(
        modelId="anthropic.claude-3-5-sonnet-20241022-v2:0",
        body={
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 200,
            "messages": [{
                "role": "user",
                "content": prompt
            }]
        }
    )

    return {
        "scenario_id": scenario["scenario_id"],
        "generated_question": response["content"][0]["text"],
        "generation_time_ms": response["metrics"]["latency_ms"],
        "input_tokens": response["usage"]["input_tokens"],
        "output_tokens": response["usage"]["output_tokens"],
        "model_version": "claude-3-5-sonnet-20241022-v2:0",
        "timestamp": datetime.now().isoformat()
    }
```

**Deliverable**: Lambda function `executeAIGeneration(scenarios) → List[Result]`

---

### **Phase 3: Automated Quality Scoring** (Week 2-3)

#### **What to Build**:
Lambda function that scores question quality using LLM-as-judge

**Quality Criteria** (from TEST_AUTOMATION_STRATEGY.md):
1. **Open-ended** (0-1): Is it a yes/no question? (0 = yes/no, 1 = open)
2. **Probing** (0-1): Does it deepen understanding?
3. **Builds on previous** (0-1): References prior answers? (Q2/Q3 only)
4. **Age-appropriate** (0-1): Language suitable for student age?
5. **Content-relevant** (0-1): Connects to key concepts?

**Scoring Approach**: LLM-as-judge (use Claude to score questions)

```python
async def score_question_quality(result, scenario):
    """
    Use Claude to score the generated question
    """
    judge_prompt = f"""
You are evaluating a Socratic question for educational quality.

STUDENT: Age {scenario['student_profile']['age']}, Grade {scenario['student_profile']['grade']}

CONTENT: {scenario['content_segment']['summary']}
Key concepts: {scenario['content_segment']['key_concepts']}

QUESTION NUMBER: {scenario['question_context']['question_number']}
{f"PREVIOUS Q&A: {scenario['question_context']['previous_qa']}" if scenario['question_context']['previous_qa'] else ""}

GENERATED QUESTION: {result['generated_question']}

Evaluate on 5 criteria (score 0.0-1.0 each):
1. open_ended: Is it open-ended (not yes/no)?
2. probing: Does it probe deeper understanding?
3. builds_on_previous: Does it reference prior answers? (N/A for Q1, score as 1.0 if appropriate)
4. age_appropriate: Is language suitable for this age?
5. content_relevant: Does it connect to key concepts?

Return ONLY a JSON object:
{{"open_ended": 0.9, "probing": 0.8, "builds_on_previous": 1.0, "age_appropriate": 1.0, "content_relevant": 0.9}}
"""

    response = await bedrock_client.invoke_model(
        modelId="anthropic.claude-3-5-sonnet-20241022-v2:0",
        body={
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 100,
            "messages": [{"role": "user", "content": judge_prompt}]
        }
    )

    scores = json.loads(response["content"][0]["text"])
    scores["overall"] = sum(scores.values()) / len(scores)

    return scores
```

**Deliverable**: Lambda function `scoreQuality(results, scenarios) → List[ScoredResult]`

---

### **Phase 4: DynamoDB Storage** (Week 3)

#### **Schema Design**:

**Table: `benchmark-test-runs`**

```yaml
PrimaryKey:
  PK: "RUN#<run_id>"          # e.g., "RUN#2025-10-25T14:30:00"
  SK: "SCENARIO#<scenario_id>" # e.g., "SCENARIO#uuid"

Attributes:
  run_id: "2025-10-25T14:30:00"
  scenario_id: "uuid"
  student_profile: {age, grade, depth_preference}
  content_segment: {segment_id, summary, key_concepts}
  question_number: 1  # or 2 or 3
  generated_question: "What aspects of..."
  quality_scores: {
    open_ended: 0.9,
    probing: 0.8,
    builds_on_previous: 1.0,
    age_appropriate: 1.0,
    content_relevant: 0.9,
    overall: 0.92
  }
  generation_time_ms: 1847
  input_tokens: 523
  output_tokens: 87
  model_version: "claude-3-5-sonnet-20241022-v2:0"
  timestamp: "2025-10-25T14:32:15"

GSI_1: ByOverallQuality
  PK: "RUN#<run_id>"
  SK: "QUALITY#<overall_score>"  # e.g., "QUALITY#0.92"
  Purpose: Retrieve all results sorted by quality

GSI_2: ByModel
  PK: "MODEL#<model_version>"
  SK: "TIME#<timestamp>"
  Purpose: Compare different model versions
```

**Deliverable**: CDK stack with DynamoDB table + GSIs

---

### **Phase 5: Step Functions Orchestration** (Week 3-4)

#### **Workflow Design**:

```json
{
  "Comment": "Automated Socratic AI Benchmark Test",
  "StartAt": "GenerateScenarios",
  "States": {
    "GenerateScenarios": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:REGION:ACCOUNT:function:generateTestScenarios",
      "Parameters": {
        "count": 120
      },
      "ResultPath": "$.scenarios",
      "Next": "ExecuteAIGeneration"
    },
    "ExecuteAIGeneration": {
      "Type": "Map",
      "ItemsPath": "$.scenarios",
      "MaxConcurrency": 10,
      "Iterator": {
        "StartAt": "GenerateQuestion",
        "States": {
          "GenerateQuestion": {
            "Type": "Task",
            "Resource": "arn:aws:lambda:REGION:ACCOUNT:function:executeAIGeneration",
            "Retry": [
              {
                "ErrorEquals": ["States.TaskFailed"],
                "IntervalSeconds": 2,
                "MaxAttempts": 3,
                "BackoffRate": 2
              }
            ],
            "End": true
          }
        }
      },
      "ResultPath": "$.results",
      "Next": "ScoreQuality"
    },
    "ScoreQuality": {
      "Type": "Map",
      "ItemsPath": "$.results",
      "MaxConcurrency": 10,
      "Iterator": {
        "StartAt": "ScoreQuestion",
        "States": {
          "ScoreQuestion": {
            "Type": "Task",
            "Resource": "arn:aws:lambda:REGION:ACCOUNT:function:scoreQuality",
            "End": true
          }
        }
      },
      "ResultPath": "$.scored_results",
      "Next": "StoreToDynamoDB"
    },
    "StoreToDynamoDB": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:REGION:ACCOUNT:function:storeResults",
      "Parameters": {
        "run_id.$": "$.run_id",
        "scored_results.$": "$.scored_results"
      },
      "ResultPath": "$.storage_result",
      "Next": "PublishMetrics"
    },
    "PublishMetrics": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:REGION:ACCOUNT:function:publishMetrics",
      "Parameters": {
        "run_id.$": "$.run_id",
        "scored_results.$": "$.scored_results"
      },
      "End": true
    }
  }
}
```

**Deliverable**: Step Functions state machine + Lambda functions

---

### **Phase 6: Amplify Dashboard** (Week 4-5)

#### **Dashboard Views**:

**1. Run Overview**
```
┌────────────────────────────────────────┐
│  Latest Test Run: 2025-10-25 14:30    │
│  Total Scenarios: 120                  │
│  Average Quality: 0.87 / 1.0           │
│  Total Cost: $1.47                     │
└────────────────────────────────────────┘
```

**2. Quality Distribution**
```
Overall Quality Scores (120 scenarios)

█████████████░░░░░  0.9-1.0  (42 scenarios, 35%)
██████████████████  0.8-0.9  (68 scenarios, 57%)
███░░░░░░░░░░░░░░░  0.7-0.8  (8 scenarios, 6%)
█░░░░░░░░░░░░░░░░░  0.6-0.7  (2 scenarios, 2%)
```

**3. Criteria Breakdown**
```
Average Scores by Criterion:

Open-ended:        0.94  ████████████████████
Probing:           0.82  ████████████████░░░░
Builds on prev:    0.88  ██████████████████░░
Age-appropriate:   0.96  ████████████████████
Content-relevant:  0.91  ███████████████████░
```

**4. Model Comparison**
```
Model Performance Over Time

Claude 3.5 Sonnet (v2):  0.87 avg quality, 1.8s avg latency
Claude 3.5 Haiku:        0.79 avg quality, 0.9s avg latency
Claude 3 Opus:           0.91 avg quality, 3.2s avg latency
```

**5. Cost Tracking**
```
Costs per 120-scenario run:

AI Generation:  $0.87  (120 calls × $0.007 avg)
AI Scoring:     $0.60  (120 calls × $0.005 avg)
Lambda:         $0.02
DynamoDB:       $0.01
Total:          $1.50 per run
```

**6. Drill-Down View**
```
Scenario Detail: scenario-abc-123

Student: Age 15, Grade 10, Moderate depth
Content: Segment 2 - Civil War era production
Question #: 2 (building on Q1)

Generated Question:
"You mentioned that Tredegar produced weapons for the Confederacy.
How might this industrial capacity have influenced the duration
or outcome of the war?"

Quality Scores:
├─ Open-ended:        1.0  ✓
├─ Probing:           0.9  ✓
├─ Builds on prev:    1.0  ✓ (references student's Q1 answer)
├─ Age-appropriate:   1.0  ✓
├─ Content-relevant:  0.9  ✓
└─ Overall:           0.96 ✓

Metrics:
├─ Generation time: 1.8s
├─ Input tokens:    487
├─ Output tokens:   43
└─ Cost:           $0.008
```

**Deliverable**: React dashboard with Recharts visualizations

---

## Testing Strategy

### **Unit Tests** (Week 1-5, ongoing)

```python
# Test scenario generation
def test_generate_scenarios():
    scenarios = generate_test_scenarios(count=10)
    assert len(scenarios) == 10
    assert all(s["student_profile"]["age"] in range(14, 19) for s in scenarios)

# Test AI generation
def test_execute_ai_generation():
    scenario = {...}
    result = execute_ai_generation(scenario)
    assert result["generated_question"] is not None
    assert result["generation_time_ms"] > 0

# Test quality scoring
def test_score_quality():
    result = {"generated_question": "Why do you think..."}
    scenario = {...}
    scores = score_question_quality(result, scenario)
    assert all(0 <= v <= 1 for v in scores.values())
    assert "overall" in scores
```

### **Integration Tests** (Week 4)

```python
# Test full Step Functions workflow
def test_full_benchmark_run():
    step_functions_client.start_execution(
        stateMachineArn="arn:aws:states:...",
        input=json.dumps({"run_id": "test-run-1", "scenario_count": 10})
    )

    # Wait for completion (max 5 min)
    result = wait_for_execution_complete(execution_arn, timeout=300)

    # Validate results in DynamoDB
    items = dynamodb.query(
        KeyConditionExpression="PK = :pk",
        ExpressionAttributeValues={":pk": "RUN#test-run-1"}
    )

    assert len(items) == 10
    assert all("quality_scores" in item for item in items)
```

### **Load Tests** (Week 5)

```python
# Test 1000 scenarios concurrently
def test_scale_to_1000_scenarios():
    start_time = time.time()

    step_functions_client.start_execution(
        stateMachineArn="arn:aws:states:...",
        input=json.dumps({"run_id": "load-test-1", "scenario_count": 1000})
    )

    result = wait_for_execution_complete(execution_arn, timeout=1800)  # 30 min

    elapsed = time.time() - start_time

    # Should complete in < 15 minutes with MaxConcurrency=50
    assert elapsed < 900
    assert result["status"] == "SUCCEEDED"
```

---

## Deployment Guide

### **Prerequisites**:
- AWS account
- AWS CLI configured
- Node.js 20+ (for CDK)
- Python 3.12+ (for Lambda functions)

### **Step 1: Deploy Infrastructure** (30 minutes)

```bash
# Clone repo
cd /Users/williamprior/Development/GitHub/socratic-ai-benchmarks

# Install CDK
npm install -g aws-cdk

# Bootstrap CDK (first time only)
cdk bootstrap aws://ACCOUNT-ID/us-east-1

# Deploy stack
cd infrastructure
cdk deploy BenchmarkPlatformStack
```

### **Step 2: Deploy Lambda Functions** (15 minutes)

```bash
# Package Lambda functions
cd lambda
./build.sh  # Creates deployment packages

# Deploy via CDK
cdk deploy LambdaStack
```

### **Step 3: Deploy Step Functions** (10 minutes)

```bash
# Deploy state machine
cdk deploy StepFunctionsStack
```

### **Step 4: Deploy Dashboard** (20 minutes)

```bash
# Deploy Amplify app
cd dashboard
amplify init
amplify push

# Deploy frontend
npm run build
amplify publish
```

### **Step 5: Run First Benchmark** (5 minutes)

```bash
# Trigger Step Functions execution
aws stepfunctions start-execution \
  --state-machine-arn arn:aws:states:us-east-1:ACCOUNT:stateMachine:BenchmarkRunner \
  --input '{"run_id": "2025-10-25T14:30:00", "scenario_count": 120}'

# Monitor execution
aws stepfunctions describe-execution \
  --execution-arn arn:aws:states:...

# View results in dashboard
open https://main.dxxxxx.amplifyapp.com
```

---

## Cost Estimate

### **Per 120-Scenario Benchmark Run**:

| Component | Usage | Cost |
|-----------|-------|------|
| **Bedrock (Generation)** | 120 calls × 500 tokens avg × $0.015/1K | $0.90 |
| **Bedrock (Scoring)** | 120 calls × 400 tokens avg × $0.015/1K | $0.72 |
| **Lambda** | 240 invocations × 512MB × 3s avg | $0.02 |
| **Step Functions** | 1 execution × 500 state transitions | $0.01 |
| **DynamoDB** | 120 writes + 1K reads | $0.01 |
| **Total per run** | | **$1.66** |

### **Monthly Costs** (Daily runs):

| Item | Cost |
|------|------|
| 30 benchmark runs × $1.66 | $49.80 |
| Amplify hosting | $15.00 |
| CloudWatch logs/metrics | $5.00 |
| DynamoDB storage (10GB) | $2.50 |
| **Total monthly** | **$72.30** |

**Much cheaper than full research platform** (~$85-111/month with students)

---

## Timeline

| Week | Phase | Deliverables |
|------|-------|--------------|
| 1 | Scenario Generator | Lambda function + test data |
| 2 | AI Generation | Bedrock integration + execution |
| 2-3 | Quality Scoring | LLM-as-judge scoring system |
| 3 | DynamoDB | Schema + storage functions |
| 3-4 | Step Functions | Orchestration workflow |
| 4-5 | Dashboard | Amplify app + visualizations |
| 5 | Testing & Launch | Load tests, production deploy |

**Total: 5 weeks to production-ready benchmark platform**

---

## Success Criteria

### **Technical**:
- [ ] Can execute 120 scenarios in < 10 minutes
- [ ] Quality scoring accuracy ≥ 90% (validated against human raters)
- [ ] Cost per run < $2.00
- [ ] Dashboard loads in < 3 seconds
- [ ] Zero data loss

### **Research**:
- [ ] Identifies low-quality questions (overall < 0.7)
- [ ] Tracks quality trends over time
- [ ] Compares different model versions
- [ ] Provides actionable insights for prompt engineering

---

## Next Steps

### **Immediate (This Week)**:

1. **Review this plan** - Does it match your "automated platform" vision?
2. **Confirm scope** - Is this the right subset of functionality?
3. **Set up AWS account** - If not already done
4. **Create test scenarios** - Define 120 test cases

### **Week 1 Tasks**:

5. Deploy CDK infrastructure
6. Build scenario generator Lambda
7. Create test data (student profiles + content segments)
8. Unit test scenario generation

---

## Differences from Full Research Platform

| Feature | Automated Benchmark | Full Research |
|---------|---------------------|---------------|
| **Users** | None (synthetic scenarios) | 120-240 real students |
| **Content** | Text summaries only | 10-min audio + transcript |
| **Location** | N/A | GPS verification, 4 locations |
| **Assessments** | N/A | Baseline + final tests |
| **IRB** | Not needed | Required for minors |
| **Cost** | $72/month | $85-111/month |
| **Timeline** | 5 weeks | 16-20 weeks |
| **Purpose** | Test AI quality | Research outcomes |

---

**This automated platform lets you iterate on prompt engineering and model selection BEFORE investing in the full research infrastructure.**

**Once you're confident in AI quality (≥0.90 overall scores), then deploy the full platform with real students.**

---

*Created: 2025-10-25*
*Version: 1.0*
*Status: Ready for Week 1 implementation*
