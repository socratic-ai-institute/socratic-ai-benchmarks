"""
Prompt templates for Socratic tutor and ASE judge.
Copied from phase1-model-selection/socratic_eval/prompts.py
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


def turn_judge_prompt(
    vector: str,
    persona: str,
    turn_index: int,
    student_utterance: str,
    ai_response: str,
) -> str:
    """
    Build a single-turn judge prompt for per-turn scoring.

    Args:
        vector: Test vector
        persona: Student persona
        turn_index: Turn number (0-indexed)
        student_utterance: What the student said
        ai_response: What the AI responded

    Returns:
        Judge prompt for this single turn
    """
    rubric = (
        "Socratic Dialogue (SD) Rubric — Score 1-5:\n"
        "1) Open-ended: Question cannot be answered with yes/no\n"
        "2) Probing depth: Targets assumptions or reasoning\n"
        "3) Non-directive: Doesn't lead to a specific answer\n"
        "4) Age-appropriate: Language fits the persona\n"
        "5) Content-relevant: Connects to the subject matter\n"
    )

    transcript = f"Turn {turn_index + 1}\nStudent: {student_utterance}\nAI: {ai_response}"

    return (
        "You are an expert evaluator of Socratic pedagogy.\n\n"
        f"Context:\n- Vector: {vector.upper()}\n- Persona: {persona}\n\n"
        f"{transcript}\n\n"
        f"{rubric}\n\n"
        "Task: Return strict JSON with keys: open_ended, probing_depth, non_directive, age_appropriate, content_relevant, overall.\n"
        "Each key should have: score (1-5 integer) and evidence (short quote from AI response).\n"
        "overall should be the average score rounded to one decimal.\n"
        "Return ONLY JSON."
    )
