#!/usr/bin/env python3
"""
Test script for new LLM-based judge system (v2).

This script tests the judge_with_llm function with sample AI responses
to verify that:
1. LLM judges correctly identify Socratic questions
2. LLM judges rate directionally_socratic scores appropriately
3. Overall scoring with penalties works as expected
"""
import sys
import os
import json

# Add lib to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lib'))

from socratic_bench import BedrockClient, judge_with_llm

# Sample AI responses to test
SAMPLE_RESPONSES = {
    "good_socratic": {
        "text": "You mentioned that you think democracy is the best form of government. What specific features make it superior to other systems in your view?",
        "expected_question": True,
        "expected_socratic_range": (0.8, 1.0),
        "token_count": 28,
    },
    "lecturing": {
        "text": "Democracy is the best form of government because it ensures equal representation, protects individual rights, and allows peaceful transfer of power. These three pillars make it superior to authoritarian systems.",
        "expected_question": False,
        "expected_socratic_range": (0.0, 0.3),
        "token_count": 35,
    },
    "confirmation_question": {
        "text": "Democracy has three key features: representation, rights, and peaceful transition. Does that make sense?",
        "expected_question": False,  # Confirmation questions are NOT Socratic
        "expected_socratic_range": (0.2, 0.5),  # Mixed: some teaching + weak question
        "token_count": 19,
    },
    "mixed": {
        "text": "Democracy typically includes features like elected representatives and protected rights. But what do you think happens when the majority votes to restrict minority rights?",
        "expected_question": True,
        "expected_socratic_range": (0.6, 0.8),  # Mostly Socratic with some context
        "token_count": 30,
    },
}


def test_judge(bedrock_client: BedrockClient):
    """Test the judge_with_llm function with sample responses."""

    print("=" * 80)
    print("Testing New LLM-Based Judge System (v2)")
    print("=" * 80)

    for name, sample in SAMPLE_RESPONSES.items():
        print(f"\n--- Testing: {name} ---")
        print(f"Response: {sample['text']}")
        print(f"Expected ends_with_question: {sample['expected_question']}")
        print(f"Expected directionally_socratic: {sample['expected_socratic_range']}")
        print(f"Token count: {sample['token_count']}")

        try:
            result = judge_with_llm(
                ai_response=sample["text"],
                bedrock_client=bedrock_client,
                scenario_context="Test scenario: Democracy discussion with high school student",
                token_count=sample["token_count"],
            )

            scores = result.scores
            print(f"\nResults:")
            print(f"  token_count: {scores['token_count']}")
            print(f"  ends_with_socratic_question: {scores['ends_with_socratic_question']}")
            print(f"  directionally_socratic: {scores['directionally_socratic']}")
            print(f"  verbosity_penalty: {scores['verbosity_penalty']}")
            print(f"  question_penalty: {scores['question_penalty']}")
            print(f"  socratic_penalty: {scores['socratic_penalty']}")
            print(f"  OVERALL SCORE: {scores['overall']}")
            print(f"\nExplanations:")
            print(f"  Question: {scores['question_explanation']}")
            print(f"  Socratic: {scores['socratic_explanation']}")
            print(f"\nLatency: {result.latency_ms:.0f}ms")

            # Validation
            if scores['ends_with_socratic_question'] != sample['expected_question']:
                print(f"⚠️  WARNING: Expected ends_with_question={sample['expected_question']}, got {scores['ends_with_socratic_question']}")

            socratic_score = scores['directionally_socratic']
            min_expected, max_expected = sample['expected_socratic_range']
            if not (min_expected <= socratic_score <= max_expected):
                print(f"⚠️  WARNING: Expected directionally_socratic in range {sample['expected_socratic_range']}, got {socratic_score}")

        except Exception as e:
            print(f"❌ ERROR: {e}")
            if hasattr(result, 'error') and result.error:
                print(f"Judge error: {result.error}")


def main():
    """Main test execution."""
    print("Initializing Bedrock client...")

    try:
        bedrock_client = BedrockClient()
        print("✓ Bedrock client initialized\n")
    except Exception as e:
        print(f"❌ Failed to initialize Bedrock client: {e}")
        print("\nMake sure:")
        print("1. AWS credentials are configured (--profile mvp)")
        print("2. Bedrock access is enabled in your AWS account")
        print("3. You have permissions for bedrock:InvokeModel")
        sys.exit(1)

    test_judge(bedrock_client)

    print("\n" + "=" * 80)
    print("Testing complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
