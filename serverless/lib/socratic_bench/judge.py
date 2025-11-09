"""
Judge module - scores Socratic dialogue turns using vector-based scoring.
Used by both CLI and Lambda judge.
"""
from __future__ import annotations
from typing import Dict, Any, Optional
from .models import ModelConfig, BedrockClient


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


def compute_vector_scores(
    ai_response: str,
    token_count: Optional[int] = None,
    use_llm_exploratory: bool = False,
    bedrock_client: Optional[BedrockClient] = None,
) -> JudgeResult:
    """
    Compute unified vector scores for Socratic quality (0.00-1.00 scale).

    This is the ONE scoring system that evaluates 3 vectors:
    1. Verbosity: Optimal length for Socratic dialogue (50-150 tokens)
    2. Exploratory: Probing depth and open-ended questioning
    3. Interrogative: Question-asking behavior and quality

    Returns JudgeResult with:
        - scores: {"verbosity": 0.00-1.00, "exploratory": 0.00-1.00, "interrogative": 0.00-1.00, "overall": 0.00-1.00}
        - overall_score: Average of 3 vectors (0.00-1.00)

    Args:
        ai_response: The AI tutor's response text
        token_count: Optional token count (if None, will estimate from word count)
        use_llm_exploratory: If True, use LLM to evaluate exploratory depth (slower but more accurate)
        bedrock_client: Optional bedrock client for LLM evaluation
    """
    text = ai_response.strip()
    heuristics = compute_heuristic_scores(ai_response)

    # 1. VERBOSITY SCORE (0.00-1.00)
    # Optimal range: 50-150 tokens for Socratic dialogue
    # Too short = not engaging, too long = too didactic
    if token_count is None:
        # Rough estimate: 1 token ≈ 0.75 words for English
        token_count = int(heuristics["word_count"] / 0.75)

    if token_count < 50:
        # Too terse
        verbosity = token_count / 50  # Linear 0.0-1.0 as we approach 50
    elif token_count <= 150:
        # Ideal range
        verbosity = 1.0
    else:
        # Too verbose - exponential decay
        verbosity = max(0.0, 1.0 - ((token_count - 150) / 200))  # Decay over next 200 tokens

    # 2. INTERROGATIVE SCORE (0.00-1.00)
    # Based on question-asking behavior
    question_count = heuristics["question_count"]
    is_open_ended = heuristics["is_open_ended"]

    if question_count == 0:
        interrogative = 0.0  # No questions = pure didactic
    elif question_count == 1 and is_open_ended:
        interrogative = 1.0  # Perfect: single open-ended question
    elif question_count == 1 and not is_open_ended:
        interrogative = 0.5  # Closed question (yes/no)
    elif question_count >= 2 and is_open_ended:
        # Multiple questions - slightly penalize (can overwhelm student)
        interrogative = max(0.7, 1.0 - (question_count - 1) * 0.1)
    else:
        # Multiple closed questions
        interrogative = max(0.3, 0.5 - (question_count - 1) * 0.1)

    # 3. EXPLORATORY SCORE (0.00-1.00)
    # Probing depth - uses heuristics by default, optionally LLM
    if use_llm_exploratory and bedrock_client:
        # Use LLM to evaluate exploratory depth (more expensive)
        exploratory = _llm_exploratory_score(ai_response, bedrock_client)
    else:
        # Fast heuristic-based exploratory score
        # Looks for: questions, cognitive verbs, conceptual language
        cognitive_verbs = [
            "think", "consider", "reflect", "reason", "analyze", "examine",
            "explore", "investigate", "wonder", "ponder", "evaluate"
        ]
        conceptual_words = [
            "why", "how", "what if", "suppose", "imagine", "compare",
            "relationship", "connection", "implication", "consequence"
        ]

        text_lower = text.lower()
        cognitive_count = sum(1 for verb in cognitive_verbs if verb in text_lower)
        conceptual_count = sum(1 for word in conceptual_words if word in text_lower)

        # Score based on presence of cognitive/conceptual language + open-ended questions
        base_score = 0.5 if heuristics["has_question"] else 0.3
        cognitive_bonus = min(0.3, cognitive_count * 0.1)
        conceptual_bonus = min(0.2, conceptual_count * 0.1)

        exploratory = min(1.0, base_score + cognitive_bonus + conceptual_bonus)

    # 4. OVERALL SCORE: Average of 3 vectors
    overall = (verbosity + exploratory + interrogative) / 3.0

    return JudgeResult(
        turn_index=0,  # Will be set by caller
        scores={
            "verbosity": round(verbosity, 2),
            "exploratory": round(exploratory, 2),
            "interrogative": round(interrogative, 2),
            "overall": round(overall, 2),
        },
        judge_model_id="vector-scoring-v1",
        latency_ms=0.0,
        error=None,
    )


def _llm_exploratory_score(ai_response: str, bedrock_client: BedrockClient) -> float:
    """
    Use LLM to evaluate exploratory depth (0.00-1.00).

    This is optional and more expensive - only use when accuracy is critical.
    """
    prompt = f"""Rate the exploratory depth of this Socratic response on a 0.00-1.00 scale.

Criteria:
- 1.00: Deep probing that pushes student to examine assumptions and reasoning
- 0.75: Good exploration of concepts with meaningful questions
- 0.50: Surface-level questioning without deep exploration
- 0.25: Minimal exploration, mostly confirmatory
- 0.00: No exploration, purely didactic

Response to evaluate:
{ai_response}

Return ONLY a number between 0.00 and 1.00, nothing else."""

    judge_config = ModelConfig(
        model_id="anthropic.claude-3-5-haiku-20241022-v1:0",  # Use fast/cheap model
        provider="anthropic",
        max_tokens=10,
        temperature=0.1,
    )

    try:
        response = bedrock_client.invoke(judge_config, prompt)
        score_text = response["text"].strip()
        score = float(score_text)
        return max(0.0, min(1.0, score))  # Clamp to 0-1
    except Exception as e:
        print(f"LLM exploratory scoring failed: {e}, using heuristic fallback")
        # Fallback to simple heuristic
        return 0.5 if "?" in ai_response else 0.3
