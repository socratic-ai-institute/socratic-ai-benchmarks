# Bedrock-Only AI Model Comparison Platform

## Purpose

**Compare AI models available on AWS Bedrock** to select the best one for Socratic question generation. All models accessed through single Bedrock API - no multi-cloud complexity.

---

## Models Available on AWS Bedrock

### **Anthropic Claude Models** (✅ Available)
1. **Claude 3.5 Sonnet v2**
   - Model ID: `anthropic.claude-3-5-sonnet-20241022-v2:0`
   - Cost: $0.003/1K input, $0.015/1K output
   - Best for: Highest quality, context understanding

2. **Claude 3.5 Haiku**
   - Model ID: `anthropic.claude-3-5-haiku-20241022-v1:0`
   - Cost: $0.001/1K input, $0.005/1K output
   - Best for: Speed + cost efficiency

3. **Claude 3 Opus**
   - Model ID: `anthropic.claude-3-opus-20240229-v1:0`
   - Cost: $0.015/1K input, $0.075/1K output
   - Best for: Maximum quality (most expensive)

4. **Claude 3 Sonnet**
   - Model ID: `anthropic.claude-3-sonnet-20240229-v1:0`
   - Cost: $0.003/1K input, $0.015/1K output
   - Best for: Balanced (previous generation)

5. **Claude 3 Haiku**
   - Model ID: `anthropic.claude-3-haiku-20240307-v1:0`
   - Cost: $0.00025/1K input, $0.00125/1K output
   - Best for: Ultra-fast, budget

### **Meta Llama Models** (✅ Available)
6. **Llama 3.1 405B Instruct**
   - Model ID: `meta.llama3-1-405b-instruct-v1:0`
   - Cost: $0.00532/1K input, $0.016/1K output
   - Best for: Open-source, largest

7. **Llama 3.1 70B Instruct**
   - Model ID: `meta.llama3-1-70b-instruct-v1:0`
   - Cost: $0.00099/1K input, $0.00099/1K output
   - Best for: Open-source, balanced

8. **Llama 3.1 8B Instruct**
   - Model ID: `meta.llama3-1-8b-instruct-v1:0`
   - Cost: $0.00022/1K input, $0.00022/1K output
   - Best for: Ultra-cheap, fast

### **Mistral AI Models** (✅ Available)
9. **Mistral Large**
   - Model ID: `mistral.mistral-large-2402-v1:0`
   - Cost: $0.004/1K input, $0.012/1K output
   - Best for: European alternative, good quality

10. **Mixtral 8x7B**
    - Model ID: `mistral.mixtral-8x7b-instruct-v0:1`
    - Cost: $0.00045/1K input, $0.0007/1K output
    - Best for: MoE architecture, efficient

### **Amazon Models** (✅ Available)
11. **Amazon Titan Text Premier** (Optional)
    - Model ID: `amazon.titan-text-premier-v1:0`
    - Cost: $0.0005/1K input, $0.0015/1K output
    - Best for: AWS-native option

---

## Recommended Test Set: 8 Models

**Skip OpenAI and Google** (not on Bedrock), focus on these 8:

| Tier | Model | Model ID | Cost/Q* | Why Test |
|------|-------|----------|---------|----------|
| **Premium** | Claude 3.5 Sonnet v2 | `anthropic.claude-3-5-sonnet-20241022-v2:0` | $0.009 | Current best Claude |
| **Premium** | Claude 3 Opus | `anthropic.claude-3-opus-20240229-v1:0` | $0.045 | Highest quality option |
| **Balanced** | Claude 3.5 Haiku | `anthropic.claude-3-5-haiku-20241022-v1:0` | $0.003 | Fast + affordable Claude |
| **Balanced** | Mistral Large | `mistral.mistral-large-2402-v1:0` | $0.008 | Non-Anthropic alternative |
| **Balanced** | Llama 3.1 70B | `meta.llama3-1-70b-instruct-v1:0` | $0.001 | Open-source contender |
| **Budget** | Llama 3.1 8B | `meta.llama3-1-8b-instruct-v1:0` | $0.0002 | Ultra-cheap baseline |
| **Budget** | Mixtral 8x7B | `mistral.mixtral-8x7b-instruct-v0:1` | $0.0006 | Efficient MoE |
| **Optional** | Claude 3 Sonnet | `anthropic.claude-3-sonnet-20240229-v1:0` | $0.009 | Previous gen comparison |

