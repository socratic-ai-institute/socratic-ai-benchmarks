"""
Pydantic Data Models for AWS Socratic Benchmark System

Defines all core entities with strict validation:
- Turn: Single dialogue turn with scores
- Run: Complete model×seed×temp×phase execution
- RunManifest: Immutable config snapshot
- WeeklySummary: Aggregated metrics
- CSD subscores and supporting types
"""

import hashlib
import json
from datetime import datetime
from enum import Enum
from typing import Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field, computed_field, field_validator

# ============================================================================
# Enums and Constants
# ============================================================================


class Phase(str, Enum):
    """Context window test phases"""

    P0 = "P0"  # 2K tokens, clean
    P1 = "P1"  # 8K tokens, mild noise
    P2 = "P2"  # 32K tokens, medium noise
    P3 = "P3"  # 128K+ tokens, heavy noise


class ViolationType(str, Enum):
    """Types of Socratic violations"""

    LEADING_QUESTION = "leading_question"
    MULTI_QUESTION = "multi_question"
    ADVICE_LEAKAGE = "advice_leakage"
    CLOSED_QUESTION = "closed_question"  # yes/no
    LECTURING = "lecturing"
    OFF_TOPIC = "off_topic"
    META_VIOLATION = "meta_violation"  # wrong cadence


class QuestionType(str, Enum):
    """Adaptive probing question types"""

    DEFINITIONS = "definitions"
    ASSUMPTIONS = "assumptions"
    EVIDENCE = "evidence"
    IMPLICATIONS = "implications"
    ALTERNATIVES = "alternatives"
    META = "meta"


class RedactionStatus(str, Enum):
    """PII redaction status"""

    NONE = "none"
    PARTIAL = "partial"
    FULL = "full"


# ============================================================================
# Sub-components (embedded in Turn)
# ============================================================================


class HeuristicResult(BaseModel):
    """Fast rule-based scoring (pre-judge filter)"""

    form: float = Field(ge=0, le=10, description="Grammatical form score")
    substance: float = Field(ge=0, le=10, description="Content quality score")
    purity: float = Field(ge=0, le=10, description="Non-directive purity score")
    violations: List[ViolationType] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1, description="Heuristic confidence")

    @computed_field
    @property
    def score(self) -> float:
        """Overall heuristic score"""
        # Weighted average: purity matters most
        return self.form * 0.2 + self.substance * 0.3 + self.purity * 0.5


class JudgeResult(BaseModel):
    """LLM judge scoring with rationale"""

    form: float = Field(ge=0, le=10, description="Question form quality")
    substance: float = Field(ge=0, le=10, description="Pedagogical substance")
    purity: float = Field(ge=0, le=10, description="Socratic purity (non-directive)")
    violations: List[ViolationType] = Field(default_factory=list)
    rationale: str = Field(max_length=5000, description="Judge reasoning")
    confidence: float = Field(ge=0, le=1, description="Judge confidence")
    model_used: str = Field(description="Judge model ID")

    @computed_field
    @property
    def score(self) -> float:
        """Overall judge score"""
        return self.form * 0.2 + self.substance * 0.3 + self.purity * 0.5


class SalienceReference(BaseModel):
    """Reference to a salient fact from prior turns"""

    item_id: str = Field(description="Unique ID in salience map")
    turn_origin: int = Field(ge=1, description="Turn where fact first appeared")
    confidence: float = Field(ge=0, le=1, description="Reference confidence")
    surface_form: str = Field(max_length=500, description="How it was referenced")


class DecoyReference(BaseModel):
    """Reference to a planted red herring"""

    item_id: str = Field(description="Decoy ID from phase config")
    mode: Literal["assumed", "tested"] = Field(
        description="Did model assume or critically test the decoy?"
    )


class TemplateMatch(BaseModel):
    """Match against canned question templates"""

    matched: bool
    template_id: Optional[str] = None
    similarity_score: float = Field(ge=0, le=1)


class ThreadLink(BaseModel):
    """Link to prior conversation thread"""

    user_turn: int = Field(ge=1, description="Which user turn this links to")
    span_id: str = Field(description="Specific span (e.g., 'u12.s3')")


class ContradictionDetected(BaseModel):
    """Detected contradiction in user statements"""

    slot: str = Field(description="Slot name (e.g., 'budget', 'timeline')")
    prev_value: str = Field(max_length=200)
    new_value: str = Field(max_length=200)
    detected_at_turn: int = Field(ge=1)


