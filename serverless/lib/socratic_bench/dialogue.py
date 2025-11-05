"""
Dialogue runner - executes multi-turn Socratic conversations.
Used by both CLI and Lambda runner.
"""
from __future__ import annotations
import time
from typing import Dict, Any, List, Optional
from .models import ModelConfig, BedrockClient
from .prompts import socratic_tutor_prompt, socratic_tutor_followup_prompt
from .scenarios import Scenario


class DialogueTurn:
    """A single turn in a Socratic dialogue."""

    def __init__(
        self,
        turn_index: int,
        student_utterance: str,
        ai_response: str,
        latency_ms: float,
        input_tokens: int,
        output_tokens: int,
    ):
        self.turn_index = turn_index
        self.student_utterance = student_utterance
        self.ai_response = ai_response
        self.latency_ms = latency_ms
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens

    def to_dict(self) -> Dict[str, Any]:
        return {
            "turn_index": self.turn_index,
            "student": self.student_utterance,
            "ai": self.ai_response,
            "latency_ms": self.latency_ms,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
        }


class DialogueResult:
    """Complete dialogue run result."""

    def __init__(
        self,
        scenario: Scenario,
        model_config: ModelConfig,
        turns: List[DialogueTurn],
        total_duration_ms: float,
    ):
        self.scenario = scenario
        self.model_config = model_config
        self.turns = turns
        self.total_duration_ms = total_duration_ms

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scenario_id": self.scenario["id"],
            "vector": self.scenario["vector"],
            "persona": self.scenario["persona"],
            "model_id": self.model_config.model_id,
            "turns": [t.to_dict() for t in self.turns],
            "total_turns": len(self.turns),
            "total_duration_ms": self.total_duration_ms,
            "total_input_tokens": sum(t.input_tokens for t in self.turns),
            "total_output_tokens": sum(t.output_tokens for t in self.turns),
        }


def run_dialogue(
    scenario: Scenario,
    model_config: ModelConfig,
    max_turns: int = 5,
    bedrock_client: Optional[BedrockClient] = None,
    simulated_student_responses: Optional[List[str]] = None,
) -> DialogueResult:
    """
    Run a multi-turn Socratic dialogue.

    Args:
        scenario: The test scenario
        model_config: Model configuration
        max_turns: Maximum number of AI turns
        bedrock_client: Optional pre-configured client
        simulated_student_responses: For testing, provide canned student replies

    Returns:
        Complete dialogue result with all turns
    """
    if bedrock_client is None:
        bedrock_client = BedrockClient()

    t0 = time.time()
    turns: List[DialogueTurn] = []
    conversation_history: List[Dict[str, str]] = []

    # Initial student prompt from scenario
    student_utterance = scenario["prompt"]

    for turn_idx in range(max_turns):
        # Build prompt (first turn vs follow-up)
        if turn_idx == 0:
            prompt = socratic_tutor_prompt(
                scenario["vector"],
                scenario["persona"],
                student_utterance,
            )
        else:
            # Add previous turn to history
            conversation_history.append({"role": "student", "content": student_utterance})
            conversation_history.append({"role": "ai", "content": turns[-1].ai_response})

            prompt = socratic_tutor_followup_prompt(
                scenario["vector"],
                scenario["persona"],
                conversation_history + [{"role": "student", "content": student_utterance}],
            )

        # Get AI response
        response = bedrock_client.invoke(model_config, prompt)

        # Record turn
        turn = DialogueTurn(
            turn_index=turn_idx,
            student_utterance=student_utterance,
            ai_response=response["text"],
            latency_ms=response["latency_ms"],
            input_tokens=response["input_tokens"],
            output_tokens=response["output_tokens"],
        )
        turns.append(turn)

        # Get next student response
        if simulated_student_responses and turn_idx < len(simulated_student_responses):
            student_utterance = simulated_student_responses[turn_idx]
        else:
            # In production, this would come from a real student
            # For serverless benchmarking, we stop here
            break

    total_duration_ms = (time.time() - t0) * 1000

    return DialogueResult(
        scenario=scenario,
        model_config=model_config,
        turns=turns,
        total_duration_ms=total_duration_ms,
    )
