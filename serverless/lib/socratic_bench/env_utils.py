"""
Environment variable validation utilities for Lambda functions.

This module provides safe environment variable loading with clear error messages
to prevent cryptic KeyError exceptions at runtime.
"""
import os
from typing import Optional, Dict, Any


class EnvironmentConfigError(Exception):
    """Raised when required environment variables are missing or invalid."""
    pass


def require_env(var_name: str) -> str:
    """
    Get required environment variable or raise clear error.

    Args:
        var_name: Name of the environment variable

    Returns:
        The environment variable value

    Raises:
        EnvironmentConfigError: If the variable is not set

    Example:
        >>> TABLE_NAME = require_env("TABLE_NAME")
    """
    value = os.environ.get(var_name)
    if value is None:
        raise EnvironmentConfigError(
            f"Required environment variable '{var_name}' is not set. "
            f"Please check Lambda configuration."
        )
    return value


def get_env(var_name: str, default: str = "") -> str:
    """
    Get optional environment variable with default.

    Args:
        var_name: Name of the environment variable
        default: Default value if not set (default: empty string)

    Returns:
        The environment variable value or default

    Example:
        >>> LOG_LEVEL = get_env("LOG_LEVEL", "INFO")
    """
    return os.environ.get(var_name, default)


def validate_lambda_env(required_vars: list[str]) -> Dict[str, str]:
    """
    Validate all required environment variables at Lambda startup.

    This should be called at the top of lambda_handler or in module initialization
    to fail fast with a clear error message.

    Args:
        required_vars: List of required environment variable names

    Returns:
        Dictionary mapping variable names to their values

    Raises:
        EnvironmentConfigError: If any required variable is missing

    Example:
        >>> # At top of Lambda handler
        >>> env = validate_lambda_env(["TABLE_NAME", "BUCKET_NAME", "QUEUE_URL"])
        >>> TABLE_NAME = env["TABLE_NAME"]
    """
    missing = []
    env_values = {}

    for var_name in required_vars:
        value = os.environ.get(var_name)
        if value is None:
            missing.append(var_name)
        else:
            env_values[var_name] = value

    if missing:
        raise EnvironmentConfigError(
            f"Missing required environment variables: {', '.join(missing)}. "
            f"Please check Lambda configuration in CDK stack."
        )

    return env_values
