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
    - Multi-provider LLM support via AWS Bedrock and Google API
    - Comprehensive prompt engineering for Socratic pedagogy

Module Organization:
    dialogue.py - Multi-turn dialogue runner with token tracking
    judge.py - Legacy vector-based scoring (verbosity, exploratory, interrogative)
    judge_v2.py - NEW LLM-based judge (token_count, ends_with_socratic_question, directionally_socratic)
    scenarios.py - Test scenario definitions and management
    models.py - Client router supporting Bedrock and Google API providers
    google_client.py - Google Generative AI API client for Gemini models
    prompts.py - Prompt templates for tutor and judge

Version History:
    0.4.0 - Multi-backend support: AWS Bedrock + Google Generative AI
    0.3.0 - LLM-based judge system with penalty-based composite scoring
    0.2.0 - Unified vector-based scoring system
    0.1.0 - Initial release with heuristic scoring
"""

__version__ = "0.4.0"

# Core dialogue and scoring functionality
from .dialogue import run_dialogue
from .judge import compute_heuristic_scores, compute_vector_scores

# New LLM-based judge system (v2)
from .judge_v2 import judge_with_llm, JudgeResult, compute_overall_score

# Scenario management
from .scenarios import get_scenario, list_scenarios

# Model configuration and client support
from .models import ModelConfig, BedrockClient

# Google Generative AI support (optional)
try:
    from .google_client import GoogleClient, GoogleModelConfig
except ImportError:
    GoogleClient = None
    GoogleModelConfig = None

# Note: cost_tracker module is planned but not yet implemented
# from .cost_tracker import calculate_cost, aggregate_costs, format_cost_summary

__all__ = [
    # Dialogue execution
    "run_dialogue",

    # Scoring functions (legacy)
    "compute_heuristic_scores",
    "compute_vector_scores",

    # LLM-based judge system (v2)
    "judge_with_llm",
    "JudgeResult",
    "compute_overall_score",

    # Scenario management
    "get_scenario",
    "list_scenarios",

    # Model configuration and clients
    "ModelConfig",
    "BedrockClient",
    "GoogleClient",
    "GoogleModelConfig",

    # Cost tracking (planned)
    # "calculate_cost",
    # "aggregate_costs",
    # "format_cost_summary",
]
