# AWS Socratic Benchmark System - Design Decisions

**Version**: 1.0
**Date**: 2025-11-05
**Status**: Architecture Locked

---

## System Overview

Weekly, automated Socratic AI benchmark measuring:
- **Socratic Disposition (SD)**: Per-turn quality (Form, Substance, Purity)
- **Socratic Half-life**: First turn where SD drops below threshold
- **Conversation-level Socratic Dynamism (CSD)**: 8-dimensional long-context evaluation

---

## Architecture Decisions

### 1. Scope & Tenancy

**Decision**: Single-tenant (Socratic AI Institute)
**Tenant Key**: N/A (future: `org_id`)
**Rationale**: Simpler for MVP; add multi-tenancy in v2 if needed

---

### 2. Core Entities

**First-class tables**:
- `Model` - Model registry with endpoint/version metadata
- `RunManifest` - Immutable config snapshot for reproducibility
- `Run` - Execution of model×seed×temp×phase
- `Turn` - Single dialogue turn (denormalized)
- `WeeklySummary` - Aggregated metrics per week
- `CalibrationItem` - Hand-labeled golden set
- `Rubric` - Versioned scoring rubric
- `Prompt` - System/judge prompts (versioned)
- `Seed` - Canonical seed scenarios
- `PhaseProfile` - Context window/noise configs (P0-P3)

**Rationale**: Normalized where it enables joins; denormalized for query performance

---

### 3. Identifiers & Immutability

**Run ID Format**: ULID (time-sortable, 26 chars)
- Example: `01HQVZ3K9XABCDEF1234567890`
- Benefits: chronological ordering, distributed generation, URL-safe

**RunManifest ID**: Content-addressed SHA256
- Format: `manifest_YYYYMMDD_<short-hash>`
- Example: `manifest_20251105_a7f3e9c2`
- Immutable: yes (changes require new manifest)

**Idempotency**: Run ID doubles as idempotency key
- Re-run with same run_id → no-op (S3 check)

**Rationale**: Time-sortable IDs improve partition performance; content addressing prevents silent config drift

---

### 4. Storage Strategy

**Architecture**: Lake-first (S3 as source-of-truth)

**S3 (Primary)**:
```
s3://socratic-bench/
├── raw/dt=YYYY-MM-DD/model=<model_id>/phase=<P0-P3>/
│   └── <run_id>.jsonl (one turn per line)
├── scores/dt=YYYY-MM-DD/
│   └── <run_id>_summary.json
├── curated/week=YYYY-WW/
│   └── weekly_summary.parquet
├── config/
│   ├── models.json
│   ├── rubrics/<version>.json
│   └── prompts/<type>/<version>.txt
└── calibration/
    └── golden_set_v<N>.jsonl
```

**DynamoDB (Hot Queries)**:
- `Runs` table: PK=run_id, SK=model#phase
- `WeeklySummary` table: PK=week#model, SK=phase#temp
- GSI: by half_life, compliance_rate for ranking

**Payload Limits**:
- Turn text (user/assistant): max 10KB in DDB (typical: 2KB)
- Judge rationale: max 5KB in DDB
- Overflow: S3 pointer with byte range

**Rationale**: S3 for analytics (Athena), DynamoDB for dashboard queries

---

### 5. Partitioning

**S3 Hive-style partitions**:
- `dt=YYYY-MM-DD` (PRIMARY - time-series queries)
- `model=<model_id>` (secondary - per-model drill-downs)
- `phase=<P0-P3>` (tertiary - phase comparisons)

**Example**: `s3://socratic-bench/raw/dt=2025-11-05/model=claude-3.5-sonnet/phase=P2/01HQV...jsonl`

**DynamoDB Keys**:
- `Runs` table: PK=`run_id`, SK=`model#phase#seed#temp`
- `WeeklySummary`: PK=`week#model`, SK=`phase#temp`

**GSI** (for rankings):
- `half_life_index`: PK=week, SK=half_life (sort ascending)
- `compliance_index`: PK=week#phase, SK=compliance_rate (sort descending)

**Rationale**: Date-first partitioning optimizes weekly trend queries; model/phase enable comparisons

---

### 6. Schema Normalization

**Decision**: Denormalized Turn record

```python
class Turn:
    run_id: str
    turn_number: int
    # ... user/assistant text
    heuristic: HeuristicResult  # embedded
    judge: JudgeResult          # embedded
    csd_subscores: CSDSubscores # embedded
```