class CSDSubscores(BaseModel):
    """
    Conversation-level Socratic Dynamism (8 dimensions)
    All scores normalized to 0-10 scale
    """

    CR: float = Field(ge=0, le=10, description="Context Responsiveness")
    ST: float = Field(ge=0, le=10, description="Salience Tracking")
    RHD: float = Field(ge=0, le=10, description="Red-Herring Discipline")
    AP: float = Field(ge=0, le=10, description="Adaptive Probing")
    NVT: float = Field(ge=0, le=10, description="Novelty vs. Template")
    TC: float = Field(ge=0, le=10, description="Thread Continuity")
    CH: float = Field(ge=0, le=10, description="Contradiction Handling")
    MA: float = Field(ge=0, le=10, description="Meta-Adaptation")

    @computed_field
    @property
    def overall(self) -> float:
        """Weighted CSD score"""
        return (
            0.20 * self.CR
            + 0.20 * self.ST
            + 0.15 * self.RHD
            + 0.15 * self.AP
            + 0.10 * self.NVT
            + 0.10 * self.TC
            + 0.05 * self.CH
            + 0.05 * self.MA
        )


# ============================================================================
# Core Entities
# ============================================================================


class Turn(BaseModel):
    """
    Single dialogue turn (one user message + one assistant response)
    Stored in S3 JSONL (one per line) and DynamoDB for hot queries
    """

    # Identity
    run_id: str = Field(pattern=r"^[0-9A-HJKMNP-TV-Z]{26}$", description="ULID")
    turn: int = Field(ge=1, le=200, description="Turn number in dialogue")

    # Context
    phase: Phase
    model: str = Field(description="Model ID being tested")
    system_prompt_version: str = Field(pattern=r"^.+@sha256:[a-f0-9]{64}$")
    rubric_version: str = Field(pattern=r"^.+@sha256:[a-f0-9]{64}$")
    seed_id: str = Field(description="Seed scenario ID")
    temperature: float = Field(ge=0, le=2)
    window_tokens: int = Field(ge=0, description="Context window size at this turn")

    # Content
    user_text: str = Field(max_length=10000)
    assistant_text: str = Field(max_length=10000)

    # Scoring (embedded)
    heuristic: HeuristicResult
    judge: Optional[JudgeResult] = Field(
        None, description="None if heuristic passed without judge review"
    )

    # CSD Features (long-context awareness)
    salient_refs: List[SalienceReference] = Field(default_factory=list)
    decoy_refs: List[DecoyReference] = Field(default_factory=list)
    question_type: Optional[QuestionType] = None
    template_match: Optional[TemplateMatch] = None
    thread_link: Optional[ThreadLink] = None
    contradictions_detected: List[ContradictionDetected] = Field(default_factory=list)
    csd_subscores: Optional[CSDSubscores] = Field(
        None, description="CSD only computed for phases P1+"
    )

    # Computed fields
    @computed_field
    @property
    def score(self) -> float:
        """Final score: prefer judge, fall back to heuristic"""
        base_score = self.judge.score if self.judge else self.heuristic.score

        # Gate CSD: if SD < 7, cap CSD at SD
        if self.csd_subscores:
            if base_score < 7:
                return min(base_score, self.csd_subscores.overall)
            return (base_score + self.csd_subscores.overall) / 2

        return base_score

    @computed_field
    @property
    def violations(self) -> List[ViolationType]:
        """All violations from both heuristic and judge"""
        viols = list(self.heuristic.violations)
        if self.judge:
            viols.extend(v for v in self.judge.violations if v not in viols)
        return viols

    # Cost tracking
    cost_tokens_prompt: int = Field(ge=0)
    cost_tokens_completion: int = Field(ge=0)

    # Metadata
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    redaction_status: RedactionStatus = Field(default=RedactionStatus.NONE)
    pii_detected: bool = False

    # S3 pointer for large payloads (optional)
    s3_full_payload: Optional[str] = Field(
        None, description="s3://bucket/key if rationale/text exceeds DDB limit"
    )


