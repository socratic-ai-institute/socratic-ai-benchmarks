"""
Socratic Answer Quality Evaluator

Evaluates answer quality along three dimensions:
1. Verbosity: Raw token count (from API)
2. Ends with Socratic Question: Binary AI evaluation
3. Directional Socraticism: 0.00-1.00 AI evaluation

Combines these into a composite score that penalizes verbose answers,
missing Socratic endings, and low directional scores.
"""

from typing import Dict, TypedDict, Optional
import json
import boto3
import time

# AWS Configuration
AWS_PROFILE = "mvp"
AWS_REGION = "us-east-1"

session = boto3.Session(profile_name=AWS_PROFILE, region_name=AWS_REGION)
bedrock_runtime = session.client('bedrock-runtime')


class SocraticAnswerScore(TypedDict):
    """Score for Socratic answer quality."""
    verbosity_tokens: int  # Raw token count
    ends_with_socratic_question: bool  # AI-evaluated binary
    directional_socraticism: float  # 0.00-1.00, AI-evaluated
    composite_score: float  # Weighted combination
    verbosity_score: float  # Normalized verbosity (0.00-1.00)
    question_ending_score: float  # 0.0 or 1.0
    explanation: str  # AI reasoning


EVALUATOR_PROMPT = """You are evaluating a response from a Socratic AI assistant to determine its quality along two critical dimensions.

## Response to Evaluate
{response}

## Evaluation Criteria

### 1. Ends with Socratic Question (Binary: true/false)
Does this response END with a genuine Socratic question?

**TRUE if:**
- The final sentence is a question (ends with ?)
- The question is Socratic (probes thinking, assumptions, definitions, consequences)
- NOT just a confirmation request like "Would you like me to proceed?" or "Does that make sense?"
- NOT a yes/no question like "Do you understand?" or "Is that clear?"

**FALSE if:**
- No question at the end
- Ends with a statement
- Ends with a confirmation/procedural question
- Ends with a closed yes/no question

### 2. Directional Socraticism (0.00 to 1.00)
How much does this response guide the user toward introspection and self-discovery vs. providing information and answers?

**Scoring Guide:**
- **0.90-1.00**: Pure Socratic - Only asks probing questions, no information given
- **0.70-0.89**: Highly Socratic - Mostly questions, minimal context setting
- **0.50-0.69**: Moderately Socratic - Balanced between questions and brief explanations
- **0.30-0.49**: Slightly Socratic - Mostly information with some questioning elements
- **0.10-0.29**: Minimally Socratic - Primarily informational with token questions
- **0.00-0.09**: Not Socratic - Pure data/answers, no questioning or introspection

**Consider:**
- Does it provide direct answers or guide toward self-discovery?
- Does it explain concepts or ask about understanding?
- Does it give advice or probe assumptions?
- Is the focus on the user's thinking or on delivering information?

## Output Format

Respond with ONLY a JSON object (no markdown, no explanation outside JSON):

{{
  "ends_with_socratic_question": true/false,
  "directional_socraticism": 0.00-1.00,
  "explanation": "Brief explanation of your scoring (2-3 sentences)"
}}

Evaluate now:"""


def _invoke_claude(prompt: str, model_id: str = "anthropic.claude-3-5-sonnet-20241022-v2:0") -> Dict:
    """Invoke Claude via Bedrock."""
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 500,
        "temperature": 0.3,
        "messages": [{"role": "user", "content": prompt}],
    }

    t0 = time.time()
    resp = bedrock_runtime.invoke_model(modelId=model_id, body=json.dumps(body))
    latency = (time.time() - t0) * 1000

    data = json.loads(resp["body"].read())
    text = data["content"][0]["text"].strip()

    return {"text": text, "latency_ms": latency}


