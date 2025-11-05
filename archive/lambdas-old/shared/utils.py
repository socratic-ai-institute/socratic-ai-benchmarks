"""
Shared utilities for Socratic Benchmarks Lambda functions
"""

import hashlib
import json
from datetime import datetime, timezone
from typing import Dict, Any
from ulid import ULID


def generate_ulid() -> str:
    """Generate a ULID (time-sortable unique ID)"""
    return str(ULID())


def compute_sha256(data: Dict[str, Any]) -> str:
    """Compute SHA-256 hash of a JSON-serializable object"""
    json_str = json.dumps(data, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(json_str.encode('utf-8')).hexdigest()


def now_iso() -> str:
    """Get current timestamp in ISO 8601 format (UTC)"""
    return datetime.now(timezone.utc).isoformat()


def parse_iso(timestamp: str) -> datetime:
    """Parse ISO 8601 timestamp to datetime"""
    return datetime.fromisoformat(timestamp.replace('Z', '+00:00'))


def build_pk_sk(entity_type: str, entity_id: str, sort_key: str = 'METADATA') -> tuple[str, str]:
    """
    Build DynamoDB partition key and sort key

    Args:
        entity_type: e.g., 'PROMPT', 'RUN', 'SEED'
        entity_id: ULID or other identifier
        sort_key: Defaults to 'METADATA'

    Returns:
        Tuple of (PK, SK)
    """
    pk = f'{entity_type}#{entity_id}'
    return (pk, sort_key)


def parse_pk(pk: str) -> tuple[str, str]:
    """
    Parse partition key into entity type and ID

    Args:
        pk: e.g., 'RUN#01HW555...'

    Returns:
        Tuple of (entity_type, entity_id)
    """
    parts = pk.split('#', 1)
    return (parts[0], parts[1] if len(parts) > 1 else '')


def s3_path(bucket: str, *path_parts: str) -> str:
    """Build S3 path from components"""
    return f"s3://{bucket}/{'/'.join(path_parts)}"


def s3_key(*path_parts: str) -> str:
    """Build S3 key from components"""
    return '/'.join(path_parts)


def truncate_text(text: str, max_length: int = 280) -> str:
    """Truncate text to max length with ellipsis"""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + '...'


class DynamoDBEncoder(json.JSONEncoder):
    """JSON encoder that handles DynamoDB Decimal types"""
    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        return super().default(obj)


def to_json(data: Any) -> str:
    """Convert to JSON string with DynamoDB Decimal support"""
    return json.dumps(data, cls=DynamoDBEncoder, separators=(',', ':'))
