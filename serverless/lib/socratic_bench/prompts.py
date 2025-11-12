"""
Prompt templates for Socratic tutor and ASE judge.
Copied from phase1-model-selection/socratic_eval/prompts.py

Updated 2025-11-08: Changed to 0-100 scoring scale with mandatory explanations.
"""


def socratic_tutor_prompt(vector: str, persona: str, student_utterance: str) -> str:
    """
    Build a Socratic tutor prompt for a given vector and student input.

    Args:
        vector: 'elenchus', 'maieutics', or 'aporia'
        persona: Student persona/context
        student_utterance: What the student just said

    Returns:
        Complete prompt for the tutor model
    """
    role = (
        "You are a Socratic facilitator. Ask only open-ended, probing questions. Do not lecture. Do not provide answers. "
        "Use the student's own words to surface assumptions. Keep language age-appropriate and concise."
    )

    if vector == "elenchus":
        objective = (
            "Objective: Elicit and probe contradictions in the student's stated belief using their own logic. "
            "Do not resolve the contradiction for them."
        )
    elif vector == "maieutics":
        objective = (
            "Objective: Scaffold from the student's correct Level-1 understanding to deeper levels by asking stepwise questions. "
            "Avoid information dumps; introduce one idea per question."
        )
    else:  # aporia
        objective = (
            "Objective: Deconstruct a deep misconception, guide the student into productive puzzlement (aporia), then begin rebuilding with questions. "
            "Stay non-directive; never substitute your explanation for their thinking."
        )

    return (
        f"{role}\n\nVector: {vector.upper()}\n{objective}\n\n"
        f"Persona: {persona}\n"
        f"Student: {student_utterance}\n\n"
        "Your response: Ask 1-2 Socratic questions only (no explanations, no answers)."
    )


def socratic_tutor_followup_prompt(
    vector: str,
    persona: str,
    conversation_history: list[dict[str, str]],
) -> str:
    """
    Build a follow-up Socratic tutor prompt with conversation history.

    Args:
        vector: 'elenchus', 'maieutics', or 'aporia'
        persona: Student persona/context
        conversation_history: List of {"role": "student"|"ai", "content": str}

    Returns:
        Complete prompt including conversation context
    """
    role = (
        "You are a Socratic facilitator. Ask only open-ended, probing questions. Do not lecture. Do not provide answers. "
        "Use the student's own words to surface assumptions. Keep language age-appropriate and concise."
    )

    if vector == "elenchus":
        objective = (
            "Objective: Elicit and probe contradictions in the student's stated belief using their own logic. "
            "Do not resolve the contradiction for them."
        )
    elif vector == "maieutics":
        objective = (
            "Objective: Scaffold from the student's correct Level-1 understanding to deeper levels by asking stepwise questions. "
            "Avoid information dumps; introduce one idea per question."
        )
    else:  # aporia
        objective = (
            "Objective: Deconstruct a deep misconception, guide the student into productive puzzlement (aporia), then begin rebuilding with questions. "
            "Stay non-directive; never substitute your explanation for their thinking."
        )

    # Format conversation history
    history_lines = []
    for turn in conversation_history:
        prefix = "Student" if turn["role"] == "student" else "AI"
        history_lines.append(f"{prefix}: {turn['content']}")

    history_text = "\n".join(history_lines)

    return (
        f"{role}\n\nVector: {vector.upper()}\n{objective}\n\n"
        f"Persona: {persona}\n\n"
        f"Conversation so far:\n{history_text}\n\n"
        "Your response: Ask 1-2 Socratic questions only (no explanations, no answers)."
    )


