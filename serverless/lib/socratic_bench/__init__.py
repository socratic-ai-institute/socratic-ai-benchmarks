"""
Socratic Benchmark Library

Shared core logic for CLI and serverless execution of Socratic AI benchmarks.

This library provides the fundamental building blocks for running and evaluating
Socratic dialogues with AI models. It abstracts away infrastructure differences
between local CLI execution and serverless AWS Lambda deployment.

Core Capabilities:
    - Dialogue execution with multi-turn conversation management
    - Vector-based scoring for Socratic quality assessment
    - Test scenario management (elenchus, maieutics, aporia)
    - Multi-provider LLM support via AWS Bedrock
    - Comprehensive prompt engineering for Socratic pedagogy

Module Organization:
    dialogue.py - Multi-turn dialogue runner with token tracking
    judge.py - Vector-based scoring system (verbosity, exploratory, interrogative)
    scenarios.py - Test scenario definitions and management
    models.py - Bedrock client with multi-provider support
    prompts.py - Prompt templates for tutor and judge

Version History:
    0.2.0 - Unified vector-based scoring system
    0.1.0 - Initial release with heuristic scoring
"""

__version__ = "0.2.0"

# Core dialogue and scoring functionality
from .dialogue import run_dialogue
from .judge import compute_heuristic_scores, compute_vector_scores

# Scenario management
from .scenarios import get_scenario, list_scenarios

# Model configuration and Bedrock client
from .models import ModelConfig, BedrockClient

# Note: cost_tracker module is planned but not yet implemented
# from .cost_tracker import calculate_cost, aggregate_costs, format_cost_summary

__all__ = [
    # Dialogue execution
    "run_dialogue",

    # Scoring functions
    "compute_heuristic_scores",
    "compute_vector_scores",

    # Scenario management
    "get_scenario",
    "list_scenarios",

    # Model configuration
    "ModelConfig",
    "BedrockClient",

    # Cost tracking (planned)
    # "calculate_cost",
    # "aggregate_costs",
    # "format_cost_summary",
]
