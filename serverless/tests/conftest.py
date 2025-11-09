"""
Pytest configuration and shared fixtures for Socratic AI Benchmarks tests.
"""
import pytest
import json
import os
from typing import Dict, Any
from unittest.mock import Mock, MagicMock
from datetime import datetime, timezone


# --- Sample Data Fixtures ---

@pytest.fixture
def sample_model_config():
    """Sample model configuration for testing."""
    return {
        "model_id": "anthropic.claude-3-5-sonnet-20241022-v2:0",
        "provider": "anthropic",
        "max_tokens": 200,
        "temperature": 0.7
    }


@pytest.fixture
def sample_scenario():
    """Sample test scenario."""
    return {
        "scenario_id": "EL-ETH-UTIL-DEON-01",
        "vector": "elenchus",
        "dimension": "ethical",
        "persona": "college student confident in utilitarian ethics",
        "initial_utterance": "I believe in 100% utilitarianism—the greatest good for the greatest number. So a doctor should sacrifice one healthy person to save five.",
        "num_turns": 5
    }


@pytest.fixture
def sample_dialogue_turn():
    """Sample dialogue turn data."""
    return {
        "run_id": "01K9HK1C5CPH6VB4HF55X3CGWC",
        "turn_index": 0,
        "vector": "elenchus",
        "persona": "college student confident in utilitarian ethics",
        "student": "I believe in utilitarianism. Should we sacrifice one to save five?",
        "ai": "When you say 'greatest good,' how do you measure that?",
        "input_tokens": 184,
        "output_tokens": 47,
        "latency_ms": 1523.4,
        "timestamp": "2025-11-08T11:18:57Z"
    }


@pytest.fixture
def sample_judge_scores():
    """Sample judge scoring results."""
    return {
        "overall_score": 84.0,
        "scores": {
            "open_ended": 75,
            "probing_depth": 82,
            "non_directive": 88,
            "age_appropriate": 85,
            "content_relevant": 90
        },
        "heuristics": {
            "has_question": True,
            "question_count": 1,
            "word_count": 9,
            "is_open_ended": True
        }
    }


# --- Mock AWS Service Fixtures ---

@pytest.fixture
def mock_bedrock_runtime():
    """Mock boto3 bedrock-runtime client."""
    mock = MagicMock()

    # Default successful response
    mock.invoke_model.return_value = {
        "body": Mock(read=lambda: json.dumps({
            "content": [{"text": "What assumptions are you making?"}],
            "usage": {"input_tokens": 100, "output_tokens": 50}
        }).encode())
    }

    return mock


@pytest.fixture
def mock_dynamodb_table():
    """Mock DynamoDB table."""
    mock = MagicMock()

    # Default successful responses
    mock.put_item.return_value = {}
    mock.get_item.return_value = {"Item": {}}
    mock.query.return_value = {"Items": []}
    mock.scan.return_value = {"Items": []}
    mock.update_item.return_value = {}

    return mock


@pytest.fixture
def mock_s3_client():
    """Mock S3 client."""
    mock = MagicMock()

    # Default successful responses
    mock.put_object.return_value = {}
    mock.get_object.return_value = {
        "Body": Mock(read=lambda: b'{"test": "data"}')
    }
    mock.list_objects_v2.return_value = {"Contents": []}

    return mock


@pytest.fixture
def mock_sqs_client():
    """Mock SQS client."""
    mock = MagicMock()

    # Default successful responses
    mock.send_message.return_value = {"MessageId": "test-message-id"}
    mock.send_message_batch.return_value = {"Successful": [], "Failed": []}

    return mock


@pytest.fixture
def mock_eventbridge_client():
    """Mock EventBridge client."""
    mock = MagicMock()

    # Default successful responses
    mock.put_events.return_value = {"FailedEntryCount": 0, "Entries": []}

    return mock


# --- Environment Variable Fixtures ---

@pytest.fixture
def lambda_env_vars(monkeypatch):
    """Set up typical Lambda environment variables."""
    env_vars = {
        "TABLE_NAME": "socratic_core",
        "BUCKET_NAME": "socratic-bench-data-test",
        "DIALOGUE_QUEUE_URL": "https://sqs.us-east-1.amazonaws.com/test/dialogue-jobs",
        "JUDGE_QUEUE_URL": "https://sqs.us-east-1.amazonaws.com/test/judge-jobs",
        "EVENT_BUS_NAME": "socratic-bench",
        "AWS_REGION": "us-east-1"
    }

    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)

    return env_vars


# --- Time/ID Fixtures ---

@pytest.fixture
def fixed_datetime(monkeypatch):
    """Fix datetime.now() to a specific time for testing."""
    fixed_time = datetime(2025, 11, 8, 11, 18, 57, tzinfo=timezone.utc)

    class MockDatetime:
        @staticmethod
        def now(tz=None):
            return fixed_time

    monkeypatch.setattr("datetime.datetime", MockDatetime)
    return fixed_time


@pytest.fixture
def sample_run_id():
    """Sample run ID for testing."""
    return "01K9HK1C5CPH6VB4HF55X3CGWC"


@pytest.fixture
def sample_manifest_id():
    """Sample manifest ID for testing."""
    return "M-20251108-727952e3f7a8"


# --- File Fixtures ---

@pytest.fixture
def temp_model_capabilities(tmp_path):
    """Create temporary model_capabilities.json for testing."""
    capabilities = {
        "anthropic.claude-3-5-sonnet-20241022-v2:0": {
            "provider": "anthropic",
            "requires_profile": False
        },
        "meta.llama4-maverick-17b-instruct-v1:0": {
            "provider": "meta",
            "requires_profile": True,
            "profile_arn": "arn:aws:bedrock:us-east-1::foundation-model/meta.llama4-maverick-17b-instruct-v1:0"
        }
    }

    capabilities_file = tmp_path / "model_capabilities.json"
    capabilities_file.write_text(json.dumps(capabilities, indent=2))

    return str(capabilities_file)


# --- Pytest Configuration Hooks ---

def pytest_configure(config):
    """Add custom markers to pytest configuration."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test (fast, no external dependencies)"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow (> 1 second)"
    )
    config.addinivalue_line(
        "markers", "bedrock: mark test as requiring AWS Bedrock"
    )


def pytest_collection_modifyitems(config, items):
    """Automatically mark tests based on their location."""
    for item in items:
        # Auto-mark based on test file location
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
