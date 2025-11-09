"""
ASE Grader: LLM-as-judge that scores Socratic dialogs using the ASE rubric.

DEPRECATED: This module uses LLM-as-judge scoring which is slower and more
expensive than the new vector-based scoring system.

For new code, use:
    from socratic_bench import compute_vector_scores

This module is retained for:
    - Backward compatibility with phase1 experiments
    - Comparison studies between LLM-judge and vector scoring
    - Historical result reproduction

ASE Rubric (1-5 scale per dimension):
    1. Pedagogical Stance: Non-directive, probing, no lecturing
    2. Conceptual Fidelity: Targets correct underlying flaw/truth
    3. Persona Adaptation: Age-appropriate language and scaffolding
    4. Dialectical Progress: Achieves the vector goal (elenchus/maieutics/aporia)
    Overall: Average of 4 dimensions

Migration Path:
    Old:
        grade = grade_transcript(vector, persona, transcript)
        score = grade["scores"]["overall"]  # 1-5 scale

    New:
        from socratic_bench import compute_vector_scores
        result = compute_vector_scores(ai_response)
        score = result.scores["overall"]  # 0-1 scale
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
    """
    Internal helper to invoke Anthropic models for judging.

    Uses low temperature (0.3) for more deterministic scoring.
    Max tokens is 300 to allow for structured JSON responses.

    Args:
        model_id: Anthropic model ID (typically Claude Sonnet for judging)
        prompt: Judge prompt with transcript to evaluate

    Returns:
        Dictionary with:
            - text: Generated JSON with scores
            - latency_ms: API call latency
    """
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
    """
    Grade a Socratic dialogue transcript using LLM-as-judge (DEPRECATED).

    This function sends the transcript to an LLM (typically Claude Sonnet) with
    the ASE rubric and asks it to score the dialogue on 4 dimensions.

    DEPRECATED: Use compute_vector_scores() from socratic_bench for faster,
    cheaper scoring that doesn't require an LLM judge call.

    Args:
        vector: Test vector ('elenchus', 'maieutics', 'aporia')
        persona: Student persona/context
        transcript: Full conversation transcript (Student ↔ AI)
        judge_model: Bedrock model ID to use for judging (default: Claude 3.5 Sonnet)

    Returns:
        Dictionary with:
            - scores: Dict with dimension scores (1-5) and overall, or None if error
            - judge_model: Model ID used for judging
            - latency_ms: Judge API call latency
            - error: Error message if grading failed, None otherwise

    Example:
        >>> transcript = "Student: I believe...\nAI: What makes you think...?"
        >>> result = grade_transcript("elenchus", "11th grade student", transcript)
        >>> if result["error"] is None:
        ...     print(f"Overall score: {result['scores']['overall']}/5")

    Expected JSON Response Format:
        {
            "ped_stance": {"score": 4, "evidence": ["..."]},
            "concept_fidelity": {"score": 3, "evidence": ["..."]},
            "persona_adapt": {"score": 5, "evidence": ["..."]},
            "dialectical_progress": {"score": 4, "evidence": ["..."]},
            "overall": 4.0
        }

    Note:
        The judge sometimes returns JSON wrapped in markdown code fencing.
        This function handles that by stripping backticks and "json" prefix.
    """
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

