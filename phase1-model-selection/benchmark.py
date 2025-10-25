#!/usr/bin/env python3
"""
Bedrock Model Comparison Benchmark
Compare 8 AWS Bedrock models for Socratic question generation

Usage:
    python benchmark.py                    # Full comparison (8 models, 120 scenarios)
    python benchmark.py --quick            # Quick test (2 models, 10 scenarios)
    python benchmark.py --models 3         # Test specific number of models
    python benchmark.py --scenarios 50     # Custom scenario count
"""

import boto3
import json
import time
import argparse
from datetime import datetime
from typing import Dict, List, Any
import os

# AWS Profile to use
AWS_PROFILE = "mvp"
AWS_REGION = "us-east-1"

# Models to test (in priority order)
BEDROCK_MODELS = [
    {
        "id": "anthropic.claude-3-5-sonnet-20241022-v2:0",
        "name": "Claude 3.5 Sonnet v2",
        "provider": "anthropic"
    },
    {
        "id": "anthropic.claude-3-opus-20240229-v1:0",
        "name": "Claude 3 Opus",
        "provider": "anthropic"
    },
    {
        "id": "anthropic.claude-3-5-haiku-20241022-v1:0",
        "name": "Claude 3.5 Haiku",
        "provider": "anthropic"
    },
    {
        "id": "mistral.mistral-large-2402-v1:0",
        "name": "Mistral Large",
        "provider": "mistral"
    },
    {
        "id": "meta.llama3-1-70b-instruct-v1:0",
        "name": "Llama 3.1 70B",
        "provider": "meta"
    },
    {
        "id": "meta.llama3-1-8b-instruct-v1:0",
        "name": "Llama 3.1 8B",
        "provider": "meta"
    },
    {
        "id": "mistral.mixtral-8x7b-instruct-v0:1",
        "name": "Mixtral 8x7B",
        "provider": "mistral"
    },
    {
        "id": "anthropic.claude-3-sonnet-20240229-v1:0",
        "name": "Claude 3 Sonnet",
        "provider": "anthropic"
    }
]

# Initialize Bedrock client with mvp profile
session = boto3.Session(profile_name=AWS_PROFILE, region_name=AWS_REGION)
bedrock_runtime = session.client('bedrock-runtime')

def load_test_scenarios(filename='test_scenarios.json') -> List[Dict]:
    """Load test scenarios from JSON file"""
    if not os.path.exists(filename):
        print(f"❌ Error: {filename} not found. Run generate_scenarios.py first.")
        exit(1)

    with open(filename, 'r') as f:
        return json.load(f)

def build_socratic_prompt(scenario: Dict) -> str:
    """Build Socratic question prompt for a scenario"""

    profile = scenario['student_profile']
    segment = scenario['content_segment']
    q_num = scenario['question_number']
    prev_qa = scenario.get('previous_qa', [])

    base_prompt = f"""You are a Socratic learning assistant helping a {profile['age']}-year-old student in grade {profile['grade']} understand educational content about Richmond history.

CONTENT JUST VIEWED:
{segment['summary']}

Key concepts: {', '.join(segment['key_concepts'])}

STUDENT PROFILE:
- Age: {profile['age']}
- Grade: {profile['grade']}
- Depth preference: {profile['depth_preference']}

YOUR ROLE:
Ask questions that help the student reflect on and understand the material.
Do NOT provide answers. Guide them to discover insights themselves.
"""

    if q_num == 1:
        return base_prompt + """
TASK: Generate ONE opening question that:
1. Connects to a key concept from the content
2. Is appropriate for this student's age and level
3. Encourages them to articulate what they understood
4. Is open-ended (not yes/no)

Return ONLY the question, nothing else."""

    elif q_num == 2:
        prev_q = prev_qa[0]['question']
        prev_a = prev_qa[0]['answer']

        return base_prompt + f"""
PREVIOUS EXCHANGE:
Question: {prev_q}
Student Answer: {prev_a}

TASK: Generate ONE follow-up question that:
1. Builds directly on their answer above
2. Probes deeper into their understanding
3. Identifies assumptions or gaps in their reasoning
4. Maintains the Socratic method (guide, don't tell)

Return ONLY the question, nothing else."""

    elif q_num == 3:
        exchange_history = "\n".join([
            f"Q{i+1}: {qa['question']}\nA{i+1}: {qa['answer']}"
            for i, qa in enumerate(prev_qa)
        ])

        return base_prompt + f"""
CONVERSATION SO FAR:
{exchange_history}

TASK: Generate ONE final synthesis question that:
1. Connects their previous answers together
2. Pushes them toward a deeper insight about the main concept
3. Helps them see patterns or implications they might have missed
4. Ends the intervention on a thought-provoking note

Return ONLY the question, nothing else."""

