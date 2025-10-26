"""
ASE Grader: LLM-as-judge that scores Socratic dialogs using the ASE rubric.
Produces JSON with dimension scores and overall.
"""
from __future__ import annotations
import json
from typing import Any, Dict

from .prompts import ase_judge_prompt

# Lightweight Bedrock caller (duplicates mapping to avoid importing benchmark.py)
import boto3
import time

AWS_PROFILE = "mvp"
AWS_REGION = "us-east-1"

session = boto3.Session(profile_name=AWS_PROFILE, region_name=AWS_REGION)
bedrock_runtime = session.client('bedrock-runtime')


def _invoke_anthropic(model_id: str, prompt: str) -> Dict[str, Any]:
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 300,
        "temperature": 0.3,
        "messages": [{"role": "user", "content": prompt}],
    }
    t0 = time.time()
    resp = bedrock_runtime.invoke_model(modelId=model_id, body=json.dumps(body))
    latency = (time.time() - t0) * 1000
    data = json.loads(resp["body"].read())
    text = data["content"][0]["text"].strip()
    return {"text": text, "latency_ms": latency}


def grade_transcript(vector: str, persona: str, transcript: str, judge_model: str = "anthropic.claude-3-5-sonnet-20241022-v2:0") -> Dict[str, Any]:
    prompt = ase_judge_prompt(vector, persona, transcript)
    try:
        result = _invoke_anthropic(judge_model, prompt)
        raw = result["text"]
        # Handle optional code fencing
        if raw.startswith("```"):
            raw = raw.strip('`')
            if raw.lower().startswith("json"):
                raw = raw[4:]
        scores = json.loads(raw)
        return {
            "scores": scores,
            "judge_model": judge_model,
            "latency_ms": result["latency_ms"],
            "error": None,
        }
    except Exception as e:
        return {"scores": None, "judge_model": judge_model, "latency_ms": 0, "error": str(e)}

