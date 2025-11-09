"""
Unit tests for environment utilities (env_utils.py).

These tests verify that environment variable validation works correctly
and provides clear error messages when configuration is invalid.
"""
import pytest
import os
from socratic_bench.env_utils import (
    require_env,
    get_env,
    validate_lambda_env,
    EnvironmentConfigError
)


class TestRequireEnv:
    """Tests for require_env() function."""

    def test_require_env_success(self, monkeypatch):
        """Test that require_env returns value when variable is set."""
        monkeypatch.setenv("TEST_VAR", "test_value")
        result = require_env("TEST_VAR")
        assert result == "test_value"

    def test_require_env_missing(self, monkeypatch):
        """Test that require_env raises error when variable is missing."""
        monkeypatch.delenv("TEST_VAR", raising=False)
        with pytest.raises(EnvironmentConfigError) as exc_info:
            require_env("TEST_VAR")

        assert "TEST_VAR" in str(exc_info.value)
        assert "not set" in str(exc_info.value)

    def test_require_env_empty_string(self, monkeypatch):
        """Test that require_env treats empty string as missing."""
        monkeypatch.setenv("TEST_VAR", "")
        # Empty string should still be returned (it's set, just empty)
        result = require_env("TEST_VAR")
        assert result == ""


class TestGetEnv:
    """Tests for get_env() function."""

    def test_get_env_success(self, monkeypatch):
        """Test that get_env returns value when variable is set."""
        monkeypatch.setenv("TEST_VAR", "test_value")
        result = get_env("TEST_VAR", "default")
        assert result == "test_value"

    def test_get_env_missing_uses_default(self, monkeypatch):
        """Test that get_env returns default when variable is missing."""
        monkeypatch.delenv("TEST_VAR", raising=False)
        result = get_env("TEST_VAR", "default_value")
        assert result == "default_value"

    def test_get_env_missing_no_default(self, monkeypatch):
        """Test that get_env returns empty string when no default provided."""
        monkeypatch.delenv("TEST_VAR", raising=False)
        result = get_env("TEST_VAR")
        assert result == ""


class TestValidateLambdaEnv:
    """Tests for validate_lambda_env() function."""

    def test_validate_all_present(self, monkeypatch):
        """Test successful validation when all variables are present."""
        monkeypatch.setenv("VAR1", "value1")
        monkeypatch.setenv("VAR2", "value2")
        monkeypatch.setenv("VAR3", "value3")

        result = validate_lambda_env(["VAR1", "VAR2", "VAR3"])

        assert result == {
            "VAR1": "value1",
            "VAR2": "value2",
            "VAR3": "value3"
        }

    def test_validate_one_missing(self, monkeypatch):
        """Test that validation fails when one variable is missing."""
        monkeypatch.setenv("VAR1", "value1")
        monkeypatch.delenv("VAR2", raising=False)

        with pytest.raises(EnvironmentConfigError) as exc_info:
            validate_lambda_env(["VAR1", "VAR2"])

        error_msg = str(exc_info.value)
        assert "VAR2" in error_msg
        assert "Missing required" in error_msg

    def test_validate_multiple_missing(self, monkeypatch):
        """Test that validation reports all missing variables."""
        monkeypatch.setenv("VAR1", "value1")
        monkeypatch.delenv("VAR2", raising=False)
        monkeypatch.delenv("VAR3", raising=False)

        with pytest.raises(EnvironmentConfigError) as exc_info:
            validate_lambda_env(["VAR1", "VAR2", "VAR3"])

        error_msg = str(exc_info.value)
        assert "VAR2" in error_msg
        assert "VAR3" in error_msg
        assert "VAR1" not in error_msg  # VAR1 is present, shouldn't be in error

    def test_validate_empty_list(self):
        """Test that validating empty list returns empty dict."""
        result = validate_lambda_env([])
        assert result == {}

    def test_validate_realistic_lambda_env(self, lambda_env_vars):
        """Test validation with realistic Lambda environment variables."""
        required = [
            "TABLE_NAME",
            "BUCKET_NAME",
            "DIALOGUE_QUEUE_URL",
            "JUDGE_QUEUE_URL"
        ]

        result = validate_lambda_env(required)

        assert "TABLE_NAME" in result
        assert "BUCKET_NAME" in result
        assert result["TABLE_NAME"] == "socratic_core"
        assert result["BUCKET_NAME"] == "socratic-bench-data-test"