def ase_judge_prompt(vector: str, persona: str, transcript: str) -> str:
    """
    Build the ASE (Automated Socratic Evaluation) judge prompt.

    Args:
        vector: Test vector ('elenchus', 'maieutics', 'aporia')
        persona: Student persona
        transcript: Full conversation transcript

    Returns:
        Judge prompt requesting structured JSON evaluation
    """
    rubric = (
        "Automated Socratic Evaluation (ASE) Rubric — Score each 1-5:\n"
        "1) Pedagogical Stance: Non-directive, probing, no lecturing.\n"
        "2) Conceptual Fidelity: Targets the correct underlying flaw/truth.\n"
        "3) Persona Adaptation: Age-appropriate language; stepwise scaffolding.\n"
        "4) Dialectical Progress: Achieves the vector goal (Elenchus / Maieutics / Aporia).\n"
    )

    return (
        "You are an expert evaluator of Socratic pedagogy acting as an automated judge.\n\n"
        f"Context:\n- Test Vector Objective: {vector.upper()}\n- Student Persona: {persona}\n\n"
        f"Transcript (Student ↔ AI):\n{transcript}\n\n"
        f"Rubric:\n{rubric}\n"
        "Task: Return strict JSON with keys: ped_stance, concept_fidelity, persona_adapt, dialectical_progress, overall, and for each key a short 'evidence' list with 1-2 quoted snippets.\n"
        "Scoring: Use integers 1-5. overall is the average rounded to one decimal.\n"
        "Return ONLY JSON."
    )


def socratic_question_judge_prompt(ai_response: str) -> str:
    """
    Judge if the AI response ends with a Socratic question.

    Returns prompt for LLM to evaluate boolean: does it end with a Socratic question?
    """
    return f"""You are evaluating if an AI tutor's response ends with a Socratic question.

AI Response:
{ai_response}

A Socratic question:
- Genuinely probes the student's thinking, assumptions, or reasoning
- Invites explanation, reflection, or exploration
- Does NOT seek yes/no confirmation to proceed (e.g., "Does that make sense?" "Ready to continue?")
- Does NOT provide answers disguised as questions (e.g., "Isn't it true that X?")

Task: Does this response END with a Socratic question?

Return ONLY a JSON object with this exact format:
{{
  "ends_with_socratic_question": true or false,
  "explanation": "1-2 sentence justification"
}}"""


def directionally_socratic_judge_prompt(ai_response: str, scenario_context: str = "") -> str:
    """
    Judge how directionally Socratic the entire response is (0.00-1.00).

    Returns prompt for LLM to score how well the response guides toward introspection vs lecturing.
    """
    context_section = f"\n\nContext: {scenario_context}\n" if scenario_context else ""

    return f"""You are a STRICT evaluator of Socratic pedagogy. Be highly critical and discriminating.

AI Response:
{ai_response}{context_section}

Socratic pedagogy GUIDES students to discover insights through their own reasoning.
It does NOT lecture, provide answers, or information-dump.

Scoring Scale (0.00-1.00) - BE STRICT:
- 1.00 = Purely Socratic: ONLY probing questions, ZERO context-setting, ZERO information given
- 0.80-0.99 = Mostly Socratic: Primarily questions with MINIMAL framing (1 brief phrase max)
- 0.60-0.79 = Somewhat Socratic: Questions present but includes hints, explanations, or multiple context phrases
- 0.40-0.59 = Mixed: Equal parts questioning and teaching
- 0.20-0.39 = Mostly Didactic: Primarily teaching/explaining with token questions
- 0.00-0.19 = Purely Didactic: Lectures, answers directly, no meaningful questions

STRICT Criteria for HIGH scores (0.80+):
- Questions that probe assumptions, reasoning, or mental models
- Reflects student's words back to them for examination
- Builds on student's existing knowledge
- ZERO information, facts, or explanations provided
- No more than ONE brief framing phrase (5 words max)

AUTOMATIC penalties:
- Any explanation or fact given: -0.20 minimum
- Multiple context-setting phrases: -0.15
- Rhetorical questions: -0.10
- Leading questions that imply answers: -0.15

Task: Rate how directionally Socratic this response is. BE CRITICAL AND STRICT.

Return ONLY a JSON object with this exact format:
{{
  "directionally_socratic": 0.65,
  "explanation": "2-3 sentences analyzing the Socratic quality and identifying any didactic elements"
}}"""
