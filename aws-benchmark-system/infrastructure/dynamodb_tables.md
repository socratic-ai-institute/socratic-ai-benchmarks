# DynamoDB Tables for Socratic Benchmark System

**Billing Mode**: On-Demand (auto-scaling for bursty weekly workload)
**Region**: us-east-1
**Encryption**: AWS-managed (SSE-DDB)

---

## Table Design Philosophy

**Lake-first architecture**: S3 is source-of-truth; DynamoDB for hot queries only

**Tables**:
1. **Runs** - RunSummary data (fast lookups by run_id or model/week)
2. **WeeklySummary** - Pre-aggregated weekly metrics
3. **CalibrationResults** - Weekly canary results

**NOT stored in DynamoDB**:
- Turn-level data (too large; query via Athena)
- Raw prompts/configs (immutable artifacts in S3)

---

## Table 1: Runs

**Purpose**: Fast access to run summaries for dashboard queries

### Schema

| Attribute | Type | Description |
|-----------|------|-------------|
| **PK** | String | `run_id` (ULID) |
| **SK** | String | `model#phase#seed#temp` (composite sort key) |
| manifest_id | String | `manifest_20251105_a7f3e9c2` |
| model | String | `claude-3.5-sonnet` |
| phase | String | `P0 | P1 | P2 | P3` |
| seed_id | String | `EL-ETH-UTIL-DEON-01` |
| temperature | Number | `0.3` |
| dt | String | `2025-11-05` (partition for GSIs) |
| week | String | `2025-W45` (ISO week) |
| half_life_turn | Number | `19` (null if never dropped) |
| total_turns | Number | `40` |
| compliance_rate | Number | `0.82` |
| leading_rate | Number | `0.06` |
| advice_leak_rate | Number | `0.09` |
| multi_question_rate | Number | `0.04` |
| csd_mean | Number | `8.2` |
| csd_p05 | Number | `6.9` |
| mean_score | Number | `8.2` |
| p05_score | Number | `6.9` |
| p50_score | Number | `8.4` |
| p95_score | Number | `9.1` |
| token_cost_usd | Number | `0.87` |
| started_at | String | ISO 8601 timestamp |
| completed_at | String | ISO 8601 timestamp |
| duration_seconds | Number | `142.3` |
| code_image_sha | String | `sha256:8f4e...` |

### Primary Key

- **PK**: `run_id` (unique ULID)
- **SK**: `model#phase#seed#temp` (e.g., `claude-3.5-sonnet#P2#seedA#0.3`)

**Rationale**: Direct lookup by run_id; SK enables filtering within a run (not typically needed, but future-proof)

### Global Secondary Indexes

#### GSI 1: HalfLifeIndex

**Purpose**: "Show me worst-performing runs this week"

| Attribute | Key Type |
|-----------|----------|
| week | HASH (PK) |
| half_life_turn | RANGE (SK) |

**Projected Attributes**: ALL

**Query Example**:
```python
response = dynamodb.query(
    IndexName='HalfLifeIndex',
    KeyConditionExpression='week = :week',
    ExpressionAttributeValues={':week': '2025-W45'},
    ScanIndexForward=True,  # Ascending (earliest half-life first)
    Limit=10
)
# Returns: 10 runs with shortest Socratic half-life
```

#### GSI 2: ComplianceIndex

**Purpose**: "Rank models by compliance rate within a phase"

| Attribute | Key Type |
|-----------|----------|
| week_phase | HASH (PK) |
| compliance_rate | RANGE (SK) |

**Note**: `week_phase` is a computed attribute: `{week}#{phase}` (e.g., `2025-W45#P2`)

**Projected Attributes**: model, compliance_rate, mean_score, half_life_turn

**Query Example**:
```python
response = dynamodb.query(
    IndexName='ComplianceIndex',
    KeyConditionExpression='week_phase = :wp',
    ExpressionAttributeValues={':wp': '2025-W45#P2'},
    ScanIndexForward=False,  # Descending (highest compliance first)
)
# Returns: All P2 runs for week 45, sorted by compliance rate
```