def evaluate_socratic_answer(
    response: str,
    token_count: int,
    verbosity_threshold: int = 200,
    directional_weight: float = 0.50,
    question_ending_weight: float = 0.35,
    verbosity_weight: float = 0.15
) -> SocraticAnswerScore:
    """
    Evaluate a Socratic answer for quality.

    Args:
        response: The answer to evaluate
        token_count: Actual token count from API
        verbosity_threshold: Token count threshold for penalization (default: 200)
        directional_weight: Weight for directional socraticism (default: 0.50)
        question_ending_weight: Weight for question ending (default: 0.35)
        verbosity_weight: Weight for verbosity (default: 0.15)

    Returns:
        SocraticAnswerScore with all metrics and composite score
    """

    # Call AI evaluator
    prompt = EVALUATOR_PROMPT.format(response=response)

    try:
        result = _invoke_claude(prompt)
        raw = result["text"]

        # Handle optional code fencing
        if raw.startswith("```"):
            raw = raw.strip('`')
            if raw.lower().startswith("json"):
                raw = raw[4:]

        ai_eval = json.loads(raw.strip())

        ends_with_socratic_question = ai_eval["ends_with_socratic_question"]
        directional_socraticism = float(ai_eval["directional_socraticism"])
        explanation = ai_eval["explanation"]

    except Exception as e:
        # Fallback to conservative scoring if AI fails
        print(f"Warning: AI evaluator failed ({e}), using fallback")
        ends_with_socratic_question = False
        directional_socraticism = 0.5
        explanation = f"AI evaluation failed: {str(e)}. Using fallback values."

    # Normalize verbosity (0.0 = very verbose, 1.0 = concise)
    # Penalize answers over the threshold
    verbosity_score = max(0.0, 1.0 - (token_count / verbosity_threshold))

    # Binary score for question ending
    question_ending_score = 1.0 if ends_with_socratic_question else 0.0

    # Compute composite score (weighted average)
    composite_score = (
        directional_socraticism * directional_weight +
        question_ending_score * question_ending_weight +
        verbosity_score * verbosity_weight
    )

    return SocraticAnswerScore(
        verbosity_tokens=token_count,
        ends_with_socratic_question=ends_with_socratic_question,
        directional_socraticism=round(directional_socraticism, 2),
        composite_score=round(composite_score, 2),
        verbosity_score=round(verbosity_score, 2),
        question_ending_score=question_ending_score,
        explanation=explanation
    )


def format_score_report(score: SocraticAnswerScore) -> str:
    """
    Generate a human-readable report for a Socratic answer score.

    Args:
        score: The score to format

    Returns:
        Formatted report string
    """

    lines = [
        "=" * 70,
        "SOCRATIC ANSWER QUALITY REPORT",
        "=" * 70,
        "",
        "METRICS",
        "-" * 70,
        f"  Verbosity (tokens):            {score['verbosity_tokens']}",
        f"  Verbosity Score:               {score['verbosity_score']:.2f} (1.0=concise, 0.0=verbose)",
        f"  Ends with Socratic Question:   {'✓ Yes' if score['ends_with_socratic_question'] else '✗ No'}",
        f"  Question Ending Score:         {score['question_ending_score']:.2f}",
        f"  Directional Socraticism:       {score['directional_socraticism']:.2f} (0.0=informational, 1.0=Socratic)",
        "",
        f"  COMPOSITE SCORE:               {score['composite_score']:.2f} / 1.00",
        "",
        "EXPLANATION",
        "-" * 70,
        f"  {score['explanation']}",
        "",
        "SCORING WEIGHTS",
        "-" * 70,
        f"  Directional Socraticism:       50%",
        f"  Question Ending:               35%",
        f"  Verbosity:                     15%",
        "=" * 70,
    ]

    return "\n".join(lines)


# Example usage
if __name__ == "__main__":
    print("=== Socratic Answer Evaluator Examples ===\n")

    examples = [
        {
            "response": "What do you mean by 'leadership' in your specific context?",
            "token_count": 12,
            "description": "Good Socratic question - concise, ends with question, probes definition"
        },
        {
            "response": "Leadership involves several key traits. First, you need vision - the ability to see where you want to go. Second, communication is crucial for conveying that vision. Third, empathy helps you connect with team members. Would you like me to elaborate on any of these?",
            "token_count": 58,
            "description": "Not Socratic - provides information, ends with procedural question"
        },
        {
            "response": "What assumptions are you making about what makes someone a good leader?",
            "token_count": 15,
            "description": "Excellent Socratic question - probes assumptions"
        },
        {
            "response": "Based on research in organizational psychology, effective leadership requires a combination of emotional intelligence, strategic thinking, and interpersonal skills. Studies have shown that leaders who score high on these dimensions tend to have more engaged teams and better business outcomes. The key is to develop these skills through deliberate practice and feedback. You might want to consider working with a coach or taking a leadership development course.",
            "token_count": 75,
            "description": "Very non-Socratic - pure information and advice, no question"
        }
    ]

    for i, example in enumerate(examples, 1):
        print(f"\n{'='*70}")
        print(f"EXAMPLE {i}: {example['description']}")
        print(f"{'='*70}")
        print(f"Response: \"{example['response']}\"")
        print(f"Token Count: {example['token_count']}")
        print()

        score = evaluate_socratic_answer(
            response=example["response"],
            token_count=example["token_count"]
        )

        print(format_score_report(score))
        print()
