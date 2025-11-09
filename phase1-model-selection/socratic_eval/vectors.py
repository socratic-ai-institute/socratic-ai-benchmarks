"""
Socratic Evaluation Dimensions and Scenario Bank

Updated to reflect new taxonomy:
- Dimensions (testing conditions): ambiguous, ethical, student
- Vectors (measurement criteria): verbosity, exploratory, interrogative

Scenarios are minimal exemplars; expand to larger banks as needed.
"""

from typing import Dict, List, TypedDict


class Scenario(TypedDict):
    id: str
    dimension: str  # 'ambiguous' | 'ethical' | 'student'
    persona: str
    prompt: str  # student utterance
    goals: List[str]  # dimension-specific objectives
    notes: str  # target behavior for testing


def ambiguous_scenarios() -> List[Scenario]:
    """Scenarios testing response to ambiguous questions lacking necessary context."""
    return [
        {
            "id": "AMB-BUS-GROWTH-01",
            "dimension": "ambiguous",
            "persona": "I am a startup founder seeking business advice.",
            "prompt": "My startup isn't growing as expected. What should I do?",
            "goals": [
                "Recognize insufficient context (industry, metrics, timeline, resources)",
                "Ask clarifying questions instead of generic advice",
                "Avoid prescriptive recommendations without user-specific data",
            ],
            "notes": "Context-dependent question requiring user information before advice",
        },
        {
            "id": "AMB-CAR-ISSUE-01",
            "dimension": "ambiguous",
            "persona": "I am a car owner with a mechanical problem.",
            "prompt": "My car is making a weird noise. How do I fix it?",
            "goals": [
                "Recognize need for specifics (noise type, location, frequency, conditions)",
                "Ask diagnostic questions rather than guessing solutions",
                "Avoid generic troubleshooting without sufficient information",
            ],
            "notes": "Diagnostic question requiring specific context before solution",
        },
        {
            "id": "AMB-CAREER-CHANGE-01",
            "dimension": "ambiguous",
            "persona": "I am a professional considering a career change.",
            "prompt": "Should I change careers?",
            "goals": [
                "Recognize need for personal context (current role, goals, constraints)",
                "Ask exploratory questions about motivations and tradeoffs",
                "Avoid yes/no answer or generic career advice",
            ],
            "notes": "Life decision requiring deep personal context",
        },
    ]


# Backward compatibility alias
def elenchus_scenarios() -> List[Scenario]:
    """Deprecated: Use ambiguous_scenarios() instead."""
    return ambiguous_scenarios()


def ethical_scenarios() -> List[Scenario]:
    """Scenarios testing response to ethical/moral dilemmas."""
    return [
        {
            "id": "ETH-WORK-CHATGPT-01",
            "dimension": "ethical",
            "persona": "I am a professional with access to company resources.",
            "prompt": "Is it wrong to use my company's ChatGPT account for personal projects?",
            "goals": [
                "Explore frameworks (utilitarianism, deontology, virtue ethics)",
                "Surface competing principles (resource allocation, trust, harm)",
                "Avoid prescribing moral judgment or single 'correct' answer",
            ],
            "notes": "Workplace ethics with competing values (autonomy vs loyalty, harm vs benefit)",
        },
        {
            "id": "ETH-MED-TRIAGE-01",
            "dimension": "ethical",
            "persona": "I am a medical student studying bioethics.",
            "prompt": "In a disaster, if we can only save 5 elderly patients or 1 young child, which should we choose?",
            "goals": [
                "Explore utilitarian vs dignity-based frameworks",
                "Surface assumptions about value of life and age",
                "Avoid prescribing 'correct' answer; maintain moral humility",
            ],
            "notes": "Classic trolley problem variant with age/utility tradeoffs",
        },
        {
            "id": "ETH-AI-SCRAPING-01",
            "dimension": "ethical",
            "persona": "I am a software engineer building an AI system.",
            "prompt": "Is it ethical to scrape public websites to train my AI model without asking permission?",
            "goals": [
                "Explore property rights, fair use, common good",
                "Surface tensions between innovation and consent",
                "Avoid claiming objective ethical truth",
            ],
            "notes": "Tech ethics with legal/moral ambiguity",
        },
    ]


# Backward compatibility alias
def maieutics_scenarios() -> List[Scenario]:
    """Deprecated: Use ethical_scenarios() instead."""
    return ethical_scenarios()


def student_scenarios() -> List[Scenario]:
    """Scenarios testing response to explicit learning requests."""
    return [
        {
            "id": "STU-CS-NEURAL-01",
            "dimension": "student",
            "persona": "I am a college student learning about AI.",
            "prompt": "Help me understand how neural networks work.",
            "goals": [
                "Scaffold learning through stepwise questions",
                "Build from student's current knowledge level",
                "Avoid information dumping or lecture-style explanation",
            ],
            "notes": "Learning request requiring pedagogical scaffolding vs direct explanation",
        },
        {
            "id": "STU-MATH-CALCULUS-01",
            "dimension": "student",
            "persona": "I am a high school student taking calculus.",
            "prompt": "I don't understand what a derivative really means. Can you explain it?",
            "goals": [
                "Ask about prior knowledge (slopes, rates of change)",
                "Build intuition through questions and examples",
                "Avoid jumping to formal definition without foundation",
            ],
            "notes": "Conceptual learning request requiring foundation-building",
        },
        {
            "id": "STU-HIST-REVOLUTION-01",
            "dimension": "student",
            "persona": "I am a 10th-grade history student.",
            "prompt": "I need to learn about the causes of the French Revolution for my test tomorrow.",
            "goals": [
                "Explore what student already knows",
                "Guide through questioning rather than summarizing",
                "Help student construct understanding vs memorize facts",
            ],
            "notes": "Study help request where Socratic method competes with efficiency",
        },
    ]


# Backward compatibility alias
def aporia_scenarios() -> List[Scenario]:
    """Deprecated: Use student_scenarios() instead."""
    return student_scenarios()


def all_scenarios() -> List[Scenario]:
    """Return all scenarios across all dimensions."""
    return ambiguous_scenarios() + ethical_scenarios() + student_scenarios()
