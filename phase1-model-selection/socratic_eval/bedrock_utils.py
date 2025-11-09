"""
Bedrock Utilities for Context Growth Evaluation

Provides a unified interface for calling AWS Bedrock models.
"""
import boto3
import json
import time
import os
from typing import Dict, Any

# AWS Configuration - prioritize environment variable, fallback to mvp
AWS_PROFILE = os.environ.get('AWS_PROFILE', 'mvp')
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')

# Initialize Bedrock client
session = boto3.Session(profile_name=AWS_PROFILE, region_name=AWS_REGION)
bedrock_runtime = session.client('bedrock-runtime')


def call_bedrock_model(model_id: str, prompt: str, max_tokens: int = 500, temperature: float = 0.7, return_metadata: bool = False):
    """
    Call Bedrock model with a prompt and return the text response.

    Args:
        model_id: Full Bedrock model ID (e.g., 'anthropic.claude-3-5-sonnet-20241022-v2:0')
        prompt: The prompt to send
        max_tokens: Maximum tokens to generate
        temperature: Sampling temperature
        return_metadata: If True, return dict with text and metadata (token counts)

    Returns:
        str: The model's text response (if return_metadata=False)
        Dict: Response dict with 'text', 'input_tokens', 'output_tokens' (if return_metadata=True)

    Raises:
        Exception: If the API call fails
    """
    # Convert to inference profile ID if needed (for newer models)
    inference_profile_id = _get_inference_profile_id(model_id)

    # Determine provider from model_id
    if 'anthropic' in model_id:
        result = _call_anthropic(inference_profile_id, prompt, max_tokens, temperature, return_metadata)
    elif 'meta' in model_id:
        result = _call_meta(inference_profile_id, prompt, max_tokens, temperature, return_metadata)
    elif 'mistral' in model_id:
        result = _call_mistral(inference_profile_id, prompt, max_tokens, temperature, return_metadata)
    elif 'amazon' in model_id or 'nova' in model_id:
        result = _call_amazon(inference_profile_id, prompt, max_tokens, temperature, return_metadata)
    elif 'cohere' in model_id:
        result = _call_cohere(inference_profile_id, prompt, max_tokens, temperature, return_metadata)
    elif 'ai21' in model_id:
        result = _call_ai21(inference_profile_id, prompt, max_tokens, temperature, return_metadata)
    elif 'deepseek' in model_id:
        result = _call_deepseek(inference_profile_id, prompt, max_tokens, temperature, return_metadata)
    elif 'qwen' in model_id:
        result = _call_qwen(inference_profile_id, prompt, max_tokens, temperature, return_metadata)
    elif 'openai' in model_id:
        result = _call_openai(inference_profile_id, prompt, max_tokens, temperature, return_metadata)
    else:
        raise ValueError(f"Unsupported model provider in: {model_id}")

    # Return based on format requested
    if return_metadata:
        return result
    else:
        # Backward compatibility: return just the text
        return result.get('text', result) if isinstance(result, dict) else result


def _get_inference_profile_id(model_id: str) -> str:
    """
    Convert model ID to inference profile ID if needed.

    Many models in Bedrock require using inference profiles with the 'us.' prefix.
    """
    # Models that require US inference profiles
    inference_profile_models = [
        # Claude 3 series
        'anthropic.claude-3-opus-20240229-v1:0',
        'anthropic.claude-3-sonnet-20240229-v1:0',
        'anthropic.claude-3-haiku-20240307-v1:0',
        # Claude 3.5 series
        'anthropic.claude-3-5-sonnet-20241022-v2:0',
        'anthropic.claude-3-5-sonnet-20240620-v1:0',
        'anthropic.claude-3-5-haiku-20241022-v1:0',
        # Claude 3.7
        'anthropic.claude-3-7-sonnet-20250219-v1:0',
        # Claude 4 series
        'anthropic.claude-sonnet-4-20250514-v1:0',
        'anthropic.claude-opus-4-20250514-v1:0',
        'anthropic.claude-opus-4-1-20250805-v1:0',
        'anthropic.claude-haiku-4-5-20251001-v1:0',
        'anthropic.claude-sonnet-4-5-20250929-v1:0',
        # Meta/Llama models
        'meta.llama3-1-8b-instruct-v1:0',
        'meta.llama3-1-70b-instruct-v1:0',
        'meta.llama3-2-1b-instruct-v1:0',
        'meta.llama3-2-3b-instruct-v1:0',
        'meta.llama3-2-11b-instruct-v1:0',
        'meta.llama3-2-90b-instruct-v1:0',
        'meta.llama3-3-70b-instruct-v1:0',
        'meta.llama4-scout-17b-instruct-v1:0',
        'meta.llama4-maverick-17b-instruct-v1:0',
        # Amazon Nova
        'amazon.nova-micro-v1:0',
        'amazon.nova-lite-v1:0',
        'amazon.nova-pro-v1:0',
        'amazon.nova-premier-v1:0',
        # DeepSeek
        'deepseek.r1-v1:0',
        # Mistral
        'mistral.pixtral-large-2502-v1:0'
    ]

    if model_id in inference_profile_models:
        return f"us.{model_id}"

    return model_id


def _call_anthropic(model_id: str, prompt: str, max_tokens: int, temperature: float, return_metadata: bool = False):
    """Call Anthropic Claude models via Bedrock."""
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": [{"role": "user", "content": prompt}]
    }

    response = bedrock_runtime.invoke_model(
        modelId=model_id,
        body=json.dumps(body)
    )

    result = json.loads(response['body'].read())
    text = result['content'][0]['text'].strip()

    if return_metadata:
        usage = result.get('usage', {})
        return {
            'text': text,
            'input_tokens': usage.get('input_tokens', 0),
            'output_tokens': usage.get('output_tokens', 0)
        }
    return text