def call_bedrock_model(model_id: str, provider: str, prompt: str) -> Dict[str, Any]:
    """Call Bedrock model with unified interface"""

    try:
        # Build request body based on provider
        if provider == "anthropic":
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 200,
                "temperature": 0.7,
                "messages": [{"role": "user", "content": prompt}]
            }
        elif provider == "meta":
            body = {
                "prompt": prompt,
                "max_gen_len": 200,
                "temperature": 0.7,
                "top_p": 0.9
            }
        elif provider == "mistral":
            body = {
                "prompt": f"<s>[INST] {prompt} [/INST]",
                "max_tokens": 200,
                "temperature": 0.7,
                "top_p": 0.9
            }
        else:
            raise ValueError(f"Unknown provider: {provider}")

        # Call Bedrock
        start_time = time.time()
        response = bedrock_runtime.invoke_model(
            modelId=model_id,
            body=json.dumps(body)
        )
        latency_ms = (time.time() - start_time) * 1000

        # Parse response
        result = json.loads(response['body'].read())

        # Extract text based on provider
        if provider == "anthropic":
            text = result['content'][0]['text']
            usage = result.get('usage', {})
            input_tokens = usage.get('input_tokens', 0)
            output_tokens = usage.get('output_tokens', 0)
        elif provider == "meta":
            text = result['generation']
            input_tokens = result.get('prompt_token_count', 0)
            output_tokens = result.get('generation_token_count', 0)
        elif provider == "mistral":
            text = result['outputs'][0]['text']
            input_tokens = 0  # Mistral doesn't return token counts
            output_tokens = 0

        return {
            "text": text.strip(),
            "latency_ms": latency_ms,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "error": None
        }

    except Exception as e:
        return {
            "text": None,
            "latency_ms": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "error": str(e)
        }

def score_question_quality(question: str, scenario: Dict) -> Dict[str, float]:
    """
    Score question quality using Claude 3.5 Sonnet as judge
    Returns scores for 5 criteria + overall
    """

    profile = scenario['student_profile']
    segment = scenario['content_segment']
    q_num = scenario['question_number']
    prev_qa = scenario.get('previous_qa', [])

    judge_prompt = f"""You are evaluating a Socratic question for educational quality.

STUDENT: Age {profile['age']}, Grade {profile['grade']}
CONTENT: {segment['summary']}
QUESTION NUMBER: {q_num}
{f"PREVIOUS Q&A: {prev_qa}" if prev_qa else ""}

GENERATED QUESTION:
{question}

Rate on 5 criteria (0.0-1.0 each):
1. open_ended: Is it open-ended (not yes/no)? Does it encourage elaboration?
2. probing: Does it deepen understanding vs surface recall?
3. builds_on_previous: Does it reference prior answers appropriately? (Score 1.0 for Q1 since no prior)
4. age_appropriate: Is language suitable for this {profile['age']}-year-old student?
5. content_relevant: Does it connect to the key concepts?

Return ONLY a JSON object with these exact keys:
{{"open_ended": 0.0, "probing": 0.0, "builds_on_previous": 0.0, "age_appropriate": 0.0, "content_relevant": 0.0}}"""

    try:
        # Use Claude 3.5 Sonnet as judge
        result = call_bedrock_model(
            "anthropic.claude-3-5-sonnet-20241022-v2:0",
            "anthropic",
            judge_prompt
        )

        if result['error']:
            # Return middle scores if judging fails
            return {
                "open_ended": 0.5,
                "probing": 0.5,
                "builds_on_previous": 0.5,
                "age_appropriate": 0.5,
                "content_relevant": 0.5,
                "overall": 0.5,
                "judge_error": result['error']
            }

        # Parse JSON from response
        text = result['text']
        # Extract JSON from response (handle markdown code blocks)
        if '```json' in text:
            text = text.split('```json')[1].split('```')[0]
        elif '```' in text:
            text = text.split('```')[1].split('```')[0]

        scores = json.loads(text.strip())

        # Calculate overall as average
        scores['overall'] = sum(scores.values()) / len(scores)

        return scores

    except Exception as e:
        print(f"      ⚠️  Scoring error: {e}")
        return {
            "open_ended": 0.5,
            "probing": 0.5,
            "builds_on_previous": 0.5,
            "age_appropriate": 0.5,
            "content_relevant": 0.5,
            "overall": 0.5,
            "judge_error": str(e)
        }

