"""
Model configuration and Bedrock client wrapper.
Handles all LLM invocations with retries and error handling.
"""
from __future__ import annotations
import json
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional
import boto3
from botocore.exceptions import ClientError


@dataclass
class ModelConfig:
    """Configuration for a Bedrock model."""
    model_id: str
    provider: str  # 'anthropic', 'meta', 'mistral'
    max_tokens: int = 200
    temperature: float = 0.7

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ModelConfig:
        return cls(
            model_id=data["model_id"],
            provider=data["provider"],
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
        elif provider in ("meta", "mistral"):
            # Meta and Mistral don't provide detailed token counts in response
            # We'd need to estimate or use a separate tokenizer
            return {"input_tokens": 0, "output_tokens": 0}
        else:
            return {"input_tokens": 0, "output_tokens": 0}