*Cost per question estimated at ~500 input tokens + ~100 output tokens

---

## Simplified Architecture (Bedrock-Only)

```
┌─────────────────────────────────────────────┐
│         Python Script (Local or Lambda)      │
│  - Generate 120 test scenarios              │
│  - Loop through 8 Bedrock models            │
│  - Call Bedrock API for each                │
│  - Score with Claude 3.5 Sonnet (judge)     │
│  - Save to JSON/CSV or DynamoDB             │
└─────────────────────────────────────────────┘
                    ↓
            ┌───────────────┐
            │  AWS Bedrock  │
            │  (All Models) │
            └───────────────┘
                    ↓
            ┌───────────────┐
            │  Results.json │
            │  or DynamoDB  │
            └───────────────┘
```

**Key Simplification**:
- ✅ Single API (Bedrock) - no OpenAI, no Google Cloud
- ✅ Same authentication (AWS credentials)
- ✅ Consistent pricing model
- ✅ All models in same region (us-east-1)

---

## Local-First Development Approach

### **Phase 1: Local Python Script** (Week 1)

**No AWS deployment needed yet!** Run everything locally:

```python
# benchmark.py
import boto3
import json
from datetime import datetime

# Initialize Bedrock client
bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')

# 8 models to test
MODELS = [
    "anthropic.claude-3-5-sonnet-20241022-v2:0",
    "anthropic.claude-3-opus-20240229-v1:0",
    "anthropic.claude-3-5-haiku-20241022-v1:0",
    "mistral.mistral-large-2402-v1:0",
    "meta.llama3-1-70b-instruct-v1:0",
    "meta.llama3-1-8b-instruct-v1:0",
    "mistral.mixtral-8x7b-instruct-v0:1",
    "anthropic.claude-3-sonnet-20240229-v1:0"
]

def generate_test_scenarios(count=120):
    """Create synthetic test scenarios"""
    scenarios = []

    # 10 student profiles
    profiles = [
        {"age": 14, "grade": 9, "depth": "surface"},
        {"age": 15, "grade": 9, "depth": "moderate"},
        # ... 8 more
    ]

    # 4 content segments
    segments = [
        {
            "id": 1,
            "summary": "Introduction to Tredegar Iron Works, founded 1837...",
            "concepts": ["industrial revolution", "Richmond's role"]
        },
        # ... 3 more
    ]

    # 3 question positions
    for profile in profiles:
        for segment in segments:
            for q_num in [1, 2, 3]:
                scenarios.append({
                    "id": f"scenario_{len(scenarios)+1}",
                    "student_profile": profile,
                    "content_segment": segment,
                    "question_number": q_num,
                    "previous_qa": []  # Simplified for now
                })

    return scenarios[:count]

def call_bedrock_model(model_id, prompt):
    """Call any Bedrock model with unified interface"""

    # Different models have different request formats
    if model_id.startswith("anthropic."):
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 200,
            "messages": [{"role": "user", "content": prompt}]
        }
    elif model_id.startswith("meta.llama"):
        body = {
            "prompt": prompt,
            "max_gen_len": 200,
            "temperature": 0.7
        }
    elif model_id.startswith("mistral."):
        body = {
            "prompt": prompt,
            "max_tokens": 200,
            "temperature": 0.7
        }

    response = bedrock.invoke_model(
        modelId=model_id,
        body=json.dumps(body)
    )

    result = json.loads(response['body'].read())

    # Extract text from different response formats
    if model_id.startswith("anthropic."):
        text = result['content'][0]['text']
    elif model_id.startswith("meta.llama"):
        text = result['generation']
    elif model_id.startswith("mistral."):
        text = result['outputs'][0]['text']

    return {
        "text": text,
        "input_tokens": result.get('usage', {}).get('input_tokens', 0),
        "output_tokens": result.get('usage', {}).get('output_tokens', 0)
    }

def run_comparison():
    """Main comparison function"""

    print("🚀 Starting Bedrock Model Comparison")
    print(f"📊 Testing {len(MODELS)} models with 120 scenarios each\n")

    # Generate scenarios once
    scenarios = generate_test_scenarios(120)
    print(f"✅ Generated {len(scenarios)} test scenarios")

    results = []

    for model_id in MODELS:
        print(f"\n🤖 Testing {model_id}...")
        model_results = []

        for i, scenario in enumerate(scenarios):
            # Build Socratic prompt
            prompt = build_socratic_prompt(scenario)

            # Call model
            try:
                start = datetime.now()
                response = call_bedrock_model(model_id, prompt)
                latency_ms = (datetime.now() - start).total_seconds() * 1000

                # Score quality (using Claude 3.5 Sonnet as judge)
                scores = score_question(response['text'], scenario)

                model_results.append({
                    "scenario_id": scenario["id"],
                    "question": response['text'],
                    "quality_scores": scores,
                    "latency_ms": latency_ms,
                    "input_tokens": response['input_tokens'],
                    "output_tokens": response['output_tokens']
                })

                if (i + 1) % 10 == 0:
                    print(f"   Progress: {i+1}/120 scenarios")

            except Exception as e:
                print(f"   ❌ Error on scenario {i+1}: {e}")
                model_results.append({"scenario_id": scenario["id"], "error": str(e)})

        # Aggregate results
        avg_quality = sum(r.get('quality_scores', {}).get('overall', 0)
                         for r in model_results) / len(model_results)
        avg_latency = sum(r.get('latency_ms', 0)
                         for r in model_results) / len(model_results)

        results.append({
            "model_id": model_id,
            "avg_quality": avg_quality,
            "avg_latency_ms": avg_latency,
            "detailed_results": model_results
        })

        print(f"   ✅ Avg Quality: {avg_quality:.3f}, Avg Latency: {avg_latency:.0f}ms")

    # Save results
    with open('comparison_results.json', 'w') as f:
        json.dump(results, f, indent=2)

    print("\n🎉 Comparison complete! Results saved to comparison_results.json")
    print_summary(results)

def print_summary(results):
    """Print ranked summary"""
    print("\n" + "="*60)
    print("MODEL COMPARISON SUMMARY")
    print("="*60)

    # Sort by quality
    sorted_results = sorted(results, key=lambda x: x['avg_quality'], reverse=True)

    print(f"\n{'Rank':<6} {'Model':<50} {'Quality':<10} {'Latency'}")
    print("-"*80)

    for i, r in enumerate(sorted_results):
        model_name = r['model_id'].split('.')[-1][:45]
        print(f"{i+1:<6} {model_name:<50} {r['avg_quality']:.3f}      {r['avg_latency_ms']:.0f}ms")

if __name__ == "__main__":
    run_comparison()
```

