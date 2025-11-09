"""
Unit tests for model configuration and Bedrock client (models.py).

These tests verify:
- ModelConfig creation and provider auto-detection
- BedrockClient request/response handling
- Error handling and retries
"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from socratic_bench.models import ModelConfig, BedrockClient, MODEL_CAPABILITIES


class TestModelConfig:
    """Tests for ModelConfig dataclass."""

    def test_direct_construction(self):
        """Test creating ModelConfig directly."""
        config = ModelConfig(
            model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
            provider="anthropic",
            max_tokens=300,
            temperature=0.8
        )

        assert config.model_id == "anthropic.claude-3-5-sonnet-20241022-v2:0"
        assert config.provider == "anthropic"
        assert config.max_tokens == 300
        assert config.temperature == 0.8

    def test_from_dict_with_provider(self):
        """Test creating ModelConfig from dict with explicit provider."""
        data = {
            "model_id": "anthropic.claude-3-5-sonnet-20241022-v2:0",
            "provider": "anthropic",
            "max_tokens": 200,
            "temperature": 0.7
        }

        config = ModelConfig.from_dict(data)

        assert config.model_id == data["model_id"]
        assert config.provider == "anthropic"
        assert config.max_tokens == 200
        assert config.temperature == 0.7

    def test_from_dict_auto_detect_provider_from_prefix(self):
        """Test provider auto-detection from model_id prefix."""
        data = {"model_id": "meta.llama3-1-70b-instruct-v1:0"}

        config = ModelConfig.from_dict(data)

        assert config.provider == "meta"

    def test_from_dict_defaults(self):
        """Test that from_dict uses default values for optional fields."""
        data = {"model_id": "anthropic.claude-3-5-sonnet-20241022-v2:0"}

        config = ModelConfig.from_dict(data)

        assert config.max_tokens == 200  # default
        assert config.temperature == 0.7  # default

    def test_from_dict_custom_values(self):
        """Test that from_dict uses provided values."""
        data = {
            "model_id": "anthropic.claude-3-5-sonnet-20241022-v2:0",
            "max_tokens": 500,
            "temperature": 0.9
        }

        config = ModelConfig.from_dict(data)

        assert config.max_tokens == 500
        assert config.temperature == 0.9

    @patch('socratic_bench.models.MODEL_CAPABILITIES', {
        "test.model-v1:0": {"provider": "test_provider", "requires_profile": False}
    })
    def test_from_dict_uses_capabilities_file(self):
        """Test that provider is detected from MODEL_CAPABILITIES."""
        data = {"model_id": "test.model-v1:0"}

        config = ModelConfig.from_dict(data)

        assert config.provider == "test_provider"

    def test_from_dict_no_dot_in_model_id(self):
        """Test handling of model_id without dot separator."""
        data = {"model_id": "some-model-without-dot"}

        config = ModelConfig.from_dict(data)

        assert config.provider == "unknown"


class TestBedrockClient:
    """Tests for BedrockClient."""

    def test_init_default_region(self):
        """Test BedrockClient initialization with default region."""
        with patch('boto3.client') as mock_boto3_client:
            client = BedrockClient()

            mock_boto3_client.assert_called_once_with(
                'bedrock-runtime',
                region_name='us-east-1'
            )

    def test_init_custom_region(self):
        """Test BedrockClient initialization with custom region."""
        with patch('boto3.client') as mock_boto3_client:
            client = BedrockClient(region='us-west-2')

            mock_boto3_client.assert_called_once_with(
                'bedrock-runtime',
                region_name='us-west-2'
            )

    def test_init_with_profile(self):
        """Test BedrockClient initialization with AWS profile."""
        with patch('boto3.Session') as mock_session:
            mock_session_instance = MagicMock()
            mock_session.return_value = mock_session_instance

            client = BedrockClient(profile='test-profile')

            mock_session.assert_called_once_with(
                profile_name='test-profile',
                region_name='us-east-1'
            )
            mock_session_instance.client.assert_called_once_with('bedrock-runtime')

    def test_invoke_success_anthropic(self, mock_bedrock_runtime):
        """Test successful model invocation for Anthropic model."""
        with patch('boto3.client', return_value=mock_bedrock_runtime):
            client = BedrockClient()
            config = ModelConfig(
                model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
                provider="anthropic",
                max_tokens=200,
                temperature=0.7
            )

            result = client.invoke(config, "What is the meaning of life?")

            assert "text" in result
            assert "latency_ms" in result
            assert "input_tokens" in result
            assert "output_tokens" in result
            assert isinstance(result["latency_ms"], float)

    def test_invoke_retry_on_throttle(self, mock_bedrock_runtime):
        """Test that invoke retries on throttling errors."""
        from botocore.exceptions import ClientError

        # Simulate throttle error then success
        mock_bedrock_runtime.invoke_model.side_effect = [
            ClientError(
                {"Error": {"Code": "ThrottlingException", "Message": "Rate exceeded"}},
                "InvokeModel"
            ),
            {
                "body": Mock(read=lambda: json.dumps({
                    "content": [{"text": "Success after retry"}],
                    "usage": {"input_tokens": 100, "output_tokens": 50}
                }).encode())
            }
        ]

        with patch('boto3.client', return_value=mock_bedrock_runtime), \
             patch('time.sleep'):  # Skip actual sleep
            client = BedrockClient()
            config = ModelConfig(
                model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
                provider="anthropic"
            )

            result = client.invoke(config, "Test prompt")

            assert mock_bedrock_runtime.invoke_model.call_count == 2
            assert result["text"] == "Success after retry"

    def test_invoke_max_retries_exhausted(self, mock_bedrock_runtime):
        """Test that invoke raises error when max retries exhausted."""
        from botocore.exceptions import ClientError

        # Always fail
        mock_bedrock_runtime.invoke_model.side_effect = ClientError(
            {"Error": {"Code": "ThrottlingException", "Message": "Rate exceeded"}},
            "InvokeModel"
        )

        with patch('boto3.client', return_value=mock_bedrock_runtime), \
             patch('time.sleep'), \
             pytest.raises(ClientError):
            client = BedrockClient()
            config = ModelConfig(
                model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
                provider="anthropic"
            )

            client.invoke(config, "Test prompt", max_retries=3)

            # Should have tried 3 times
            assert mock_bedrock_runtime.invoke_model.call_count == 3
