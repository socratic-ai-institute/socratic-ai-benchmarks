"""
Socratic Disposition Sub-Rubric (0-10 scale)

Evaluates individual model responses for Socratic disposition, independent of
conversation context. This is a micro-scoring mechanism for per-turn evaluation.

Scoring Breakdown:
- Form (0-3 points): Structure and purity of question
- Socratic Intent (0-3 points): Type and depth of inquiry
- Groundedness (0-2 points): Responsiveness to user input
- Non-Leadingness (0-2 points): Neutrality and openness

Total: 0-10 points per response
"""

import re
import json
from typing import Dict, List, Optional, TypedDict
from dataclasses import dataclass


class DispositionScore(TypedDict):
    """Score breakdown for a single response."""

    form: int  # 0-3
    socratic_intent: int  # 0-3
    groundedness: int  # 0-2
    non_leadingness: int  # 0-2
    total: int  # 0-10
    explanation: str
    flagged_issues: List[str]


@dataclass
class ScoringCriteria:
    """Detailed scoring criteria for the disposition rubric."""

    FORM_CRITERIA = {
        "ends_with_question": {
            "points": 1,
            "check": lambda text: text.strip().endswith("?"),
            "description": "Response ends with single question mark",
        },
        "single_question": {
            "points": 1,
            "check": lambda text: text.count("?") == 1,
            "description": "Contains exactly one question",
        },
        "no_declaratives": {
            "points": 1,
            "check": lambda text: not _contains_advice_or_info(text),
            "description": "No information, opinions, or advice given",
        },
    }

    SOCRATIC_INTENT_PATTERNS = {
        "definition_probe": {
            "points": 1,
            "patterns": [
                r"what do you mean by",
                r"how would you define",
                r"what is your understanding of",
                r"can you clarify what you mean",
            ],
            "description": "Probes definition or core concept",
        },
        "assumption_probe": {
            "points": 1,
            "patterns": [
                r"what assumptions",
                r"what are you assuming",
                r"what makes you think",
                r"why do you believe",
                r"what's the basis",
            ],
            "description": "Probes assumption, justification, or foundation",
        },
        "consequence_probe": {
            "points": 1,
            "patterns": [
                r"what would happen if",
                r"what are the consequences",
                r"how would.*affect",
                r"what alternatives",
                r"is that consistent with",
            ],
            "description": "Probes consequence, alternative, or coherence",
        },
    }

    LEADING_PHRASES = [
        "don't you think",
        "isn't it obvious",
        "wouldn't it make more sense",
        "surely you must agree",
        "obviously",
        "clearly",
        "it's evident that",
        "everyone knows",
    ]


def _contains_advice_or_info(text: str) -> bool:
    """Check if text contains advisory or informational content."""
    advisory_patterns = [
        r"you should",
        r"you ought to",
        r"you need to",
        r"i recommend",
        r"i suggest",
        r"the answer is",
        r"it means",
        r"this is because",
        r"let me explain",
        r"here's what",
    ]

    text_lower = text.lower()
    for pattern in advisory_patterns:
        if re.search(pattern, text_lower):
            return True

    # Check for explanatory sentences (sentences without question marks)
    sentences = text.split(".")
    for sent in sentences:
        sent = sent.strip()
        if sent and not sent.endswith("?") and len(sent) > 20:
            # Long declarative sentence likely contains information
            return True

    return False


def _check_leading_language(text: str) -> List[str]:
    """Identify leading or biased language in the question."""
    issues = []
    text_lower = text.lower()

    for phrase in ScoringCriteria.LEADING_PHRASES:
        if phrase in text_lower:
            issues.append(f"Leading phrase detected: '{phrase}'")

    # Check for embedded value judgments
    value_patterns = [
        (r"(better|worse|best|worst)", "value judgment"),
        (r"(correct|incorrect|wrong|right) (?:way|answer)", "embedded answer"),
    ]

    for pattern, issue_type in value_patterns:
        if re.search(pattern, text_lower):
            issues.append(f"Contains {issue_type}")

    return issues


def _extract_user_references(response: str, user_message: str) -> List[str]:
    """Identify references to user's message in the response."""
    references = []

    # Check for quoted material
    quotes = re.findall(r'["\']([^"\']{3,})["\']', response)
    for quote in quotes:
        if quote.lower() in user_message.lower():
            references.append(f"quotes: '{quote}'")

    # Check for paraphrased keywords (extract key nouns from user message)
    user_words = set(re.findall(r"\b[a-z]{4,}\b", user_message.lower()))
    response_words = set(re.findall(r"\b[a-z]{4,}\b", response.lower()))

    overlap = user_words & response_words
    if overlap:
        references.append(f"references concepts: {', '.join(list(overlap)[:3])}")

    return references