**vs. Normalized** (separate `JudgeResults` table):
- ❌ Slower: requires join for every turn query
- ❌ More complex: 3+ table queries for drill-downs
- ✅ Smaller: avoids denormalization bloat

**Chosen**: Denormalized
**Rationale**: Analytics workload favors read performance over storage; turns are immutable (no update anomalies)

**Versioned References**:
- `rubric_version: str` → `"rubric-1.1@sha256:a7f3..."`
- `system_prompt_version: str` → `"soc-1.2@sha256:9c4d..."`

---

### 7. Retention & Lifecycle

**S3 Lifecycle Policies**:
- `raw/`: 365 days → Glacier Deep Archive
- `scores/`: 180 days → Glacier → 365 days delete
- `curated/`: indefinite (small, aggregated)
- `config/`: indefinite (immutable registry)

**DynamoDB TTL**:
- `Turn` records: no TTL (query via S3/Athena after 90 days)
- `WeeklySummary`: indefinite

**Rationale**: Balance cost (S3 Glacier ~$1/TB/mo) with audit needs

---

### 8. Governance & Provenance

**Tamper Evidence**:
- RunManifest includes SHA256 of all configs/prompts
- Each Run stores: manifest_hash, code_image_sha, timestamp

**Provenance Chain**:
```json
{
  "run_id": "01HQV...",
  "manifest_id": "manifest_20251105_a7f3",
  "code_image": "socratic-runner:v2.3.1@sha256:8f4e...",
  "infrastructure_version": "cdk-v1.2.0",
  "executed_by": "EventBridge cron (weekly)",
  "executed_at": "2025-11-05T03:00:00Z"
}
```

**Audit Trail**: CloudTrail logs all S3/DynamoDB writes

**Rationale**: Research-grade reproducibility; regulatory readiness

---

### 9. PII & Redaction

**Assumption**: Seeds are synthetic/curated (no PII)

**Future-proofing**:
- `Turn.redaction_status`: `none | partial | full`
- `Turn.pii_detected`: `false` (add redaction pipeline if needed)

**Rationale**: Don't over-engineer; add if real PII risk emerges

---

### 10. Scale & Cost

**Expected Load** (weekly):
- Models: 5
- Temps: 3 (0.0, 0.3, 0.7)
- Seeds: 3
- Phases: 4 (P0-P3)
- Turns/run: 40
- **Total turns**: 5 × 3 × 3 × 4 × 40 = **7,200 turns/week**

**Token Usage**:
- Avg prompt: 300 tokens/turn (context growth)
- Avg completion: 150 tokens/turn
- **Total**: 3.24M tokens/week

**Cost Estimate** (Claude 3.5 Sonnet @ $3/$15 per 1M tokens):
- Prompt: 972K × $3 = $2.92
- Completion: 1.08M × $15 = $16.20
- Judge calls (7,200 × 0.8 after heuristics): ~$8
- **Total**: ~$27/week (~$1,400/year)

**AWS Costs**:
- S3: ~$5/month (50GB)
- DynamoDB: ~$10/month (on-demand)
- Batch/Fargate: ~$15/month (2-hour weekly run)
- Athena: ~$5/month (query scans)
- **Total**: ~$35/month (~$420/year)

**Grand Total**: ~$1,820/year

---

### 11. Calibration & Canaries

**CalibrationItem Table**:
- Hand-labeled by 2-3 experts (inter-rater reliability)
- 200-500 items covering all vectors/phases
- Immutable: versioned sets (golden_set_v1, golden_set_v2)

**Weekly Canary**:
- Run judge on calibration set
- Alert if deviation >5% from baseline
- Stored separately: `s3://socratic-bench/calibration/results/YYYY-MM-DD.json`

**Rationale**: Detect judge drift before it contaminates real runs

---

### 12. Replays & Lineage

**Replay Strategy**: Append, don't replace

**Scenario**: Re-run 2025-11-03 with improved prompts
- Old run: `run_id=01HQVA...`, `manifest_id=manifest_20251103_abc123`
- New run: `run_id=01HQVB...`, `manifest_id=manifest_20251103_def456`

**Comparison View**:
```sql
SELECT model, half_life_turn, manifest_id
FROM runs
WHERE dt = '2025-11-03'
ORDER BY manifest_id, model;
```

**Lineage Link**: `Run.replaces_run_id` (optional pointer for supersession)

**Rationale**: Preserves history; enables A/B comparisons

---

### 13. Observability Tiers

**Real-time (CloudWatch EMF)**:
- `socratic.half_life` (avg, p50, p95 by model)
- `socratic.compliance_rate` (avg by phase)
- `socratic.judge_latency` (p95)
- `socratic.cost_per_run` (sum)

