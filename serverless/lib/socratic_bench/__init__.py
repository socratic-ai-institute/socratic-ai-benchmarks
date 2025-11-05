"""
Socratic Benchmark Library

Shared core logic for CLI and serverless execution.
Provides dialogue running, turn judging, and scenario management.
"""

__version__ = "0.1.0"

from .dialogue import run_dialogue
from .judge import judge_turn
from .scenarios import get_scenario, list_scenarios
from .models import ModelConfig, BedrockClient

__all__ = [
    "run_dialogue",
    "judge_turn",
    "get_scenario",
    "list_scenarios",
    "ModelConfig",
    "BedrockClient",
]
