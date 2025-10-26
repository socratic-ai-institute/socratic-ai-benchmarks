"""
Prompt builders for Socratic tutor (by vector) and ASE judge rubric prompts.
"""
from typing import Dict


def socratic_tutor_prompt(vector: str, persona: str, student_utterance: str) -> str:
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


def ase_judge_prompt(vector: str, persona: str, transcript: str) -> str:
    """
    Build the judge meta-prompt with the ASE rubric.

    NOTE: For safety and reproducibility, we ask for concise evidence quotes rather than free-form chain-of-thought.
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

