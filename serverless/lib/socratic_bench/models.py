"""
Model configuration and Bedrock client wrapper.
Handles all LLM invocations with retries, error handling, and inference profiles.
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
    """Load model capability map from JSON file."""
    capabilities_path = os.path.join(os.path.dirname(__file__), "model_capabilities.json")
    try:
        with open(capabilities_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # Fallback if file doesn't exist
        return {}


MODEL_CAPABILITIES = load_model_capabilities()


@dataclass
class ModelConfig:
    """Configuration for a Bedrock model."""
    model_id: str
    provider: str
    max_tokens: int = 200
    temperature: float = 0.7

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ModelConfig:
        model_id = data["model_id"]

        # Auto-detect provider from capabilities or model_id prefix
        if model_id in MODEL_CAPABILITIES:
            provider = MODEL_CAPABILITIES[model_id]["provider"]
        elif "provider" in data:
            provider = data["provider"]
        else:
            # Fallback: infer from model_id prefix
            provider = model_id.split(".")[0] if "." in model_id else "unknown"

        return cls(
            model_id=model_id,
            provider=provider,
            max_tokens=data.get("max_tokens", 200),
            temperature=data.get("temperature", 0.7),
        )


class BedrockClient:
    """Wrapper for AWS Bedrock runtime with error handling and retries."""

    def __init__(self, region: str = "us-east-1", profile: Optional[str] = None):
        if profile:
            session = boto3.Session(profile_name=profile, region_name=region)
            self.runtime = session.client('bedrock-runtime')
        else:
            self.runtime = boto3.client('bedrock-runtime', region_name=region)

    def invoke(
        self,
        model_config: ModelConfig,
        prompt: str,
        max_retries: int = 3,
    ) -> Dict[str, Any]:
        """
        Invoke a Bedrock model with automatic retries.
        Supports both direct modelId and inference profile ARN invocation.

        Returns:
            {
                "text": str,
                "latency_ms": float,
                "input_tokens": int,
                "output_tokens": int,
            }
        """
        body = self._build_request_body(model_config, prompt)

        for attempt in range(max_retries):
            try:
                t0 = time.time()

                # Check if model requires inference profile
                model_info = MODEL_CAPABILITIES.get(model_config.model_id, {})

                if model_info.get("requires_profile"):
                    # Use inference profile ARN as modelId
                    profile_arn = model_info["profile_arn"]
                    response = self.runtime.invoke_model(
                        modelId=profile_arn,
                        body=json.dumps(body)
                    )
                else:
                    # Use direct modelId
                    response = self.runtime.invoke_model(
                        modelId=model_config.model_id,
                        body=json.dumps(body)
                    )

                latency_ms = (time.time() - t0) * 1000

                data = json.loads(response["body"].read())
                text = self._extract_text(model_config.provider, data)

                # Extract token usage
                usage = self._extract_usage(model_config.provider, data)

                return {
                    "text": text,
                    "latency_ms": latency_ms,
                    "input_tokens": usage.get("input_tokens", 0),
                    "output_tokens": usage.get("output_tokens", 0),
                }

            except ClientError as e:
                if attempt == max_retries - 1:
                    raise
                # Exponential backoff: 2s, 4s, 8s
                time.sleep(2 ** (attempt + 1))

        raise RuntimeError(f"Failed to invoke model after {max_retries} attempts")

    def _build_request_body(self, config: ModelConfig, prompt: str) -> Dict[str, Any]:
        """Build provider-specific request body."""
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
        """Extract response text from provider-specific response."""
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
        """Extract token usage from provider-specific response."""
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