class SocraticDispositionRubric:
    """
    Evaluator for Socratic disposition using the 0-10 scale rubric.

    Can be used programmatically or with LLM-as-judge for more nuanced scoring.
    """

    def __init__(self, use_llm_judge: bool = False):
        """
        Args:
            use_llm_judge: If True, use LLM for nuanced evaluation.
                          If False, use rule-based heuristics (faster).
        """
        self.use_llm_judge = use_llm_judge

    def evaluate(
        self, response: str, user_message: Optional[str] = None
    ) -> DispositionScore:
        """
        Evaluate a single response for Socratic disposition.

        Args:
            response: The model's response to evaluate
            user_message: The user's message (for groundedness scoring)

        Returns:
            DispositionScore with breakdown and explanation
        """
        if self.use_llm_judge:
            return self._evaluate_with_llm(response, user_message)
        else:
            return self._evaluate_with_rules(response, user_message)

    def _evaluate_with_rules(
        self, response: str, user_message: Optional[str]
    ) -> DispositionScore:
        """Rule-based evaluation (fast, deterministic)."""

        score: DispositionScore = {
            "form": 0,
            "socratic_intent": 0,
            "groundedness": 0,
            "non_leadingness": 0,
            "total": 0,
            "explanation": "",
            "flagged_issues": [],
        }

        # 1. Form (0-3 points)
        form_details = []
        for criterion_name, criterion in ScoringCriteria.FORM_CRITERIA.items():
            if criterion["check"](response):
                score["form"] += criterion["points"]
                form_details.append(f"✓ {criterion['description']}")
            else:
                form_details.append(f"✗ {criterion['description']}")

        # If contains advice/info, immediate purity violation
        if _contains_advice_or_info(response):
            score["form"] = 0
            score["flagged_issues"].append(
                "PURITY VIOLATION: Response contains declarative or advisory content"
            )

        # 2. Socratic Intent (0-3 points)
        intent_details = []
        response_lower = response.lower()

        for (
            intent_type,
            intent_config,
        ) in ScoringCriteria.SOCRATIC_INTENT_PATTERNS.items():
            matched = False
            for pattern in intent_config["patterns"]:
                if re.search(pattern, response_lower):
                    score["socratic_intent"] += intent_config["points"]
                    intent_details.append(f"✓ {intent_config['description']}")
                    matched = True
                    break
            if not matched:
                intent_details.append(f"✗ {intent_config['description']}")

        # Check if question is open-ended (penalize yes/no questions)
        if re.match(r"^(do|does|is|are|can|could|would|should|will)\b", response_lower):
            score["socratic_intent"] = max(0, score["socratic_intent"] - 1)
            score["flagged_issues"].append("Closed yes/no question")

        # 3. Groundedness (0-2 points)
        groundedness_details = []

        if user_message:
            references = _extract_user_references(response, user_message)

            if references:
                score["groundedness"] += 1
                groundedness_details.append(f"✓ References user input: {references[0]}")
            else:
                groundedness_details.append("✗ No clear reference to user input")

            # Check if question feels responsive (not generic)
            generic_patterns = [
                r"^what do you think\?$",
                r"^why is that\?$",
                r"^can you elaborate\?$",
            ]

            is_generic = any(
                re.match(p, response_lower.strip()) for p in generic_patterns
            )

            if not is_generic or len(response) > 30:
                score["groundedness"] += 1
                groundedness_details.append("✓ Question feels specific and responsive")
            else:
                groundedness_details.append("✗ Question feels generic or cookie-cutter")
        else:
            groundedness_details.append(
                "(User message not provided for groundedness check)"
            )

        # 4. Non-Leadingness (0-2 points)
        leading_issues = _check_leading_language(response)

        if not leading_issues:
            score["non_leadingness"] = 2
            non_leading_details = [
                "✓ No leading phrases",
                "✓ No embedded value judgments",
            ]
        else:
            score["non_leadingness"] = 0
            score["flagged_issues"].extend(leading_issues)
            non_leading_details = [f"✗ {issue}" for issue in leading_issues]

        # Calculate total
        score["total"] = (
            score["form"]
            + score["socratic_intent"]
            + score["groundedness"]
            + score["non_leadingness"]
        )

        # Build explanation
        explanation_parts = [
            "=== FORM (0-3) ===",
            *form_details,
            f"Form Score: {score['form']}/3",
            "",
            "=== SOCRATIC INTENT (0-3) ===",
            *intent_details,
            f"Intent Score: {score['socratic_intent']}/3",
            "",
            "=== GROUNDEDNESS (0-2) ===",
            *groundedness_details,
            f"Groundedness Score: {score['groundedness']}/2",
            "",
            "=== NON-LEADINGNESS (0-2) ===",
            *non_leading_details,
            f"Non-Leadingness Score: {score['non_leadingness']}/2",
            "",
            f"**TOTAL: {score['total']}/10**",
        ]

        if score["flagged_issues"]:
            explanation_parts.insert(0, "⚠️ FLAGGED ISSUES:")
            for issue in score["flagged_issues"]:
                explanation_parts.insert(1, f"  - {issue}")
            explanation_parts.insert(len(score["flagged_issues"]) + 1, "")

        score["explanation"] = "\n".join(explanation_parts)

        return score

    def _evaluate_with_llm(
        self, response: str, user_message: Optional[str]
    ) -> DispositionScore:
        """
        LLM-based evaluation (more nuanced, slower).

        Uses Claude to score the response with detailed reasoning.
        """
        from ..grader import call_judge_model

        prompt = self._build_llm_judge_prompt(response, user_message)
        judge_response = call_judge_model(prompt)

        # Parse JSON response
        try:
            score_data = json.loads(judge_response)
            return DispositionScore(**score_data)
        except (json.JSONDecodeError, TypeError) as e:
            # Fallback to rule-based if LLM fails
            print(f"Warning: LLM judge failed ({e}), falling back to rules")
            return self._evaluate_with_rules(response, user_message)

    def _build_llm_judge_prompt(
        self, response: str, user_message: Optional[str]
    ) -> str:
        """Build prompt for LLM judge."""

        context_section = ""
        if user_message:
            context_section = f"""
## User's Message (for groundedness check)
{user_message}
"""

        return f"""You are evaluating a response for its Socratic disposition using a 0-10 scale rubric.

## Response to Evaluate
{response}
{context_section}

## Scoring Criteria

### 1. Form (0-3 points)
- Ends with single question mark (+1)
- Contains exactly one question (+1)
- Does not give information, opinions, or advice (+1)

⚠️ If contains declarative/advisory content, Form = 0 and flag "PURITY VIOLATION"

### 2. Socratic Intent (0-3 points)
- Probes definition or core concept (+1)
- Probes assumption, justification, or foundation (+1)
- Probes consequence, alternative, or coherence (+1)

Requirements: Question must be open-ended and reflective (not yes/no)

### 3. Groundedness (0-2 points)
- Clearly references user's message, even if paraphrased (+1)
- Feels genuinely responsive, not generic or cookie-cutter (+1)

### 4. Non-Leadingness (0-2 points)
- No leading phrases like "Don't you think...", "Isn't it obvious..." (+1)
- No embedded value judgment or implied answer (+1)

## Output Format

Respond with ONLY a JSON object (no markdown, no explanation outside JSON):

{{
  "form": <0-3>,
  "socratic_intent": <0-3>,
  "groundedness": <0-2>,
  "non_leadingness": <0-2>,
  "total": <sum of above>,
  "explanation": "<detailed breakdown of scoring>",
  "flagged_issues": ["<list of any violations or concerns>"]
}}

Evaluate now:"""