#### GSI 3: ModelWeekIndex

**Purpose**: "Show me all runs for a specific model over last 12 weeks"

| Attribute | Key Type |
|-----------|----------|
| model | HASH (PK) |
| dt | RANGE (SK) |

**Projected Attributes**: ALL

**Query Example**:
```python
response = dynamodb.query(
    IndexName='ModelWeekIndex',
    KeyConditionExpression='model = :model AND dt >= :start_date',
    ExpressionAttributeValues={
        ':model': 'claude-3.5-sonnet',
        ':start_date': '2025-08-05'
    }
)
# Returns: All runs for Claude 3.5 Sonnet since Aug 5
```

### Cost Estimate

**Storage**: ~1 KB/item × 7,200 runs/week × 52 weeks = ~375 MB/year

**Reads** (monthly):
- Dashboard queries: ~10K reads
- Cost: $1.25/million reads × 0.01M = **$0.01**

**Writes** (monthly):
- 4 weeks × 7,200 runs = 28,800 writes
- Cost: $1.25/million writes × 0.03M = **$0.04**

**GSI storage**: ~3 × 375 MB = 1.1 GB (negligible cost)

**Total**: **$0.05/month**

---

## Table 2: WeeklySummary

**Purpose**: Pre-aggregated metrics for fast trending (avoiding re-computation)

### Schema

| Attribute | Type | Description |
|-----------|------|-------------|
| **PK** | String | `week#model` (e.g., `2025-W45#claude-3.5-sonnet`) |
| **SK** | String | `phase#temp` (e.g., `P2#0.3`) |
| week | String | `2025-W45` |
| model | String | `claude-3.5-sonnet` |
| phase | String | `P2` |
| runs_count | Number | `9` (3 seeds × 3 temps) |
| avg_half_life_turn | Number | `18.7` |
| avg_compliance_rate | Number | `0.81` |
| avg_csd_mean | Number | `8.1` |
| avg_leading_rate | Number | `0.07` |
| avg_advice_leak_rate | Number | `0.10` |
| avg_multi_question_rate | Number | `0.05` |
| total_cost_usd | Number | `7.83` |
| avg_cost_per_run | Number | `0.87` |
| wow_half_life_change | Number | `-0.12` (12% worse than last week) |
| wow_compliance_change | Number | `+0.03` |
| manifest_ids | List | `["manifest_20251105_a7f3", ...]` |
| generated_at | String | ISO 8601 timestamp |

### Primary Key

- **PK**: `week#model` (e.g., `2025-W45#claude-3.5-sonnet`)
- **SK**: `phase#temp` (e.g., `P2#0.3`)

**Rationale**: Direct access to weekly trends by model; SK enables phase/temp drill-downs

### Global Secondary Index

#### GSI 4: WeekIndex

**Purpose**: "Compare all models for a specific week/phase"

| Attribute | Key Type |
|-----------|----------|
| week_phase | HASH (PK) |
| avg_half_life_turn | RANGE (SK) |

**Projected Attributes**: model, avg_half_life_turn, avg_compliance_rate, avg_csd_mean

**Query Example**:
```python
response = dynamodb.query(
    IndexName='WeekIndex',
    KeyConditionExpression='week_phase = :wp',
    ExpressionAttributeValues={':wp': '2025-W45#P2'}
)
# Returns: All models for week 45 / phase P2, sorted by half-life
```

### Cost Estimate

**Storage**: ~0.5 KB/item × (5 models × 4 phases × 3 temps) × 52 weeks = ~3.1 MB/year

**Reads/Writes**: Negligible (~1K reads/month, ~60 writes/week)

**Total**: **<$0.01/month**

---

## Table 3: CalibrationResults

**Purpose**: Weekly canary results for judge drift detection

### Schema

