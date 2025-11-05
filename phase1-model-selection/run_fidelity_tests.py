#!/usr/bin/env python3
"""
Run Fidelity Tests - Context-Based Socratic Disposition Testing

This script demonstrates how to run fidelity tests that stress-test
Socratic disposition across different contexts where models have strong
instincts to provide direct answers.

Usage Examples:

    # Run all fidelity tests on Claude Sonnet
    python run_fidelity_tests.py --models anthropic.claude-3-5-sonnet-20241022-v2:0

    # Run only knowledge-heavy context tests
    python run_fidelity_tests.py --context-type knowledge_heavy

    # Run multiple models in parallel
    python run_fidelity_tests.py --models claude-3-sonnet,claude-3-opus

    # Run specific contexts
    python run_fidelity_tests.py --context-type emotional,technical_debugging

    # Use LLM-as-judge for scoring (more accurate but slower)
    python run_fidelity_tests.py --use-llm-judge

    # Mock mode for testing without AWS credentials
    python run_fidelity_tests.py --mock-mode
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

# Add module to path
sys.path.insert(0, str(Path(__file__).parent))

from socratic_eval.context_growth.test_scenarios import (
    get_all_test_scenarios,
    get_scenarios_by_context_type,
)
from socratic_eval.context_growth.fidelity_tests import get_all_fidelity_scenarios
from socratic_eval.context_growth.runner import ContextGrowthEvaluator
from socratic_eval.context_growth.generate_dashboard import generate_html_dashboard


CONTEXT_TYPES = [
    "knowledge_heavy",
    "technical_debugging",
    "instruction_override",
    "emotional",
    "creative_writing",
]


def run_fidelity_evaluation(
    model_ids: List[str],
    context_types: Optional[List[str]] = None,
    use_llm_judge: bool = False,
    mock_mode: bool = False,
    output_dir: str = "fidelity_results"
):
    """
    Run fidelity tests and generate results.

    Args:
        model_ids: List of model IDs to test
        context_types: List of context types to test (None = all)
        use_llm_judge: Whether to use LLM for scoring
        mock_mode: Whether to use mock responses
        output_dir: Directory to save results
    """

    print("=" * 80)
    print("SOCRATIC FIDELITY EVALUATION")
    print("=" * 80)
    print(f"\nTimestamp: {datetime.now().isoformat()}")
    print(f"Models: {', '.join(model_ids)}")
    print(f"Context Types: {context_types or 'ALL'}")
    print(f"LLM Judge: {use_llm_judge}")
    print(f"Mock Mode: {mock_mode}")
    print(f"Output Directory: {output_dir}")
    print()

    # Get scenarios
    if context_types:
        scenarios = []
        for context_type in context_types:
            scenarios.extend(get_scenarios_by_context_type(context_type))
    else:
        scenarios = get_all_fidelity_scenarios()

    print(f"Total scenarios: {len(scenarios)}\n")

    # Initialize evaluator
    evaluator = ContextGrowthEvaluator(
        model_ids=model_ids,
        use_llm_judge=use_llm_judge,
        mock_mode=mock_mode
    )

    # Run evaluation
    all_results = {}

    for model_id in model_ids:
        print(f"\n{'#' * 80}")
        print(f"# MODEL: {model_id}")
        print(f"{'#' * 80}\n")

        model_results = []

        for scenario in scenarios:
            try:
                result = evaluator.run_scenario(model_id, scenario)
                model_results.append(result)
            except Exception as e:
                print(f"ERROR running {scenario['id']}: {e}")
                continue

        all_results[model_id] = model_results

    # Save results
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = output_path / f"fidelity_results_{timestamp}.json"

    with open(results_file, 'w') as f:
        json.dump(all_results, f, indent=2)

    print(f"\n{'=' * 80}")
    print(f"Results saved to: {results_file}")
    print(f"{'=' * 80}\n")

    # Generate summary
    print_summary(all_results)

    # Generate dashboard if multiple models
    if len(model_ids) > 1:
        dashboard_file = output_path / f"fidelity_dashboard_{timestamp}.html"
        try:
            generate_html_dashboard(all_results, str(dashboard_file))
            print(f"\nDashboard generated: {dashboard_file}")
        except Exception as e:
            print(f"\nWarning: Could not generate dashboard: {e}")

    return all_results


def print_summary(results: dict):
    """Print summary of results."""

    print("\n" + "=" * 80)
    print("SUMMARY BY CONTEXT TYPE")
    print("=" * 80 + "\n")

    for model_id, model_results in results.items():
        print(f"\nModel: {model_id}")
        print("-" * 80)

        # Group by context type
        by_context = {}
        for result in model_results:
            context_type = result.get("context_type", "unknown")
            if context_type not in by_context:
                by_context[context_type] = []
            by_context[context_type].append(result)

        # Print stats for each context
        for context_type, context_results in sorted(by_context.items()):
            avg_score = sum(r["overall_score"]["overall"] for r in context_results) / len(context_results)

            print(f"\n  {context_type.upper().replace('_', ' ')}:")
            print(f"    Scenarios: {len(context_results)}")
            print(f"    Avg Score: {avg_score:.2f}/10")

            # Show individual scenario scores
            for r in context_results:
                scenario_name = r.get("scenario_name", "Unknown")
                overall = r["overall_score"]["overall"]
                print(f"      {scenario_name}: {overall:.2f}/10")

    print("\n" + "=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description="Run Socratic fidelity tests across different contexts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        "--models",
        type=str,
        default="anthropic.claude-3-5-sonnet-20241022-v2:0",
        help="Comma-separated list of model IDs (default: Claude Sonnet 3.5)"
    )

    parser.add_argument(
        "--context-type",
        type=str,
        help=f"Comma-separated context types to test. Options: {', '.join(CONTEXT_TYPES)}"
    )

    parser.add_argument(
        "--use-llm-judge",
        action="store_true",
        help="Use LLM for scoring (slower but more accurate)"
    )

    parser.add_argument(
        "--mock-mode",
        action="store_true",
        help="Use mock responses (for testing without AWS)"
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default="fidelity_results",
        help="Directory to save results (default: fidelity_results)"
    )

    parser.add_argument(
        "--list-contexts",
        action="store_true",
        help="List available context types and exit"
    )

    args = parser.parse_args()

    # List contexts if requested
    if args.list_contexts:
        print("\nAvailable Context Types:")
        print("=" * 50)
        for context_type in CONTEXT_TYPES:
            scenarios = get_scenarios_by_context_type(context_type)
            print(f"\n{context_type.upper().replace('_', ' ')} ({len(scenarios)} scenarios)")
            for s in scenarios:
                print(f"  - {s['name']}")
        return

    # Parse arguments
    model_ids = [m.strip() for m in args.models.split(",")]
    context_types = None
    if args.context_type:
        context_types = [c.strip() for c in args.context_type.split(",")]
        # Validate context types
        invalid = set(context_types) - set(CONTEXT_TYPES)
        if invalid:
            print(f"Error: Invalid context types: {invalid}")
            print(f"Valid options: {', '.join(CONTEXT_TYPES)}")
            sys.exit(1)

    # Run evaluation
    run_fidelity_evaluation(
        model_ids=model_ids,
        context_types=context_types,
        use_llm_judge=args.use_llm_judge,
        mock_mode=args.mock_mode,
        output_dir=args.output_dir
    )


if __name__ == "__main__":
    main()
