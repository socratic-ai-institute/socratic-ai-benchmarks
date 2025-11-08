"""
Socratic Benchmark Library

Shared core logic for CLI and serverless execution.
Provides dialogue running, turn judging, and scenario management.
"""

__version__ = "0.2.0"

from .dialogue import run_dialogue
from .judge import judge_turn, compute_heuristic_scores
from .scenarios import get_scenario, list_scenarios
from .models import ModelConfig, BedrockClient
from .cost_tracker import calculate_cost, aggregate_costs, format_cost_summary

__all__ = [
    "run_dialogue",
    "judge_turn",
    "compute_heuristic_scores",
    "get_scenario",
    "list_scenarios",
    "ModelConfig",
    "BedrockClient",
    "calculate_cost",
    "aggregate_costs",
    "format_cost_summary",
]
