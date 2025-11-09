#!/usr/bin/env python3
"""
Run Socratic three-vector evaluation for one or more Bedrock models.

Current scope:
- Single-turn tutoring response per scenario (per vector).
- ASE LLM-as-judge scoring (1–5 per dimension + overall).

Next: extend Vector 3 to multi-turn dialogues with aporia detection.
"""

from __future__ import annotations
import argparse
import json
import time
from datetime import datetime
from typing import Any, Dict, List

import boto3

from .vectors import elenchus_scenarios, maieutics_scenarios, aporia_scenarios
from .prompts import socratic_tutor_prompt
from .grader import grade_transcript


AWS_PROFILE = "mvp"
AWS_REGION = "us-east-1"

# Example model list (reuses IDs from phase1 benchmark)
DEFAULT_MODELS = [
    {
        "id": "anthropic.claude-3-5-sonnet-20241022-v2:0",
        "name": "Claude 3.5 Sonnet v2",
        "provider": "anthropic",
    },
    {
        "id": "anthropic.claude-3-5-haiku-20241022-v1:0",
        "name": "Claude 3.5 Haiku",
        "provider": "anthropic",
    },
]


session = boto3.Session(profile_name=AWS_PROFILE, region_name=AWS_REGION)
bedrock_runtime = session.client("bedrock-runtime")


def call_model(model_id: str, provider: str, prompt: str) -> Dict[str, Any]:
    """
    Invoke a Bedrock model and return the generated text.

    This is a simplified version compared to serverless/lib/socratic_bench/models.py.
    It only supports 3 providers (anthropic, meta, mistral) and doesn't have
    retry logic or inference profile support.

    Args:
        model_id: Full Bedrock model identifier
        provider: Provider name (anthropic, meta, or mistral)
        prompt: The prompt text to send

    Returns:
        Dictionary with:
            - text: Generated response text
            - latency_ms: API call latency in milliseconds

    Raises:
        ValueError: If provider is not supported
        ClientError: If Bedrock API call fails

    Note:
        For production use, prefer BedrockClient from serverless/lib/socratic_bench/models.py
        which has better error handling, retry logic, and supports more providers.
    """
    body: Dict[str, Any]
    if provider == "anthropic":
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 200,
            "temperature": 0.7,
            "messages": [{"role": "user", "content": prompt}],
        }
    elif provider == "meta":
        body = {"prompt": prompt, "max_gen_len": 200, "temperature": 0.7, "top_p": 0.9}
    elif provider == "mistral":
        body = {
            "prompt": f"<s>[INST] {prompt} [/INST]",
            "max_tokens": 200,
            "temperature": 0.7,
            "top_p": 0.9,
        }
    else:
        raise ValueError(f"Unknown provider: {provider}")

    t0 = time.time()
    resp = bedrock_runtime.invoke_model(modelId=model_id, body=json.dumps(body))
    latency = (time.time() - t0) * 1000
    data = json.loads(resp["body"].read())

    if provider == "anthropic":
        text = data["content"][0]["text"].strip()
    elif provider == "meta":
        text = data.get("generation", "").strip()
    else:  # mistral
        text = data["outputs"][0]["text"].strip()

    return {"text": text, "latency_ms": latency}


def run_vector(
    models: List[Dict[str, str]], vector: str, scenarios: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Run all scenarios for a specific Socratic vector across multiple models.

    This is the core evaluation function that:
    1. For each model and each scenario:
       - Generates tutor prompt
       - Calls model to get AI response
       - Grades response using LLM-as-judge
    2. Aggregates scores across scenarios

    Args:
        models: List of model configs with keys: id, name, provider
        vector: Which Socratic method to test ('elenchus', 'maieutics', or 'aporia')
        scenarios: List of test scenarios (from vectors.py)

    Returns:
        Dictionary with:
            - vector: Name of the vector tested
            - results: List of per-model results with:
                - model_id, model_name, provider
                - scenarios: List of per-scenario results
                - ped_stance, concept_fidelity, etc.: Averaged scores (1-5 scale)

    Scoring:
        Uses ASE (Automated Socratic Evaluation) rubric with 4 dimensions:
        1. Pedagogical Stance (1-5): Non-directive, probing, no lecturing
        2. Conceptual Fidelity (1-5): Targets correct underlying flaw/truth
        3. Persona Adaptation (1-5): Age-appropriate language and scaffolding
        4. Dialectical Progress (1-5): Achieves the vector goal
        Overall: Average of 4 dimensions

    Note:
        This uses the old LLM-as-judge approach. The newer serverless platform
        uses vector-based scoring (verbosity, exploratory, interrogative) which
        is faster and doesn't require an LLM judge.
    """
    out = {"vector": vector, "results": []}
    for m in models:
        per_model: Dict[str, Any] = {
            "model_id": m["id"],
            "model_name": m["name"],
            "provider": m["provider"],
            "scenarios": [],
        }
        for s in scenarios:
            tutor_prompt = socratic_tutor_prompt(vector, s["persona"], s["prompt"])
            gen = call_model(m["id"], m["provider"], tutor_prompt)
            transcript = f"Student: {s['prompt']}\nAI: {gen['text']}"
            grade = grade_transcript(vector, s["persona"], transcript)
            per_model["scenarios"].append(
                {
                    "scenario_id": s["id"],
                    "persona": s["persona"],
                    "student_prompt": s["prompt"],
                    "ai_response": gen["text"],
                    "tutor_latency_ms": gen["latency_ms"],
                    "judge": grade,
                }
            )
        # Aggregate simple averages (1–5 scale)
        scored = [x for x in per_model["scenarios"] if x["judge"]["scores"]]
        for key in (
            "ped_stance",
            "concept_fidelity",
            "persona_adapt",
            "dialectical_progress",
            "overall",
        ):
            vals = [x["judge"]["scores"].get(key, 0) for x in scored]
            per_model[key] = sum(vals) / len(vals) if vals else 0
        out["results"].append(per_model)
    return out


def main():
    parser = argparse.ArgumentParser(description="Run Socratic 3-vector benchmark")
    parser.add_argument(
        "--models",
        nargs="*",
        help="Optional model IDs (defaults to two Anthropic models)",
    )
    args = parser.parse_args()

    models = (
        DEFAULT_MODELS
        if not args.models
        else [{"id": mid, "name": mid, "provider": "anthropic"} for mid in args.models]
    )

    payload = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "aws_profile": AWS_PROFILE,
            "aws_region": AWS_REGION,
            "models": [m["id"] for m in models],
        },
        "vectors": [],
    }

    payload["vectors"].append(run_vector(models, "elenchus", elenchus_scenarios()))
    payload["vectors"].append(run_vector(models, "maieutics", maieutics_scenarios()))
    payload["vectors"].append(run_vector(models, "aporia", aporia_scenarios()))

    out_file = f"socratic_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(out_file, "w") as f:
        json.dump(payload, f, indent=2)
    print(f"✅ Socratic 3-vector results saved to: {out_file}")


if __name__ == "__main__":
    main()