| Attribute | Type | Description |
|-----------|------|-------------|
| **PK** | String | `golden_set_version` (e.g., `golden_set_v1`) |
| **SK** | String | `dt` (e.g., `2025-11-05`) |
| judge_model | String | `claude-3-opus` |
| items_tested | Number | `200` |
| avg_deviation | Number | `0.03` |
| max_deviation | Number | `0.08` |
| p95_deviation | Number | `0.06` |
| alert_threshold | Number | `0.05` |
| alert_triggered | Boolean | `true` |
| details_s3 | String | `s3://socratic-bench/calibration/results/2025-11-05.json` |
| generated_at | String | ISO 8601 timestamp |

### Primary Key

- **PK**: `golden_set_version` (e.g., `golden_set_v1`)
- **SK**: `dt` (date string, sortable)

**Rationale**: Track drift over time for a specific golden set version

### Global Secondary Index

#### GSI 5: AlertIndex

**Purpose**: "Show me all weeks where canary triggered an alert"

| Attribute | Key Type |
|-----------|----------|
| alert_triggered | HASH (PK) |
| dt | RANGE (SK) |

**Projected Attributes**: golden_set_version, judge_model, avg_deviation, max_deviation

**Query Example**:
```python
response = dynamodb.query(
    IndexName='AlertIndex',
    KeyConditionExpression='alert_triggered = :true',
    ExpressionAttributeValues={':true': True},
    ScanIndexForward=False,  # Most recent first
    Limit=10
)
# Returns: Last 10 canary alerts
```

### Cost Estimate

**Storage**: ~0.3 KB/item × 52 weeks × 3 golden set versions = ~50 KB/year

**Reads/Writes**: ~100 reads/month, ~4 writes/week

**Total**: **<$0.01/month**

---

## Access Patterns Summary

| Pattern | Table | Index | Complexity |
|---------|-------|-------|------------|
| Get run by ID | Runs | - | O(1) |
| Worst half-life this week | Runs | HalfLifeIndex | O(log N) |
| Top models by compliance (phase) | Runs | ComplianceIndex | O(log N) |
| Model trend over 12 weeks | Runs | ModelWeekIndex | O(log N) |
| Weekly summary for model/phase | WeeklySummary | - | O(1) |
| Compare all models (week/phase) | WeeklySummary | WeekIndex | O(log N) |
| Canary history for golden set | CalibrationResults | - | O(log N) |
| Recent canary alerts | CalibrationResults | AlertIndex | O(log N) |

**All queries**: Single-digit millisecond latency

---

## CDK Table Definitions (TypeScript)