def test_model(model: Dict, scenarios: List[Dict], progress_callback=None) -> Dict:
    """Test a single model across all scenarios"""

    print(f"\n🤖 Testing {model['name']} ({model['id']})")

    results = []
    errors = 0

    for i, scenario in enumerate(scenarios):
        # Build prompt
        prompt = build_socratic_prompt(scenario)

        # Generate question
        generation = call_bedrock_model(model['id'], model['provider'], prompt)

        if generation['error']:
            errors += 1
            results.append({
                "scenario_id": scenario['id'],
                "error": generation['error']
            })
            print(f"   ❌ Scenario {i+1}/{len(scenarios)}: ERROR - {generation['error'][:50]}")
            continue

        # Score quality
        scores = score_question_quality(generation['text'], scenario)

        results.append({
            "scenario_id": scenario['id'],
            "question": generation['text'],
            "quality_scores": scores,
            "latency_ms": generation['latency_ms'],
            "input_tokens": generation['input_tokens'],
            "output_tokens": generation['output_tokens']
        })

        # Progress update
        if (i + 1) % 10 == 0:
            avg_quality = sum(r.get('quality_scores', {}).get('overall', 0)
                            for r in results if 'quality_scores' in r) / len([r for r in results if 'quality_scores' in r])
            print(f"   ✓ Progress: {i+1}/{len(scenarios)} | Avg Quality: {avg_quality:.3f}")

        if progress_callback:
            progress_callback(i + 1, len(scenarios))

    # Calculate aggregated metrics
    successful_results = [r for r in results if 'quality_scores' in r]

    if successful_results:
        avg_quality = sum(r['quality_scores']['overall'] for r in successful_results) / len(successful_results)
        avg_latency = sum(r['latency_ms'] for r in successful_results) / len(successful_results)

        # Criteria breakdown
        criteria = ['open_ended', 'probing', 'builds_on_previous', 'age_appropriate', 'content_relevant']
        criteria_scores = {
            c: sum(r['quality_scores'][c] for r in successful_results) / len(successful_results)
            for c in criteria
        }
    else:
        avg_quality = 0
        avg_latency = 0
        criteria_scores = {}

    summary = {
        "model_id": model['id'],
        "model_name": model['name'],
        "total_scenarios": len(scenarios),
        "successful": len(successful_results),
        "errors": errors,
        "success_rate": len(successful_results) / len(scenarios) if scenarios else 0,
        "avg_quality": avg_quality,
        "avg_latency_ms": avg_latency,
        "criteria_scores": criteria_scores,
        "detailed_results": results
    }

    print(f"   ✅ Complete: {summary['successful']}/{len(scenarios)} successful | Avg Quality: {avg_quality:.3f} | Avg Latency: {avg_latency:.0f}ms")

    return summary

def run_comparison(models_to_test: int = None, scenario_count: int = None):
    """Run full model comparison"""

    print("=" * 70)
    print("🚀 BEDROCK MODEL COMPARISON BENCHMARK")
    print("=" * 70)
    print(f"AWS Profile: {AWS_PROFILE}")
    print(f"Region: {AWS_REGION}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()

    # Load scenarios
    print("📊 Loading test scenarios...")
    all_scenarios = load_test_scenarios()

    if scenario_count:
        scenarios = all_scenarios[:scenario_count]
    else:
        scenarios = all_scenarios

    print(f"✅ Loaded {len(scenarios)} test scenarios")

    # Select models
    if models_to_test:
        models = BEDROCK_MODELS[:models_to_test]
    else:
        models = BEDROCK_MODELS

    print(f"✅ Testing {len(models)} models")
    print()

    # Test each model
    all_results = []

    for model in models:
        result = test_model(model, scenarios)
        all_results.append(result)

        # Small delay between models to avoid rate limiting
        time.sleep(2)

    # Save results
    output_file = f"comparison_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    output = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "aws_profile": AWS_PROFILE,
            "aws_region": AWS_REGION,
            "total_scenarios": len(scenarios),
            "models_tested": len(models)
        },
        "results": all_results
    }

    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)

    print()
    print("=" * 70)
    print("✅ COMPARISON COMPLETE")
    print("=" * 70)
    print(f"Results saved to: {output_file}")
    print()

    # Print summary
    print_summary(all_results)

    return output

def print_summary(results: List[Dict]):
    """Print ranked summary table"""

    print("\n" + "=" * 90)
    print("📊 MODEL COMPARISON SUMMARY")
    print("=" * 90)

    # Sort by quality
    sorted_results = sorted(results, key=lambda x: x['avg_quality'], reverse=True)

    print(f"\n{'Rank':<6} {'Model':<35} {'Quality':<10} {'Latency':<12} {'Success':<10}")
    print("-" * 90)

    for i, r in enumerate(sorted_results):
        quality_str = f"{r['avg_quality']:.3f}"
        latency_str = f"{r['avg_latency_ms']:.0f}ms"
        success_str = f"{r['success_rate']*100:.0f}%"

        # Add emoji for top 3
        rank_display = f"{i+1}"
        if i == 0:
            rank_display += " 🏆"
        elif i == 1:
            rank_display += " 🥈"
        elif i == 2:
            rank_display += " 🥉"

        print(f"{rank_display:<6} {r['model_name']:<35} {quality_str:<10} {latency_str:<12} {success_str:<10}")

    print()
    print("Next step: Run generate_dashboard.py to create visual report")
    print()

def main():
    parser = argparse.ArgumentParser(description='Bedrock Model Comparison Benchmark')
    parser.add_argument('--quick', action='store_true', help='Quick test (2 models, 10 scenarios)')
    parser.add_argument('--models', type=int, help='Number of models to test (default: all 8)')
    parser.add_argument('--scenarios', type=int, help='Number of scenarios to use (default: 120)')

    args = parser.parse_args()

    if args.quick:
        print("⚡ Running QUICK TEST (2 models, 10 scenarios)")
        run_comparison(models_to_test=2, scenario_count=10)
    else:
        run_comparison(models_to_test=args.models, scenario_count=args.scenarios)

if __name__ == "__main__":
    main()