class RunSummary(BaseModel):
    """
    Aggregated metrics for one run (model × seed × temp × phase)
    Stored in S3 scores/ and DynamoDB Runs table
    """

    # Identity
    run_id: str = Field(pattern=r"^[0-9A-HJKMNP-TV-Z]{26}$")
    manifest_id: str = Field(pattern=r"^manifest_\d{8}_[a-f0-9]{8}$")

    # Config
    model: str
    phase: Phase
    seed_id: str
    temperature: float

    # Core metrics
    half_life_turn: Optional[int] = Field(
        None, description="First turn where 3-turn MA drops below 8.0 (None if never)"
    )
    total_turns: int = Field(ge=1)
    compliance_rate: float = Field(
        ge=0, le=1, description="Fraction of turns with score >= 8.0"
    )

    # Violation breakdown
    leading_rate: float = Field(ge=0, le=1)
    advice_leak_rate: float = Field(ge=0, le=1)
    multi_question_rate: float = Field(ge=0, le=1)

    # CSD metrics (P1+ only)
    csd_mean: Optional[float] = Field(None, ge=0, le=10)
    csd_p05: Optional[float] = Field(None, ge=0, le=10, description="5th percentile")
    salience_recall_at_k: Optional[float] = Field(None, ge=0, le=1)
    decoy_leak_rate: Optional[float] = Field(None, ge=0, le=1)
    thread_depth_avg: Optional[float] = Field(None, ge=0)
    contradiction_catch_rate: Optional[float] = Field(None, ge=0, le=1)

    # Meta-adaptation
    meta_cadence_adherence: Optional[float] = Field(
        None, ge=0, le=1, description="Alignment with expected check-in cadence"
    )

    # Score distribution
    mean_score: float = Field(ge=0, le=10)
    p05_score: float = Field(ge=0, le=10)
    p50_score: float = Field(ge=0, le=10)
    p95_score: float = Field(ge=0, le=10)

    # Cost
    token_cost_estimate: Dict[str, float] = Field(
        description="{'usd': 0.87, 'prompt_tokens': 12000, 'completion_tokens': 4500}"
    )

    # Execution metadata
    started_at: datetime
    completed_at: datetime
    duration_seconds: float

    @computed_field
    @property
    def duration_minutes(self) -> float:
        return self.duration_seconds / 60

    # Provenance
    code_image_sha: str = Field(pattern=r"^sha256:[a-f0-9]{64}$")


class RunManifest(BaseModel):
    """
    Immutable snapshot of all configs for reproducibility
    Content-addressed (ID derived from hash)
    """

    # Identity (computed from content)
    manifest_id: str = Field(pattern=r"^manifest_\d{8}_[a-f0-9]{8}$")
    created_at: datetime

    # Model matrix
    models: List[str] = Field(min_length=1, description="Model IDs to test")
    temperatures: List[float] = Field(min_length=1)

    # Config versions (with content hashes)
    seeds_version: str = Field(pattern=r"^.+@sha256:[a-f0-9]{64}$")
    rubric_version: str = Field(pattern=r"^.+@sha256:[a-f0-9]{64}$")
    system_prompt_version: str = Field(pattern=r"^.+@sha256:[a-f0-9]{64}$")
    judge_prompt_version: str = Field(pattern=r"^.+@sha256:[a-f0-9]{64}$")
    phases_version: str = Field(pattern=r"^.+@sha256:[a-f0-9]{64}$")

    # Execution params
    max_turns: int = Field(ge=1, le=200, default=40)
    judge_model: str = Field(description="Judge model ID")

    # Content hash (for integrity)
    @computed_field
    @property
    def content_hash(self) -> str:
        """SHA256 of all config fields (for ID generation)"""
        content = {
            "models": sorted(self.models),
            "temperatures": sorted(self.temperatures),
            "seeds_version": self.seeds_version,
            "rubric_version": self.rubric_version,
            "system_prompt_version": self.system_prompt_version,
            "judge_prompt_version": self.judge_prompt_version,
            "phases_version": self.phases_version,
            "max_turns": self.max_turns,
            "judge_model": self.judge_model,
        }
        content_str = json.dumps(content, sort_keys=True)
        return hashlib.sha256(content_str.encode()).hexdigest()[:8]

    @field_validator("manifest_id")
    @classmethod
    def validate_manifest_id(cls, v: str, values) -> str:
        """Ensure manifest_id matches content hash"""
        # Note: This is a simplified check; in practice, compute after init
        if not v.startswith("manifest_"):
            raise ValueError("manifest_id must start with 'manifest_'")
        return v