```typescript
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import { RemovalPolicy } from 'aws-cdk-lib';

// Table 1: Runs
const runsTable = new dynamodb.Table(this, 'SocraticBenchRuns', {
  tableName: 'SocraticBench-Runs',
  partitionKey: { name: 'run_id', type: dynamodb.AttributeType.STRING },
  sortKey: { name: 'model_phase_seed_temp', type: dynamodb.AttributeType.STRING },
  billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
  encryption: dynamodb.TableEncryption.AWS_MANAGED,
  pointInTimeRecovery: true,
  removalPolicy: RemovalPolicy.RETAIN,
});

// GSI 1: HalfLifeIndex
runsTable.addGlobalSecondaryIndex({
  indexName: 'HalfLifeIndex',
  partitionKey: { name: 'week', type: dynamodb.AttributeType.STRING },
  sortKey: { name: 'half_life_turn', type: dynamodb.AttributeType.NUMBER },
  projectionType: dynamodb.ProjectionType.ALL,
});

// GSI 2: ComplianceIndex
runsTable.addGlobalSecondaryIndex({
  indexName: 'ComplianceIndex',
  partitionKey: { name: 'week_phase', type: dynamodb.AttributeType.STRING },
  sortKey: { name: 'compliance_rate', type: dynamodb.AttributeType.NUMBER },
  projectionType: dynamodb.ProjectionType.INCLUDE,
  nonKeyAttributes: ['model', 'mean_score', 'half_life_turn'],
});

// GSI 3: ModelWeekIndex
runsTable.addGlobalSecondaryIndex({
  indexName: 'ModelWeekIndex',
  partitionKey: { name: 'model', type: dynamodb.AttributeType.STRING },
  sortKey: { name: 'dt', type: dynamodb.AttributeType.STRING },
  projectionType: dynamodb.ProjectionType.ALL,
});

// Table 2: WeeklySummary
const weeklySummaryTable = new dynamodb.Table(this, 'SocraticBenchWeeklySummary', {
  tableName: 'SocraticBench-WeeklySummary',
  partitionKey: { name: 'week_model', type: dynamodb.AttributeType.STRING },
  sortKey: { name: 'phase_temp', type: dynamodb.AttributeType.STRING },
  billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
  encryption: dynamodb.TableEncryption.AWS_MANAGED,
  removalPolicy: RemovalPolicy.RETAIN,
});

// GSI 4: WeekIndex
weeklySummaryTable.addGlobalSecondaryIndex({
  indexName: 'WeekIndex',
  partitionKey: { name: 'week_phase', type: dynamodb.AttributeType.STRING },
  sortKey: { name: 'avg_half_life_turn', type: dynamodb.AttributeType.NUMBER },
  projectionType: dynamodb.ProjectionType.INCLUDE,
  nonKeyAttributes: ['model', 'avg_compliance_rate', 'avg_csd_mean'],
});

// Table 3: CalibrationResults
const calibrationTable = new dynamodb.Table(this, 'SocraticBenchCalibration', {
  tableName: 'SocraticBench-CalibrationResults',
  partitionKey: { name: 'golden_set_version', type: dynamodb.AttributeType.STRING },
  sortKey: { name: 'dt', type: dynamodb.AttributeType.STRING },
  billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
  encryption: dynamodb.TableEncryption.AWS_MANAGED,
  removalPolicy: RemovalPolicy.RETAIN,
});

// GSI 5: AlertIndex
calibrationTable.addGlobalSecondaryIndex({
  indexName: 'AlertIndex',
  partitionKey: { name: 'alert_triggered', type: dynamodb.AttributeType.BOOLEAN },
  sortKey: { name: 'dt', type: dynamodb.AttributeType.STRING },
  projectionType: dynamodb.ProjectionType.INCLUDE,
  nonKeyAttributes: ['golden_set_version', 'judge_model', 'avg_deviation', 'max_deviation'],
});
```

---

## Data Consistency Strategy

**Writes**:
1. Batch task writes JSONL to S3 (durable, write-ahead)
2. Lambda triggered by S3 event → writes to DynamoDB
3. If DynamoDB write fails → retry with exponential backoff (max 3 attempts)
4. If all retries fail → log to CloudWatch + send alert (S3 is still source-of-truth)

**Reads**:
- Dashboard reads from DynamoDB (fast, eventually consistent)
- Deep analytics read from S3/Athena (strongly consistent, slower)

**Reconciliation**:
- Daily Lambda scans S3 for runs not in DynamoDB → backfills
- Metric: `socratic.dynamodb_lag` (count of missing runs)

---

## Backup & Recovery

**Point-in-Time Recovery**: Enabled (35-day retention)

**On-Demand Backups**: Weekly full backup (retained for 1 year)

**Disaster Recovery**:
- RTO: 4 hours (restore from S3 + reindex)
- RPO: 0 (S3 is source-of-truth; DynamoDB can be rebuilt)

---

## Cost Summary (Monthly)

| Table | Storage | Reads | Writes | GSIs | Total |
|-------|---------|-------|--------|------|-------|
| Runs | $0.01 | $0.01 | $0.04 | $0.03 | $0.09 |
| WeeklySummary | $0.00 | $0.00 | $0.00 | $0.00 | $0.00 |
| CalibrationResults | $0.00 | $0.00 | $0.00 | $0.00 | $0.00 |
| **Total** | | | | | **~$0.10/month** |

**Annual**: ~$1.20

---

## Next Steps

1. Deploy tables via CDK
2. Seed with test data
3. Build aggregation Lambda (S3 → DynamoDB indexer)
4. Test access patterns with sample queries
5. Set up CloudWatch alarms for throttling (should never occur with on-demand)

---

**Related**: See `s3_layout.md` for source-of-truth data storage
