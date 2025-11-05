"""
Context Growth Evaluation Runner

Main orchestrator for running context-growth evaluations comparing
reasoning vs. non-reasoning models on Socratic use cases.

Usage:
    python -m socratic_eval.context_growth.runner --models claude-sonnet-4,claude-opus-4
"""

import json
import argparse
import time
from datetime import datetime
from typing import List, Dict, Optional
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .test_scenarios import get_all_test_scenarios, get_scenarios_by_type, TestScenario
from .disposition_rubric import SocraticDispositionRubric, DispositionScore
from .context_expander import ContextExpander
from .scorer import ContextGrowthScorer, TurnResult, OverallScore, compare_models

# Import Bedrock utilities from parent module
try:
    from ..grader import call_bedrock_model, AWS_PROFILE, AWS_REGION
except ImportError:
    print("Warning: Could not import Bedrock utilities. Using mock mode.")

    def call_bedrock_model(model_id, prompt, **kwargs):
        """Mock function for testing without AWS."""
        return "What do you mean by that? [MOCK RESPONSE]"

    AWS_PROFILE = "default"
    AWS_REGION = "us-east-1"


class ContextGrowthEvaluator:
    """
    Main evaluator for context growth testing.

    Runs test scenarios and collects results.
    """

    def __init__(
        self,
        model_ids: List[str],
        use_llm_judge: bool = False,
        mock_mode: bool = False
    ):
        """
        Args:
            model_ids: List of model IDs to evaluate
            use_llm_judge: Whether to use LLM for disposition scoring
            mock_mode: If True, don't call actual models (for testing)
        """
        self.model_ids = model_ids
        self.use_llm_judge = use_llm_judge
        self.mock_mode = mock_mode
        self.rubric = SocraticDispositionRubric(use_llm_judge=use_llm_judge)

    def run_scenario(
        self,
        model_id: str,
        scenario: TestScenario
    ) -> Dict[str, any]:
        """
        Run a single scenario for one model.

        Args:
            model_id: Model to evaluate
            scenario: Test scenario

        Returns:
            Results dict with scores and metadata
        """

        print(f"\n{'='*70}")
        print(f"Running: {scenario['name']}")
        print(f"Model:   {model_id}")
        print(f"Type:    {scenario['test_type']}")
        print(f"{'='*70}\n")

        # Initialize context expander
        expander = ContextExpander(strategy=scenario["context_growth_strategy"])

        # Initialize scorer
        scorer = ContextGrowthScorer()

        # Process each turn
        turn_results = []

        for i, turn in enumerate(scenario["conversation_turns"], 1):
            print(f"Turn {i}/{len(scenario['conversation_turns'])}: ", end="", flush=True)

            # Build prompt with current context
            full_prompt = expander.build_prompt(
                system_prompt=scenario["system_prompt"],
                include_history=True
            )

            # Add current user message to context
            expander.add_turn(
                user_message=turn["user_message"],
                distractor_text=turn.get("distractor_text")
            )

            # Get user message for this turn (with distractors if applicable)
            current_user_message = expander.conversation_history[-1]["user"]

            # Build full prompt with new turn
            full_prompt = expander.build_prompt(
                system_prompt=scenario["system_prompt"],
                include_history=False
            ) + f"\n\nUser: {current_user_message}\n\nAssistant:"

            # Call model
            if self.mock_mode:
                model_response = self._mock_response(turn["user_message"], i)
            else:
                model_response = self._call_model(model_id, full_prompt)

            print(f"✓ ({len(model_response)} chars)")

            # Update context with response
            expander.conversation_history[-1]["assistant"] = model_response

            # Score disposition
            disposition_score = self.rubric.evaluate(
                response=model_response,
                user_message=turn["user_message"]  # Use original message without distractors
            )

            # Get context stats
            context_stats = expander.get_context_stats()

            # Create turn result
            turn_result = TurnResult(
                turn_number=i,
                user_message=turn["user_message"],
                model_response=model_response,
                disposition_score=disposition_score,
                context_size_tokens=context_stats["estimated_tokens"],
                flagged_issues=disposition_score["flagged_issues"]
            )

            turn_results.append(turn_result)
            scorer.add_turn_result(turn_result)

            # Print turn score
            print(f"    Disposition: {disposition_score['total']}/10  ", end="")
            print(f"Context: ~{context_stats['estimated_tokens']} tokens")

            if disposition_score["flagged_issues"]:
                for issue in disposition_score["flagged_issues"]:
                    print(f"    ⚠️  {issue}")

        # Compute overall scores
        overall_score = scorer.compute_overall_score()

        print(f"\n{'-'*70}")
        print(f"SCENARIO COMPLETE")
        print(f"{'-'*70}")
        print(f"Overall Score:          {overall_score['overall']:.2f}/10")
        print(f"  Persistence:          {overall_score['persistence']:.2f}/10")
        print(f"  Cognitive Depth:      {overall_score['cognitive_depth']:.2f}/10")
        print(f"  Context Adaptability: {overall_score['context_adaptability']:.2f}/10")
        print(f"  Resistance to Drift:  {overall_score['resistance_to_drift']:.2f}/10")
        print(f"  Memory Preservation:  {overall_score['memory_preservation']:.2f}/10")

        result = {
            "scenario_id": scenario["id"],
            "scenario_name": scenario["name"],
            "test_type": scenario["test_type"],
            "model_id": model_id,
            "turn_results": [
                {
                    "turn_number": tr.turn_number,
                    "user_message": tr.user_message,
                    "model_response": tr.model_response,
                    "disposition_score": dict(tr.disposition_score),
                    "context_size_tokens": tr.context_size_tokens
                }
                for tr in turn_results
            ],
            "overall_score": dict(overall_score),
            "timestamp": datetime.now().isoformat()
        }

        # Include context_type if present (for fidelity tests)
        if "context_type" in scenario:
            result["context_type"] = scenario["context_type"]

        return result

    def _call_model(self, model_id: str, prompt: str) -> str:
        """Call Bedrock model with error handling."""

        try:
            response = call_bedrock_model(model_id, prompt, max_tokens=500)
            return response
        except Exception as e:
            print(f"\nError calling model: {e}")
            return f"[ERROR: {str(e)}]"

    def _mock_response(self, user_message: str, turn_number: int) -> str:
        """Generate mock response for testing."""

        # Simulate good Socratic responses that degrade over time
        if turn_number == 1:
            return "What do you mean by that term in your specific context?"
        elif turn_number == 2:
            return "What assumptions are you making about this situation?"
        elif turn_number == 3:
            return "Have you considered why this might be the case?"
        else:
            # Degrade to non-Socratic after turn 3
            return "That's a good question. Let me explain the key points you should consider..."

    def run_full_evaluation(
        self,
        scenarios: Optional[List[TestScenario]] = None,
        test_types: Optional[List[str]] = None
    ) -> Dict[str, any]:
        """
        Run full evaluation across multiple models and scenarios.

        Args:
            scenarios: Specific scenarios to run (if None, runs all)
            test_types: Filter by test types (if None, runs all types)

        Returns:
            Results dict with all evaluations
        """

        # Determine which scenarios to run
        if scenarios is None:
            if test_types:
                scenarios = []
                for test_type in test_types:
                    scenarios.extend(get_scenarios_by_type(test_type))
            else:
                scenarios = get_all_test_scenarios()

        print(f"\n{'='*70}")
        print(f"CONTEXT GROWTH EVALUATION")
        print(f"{'='*70}")
        print(f"Models:    {len(self.model_ids)}")
        print(f"Scenarios: {len(scenarios)}")
        print(f"Profile:   {AWS_PROFILE}")
        print(f"Region:    {AWS_REGION}")
        print(f"{'='*70}\n")

        results = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "models": self.model_ids,
                "num_scenarios": len(scenarios),
                "test_types": list(set(s["test_type"] for s in scenarios)),
                "aws_profile": AWS_PROFILE,
                "aws_region": AWS_REGION,
                "use_llm_judge": self.use_llm_judge,
                "mock_mode": self.mock_mode
            },
            "scenario_results": []
        }

        # Run each scenario for each model
        for scenario in scenarios:
            scenario_data = {
                "scenario_id": scenario["id"],
                "scenario_name": scenario["name"],
                "test_type": scenario["test_type"],
                "model_results": []
            }

            for model_id in self.model_ids:
                start_time = time.time()

                try:
                    result = self.run_scenario(model_id, scenario)
                    result["duration_seconds"] = time.time() - start_time
                    result["status"] = "success"
                except Exception as e:
                    result = {
                        "model_id": model_id,
                        "status": "error",
                        "error": str(e),
                        "duration_seconds": time.time() - start_time
                    }
                    print(f"\n❌ Error running scenario: {e}\n")

                scenario_data["model_results"].append(result)

            results["scenario_results"].append(scenario_data)

        # Compute aggregate statistics
        results["summary"] = self._compute_summary(results)

        return results

    def _compute_summary(self, results: Dict) -> Dict[str, any]:
        """Compute summary statistics across all scenarios."""

        summary = {
            "by_model": {},
            "by_test_type": {}
        }

        # Aggregate by model
        for model_id in self.model_ids:
            model_scores = []

            for scenario_result in results["scenario_results"]:
                for model_result in scenario_result["model_results"]:
                    if (model_result.get("model_id") == model_id and
                        model_result.get("status") == "success"):
                        model_scores.append(model_result["overall_score"])

            if model_scores:
                summary["by_model"][model_id] = self._aggregate_scores(model_scores)

        # Aggregate by test type
        test_types = set(s["test_type"] for s in results["scenario_results"])

        for test_type in test_types:
            type_scores = []

            for scenario_result in results["scenario_results"]:
                if scenario_result["test_type"] == test_type:
                    for model_result in scenario_result["model_results"]:
                        if model_result.get("status") == "success":
                            type_scores.append(model_result["overall_score"])

            if type_scores:
                summary["by_test_type"][test_type] = self._aggregate_scores(type_scores)

        return summary

    def _aggregate_scores(self, scores: List[Dict]) -> Dict[str, float]:
        """Aggregate multiple overall scores."""

        metrics = [
            "persistence",
            "cognitive_depth",
            "context_adaptability",
            "resistance_to_drift",
            "memory_preservation",
            "overall"
        ]

        aggregated = {}

        for metric in metrics:
            values = [s[metric] for s in scores if metric in s]
            if values:
                aggregated[f"{metric}_mean"] = round(sum(values) / len(values), 2)
                aggregated[f"{metric}_min"] = round(min(values), 2)
                aggregated[f"{metric}_max"] = round(max(values), 2)

        aggregated["num_scenarios"] = len(scores)

        return aggregated


