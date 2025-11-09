"""
Socratic Evaluation Framework - Phase 1 Local Testing

This package provides tools for locally testing AI models' Socratic teaching abilities.
It's the predecessor to the serverless platform and is used for:
- Local development and testing
- Model comparison experiments
- Rapid prototyping of new scenarios
- Cost estimation before cloud deployment

Key Modules:
    vectors.py - Test scenario definitions (elenchus, maieutics, aporia)
    prompts.py - Prompt templates for tutor and judge
    bedrock_utils.py - AWS Bedrock invocation utilities
    run_vectors.py - CLI tool for running benchmarks
    grader.py - LLM-as-judge scoring (deprecated, use vector scoring)

Migration Note:
    This codebase has been largely superseded by serverless/lib/socratic_bench/
    which uses unified vector-based scoring instead of LLM-as-judge.

Usage:
    # Run local benchmark
    python -m socratic_eval.run_vectors --models anthropic.claude-3-5-sonnet...

    # Or use as library
    from socratic_eval.vectors import elenchus_scenarios
    from socratic_eval.prompts import socratic_tutor_prompt
"""

__version__ = "1.0.0"
