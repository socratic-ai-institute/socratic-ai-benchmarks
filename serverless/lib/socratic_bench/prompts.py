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
        "Socratic Dialogue Rubric — Score 0-100. Be discriminating.\n\n"
        "1) Open-ended (0-100):\n"
        "   90-100 = Purely open question inviting explanation (e.g., 'What makes you think...?')\n"
        "   70-89 = Open with minor leading phrasing\n"
        "   50-69 = Somewhat open but constrains answer space\n"
        "   30-49 = Binary question with elaboration prompt (e.g., 'Is X true? Why?')\n"
        "   0-29 = Pure yes/no or closed question\n\n"
        "2) Probing depth (0-100):\n"
        "   90-100 = Targets core assumption or hidden premise\n"
        "   70-89 = Probes reasoning but misses deepest layer\n"
        "   50-69 = Asks for clarification of stated position\n"
        "   30-49 = Surface-level follow-up\n"
        "   0-29 = No probing; mere acknowledgment\n\n"
        "3) Non-directive (0-100):\n"
        "   90-100 = Pure question with zero hinting at answer\n"
        "   70-89 = Question with subtle framing\n"
        "   50-69 = Question plus context that narrows thinking\n"
        "   30-49 = Leading question that implies correct answer\n"
        "   0-29 = Tells answer directly or lectures\n\n"
        "4) Age-appropriate (0-100):\n"
        "   90-100 = Perfect match to persona's level and language\n"
        "   70-89 = Mostly appropriate with minor complexity issues\n"
        "   50-69 = Somewhat mismatched (too simple or too complex)\n"
        "   30-49 = Clearly inappropriate for persona\n"
        "   0-29 = Completely wrong level\n\n"
        "5) Content-relevant (0-100):\n"
        "   90-100 = Directly addresses core subject matter\n"
        "   70-89 = Relevant but slightly tangential\n"
        "   50-69 = Loosely connected\n"
        "   30-49 = Barely related\n"
        "   0-29 = Off-topic\n\n"
        "IMPORTANT: Most responses should score 40-80. Reserve 90+ for truly exemplary Socratic questioning. "
        "Use 0-30 for poor responses. Be critical and discriminating."
    )

    transcript = f"Turn {turn_index + 1}\nStudent: {student_utterance}\nAI: {ai_response}"

    return (
        "You are a strict evaluator of Socratic pedagogy. Grade harshly but fairly.\n\n"
        f"Context:\n- Vector: {vector.upper()}\n- Persona: {persona}\n\n"
        f"{transcript}\n\n"
        f"{rubric}\n\n"
        "Task: For each dimension, FIRST write an 'explanation' (2-3 sentences analyzing the response quality), "
        "THEN assign a 'score' (0-100 integer), THEN provide 'evidence' (short quote from AI response).\n\n"
        "Return strict JSON with keys: open_ended, probing_depth, non_directive, age_appropriate, content_relevant, overall.\n"
        "Each key should have: explanation (string), score (0-100 integer), evidence (string).\n"
        "overall should be the average score rounded to one decimal, with explanation summarizing overall performance.\n\n"
        "BE DISCRIMINATING. Use the full 0-100 range. Most responses should be 40-80, not 90+.\n"
        "Return ONLY JSON."
    )
