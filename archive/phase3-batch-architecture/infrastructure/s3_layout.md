# S3 Bucket Layout

**Bucket Name**: `socratic-bench` (or `socratic-bench-{account-id}` for uniqueness)
**Region**: `us-east-1`
**Encryption**: SSE-S3 (AES-256)
**Versioning**: Enabled for config/ and calibration/

---

## Directory Structure

```
s3://socratic-bench/
│
├── raw/                              # Raw turn data (JSONL)
│   └── dt=YYYY-MM-DD/
│       └── model=<model_id>/
│           └── phase=<P0-P3>/
│               └── <run_id>.jsonl    # One turn per line
│
├── scores/                           # Run summaries
│   └── dt=YYYY-MM-DD/
│       └── <run_id>_summary.json     # RunSummary JSON
│
├── curated/                          # Parquet for analytics
│   └── week=YYYY-WNN/
│       ├── turns.parquet             # All turns (denormalized)
│       └── weekly_summary.parquet    # Pre-aggregated
│
├── config/                           # Immutable config registry
│   ├── models.json                   # ModelConfig list
│   ├── seeds/
│   │   └── seeds-YYYYMMDD@sha256_<hash>.json
│   ├── rubrics/
│   │   └── rubric-1.1@sha256_<hash>.json
│   ├── prompts/
│   │   ├── system/
│   │   │   └── soc-1.2@sha256_<hash>.txt
│   │   └── judge/
│   │       └── judge-2.3@sha256_<hash>.txt
│   └── phases/
│       └── phases-1.0@sha256_<hash>.json
│
├── manifests/                        # Run manifests (immutable)
│   └── manifest_YYYYMMDD_<hash>.json
│
├── calibration/                      # Judge calibration
│   ├── golden_sets/
│   │   └── golden_set_v1.jsonl       # Hand-labeled items
│   └── results/
│       └── YYYY-MM-DD.json           # Weekly canary results
│
└── exports/                          # Ad-hoc exports
    └── YYYY-MM-DD_<export_id>.csv
```

---

## Partition Patterns

### Raw Turns (Hive-style partitioning)

**Path**: `s3://socratic-bench/raw/dt=YYYY-MM-DD/model=<model_id>/phase=<phase>/<run_id>.jsonl`

**Example**:
```
s3://socratic-bench/raw/
├── dt=2025-11-05/
│   ├── model=claude-3.5-sonnet/
│   │   ├── phase=P0/
│   │   │   ├── 01HQVZ3K9X1234567890ABCDEF.jsonl
│   │   │   └── 01HQVZ3K9X9876543210FEDCBA.jsonl
│   │   └── phase=P1/
│   │       └── 01HQVZ3K9XANOTHERULID12345.jsonl
│   └── model=gpt-4-turbo/
│       └── phase=P0/
│           └── 01HQVZ3K9XGPTULID1234567890.jsonl
└── dt=2025-11-12/
    └── ...
```

**Athena Query Example**:
```sql
SELECT model, phase, AVG(score) as avg_score
FROM turns
WHERE dt >= '2025-10-01' AND dt < '2025-11-01'
GROUP BY model, phase;
```

**Benefits**:
- Partition pruning reduces scan cost
- Time-series queries (by date) are fast
- Model comparisons within a date range

---

### Scores (RunSummary)

**Path**: `s3://socratic-bench/scores/dt=YYYY-MM-DD/<run_id>_summary.json`

**Example**:
```json
{
  "run_id": "01HQVZ3K9X1234567890ABCDEF",
  "manifest_id": "manifest_20251105_a7f3e9c2",
  "model": "claude-3.5-sonnet",
  "phase": "P2",
  "half_life_turn": 19,
  "compliance_rate": 0.82,
  "mean_score": 8.2,
  "token_cost_estimate": {"usd": 0.87}
}
```

---

### Curated (Weekly Parquet)

**Path**: `s3://socratic-bench/curated/week=YYYY-WNN/turns.parquet`

**Purpose**: Pre-aggregated Parquet for fast QuickSight queries

**Schema**: Flattened Turn schema (one row per turn, all fields)

**Benefits**:
- Columnar format (much faster than JSONL)
- Pre-partitioned by week
- Direct QuickSight SPICE import

---

## Config Registry (Immutable Artifacts)

### Models

**File**: `s3://socratic-bench/config/models.json`

**Content**:
```json
[
  {
    "model_id": "claude-3.5-sonnet",
    "provider": "anthropic",
    "endpoint": "anthropic.claude-3-5-sonnet-20241022-v2:0",
    "version": "20241022-v2",
    "cost_per_1m_prompt": 3.0,
    "cost_per_1m_completion": 15.0,
    "max_tokens": 200000,
    "tags": {"generation": "3.5", "speed": "balanced"}
  }
]
```

### Seeds

**File**: `s3://socratic-bench/config/seeds/seeds-20251105@sha256_a7f3e9c2.json`

**Naming**: `seeds-<YYYYMMDD>@sha256_<hash>.json` (date + content hash)

**Content**: Array of Seed objects

### Rubrics

**File**: `s3://socratic-bench/config/rubrics/rubric-1.1@sha256_9c4d12e7.json`

**Content**:
```json
{
  "version": "rubric-1.1",
  "dimensions": {
    "form": {
      "weight": 0.2,
      "criteria": ["open_ended", "single_question", "grammatical"]
    },
    "substance": {
      "weight": 0.3,
      "criteria": ["probing_depth", "relevance", "builds_on_prior"]
    },
    "purity": {
      "weight": 0.5,
      "criteria": ["non_directive", "no_advice", "no_leading"]
    }
  }
}
```

### Prompts

**System Prompt**: `s3://socratic-bench/config/prompts/system/soc-1.2@sha256_8f4e56d1.txt`

