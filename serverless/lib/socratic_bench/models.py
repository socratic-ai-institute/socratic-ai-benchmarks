"""
Model Configuration and Bedrock Client Wrapper

This module provides a unified interface for invoking multiple LLM providers via AWS Bedrock.
It handles provider-specific request/response formats, retry logic, error handling, and
inference profile management.

Supported Providers (as of 2025-11):
    - Anthropic: Claude 3.5 Sonnet, Claude 3 Haiku, etc.
    - Meta: Llama 3/4 models (Scout, Maverick, etc.)
    - Amazon: Nova models (Micro, Lite, Pro)
    - Mistral: Mistral 7B, Mixtral, etc.
    - Cohere: Command models
    - AI21: Jamba models
    - Qwen: Qwen2 models
    - DeepSeek: DeepSeek models
    - OpenAI: GPT models (via Bedrock)

Key Challenges This Module Solves:
    1. Provider API Inconsistency: Each provider has different request/response formats
    2. Token Extraction Variance: Token usage reporting varies wildly across providers
    3. Inference Profiles: Some models require special ARN-based invocation
    4. Retry Logic: Transient failures need exponential backoff
    5. Error Handling: Provider-specific error messages need normalization

Architecture Notes:
    - ModelConfig: Lightweight configuration dataclass
    - BedrockClient: Stateful client with boto3 runtime connection
    - Provider-specific methods: _build_request_body, _extract_text, _extract_usage
    - Capabilities file: External JSON mapping models to providers and profiles
"""
from __future__ import annotations
import json
import time
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional
import boto3
from botocore.exceptions import ClientError


