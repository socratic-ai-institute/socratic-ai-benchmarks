"""
Judge module - scores Socratic dialogue turns using LLM-as-judge.
Used by both CLI and Lambda judge.
"""
from __future__ import annotations
import json
from typing import Dict, Any, Optional
from .models import ModelConfig, BedrockClient
from .prompts import turn_judge_prompt, ase_judge_prompt


class JudgeResult:
    """Result from judging a dialogue turn."""

    def __init__(
        self,
        turn_index: int,
        scores: Dict[str, Any],
        judge_model_id: str,
        latency_ms: float,
        error: Optional[str] = None,
    ):
        self.turn_index = turn_index
        self.scores = scores
        self.judge_model_id = judge_model_id
        self.latency_ms = latency_ms
        self.error = error

    def to_dict(self) -> Dict[str, Any]:
        return {
            "turn_index": self.turn_index,
            "scores": self.scores,
            "judge_model_id": self.judge_model_id,
            "latency_ms": self.latency_ms,
            "error": self.error,
        }

    @property
    def overall_score(self) -> float:
        """Get the overall score (0 if error)."""
        if self.error or not self.scores:
            return 0.0
        overall = self.scores.get("overall", {})
        if isinstance(overall, dict):
            return float(overall.get("score", 0.0))
        return float(overall)


def judge_turn(
    vector: str,
    persona: str,
    turn_index: int,
    student_utterance: str,
    ai_response: str,
    judge_model_id: str = "anthropic.claude-3-5-sonnet-20240620-v1:0",
    bedrock_client: Optional[BedrockClient] = None,
) -> JudgeResult:
    """
    Judge a single dialogue turn using LLM-as-judge.

    Args:
        vector: Test vector ('elenchus', 'maieutics', 'aporia')
        persona: Student persona
        turn_index: Turn number (0-indexed)
        student_utterance: What the student said
        ai_response: What the AI tutor responded
        judge_model_id: Model to use for judging
        bedrock_client: Optional pre-configured client

    Returns:
        JudgeResult with scores and metadata
    """
    if bedrock_client is None:
        bedrock_client = BedrockClient()

    # Build judge prompt
    prompt = turn_judge_prompt(
        vector=vector,
        persona=persona,
        turn_index=turn_index,
        student_utterance=student_utterance,
        ai_response=ai_response,
    )

    # Create judge model config (always Anthropic Claude for now)
    judge_config = ModelConfig(
        model_id=judge_model_id,
        provider="anthropic",
        max_tokens=400,
        temperature=0.3,  # Lower temperature for consistency
    )

    try:
        response = bedrock_client.invoke(judge_config, prompt)
        raw_text = response["text"]

        # Parse JSON (handle optional code fencing)
        if raw_text.startswith("```"):
            raw_text = raw_text.strip('`')
            if raw_text.lower().startswith("json"):
                raw_text = raw_text[4:]

        scores = json.loads(raw_text)

        return JudgeResult(
            turn_index=turn_index,
            scores=scores,
            judge_model_id=judge_model_id,
            latency_ms=response["latency_ms"],
            error=None,
        )

    except Exception as e:
        return JudgeResult(
            turn_index=turn_index,
            scores={},
            judge_model_id=judge_model_id,
            latency_ms=0.0,
            error=str(e),
        )


def judge_transcript(
    vector: str,
    persona: str,
    transcript: str,
    judge_model_id: str = "anthropic.claude-3-5-sonnet-20241022-v2:0",
    bedrock_client: Optional[BedrockClient] = None,
) -> JudgeResult:
    """
    Judge an entire transcript using the ASE rubric.

    Args:
        vector: Test vector
        persona: Student persona
        transcript: Full conversation transcript
        judge_model_id: Model to use for judging
        bedrock_client: Optional pre-configured client

    Returns:
        JudgeResult with ASE scores
    """
    if bedrock_client is None:
        bedrock_client = BedrockClient()

    # Build ASE judge prompt
    prompt = ase_judge_prompt(
        vector=vector,
        persona=persona,
        transcript=transcript,
    )

    # Create judge model config
    judge_config = ModelConfig(
        model_id=judge_model_id,
        provider="anthropic",
        max_tokens=400,
        temperature=0.3,
    )

    try:
        response = bedrock_client.invoke(judge_config, prompt)
        raw_text = response["text"]

        # Parse JSON (handle optional code fencing)
        if raw_text.startswith("```"):
            raw_text = raw_text.strip('`')
            if raw_text.lower().startswith("json"):
                raw_text = raw_text[4:]

        scores = json.loads(raw_text)

        return JudgeResult(
            turn_index=-1,  # Whole transcript
            scores=scores,
            judge_model_id=judge_model_id,
            latency_ms=response["latency_ms"],
            error=None,
        )

    except Exception as e:
        return JudgeResult(
            turn_index=-1,
            scores={},
            judge_model_id=judge_model_id,
            latency_ms=0.0,
            error=str(e),
        )


def compute_heuristic_scores(ai_response: str) -> Dict[str, Any]:
    """
    Compute simple heuristic scores without LLM judge.

    Returns:
        {
            "has_question": bool,
            "question_count": int,
            "word_count": int,
            "is_open_ended": bool (simple heuristic),
        }
    """
    text = ai_response.strip()
    question_count = text.count("?")

    # Simple open-ended heuristic: contains "?" but not yes/no keywords
    yes_no_keywords = ["yes", "no", "is it", "are you", "do you", "did you", "can you"]
    is_open_ended = question_count > 0 and not any(
        keyword in text.lower() for keyword in yes_no_keywords
    )

    return {
        "has_question": question_count > 0,
        "question_count": question_count,
        "word_count": len(text.split()),
        "is_open_ended": is_open_ended,
    }