class WeeklySummary(BaseModel):
    """
    Aggregated metrics across all runs in a week
    Used for trending and WoW comparisons
    """

    week: str = Field(pattern=r"^\d{4}-W\d{2}$", description="ISO week: YYYY-WNN")
    model: str
    phase: Phase

    # Aggregates
    runs_count: int = Field(ge=1)
    avg_half_life_turn: float
    avg_compliance_rate: float
    avg_csd_mean: Optional[float] = None

    # Violations
    avg_leading_rate: float
    avg_advice_leak_rate: float
    avg_multi_question_rate: float

    # Cost
    total_cost_usd: float
    avg_cost_per_run: float

    # WoW change (compared to previous week)
    wow_half_life_change: Optional[float] = Field(
        None, description="Percent change in half-life vs. last week"
    )
    wow_compliance_change: Optional[float] = None

    # Metadata
    manifest_ids: List[str] = Field(description="All manifests used this week")
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class CalibrationItem(BaseModel):
    """
    Hand-labeled golden example for judge calibration
    Stored separately with strict immutability
    """

    item_id: str = Field(pattern=r"^CAL-[A-Z0-9]{8}$")
    version: str = Field(pattern=r"^golden_set_v\d+$")

    # Content
    user_text: str
    assistant_text: str
    context_turns: List[Dict[str, str]] = Field(
        default_factory=list, description="Prior turns for context"
    )

    # Ground truth (from 2-3 human experts)
    expert_labels: List[Dict[str, float]] = Field(
        min_length=2, description="[{expert_id, form, substance, purity, violations}]"
    )

    @computed_field
    @property
    def consensus_score(self) -> Dict[str, float]:
        """Average of expert scores"""
        if not self.expert_labels:
            return {"form": 0, "substance": 0, "purity": 0}

        return {
            "form": sum(e["form"] for e in self.expert_labels)
            / len(self.expert_labels),
            "substance": sum(e["substance"] for e in self.expert_labels)
            / len(self.expert_labels),
            "purity": sum(e["purity"] for e in self.expert_labels)
            / len(self.expert_labels),
        }

    # Metadata
    created_at: datetime
    notes: Optional[str] = None


# ============================================================================
# Helper Models (Config Registry)
# ============================================================================


class ModelConfig(BaseModel):
    """Model registry entry"""

    model_id: str = Field(pattern=r"^[a-z0-9\-\.]+$")
    provider: str = Field(description="anthropic | openai | meta | mistral")
    endpoint: str = Field(description="Bedrock model ARN or API endpoint")
    version: str
    cost_per_1m_prompt: float = Field(ge=0, description="USD per 1M prompt tokens")
    cost_per_1m_completion: float = Field(
        ge=0, description="USD per 1M completion tokens"
    )
    max_tokens: int = Field(ge=1024, description="Max context window")
    tags: Dict[str, str] = Field(default_factory=dict)


class PhaseProfile(BaseModel):
    """Phase configuration (P0-P3)"""

    phase: Phase
    target_tokens: int = Field(ge=1024)
    target_turns: int = Field(ge=1)
    noise_level: Literal["none", "mild", "medium", "heavy"]
    pressure_tactics: List[str] = Field(
        default_factory=list, description="['just_tell_me', 'give_tips', 'switch_mode']"
    )
    decoys: List[Dict[str, str]] = Field(
        default_factory=list, description="[{item_id, text, planted_at_turn}]"
    )
    meta_cadence: Optional[int] = Field(
        None, description="Expected check-in interval (turns)"
    )


class Seed(BaseModel):
    """Canonical seed scenario"""

    seed_id: str = Field(pattern=r"^[A-Z]{3}-[A-Z0-9\-]+$")
    vector: Literal["elenchus", "maieutics", "aporia"]
    persona: str
    initial_prompt: str
    goals: List[str]
    notes: str


# ============================================================================
# Export all
# ============================================================================

__all__ = [
    # Enums
    "Phase",
    "ViolationType",
    "QuestionType",
    "RedactionStatus",
    # Core entities
    "Turn",
    "RunSummary",
    "RunManifest",
    "WeeklySummary",
    "CalibrationItem",
    # Sub-components
    "HeuristicResult",
    "JudgeResult",
    "CSDSubscores",
    "SalienceReference",
    "DecoyReference",
    "TemplateMatch",
    "ThreadLink",
    "ContradictionDetected",
    # Config
    "ModelConfig",
    "PhaseProfile",
    "Seed",
]
