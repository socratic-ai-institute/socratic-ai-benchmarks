"""
Context Growth Evaluation Module

This module provides tools for evaluating how reasoning vs. non-reasoning models
perform in Socratic use cases as the context window grows.

Key components:
- disposition_rubric: Per-turn Socratic scoring (0-10 scale)
- test_scenarios: Five scenario types for testing Socratic persistence
- context_expander: Tools for gradually expanding context
- scorer: Overall metrics (Persistence, Cognitive Depth, etc.)
- runner: Main evaluation orchestrator
"""

from .disposition_rubric import (
    SocraticDispositionRubric,
    evaluate_response_disposition,
    DispositionScore
)
from .test_scenarios import (
    ConsistencyTest,
    ComplexityTest,
    AmbiguityTest,
    InterruptRedirectTest,
    ChainOfThoughtTest,
    get_all_test_scenarios
)
from .context_expander import ContextExpander
from .scorer import ContextGrowthScorer
from .runner import run_context_growth_evaluation

__all__ = [
    'SocraticDispositionRubric',
    'evaluate_response_disposition',
    'DispositionScore',
    'ConsistencyTest',
    'ComplexityTest',
    'AmbiguityTest',
    'InterruptRedirectTest',
    'ChainOfThoughtTest',
    'get_all_test_scenarios',
    'ContextExpander',
    'ContextGrowthScorer',
    'run_context_growth_evaluation'
]