**Analytical (Athena/QuickSight)**:
- Violation mix (leading, multi-question, advice leakage)
- CSD subscores (8 dimensions)
- Salience recall, decoy leak rate
- Judge-heuristic agreement

**Alerts (SNS)**:
- Half-life drop >20% WoW → Slack
- Compliance drop >10 pts → email
- Judge-heuristic disagreement >15% → PagerDuty (optional)
- Canary deviation >5% → Slack

**Rationale**: Separate hot-path metrics (EMF) from deep analytics (Athena)

---

### 14. Conversation-Level Socratic Dynamism (CSD)

**8 Sub-metrics** (0-10 scale):
1. **Context Responsiveness (CR)**: Semantic similarity to last user turn
2. **Salience Tracking (ST)**: References important prior facts
3. **Red-Herring Discipline (RHD)**: Avoids planted decoys
4. **Adaptive Probing (AP)**: Question type matches dialogue state
5. **Novelty vs. Template (NVT)**: Avoids canned questions
6. **Thread Continuity (TC)**: Maintains coherent inquiry chains
7. **Contradiction Handling (CH)**: Detects user contradictions
8. **Meta-Adaptation (MA)**: Timely check-ins

**CSD Formula**:
```
CSD = 0.20×CR + 0.20×ST + 0.15×RHD + 0.15×AP + 0.10×NVT + 0.10×TC + 0.05×CH + 0.05×MA
```

**Gating**: If Socratic Disposition (SD) < 7, cap CSD at SD

**Storage**: Embedded in Turn record as `csd_subscores: CSDSubscores`

---

### 15. Phases (Context Window Profiles)

| Phase | Tokens | Turns | Noise | Pressure |
|-------|--------|-------|-------|----------|
| **P0** | 2K | 10 | None | None |
| **P1** | 8K | 15 | Mild | "Just tell me" |
| **P2** | 32K | 20 | Medium | Sidebars + "Give tips" |
| **P3** | 128K+ | 40 | Heavy | Explicit "Switch mode" |

**Test Patterns**:
- Early Decoy, Late Check (RHD)
- Constraint Drift (CH)
- Threading Challenge (TC)
- Noise Flood (CR, ST, NVT)

---

### 16. Judge Design

**Primary Judge**: Claude 3.7 Opus (or strongest available)

**Two-Stage Scoring**:
1. **Heuristic** (fast, rule-based): 30-50% of turns pass without LLM
2. **LLM Judge** (slow, nuanced): remaining turns + all disagreements

**Secondary Judge** (tie-breaker): Triggered if |heuristic - judge| > 2 points

**Calibration**: Weekly canary on golden set

**Versioning**: Judge prompt pinned (e.g., `judge-2.3@sha256:...`)

---

### 17. Deployment Model

**Infrastructure as Code**: AWS CDK (TypeScript)

**Containers**:
- `socratic-runner:v<X>` - Dialogue simulation (LangChain)
- `socratic-judge:v<X>` - Judge + heuristics

**Orchestration**: Step Functions (see `infrastructure/step_functions/`)

**Scheduling**: EventBridge cron: `cron(0 3 ? * MON *)` (weekly Monday 3 AM UTC)

**Monitoring**: CloudWatch + X-Ray

---

## Key Trade-offs

| Decision | Chosen | Alternative | Rationale |
|----------|--------|-------------|-----------|
| **ID Format** | ULID | UUIDv4 | Time-sortable improves range queries |
| **Storage** | Lake-first | DDB-first | Analytics workload, cost efficiency |
| **Partitioning** | Date-first | Model-first | Time-series is primary access pattern |
| **Schema** | Denormalized | Normalized | Read performance > storage cost |
| **Judge** | Two-stage | LLM-only | 30-50% cost reduction via heuristics |
| **Replays** | Append | Replace | Preserves history for comparisons |

---

## Next Steps

1. ✅ Lock design decisions (this document)
2. ⏳ Create Pydantic schemas
3. ⏳ Build S3 bucket layout + IAM
4. ⏳ Design DynamoDB tables
5. ⏳ Implement Step Functions orchestrator
6. ⏳ Build dialogue runner (Batch task)
7. ⏳ Implement judge (heuristic + LLM)
8. ⏳ Create CSD feature extractors
9. ⏳ Set up Glue/Athena
10. ⏳ Build QuickSight dashboards

---

**Status**: Design locked, ready for implementation
**Reviewed by**: Claude (AI architect)
**Approved**: 2025-11-05