**Judge Prompt**: `s3://socratic-bench/config/prompts/judge/judge-2.3@sha256_3b9a17c8.txt`

**Versioning**: `<name>-<semver>@sha256_<hash>.txt`

### Phases

**File**: `s3://socratic-bench/config/phases/phases-1.0@sha256_e5f2c9a3.json`

**Content**:
```json
{
  "version": "phases-1.0",
  "profiles": [
    {
      "phase": "P0",
      "target_tokens": 2000,
      "target_turns": 10,
      "noise_level": "none",
      "pressure_tactics": [],
      "decoys": [],
      "meta_cadence": null
    },
    {
      "phase": "P2",
      "target_tokens": 32000,
      "target_turns": 20,
      "noise_level": "medium",
      "pressure_tactics": ["sidebars", "give_tips"],
      "decoys": [
        {"item_id": "d1", "text": "board delayed launch to Q2", "planted_at_turn": 5}
      ],
      "meta_cadence": 6
    }
  ]
}
```

---

## Manifests

**File**: `s3://socratic-bench/manifests/manifest_20251105_a7f3e9c2.json`

**Content**: RunManifest JSON (see schemas/models.py)

**Immutability**: Write-once, never modified

---

## Calibration

### Golden Set

**File**: `s3://socratic-bench/calibration/golden_sets/golden_set_v1.jsonl`

**Format**: JSONL (one CalibrationItem per line)

**Update Cadence**: Quarterly (v1 → v2 → v3)

### Weekly Canary Results

**File**: `s3://socratic-bench/calibration/results/2025-11-05.json`

**Content**:
```json
{
  "date": "2025-11-05",
  "judge_model": "claude-3-opus",
  "golden_set_version": "golden_set_v1",
  "items_tested": 200,
  "avg_deviation": 0.03,
  "max_deviation": 0.08,
  "alert_threshold": 0.05,
  "alert_triggered": true,
  "details": [
    {"item_id": "CAL-A1B2C3D4", "expert_score": 8.2, "judge_score": 7.5, "deviation": 0.7}
  ]
}
```

---

## Lifecycle Policies

### Raw Turns

**Policy**: Transition to Glacier Deep Archive after 365 days

```json
{
  "Rules": [
    {
      "Id": "ArchiveRawTurns",
      "Status": "Enabled",
      "Prefix": "raw/",
      "Transitions": [
        {
          "Days": 365,
          "StorageClass": "DEEP_ARCHIVE"
        }
      ]
    }
  ]
}
```

### Scores

**Policy**: Transition to Glacier after 180 days, delete after 365 days

```json
{
  "Rules": [
    {
      "Id": "ArchiveScores",
      "Status": "Enabled",
      "Prefix": "scores/",
      "Transitions": [
        {
          "Days": 180,
          "StorageClass": "GLACIER"
        }
      ],
      "Expiration": {
        "Days": 365
      }
    }
  ]
}
```

### Config (Immutable, never delete)

**Policy**: No lifecycle (keep forever)

---

## Access Patterns

### Weekly Benchmark Queries

1. **Half-life trend** (last 12 weeks):
   ```sql
   SELECT week, model, AVG(half_life_turn) as avg_half_life
   FROM runs
   WHERE dt >= date_add('week', -12, current_date)
   GROUP BY week, model
   ORDER BY week DESC, avg_half_life DESC;
   ```

2. **Violation mix** (by model):
   ```sql
   SELECT model, violation, COUNT(*) as count
   FROM turns
   CROSS JOIN UNNEST(violations) AS t(violation)
   WHERE dt = '2025-11-05'
   GROUP BY model, violation;
   ```

3. **CSD subscores** (radar chart):
   ```sql
   SELECT model,
          AVG(csd_subscores.CR) as avg_CR,
          AVG(csd_subscores.ST) as avg_ST,
          ...
   FROM turns
   WHERE dt >= '2025-11-01' AND phase = 'P2'
   GROUP BY model;
   ```

---

## Cost Estimates

### Storage (monthly)

| Prefix | Size | Storage Class | Cost/GB | Total |
|--------|------|---------------|---------|-------|
| raw/ | 20 GB | S3 Standard | $0.023 | $0.46 |
| scores/ | 2 GB | S3 Standard | $0.023 | $0.05 |
| curated/ | 10 GB | S3 Standard | $0.023 | $0.23 |
| config/ | 100 MB | S3 Standard | $0.023 | $0.00 |
| **Total** | 32 GB | | | **$0.74** |

### Retrieval (monthly)

- Athena queries: 50 GB scanned × $5/TB = $0.25
- S3 GET requests: 10K × $0.0004/1K = $0.004
- **Total**: $0.25

**Grand Total**: ~$1/month storage + retrieval

---

## S3 Event Notifications

**Trigger**: Lambda on `PUT` to `raw/` → update DynamoDB index

**Configuration**:
```json
{
  "LambdaFunctionConfigurations": [
    {
      "Id": "IndexNewRun",
      "LambdaFunctionArn": "arn:aws:lambda:us-east-1:123456789012:function:IndexRun",
      "Events": ["s3:ObjectCreated:*"],
      "Filter": {
        "Key": {
          "FilterRules": [
            {"Name": "prefix", "Value": "raw/"},
            {"Name": "suffix", "Value": ".jsonl"}
          ]
        }
      }
    }
  ]
}
```

---

## Backup & Disaster Recovery

**Replication**: Enable cross-region replication to `us-west-2` for config/ and calibration/

**Versioning**: Enabled for all immutable artifacts (config/, manifests/, calibration/)

**Recovery**: RTO = 1 hour, RPO = 0 (all writes are durable before acknowledgment)

---

**Next**: See `iam_policies.json` for access control
