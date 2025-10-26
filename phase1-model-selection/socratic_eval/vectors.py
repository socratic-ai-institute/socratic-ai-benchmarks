"""
Socratic Evaluation Vectors and Scenario Bank

Implements three orthogonal test vectors:
- Elenchus (refutation)
- Maieutics (scaffolding)
- Aporia challenge (misconception deconstruction + rebuild)

Scenarios are minimal exemplars; expand to larger banks as needed.
"""
from typing import Dict, List, TypedDict


class Scenario(TypedDict):
    id: str
    vector: str  # 'elenchus' | 'maieutics' | 'aporia'
    persona: str
    prompt: str  # student utterance
    goals: List[str]  # vector-specific objectives
    notes: str  # target contradiction/misconception/scaffold levels


def elenchus_scenarios() -> List[Scenario]:
    return [
        {
            "id": "EL-ETH-UTIL-DEON-01",
            "vector": "elenchus",
            "persona": "I am an 11th-grade student in an ethics class.",
            "prompt": (
                "I believe in 100% utilitarianism—the greatest good for the greatest number is the only moral rule that matters. "
                "Following this, I've concluded that it is not just permissible but morally required for a doctor to sacrifice one healthy person to harvest their organs if it can save five other people."
            ),
            "goals": [
                "Probe the internal contradiction/value conflict using the student's own stated logic",
                "Do not provide answers; stay non-directive",
            ],
            "notes": "Utilitarian absolutism vs rights/deontology conflict",
        },
        {
            "id": "EL-CIV-FREE-HARM-01",
            "vector": "elenchus",
            "persona": "I am a 10th-grade student in a civics class.",
            "prompt": (
                "I'm a total absolutist on free speech; I believe everyone has the right to say anything they want, no exceptions. "
                "But, I also think people who post hateful, offensive things online that really hurt people's feelings should be arrested and have their accounts deleted."
            ),
            "goals": [
                "Surface the contradiction without lecturing",
                "Force the student to examine how both claims can be true simultaneously",
            ],
            "notes": "Free speech absolutism vs harm/punishment contradiction",
        },
    ]


def maieutics_scenarios() -> List[Scenario]:
    return [
        {
            "id": "MAI-BIO-CRISPR-01",
            "vector": "maieutics",
            "persona": "I'm a 12th-grade AP Biology student.",
            "prompt": (
                "I get the basics of CRISPR. I know that the Cas9 enzyme is like 'molecular scissors' that can cut DNA. "
                "But how does it know where to cut? The genome is huge."
            ),
            "goals": [
                "Guide student to discover guide RNA (gRNA) role",
                "Then introduce/lead to PAM concept (Level 3)",
            ],
            "notes": "Level progression: Cas9 → gRNA → PAM",
        },
        {
            "id": "MAI-ECO-INFL-01",
            "vector": "maieutics",
            "persona": "I'm an 11th-grade economics student.",
            "prompt": (
                "I understand that inflation means prices are going up. And I think it's because the government just prints too much money."
            ),
            "goals": [
                "Expand to demand-pull and cost-push",
                "Introduce expectations and wage-price spiral",
            ],
            "notes": "Level progression: Monetarist seed → multi-factor inflation",
        },
    ]


def aporia_scenarios() -> List[Scenario]:
    return [
        {
            "id": "APO-PHY-HEAT-TEMP-01",
            "vector": "aporia",
            "persona": "I'm a 10th-grade physics student.",
            "prompt": (
                "We're learning about heat. My idea is that to make my soup heat up faster, I should use a metal spoon to stir it, because metal gets hotter than the soup. "
                "My plastic spoon doesn't get as hot, so it doesn't transfer as much heat."
            ),
            "goals": [
                "Expose confusion between heat and temperature",
                "Correct misconceptions about conduction (without lecturing)",
                "Induce productive puzzlement then rebuild",
            ],
            "notes": "Ontological misconception: heat-as-substance; conduction",
        },
        {
            "id": "APO-BIO-GENE-DETERM-01",
            "vector": "aporia",
            "persona": "I'm a 12th-grade student.",
            "prompt": (
                "My idea for a science project is to make humans more drought-resistant. I read that camels have a gene that lets them store water, "
                "so I'd just use genetic engineering to take that one gene from a camel and put it into a person."
            ),
            "goals": [
                "Challenge one-gene/one-trait determinism",
                "Surface regulation/polygenic expression",
                "Aporia then scaffold toward accurate model",
            ],
            "notes": "Determinism and gene regulation misconceptions",
        },
        {
            "id": "APO-BIO-EVOL-LAM-01",
            "vector": "aporia",
            "persona": "I'm an 11th-grade biology student.",
            "prompt": (
                "I'm confused about evolution. It seems like giraffes needed longer necks to reach the high leaves, so they stretched their necks, and their children were born with longer necks, right? The need must have driven the change."
            ),
            "goals": [
                "Expose inheritance-of-acquired-traits flaw",
                "Lead to random variation and selection",
            ],
            "notes": "Teleology/Lamarckian misconception",
        },
        {
            "id": "APO-PHY-QUANT-OBS-01",
            "vector": "aporia",
            "persona": "I'm a 12th-grade student.",
            "prompt": (
                "I'm stuck on the double-slit experiment. It's bizarre. My idea is that the particle must 'know' we are watching it, so it decides to stop being a wave and act like a particle."
            ),
            "goals": [
                "Remove anthropomorphic explanation",
                "Differentiate observation vs measurement interaction",
            ],
            "notes": "Observer anthropomorphism",
        },
    ]


def all_scenarios() -> List[Scenario]:
    return elenchus_scenarios() + maieutics_scenarios() + aporia_scenarios()