def run_context_growth_evaluation(
    model_ids: List[str],
    output_file: Optional[str] = None,
    test_types: Optional[List[str]] = None,
    use_llm_judge: bool = False,
    mock_mode: bool = False
) -> Dict:
    """
    Main entry point for running context growth evaluation.

    Args:
        model_ids: List of model IDs to evaluate
        output_file: Path to save results JSON (if None, uses timestamp)
        test_types: Filter scenarios by type (if None, runs all)
        use_llm_judge: Whether to use LLM for disposition scoring
        mock_mode: If True, uses mock responses (for testing)

    Returns:
        Results dict
    """

    evaluator = ContextGrowthEvaluator(
        model_ids=model_ids,
        use_llm_judge=use_llm_judge,
        mock_mode=mock_mode
    )

    results = evaluator.run_full_evaluation(test_types=test_types)

    # Save results
    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"context_growth_results_{timestamp}.json"

    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n{'='*70}")
    print(f"Results saved to: {output_file}")
    print(f"{'='*70}\n")

    # Print summary
    print_summary(results)

    return results


def print_summary(results: Dict):
    """Print human-readable summary of results."""

    print("\n" + "="*70)
    print("EVALUATION SUMMARY")
    print("="*70)

    summary = results.get("summary", {})

    # Print by-model summary
    if "by_model" in summary:
        print("\nBY MODEL:")
        print("-"*70)

        for model_id, scores in summary["by_model"].items():
            print(f"\n{model_id}:")
            print(f"  Overall:              {scores.get('overall_mean', 0):.2f}/10")
            print(f"  Persistence:          {scores.get('persistence_mean', 0):.2f}/10")
            print(f"  Cognitive Depth:      {scores.get('cognitive_depth_mean', 0):.2f}/10")
            print(f"  Context Adaptability: {scores.get('context_adaptability_mean', 0):.2f}/10")
            print(f"  Resistance to Drift:  {scores.get('resistance_to_drift_mean', 0):.2f}/10")
            print(f"  Memory Preservation:  {scores.get('memory_preservation_mean', 0):.2f}/10")
            print(f"  Scenarios:            {scores.get('num_scenarios', 0)}")

    # Print by-test-type summary
    if "by_test_type" in summary:
        print("\n\nBY TEST TYPE:")
        print("-"*70)

        for test_type, scores in summary["by_test_type"].items():
            print(f"\n{test_type.upper()}:")
            print(f"  Overall:              {scores.get('overall_mean', 0):.2f}/10")
            print(f"  Scenarios:            {scores.get('num_scenarios', 0)}")

    print("\n" + "="*70 + "\n")


def main():
    """CLI entry point."""

    parser = argparse.ArgumentParser(
        description="Run context growth evaluation for Socratic AI models"
    )

    parser.add_argument(
        "--models",
        type=str,
        required=True,
        help="Comma-separated list of model IDs to evaluate"
    )

    parser.add_argument(
        "--test-types",
        type=str,
        default=None,
        help="Comma-separated list of test types to run (consistency,complexity,ambiguity,interrupt_redirect,chain_of_thought)"
    )

    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output file path (default: context_growth_results_TIMESTAMP.json)"
    )

    parser.add_argument(
        "--use-llm-judge",
        action="store_true",
        help="Use LLM for disposition scoring (slower, more nuanced)"
    )

    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use mock mode for testing (doesn't call real models)"
    )

    args = parser.parse_args()

    # Parse model IDs
    model_ids = [m.strip() for m in args.models.split(",")]

    # Parse test types
    test_types = None
    if args.test_types:
        test_types = [t.strip() for t in args.test_types.split(",")]

    # Run evaluation
    run_context_growth_evaluation(
        model_ids=model_ids,
        output_file=args.output,
        test_types=test_types,
        use_llm_judge=args.use_llm_judge,
        mock_mode=args.mock
    )


if __name__ == "__main__":
    main()