# Load model capabilities (provider + profile requirements)
def load_model_capabilities() -> Dict[str, Dict[str, Any]]:
    """
    Load model capability map from JSON file.

    The model_capabilities.json file maps model IDs to their provider and
    whether they require inference profile ARN invocation.

    Expected Format:
        {
            "model_id": {
                "provider": "anthropic|meta|amazon|...",
                "requires_profile": true|false,
                "profile_arn": "arn:aws:bedrock:..." (if requires_profile=true)
            }
        }

    Returns:
        Dictionary mapping model_id → capability info, or empty dict if file missing

    Note:
        If model_capabilities.json is missing, provider is inferred from model_id prefix.
        Example: "anthropic.claude-3-5-sonnet-..." → provider="anthropic"
    """
    capabilities_path = os.path.join(os.path.dirname(__file__), "model_capabilities.json")
    try:
        with open(capabilities_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # Fallback if file doesn't exist - will use model_id prefix inference
        return {}


# Global capabilities registry loaded at module import time
# This avoids re-reading the JSON file for every model invocation
MODEL_CAPABILITIES = load_model_capabilities()


@dataclass
class ModelConfig:
    """
    Configuration for a Bedrock model.

    This lightweight dataclass bundles all the parameters needed to invoke
    a model via Bedrock. It supports auto-detection of provider from model_id.

    Attributes:
        model_id: Full Bedrock model identifier (e.g., "anthropic.claude-3-5-sonnet-20241022-v2:0")
        provider: Provider name (anthropic, meta, amazon, etc.)
        max_tokens: Maximum tokens to generate in response (default: 200)
        temperature: Sampling temperature 0.0-1.0 (default: 0.7)

    Provider Detection Strategy (in order of precedence):
        1. Use MODEL_CAPABILITIES[model_id]["provider"] if available
        2. Use explicit "provider" field from input data
        3. Fallback: Extract prefix from model_id (e.g., "anthropic.claude..." → "anthropic")

    Usage:
        >>> # Explicit construction
        >>> config = ModelConfig(model_id="anthropic.claude-3-5-sonnet-...", provider="anthropic")
        >>>
        >>> # From dictionary (auto-detects provider)
        >>> config = ModelConfig.from_dict({"model_id": "anthropic.claude-3-5-sonnet-..."})
    """
    model_id: str
    provider: str
    max_tokens: int = 200
    temperature: float = 0.7

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ModelConfig:
        """
        Create ModelConfig from dictionary with automatic provider detection.

        This is the preferred way to create configs from JSON configuration files.

        Args:
            data: Dictionary with at least "model_id" key, optionally "provider",
                 "max_tokens", and "temperature"

        Returns:
            ModelConfig instance with provider auto-detected if not specified

        Example:
            >>> data = {"model_id": "meta.llama4-maverick-v1:0", "max_tokens": 300}
            >>> config = ModelConfig.from_dict(data)
            >>> print(config.provider)  # "meta" (auto-detected)
        """
        model_id = data["model_id"]

        # Auto-detect provider using 3-tier fallback strategy
        if model_id in MODEL_CAPABILITIES:
            # Tier 1: Use capabilities file (most reliable)
            provider = MODEL_CAPABILITIES[model_id]["provider"]
        elif "provider" in data:
            # Tier 2: Use explicit provider from data (user override)
            provider = data["provider"]
        else:
            # Tier 3: Infer from model_id prefix (last resort)
            # Example: "anthropic.claude-3-5-sonnet-..." → "anthropic"
            provider = model_id.split(".")[0] if "." in model_id else "unknown"

        return cls(
            model_id=model_id,
            provider=provider,
            max_tokens=data.get("max_tokens", 200),
            temperature=data.get("temperature", 0.7),
        )


class BedrockClient:
    """
    Wrapper for AWS Bedrock runtime with error handling and retries.

    This class provides a high-level interface to AWS Bedrock Runtime API, abstracting
    away provider-specific details and adding robustness features like retries.

    Features:
        - Unified invoke() interface for all providers
        - Automatic exponential backoff for transient failures
        - Support for both direct model invocation and inference profile ARNs
        - Provider-specific request/response formatting
        - Token usage extraction (where supported by provider)

    Attributes:
        runtime: boto3 bedrock-runtime client for API calls

    Threading Notes:
        - BedrockClient instances are NOT thread-safe (boto3 clients aren't)
        - For concurrent invocations, create separate client instances per thread
        - Or use a thread-safe connection pool (not implemented here)
    """

    def __init__(self, region: str = "us-east-1", profile: Optional[str] = None):
        """
        Initialize Bedrock runtime client.

        Args:
            region: AWS region (default: us-east-1 where most Bedrock models available)
            profile: Optional AWS profile name for credential resolution
                    If None, uses default credential chain (env vars, IAM role, etc.)

        Usage:
            >>> # Use default credentials
            >>> client = BedrockClient()
            >>>
            >>> # Use specific profile
            >>> client = BedrockClient(profile="my-aws-profile")
        """
        if profile:
            # Use explicit AWS profile (for local dev/testing)
            session = boto3.Session(profile_name=profile, region_name=region)
            self.runtime = session.client('bedrock-runtime')
        else:
            # Use default credential chain (for Lambda, uses IAM role automatically)
            self.runtime = boto3.client('bedrock-runtime', region_name=region)

    def invoke(
        self,
        model_config: ModelConfig,
        prompt: str,
        max_retries: int = 3,
    ) -> Dict[str, Any]:
        """
        Invoke a Bedrock model with automatic retries.

        This is the main entry point for all model invocations. It handles:
        1. Building provider-specific request body
        2. Determining whether to use direct model ID or inference profile ARN
        3. Invoking the Bedrock API
        4. Extracting response text and token usage
        5. Retrying with exponential backoff on failures

        Args:
            model_config: Model configuration (model_id, provider, etc.)
            prompt: The prompt text to send to the model
            max_retries: Maximum retry attempts for transient failures (default: 3)

        Returns:
            Dictionary with keys:
                - text: Generated response text
                - latency_ms: API call latency in milliseconds
                - input_tokens: Number of input tokens (0 if provider doesn't report)
                - output_tokens: Number of output tokens (0 if provider doesn't report)

        Raises:
            ClientError: If API call fails after all retries
            RuntimeError: If retries exhausted without success
            ValueError: If provider is unknown or response format is invalid

        Performance Notes:
            - Typical latency: 1-4 seconds depending on model and response length
            - Retries add 2s, 4s, 8s delays (exponential backoff)
            - Token extraction is fast (<1ms) - just JSON parsing

        Inference Profile ARNs:
            Some models (like Llama 4) require special ARN-based invocation instead
            of using the model_id directly. This is configured in model_capabilities.json.
        """
        # Build provider-specific request body (formats vary widely)
        body = self._build_request_body(model_config, prompt)

        # Retry loop with exponential backoff
        for attempt in range(max_retries):
            try:
                # Start latency timer
                t0 = time.time()

                # Determine invocation method: direct model ID vs inference profile ARN
                model_info = MODEL_CAPABILITIES.get(model_config.model_id, {})

                if model_info.get("requires_profile"):
                    # Some models require inference profile ARN invocation
                    # Example: Llama 4 models use us.meta.llama4-* ARNs
                    profile_arn = model_info["profile_arn"]
                    response = self.runtime.invoke_model(
                        modelId=profile_arn,  # ARN instead of model_id
                        body=json.dumps(body)
                    )
                else:
                    # Standard invocation using direct model ID
                    # This is the common case for most models
                    response = self.runtime.invoke_model(
                        modelId=model_config.model_id,
                        body=json.dumps(body)
                    )

                # Measure latency (includes network + model inference time)
                latency_ms = (time.time() - t0) * 1000

                # Parse response body (StreamingBody → dict)
                data = json.loads(response["body"].read())

                # Extract text using provider-specific logic
                text = self._extract_text(model_config.provider, data)

                # Extract token usage (some providers don't report this)
                usage = self._extract_usage(model_config.provider, data)

                # Return unified response format
                return {
                    "text": text,
                    "latency_ms": latency_ms,
                    "input_tokens": usage.get("input_tokens", 0),
                    "output_tokens": usage.get("output_tokens", 0),
                }

            except ClientError as e:
                # Handle transient errors with retry
                if attempt == max_retries - 1:
                    # Last attempt failed - re-raise original error
                    raise

                # Exponential backoff: wait 2s, 4s, 8s before retrying
                # This gives transient issues time to resolve
                time.sleep(2 ** (attempt + 1))

        # Should never reach here (loop always returns or raises)
        # But included for type safety and defensive programming
        raise RuntimeError(f"Failed to invoke model after {max_retries} attempts")

    def _build_request_body(self, config: ModelConfig, prompt: str) -> Dict[str, Any]:
        """
        Build provider-specific request body.

        Each LLM provider on Bedrock has a different API format. This method
        translates our unified ModelConfig + prompt into the format each provider expects.

        Args:
            config: Model configuration with provider, max_tokens, temperature
            prompt: The prompt text to send

        Returns:
            Dictionary in provider-specific format, ready for JSON serialization

        Provider Formats:
            - anthropic: Messages API with anthropic_version
            - meta: Simple prompt with max_gen_len
            - amazon: Messages with inferenceConfig
            - mistral: Wrapped prompt with Instruct tags
            - cohere: Message field (not messages)
            - ai21/qwen/deepseek/openai: Standard messages array

        Raises:
            ValueError: If provider is unknown
        """
        if config.provider == "anthropic":
            return {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": config.max_tokens,
                "temperature": config.temperature,
                "messages": [{"role": "user", "content": prompt}],
            }
        elif config.provider == "meta":
            return {
                "prompt": prompt,
                "max_gen_len": config.max_tokens,
                "temperature": config.temperature,
                "top_p": 0.9,
            }
        elif config.provider == "mistral":
            return {
                "prompt": f"<s>[INST] {prompt} [/INST]",
                "max_tokens": config.max_tokens,
                "temperature": config.temperature,
                "top_p": 0.9,
            }
        elif config.provider == "amazon":
            # Amazon Nova models
            return {
                "messages": [{"role": "user", "content": [{"text": prompt}]}],
                "inferenceConfig": {
                    "maxTokens": config.max_tokens,
                    "temperature": config.temperature,
                    "topP": 0.9,
                },
            }
        elif config.provider == "cohere":
            return {
                "message": prompt,
                "max_tokens": config.max_tokens,
                "temperature": config.temperature,
            }
        elif config.provider == "ai21":
            # AI21 Jamba uses messages format
            return {
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": config.max_tokens,
                "temperature": config.temperature,
                "top_p": 0.9,
            }
        elif config.provider == "qwen":
            # Qwen uses standard messages format like OpenAI
            return {
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": config.max_tokens,
                "temperature": config.temperature,
            }
        elif config.provider == "deepseek":
            return {
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": config.max_tokens,
                "temperature": config.temperature,
            }
        elif config.provider == "openai":
            return {
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": config.max_tokens,
                "temperature": config.temperature,
            }
        else:
            raise ValueError(f"Unknown provider: {config.provider}")

    def _extract_text(self, provider: str, data: Dict[str, Any]) -> str:
        """
        Extract response text from provider-specific response.

        Each provider returns responses in different JSON structures. This method
        knows how to navigate each structure to extract the generated text.

        Args:
            provider: Provider name (anthropic, meta, etc.)
            data: Parsed JSON response from Bedrock API

        Returns:
            The generated text, stripped of whitespace

        Response Formats:
            - anthropic: data["content"][0]["text"]
            - meta: data["generation"]
            - amazon: data["output"]["message"]["content"][0]["text"]
            - mistral: data["outputs"][0]["text"]
            - cohere: data["text"]
            - ai21/qwen/openai: data["choices"][0]["message"]["content"]
            - deepseek: Same as OpenAI, but content can be null

        Raises:
            ValueError: If provider is unknown
            KeyError: If response format is unexpected (malformed API response)
        """
        if provider == "anthropic":
            return data["content"][0]["text"].strip()
        elif provider == "meta":
            return data.get("generation", "").strip()
        elif provider == "mistral":
            return data["outputs"][0]["text"].strip()
        elif provider == "amazon":
            # Amazon Nova response format
            return data["output"]["message"]["content"][0]["text"].strip()
        elif provider == "cohere":
            return data["text"].strip()
        elif provider == "ai21":
            # AI21 Jamba uses choices format with messages API
            return data["choices"][0]["message"]["content"].strip()
        elif provider == "qwen":
            # Qwen uses standard choices format
            return data["choices"][0]["message"]["content"].strip()
        elif provider == "deepseek":
            # DeepSeek can return null content for some responses
            content = data["choices"][0]["message"].get("content")
            return content.strip() if content else ""
        elif provider == "openai":
            return data["choices"][0]["message"]["content"].strip()
        else:
            raise ValueError(f"Unknown provider: {provider}")

    def _extract_usage(self, provider: str, data: Dict[str, Any]) -> Dict[str, int]:
        """
        Extract token usage from provider-specific response.

        Token usage reporting is highly inconsistent across providers. Some report
        detailed usage, others don't report at all. This method extracts what's available.

        Args:
            provider: Provider name (anthropic, meta, etc.)
            data: Parsed JSON response from Bedrock API

        Returns:
            Dictionary with keys:
                - input_tokens: Number of tokens in input/prompt
                - output_tokens: Number of tokens generated
            Returns 0 for both if provider doesn't report usage.

        Provider Support:
            - Full support: anthropic, amazon, cohere, qwen, deepseek, openai
            - No support: meta, mistral, ai21 (return 0s)

        Usage Fields by Provider:
            - anthropic: usage.input_tokens, usage.output_tokens
            - amazon: usage.inputTokens, usage.outputTokens (camelCase!)
            - cohere: prompt_tokens, generation_tokens
            - qwen: usage.input_tokens, usage.output_tokens
            - deepseek/openai: usage.prompt_tokens, usage.completion_tokens
        """
        if provider == "anthropic":
            usage = data.get("usage", {})
            return {
                "input_tokens": usage.get("input_tokens", 0),
                "output_tokens": usage.get("output_tokens", 0),
            }
        elif provider == "amazon":
            usage = data.get("usage", {})
            return {
                "input_tokens": usage.get("inputTokens", 0),
                "output_tokens": usage.get("outputTokens", 0),
            }
        elif provider == "cohere":
            return {
                "input_tokens": data.get("prompt_tokens", 0),
                "output_tokens": data.get("generation_tokens", 0),
            }
        elif provider == "qwen":
            usage = data.get("usage", {})
            return {
                "input_tokens": usage.get("input_tokens", 0),
                "output_tokens": usage.get("output_tokens", 0),
            }
        elif provider in ("deepseek", "openai"):
            usage = data.get("usage", {})
            return {
                "input_tokens": usage.get("prompt_tokens", 0),
                "output_tokens": usage.get("completion_tokens", 0),
            }
        elif provider in ("meta", "mistral", "ai21"):
            # These providers don't provide detailed token counts
            return {"input_tokens": 0, "output_tokens": 0}
        else:
            return {"input_tokens": 0, "output_tokens": 0}