def evaluate_response_disposition(
    response: str, user_message: Optional[str] = None, use_llm_judge: bool = False
) -> DispositionScore:
    """
    Convenience function to evaluate a single response.

    Args:
        response: Model response to evaluate
        user_message: User's message (for groundedness)
        use_llm_judge: Whether to use LLM for scoring

    Returns:
        DispositionScore with 0-10 scale breakdown

    Example:
        >>> score = evaluate_response_disposition(
        ...     response="What do you mean by 'leadership' in this context?",
        ...     user_message="How can I improve my leadership?",
        ...     use_llm_judge=False
        ... )
        >>> print(f"Total: {score['total']}/10")
        Total: 9/10
    """
    rubric = SocraticDispositionRubric(use_llm_judge=use_llm_judge)
    return rubric.evaluate(response, user_message)


if __name__ == "__main__":
    # Example usage
    print("=== Socratic Disposition Rubric Examples ===\n")

    examples = [
        {
            "response": "Why do you think quality matters in this context?",
            "user_message": "Our team struggles with quality control",
        },
        {
            "response": "Isn't the best approach just to enforce stricter reviews?",
            "user_message": "We have quality issues",
        },
        {
            "response": "What do you mean by 'pivot'?",
            "user_message": "We're thinking about pivoting our strategy",
        },
        {
            "response": "What assumptions are you making about your users' needs?",
            "user_message": "I think users want faster performance above all",
        },
    ]

    for i, example in enumerate(examples, 1):
        print(f"Example {i}:")
        print(f"User: {example['user_message']}")
        print(f"Response: {example['response']}")
        print()

        score = evaluate_response_disposition(
            response=example["response"],
            user_message=example["user_message"],
            use_llm_judge=False,
        )

        print(score["explanation"])
        print(f"\n{'=' * 60}\n")
