#!/usr/bin/env python3
"""
Simple test to verify the Socratic answer evaluator works correctly.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from socratic_eval.context_growth.socratic_answer_evaluator import evaluate_socratic_answer, format_score_report

def main():
    print("=" * 70)
    print("TESTING SOCRATIC ANSWER EVALUATOR")
    print("=" * 70)
    print()

    test_cases = [
        {
            "name": "Good Socratic Question",
            "response": "What do you mean by 'leadership' in your specific context?",
            "token_count": 12,
            "expected": {
                "ends_with_socratic_question": True,
                "directional_socraticism": ">0.7"
            }
        },
        {
            "name": "Not Socratic - Pure Information",
            "response": "Leadership involves several key traits. First, you need vision - the ability to see where you want to go. Second, communication is crucial for conveying that vision. Third, empathy helps you connect with team members.",
            "token_count": 45,
            "expected": {
                "ends_with_socratic_question": False,
                "directional_socraticism": "<0.3"
            }
        },
        {
            "name": "Excellent Socratic - Probes Assumptions",
            "response": "What assumptions are you making about what makes someone a good leader?",
            "token_count": 13,
            "expected": {
                "ends_with_socratic_question": True,
                "directional_socraticism": ">0.8"
            }
        },
        {
            "name": "Not Socratic - Ends with Procedural Question",
            "response": "Based on my analysis, the best approach would be to focus on three key areas: strategic planning, team communication, and stakeholder management. Would you like me to elaborate on any of these?",
            "token_count": 42,
            "expected": {
                "ends_with_socratic_question": False,
                "directional_socraticism": "<0.4"
            }
        }
    ]

    for i, test in enumerate(test_cases, 1):
        print(f"\nTest Case {i}: {test['name']}")
        print(f"{'=' * 70}")
        print(f"Response: \"{test['response']}\"")
        print(f"Token Count: {test['token_count']}")
        print()

        try:
            score = evaluate_socratic_answer(
                response=test["response"],
                token_count=test["token_count"]
            )

            print(format_score_report(score))

            # Validate expectations
            print("\nValidation:")
            print(f"  Expected Socratic Ending: {test['expected']['ends_with_socratic_question']}")
            print(f"  Actual:                   {score['ends_with_socratic_question']}")
            print(f"  ✓ PASS" if score['ends_with_socratic_question'] == test['expected']['ends_with_socratic_question'] else "  ✗ FAIL")

            print(f"\n  Expected Directional:     {test['expected']['directional_socraticism']}")
            print(f"  Actual:                   {score['directional_socraticism']:.2f}")

            # Check if directional score meets expectation
            if ">" in test['expected']['directional_socraticism']:
                threshold = float(test['expected']['directional_socraticism'][1:])
                passes = score['directional_socraticism'] > threshold
            else:
                threshold = float(test['expected']['directional_socraticism'][1:])
                passes = score['directional_socraticism'] < threshold

            print(f"  {'✓ PASS' if passes else '✗ FAIL'}")

        except Exception as e:
            print(f"✗ ERROR: {e}")
            import traceback
            traceback.print_exc()

        print()

    print("=" * 70)
    print("TESTING COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