**Run locally**:
```bash
# Install dependencies
pip install boto3

# Configure AWS credentials (one-time)
aws configure

# Run comparison
python benchmark.py
```

**Output**: `comparison_results.json` with full data

**Time**: ~30-45 minutes for 8 models × 120 scenarios

**Cost**: ~$10-15 (all through Bedrock)

---

### **Phase 2: Simple Dashboard** (Week 2, Optional)

**If you want visualization, create simple HTML dashboard**:

```python
# generate_dashboard.py
import json
from datetime import datetime

def generate_html_dashboard(results_file='comparison_results.json'):
    """Generate static HTML dashboard from results"""

    with open(results_file) as f:
        results = json.load(f)

    html = """
<!DOCTYPE html>
<html>
<head>
    <title>Bedrock Model Comparison</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .chart-container { width: 80%; margin: 40px auto; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #4CAF50; color: white; }
        .winner { background-color: #d4edda; }
    </style>
</head>
<body>
    <h1>🏆 Bedrock Model Comparison Results</h1>

    <h2>Model Rankings</h2>
    <table>
        <tr>
            <th>Rank</th>
            <th>Model</th>
            <th>Avg Quality</th>
            <th>Avg Latency (ms)</th>
            <th>Est. Cost/Question</th>
        </tr>
"""

    sorted_results = sorted(results, key=lambda x: x['avg_quality'], reverse=True)

    for i, r in enumerate(sorted_results):
        row_class = 'winner' if i == 0 else ''
        html += f"""
        <tr class="{row_class}">
            <td>{i+1}</td>
            <td>{r['model_id']}</td>
            <td>{r['avg_quality']:.3f}</td>
            <td>{r['avg_latency_ms']:.0f}</td>
            <td>${r.get('avg_cost', 0.009):.4f}</td>
        </tr>
"""

    html += """
    </table>

    <div class="chart-container">
        <canvas id="qualityChart"></canvas>
    </div>

    <script>
        const ctx = document.getElementById('qualityChart').getContext('2d');
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: """ + json.dumps([r['model_id'].split('.')[-1] for r in sorted_results]) + """,
                datasets: [{
                    label: 'Average Quality Score',
                    data: """ + json.dumps([r['avg_quality'] for r in sorted_results]) + """,
                    backgroundColor: 'rgba(75, 192, 192, 0.6)'
                }]
            },
            options: {
                scales: {
                    y: { beginAtZero: true, max: 1.0 }
                }
            }
        });
    </script>
</body>
</html>
"""

    with open('dashboard.html', 'w') as f:
        f.write(html)

    print("✅ Dashboard generated: dashboard.html")
    print("   Open in browser to view results")

if __name__ == "__main__":
    generate_html_dashboard()
```