def _estimate_tokens(text: str) -> int:
    """Estimate token count from text (rough heuristic: ~4 chars per token)."""
    return len(text) // 4


def _call_meta(model_id: str, prompt: str, max_tokens: int, temperature: float, return_metadata: bool = False):
    """Call Meta Llama models via Bedrock."""
    body = {
        "prompt": prompt,
        "max_gen_len": max_tokens,
        "temperature": temperature,
        "top_p": 0.9
    }

    response = bedrock_runtime.invoke_model(
        modelId=model_id,
        body=json.dumps(body)
    )

    result = json.loads(response['body'].read())
    text = result['generation'].strip()

    if return_metadata:
        return {
            'text': text,
            'input_tokens': _estimate_tokens(prompt),
            'output_tokens': _estimate_tokens(text)
        }
    return text


def _call_mistral(model_id: str, prompt: str, max_tokens: int, temperature: float, return_metadata: bool = False):
    """Call Mistral models via Bedrock."""
    body = {
        "prompt": f"<s>[INST] {prompt} [/INST]",
        "max_tokens": max_tokens,
        "temperature": temperature,
        "top_p": 0.9
    }

    response = bedrock_runtime.invoke_model(
        modelId=model_id,
        body=json.dumps(body)
    )

    result = json.loads(response['body'].read())

    # Mistral returns outputs as a list
    if isinstance(result.get('outputs'), list) and len(result['outputs']) > 0:
        text = result['outputs'][0]['text'].strip()
    else:
        text = result.get('text', '').strip()

    if return_metadata:
        return {
            'text': text,
            'input_tokens': _estimate_tokens(prompt),
            'output_tokens': _estimate_tokens(text)
        }
    return text


def _call_amazon(model_id: str, prompt: str, max_tokens: int, temperature: float, return_metadata: bool = False):
    """Call Amazon Nova/Titan models via Bedrock."""
    body = {
        "messages": [{"role": "user", "content": [{"text": prompt}]}],
        "inferenceConfig": {
            "max_new_tokens": max_tokens,
            "temperature": temperature,
            "top_p": 0.9
        }
    }

    response = bedrock_runtime.invoke_model(
        modelId=model_id,
        body=json.dumps(body)
    )

    result = json.loads(response['body'].read())
    text = result['output']['message']['content'][0]['text'].strip()

    if return_metadata:
        return {
            'text': text,
            'input_tokens': _estimate_tokens(prompt),
            'output_tokens': _estimate_tokens(text)
        }
    return text


def _call_cohere(model_id: str, prompt: str, max_tokens: int, temperature: float, return_metadata: bool = False):
    """Call Cohere Command models via Bedrock."""
    body = {
        "message": prompt,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "p": 0.9
    }

    response = bedrock_runtime.invoke_model(
        modelId=model_id,
        body=json.dumps(body)
    )

    result = json.loads(response['body'].read())
    text = result['text'].strip()

    if return_metadata:
        return {
            'text': text,
            'input_tokens': _estimate_tokens(prompt),
            'output_tokens': _estimate_tokens(text)
        }
    return text


def _call_ai21(model_id: str, prompt: str, max_tokens: int, temperature: float, return_metadata: bool = False):
    """Call AI21 Jamba models via Bedrock."""
    body = {
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": temperature,
        "top_p": 0.9
    }

    response = bedrock_runtime.invoke_model(
        modelId=model_id,
        body=json.dumps(body)
    )

    result = json.loads(response['body'].read())
    text = result['choices'][0]['message']['content'].strip()

    if return_metadata:
        return {
            'text': text,
            'input_tokens': _estimate_tokens(prompt),
            'output_tokens': _estimate_tokens(text)
        }
    return text


def _call_deepseek(model_id: str, prompt: str, max_tokens: int, temperature: float, return_metadata: bool = False):
    """Call DeepSeek models via Bedrock."""
    body = {
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": temperature
    }

    response = bedrock_runtime.invoke_model(
        modelId=model_id,
        body=json.dumps(body)
    )

    result = json.loads(response['body'].read())
    text = result['choices'][0]['message']['content'].strip()

    if return_metadata:
        return {
            'text': text,
            'input_tokens': _estimate_tokens(prompt),
            'output_tokens': _estimate_tokens(text)
        }
    return text


def _call_qwen(model_id: str, prompt: str, max_tokens: int, temperature: float, return_metadata: bool = False):
    """Call Qwen models via Bedrock."""
    body = {
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": temperature,
        "top_p": 0.9
    }

    response = bedrock_runtime.invoke_model(
        modelId=model_id,
        body=json.dumps(body)
    )

    result = json.loads(response['body'].read())
    text = result['choices'][0]['message']['content'].strip()

    if return_metadata:
        return {
            'text': text,
            'input_tokens': _estimate_tokens(prompt),
            'output_tokens': _estimate_tokens(text)
        }
    return text


def _call_openai(model_id: str, prompt: str, max_tokens: int, temperature: float, return_metadata: bool = False):
    """Call OpenAI models via Bedrock."""
    body = {
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": temperature
    }

    response = bedrock_runtime.invoke_model(
        modelId=model_id,
        body=json.dumps(body)
    )

    result = json.loads(response['body'].read())
    text = result['choices'][0]['message']['content'].strip()

    if return_metadata:
        return {
            'text': text,
            'input_tokens': _estimate_tokens(prompt),
            'output_tokens': _estimate_tokens(text)
        }
    return text