**Run**:
```bash
python generate_dashboard.py
open dashboard.html  # Opens in browser
```

---

### **Phase 3: Deploy to AWS** (Week 3, Optional)

**Only if you want automation/scheduling**:

```bash
# Deploy Lambda + DynamoDB + EventBridge
cdk deploy BenchmarkStack

# Lambda runs comparison daily/weekly
# Results stored in DynamoDB
# Amplify dashboard queries DynamoDB
```

---

## Quick Start Guide

### **Today (30 minutes)**:

1. **Set up AWS credentials**:
```bash
aws configure
# Enter: Access Key, Secret Key, us-east-1, json
```

2. **Request Bedrock model access** (one-time, takes 1-2 hours):
```bash
# Go to AWS Console → Bedrock → Model Access
# Request access to:
# - All Anthropic Claude models
# - All Meta Llama models
# - All Mistral models
```

3. **Create test scenarios file**:
```bash
# I'll generate this for you in next message
```

### **Tomorrow (2-3 hours)**:

4. **Run first test with 2 models**:
```python
# Test just Claude 3.5 Sonnet vs Haiku first
MODELS = [
    "anthropic.claude-3-5-sonnet-20241022-v2:0",
    "anthropic.claude-3-5-haiku-20241022-v1:0"
]
# 2 models × 10 scenarios = 20 API calls (~2 min)
```

5. **Validate results look good**

6. **Run full comparison** (8 models × 120 scenarios)

### **This Week**:

7. **Analyze results**
8. **Select winning model**
9. **Document decision**

---

## Cost Estimate (Bedrock-Only)

### **Per Full Comparison** (8 models × 120 scenarios):

| Model | Cost/Question | 120 Scenarios | % of Total |
|-------|---------------|---------------|------------|
| Claude 3 Opus | $0.045 | $5.40 | 52% |
| Claude 3.5 Sonnet | $0.009 | $1.08 | 10% |
| Mistral Large | $0.008 | $0.96 | 9% |
| Claude 3.5 Haiku | $0.003 | $0.36 | 3% |
| Claude 3 Sonnet | $0.009 | $1.08 | 10% |
| Llama 3.1 70B | $0.001 | $0.12 | 1% |
| Mixtral 8x7B | $0.0006 | $0.07 | 1% |
| Llama 3.1 8B | $0.0002 | $0.02 | <1% |
| **Subtotal Generation** | | **$9.09** | 87% |
| **Scoring** (960 calls) | | **$1.35** | 13% |
| **TOTAL** | | **$10.44** | 100% |

**Much cheaper than original $13.39** (no OpenAI/Google markup)

---

## Expected Timeline

| Day | Activity | Time | Output |
|-----|----------|------|--------|
| **Day 1** | AWS setup, request Bedrock access | 1 hour | Credentials configured |
| **Day 2** | Test scenarios + 2-model test | 3 hours | Validation run complete |
| **Day 3** | Full 8-model comparison | 4 hours | comparison_results.json |
| **Day 4** | Analysis + dashboard | 2 hours | dashboard.html + decision |
| **Day 5** | Documentation | 1 hour | Model selection report |

**Total: 5 days from zero to model selection**

---

## Next Steps

### **Right Now**:

1. **Confirm model list** - Are these 8 Bedrock models the right set?
2. **AWS credentials** - Do you have AWS access keys?
3. **Bedrock access** - Have you requested model access in Bedrock console?

### **I Can Help With**:

- Generate the 120 test scenarios JSON file
- Write the complete `benchmark.py` script
- Create the Socratic prompt templates
- Build the scoring function
- Generate the dashboard HTML

**Want me to create the test scenarios file and complete Python script now?** 🚀
