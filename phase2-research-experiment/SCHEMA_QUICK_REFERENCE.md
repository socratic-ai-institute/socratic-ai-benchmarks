# DynamoDB Schema Quick Reference
## Socratic AI Benchmarks Platform

---

## Table Structure at a Glance

```
Table: SocraticBenchmarks
├── Primary Keys: PK (Hash), SK (Range)
└── GSIs (5):
    ├── GSI1: By Condition (location + interval + intervention)
    ├── GSI2: By Student (longitudinal tracking)
    ├── GSI3: By Location (location comparison)
    ├── GSI4: By Intervention Type (static vs dynamic)
    └── GSI5: By Date (time-series analytics)
```

---

## Entity Hierarchy

```
STUDENT#<id>
└── PROFILE

SESSION#<id>
├── METADATA
├── LOCATION_VERIFICATION
├── CONTENT_DELIVERY
├── INTERVENTION#<timestamp>#<segment_id> (×4 for 2.5min intervals)
├── ASSESSMENT#baseline#<timestamp>
├── ASSESSMENT#midpoint#<timestamp> (optional)
├── ASSESSMENT#final#<timestamp>
└── POST_SURVEY

STATS#CONDITION#<location>#<interval>#<intervention>
└── AGGREGATE#<date_range>
```

---

## Key Patterns

### Pattern Format
```
PK = <Entity Type>#<ID>
SK = <Record Type>#<Optional Timestamp/Qualifier>
```

### Examples

| Entity | PK | SK |
|--------|----|----|
| Student | `STUDENT#550e8400...` | `PROFILE` |
| Session Metadata | `SESSION#7f3e8b2a...` | `METADATA` |
| Location Check | `SESSION#7f3e8b2a...` | `LOCATION_VERIFICATION` |
| Content | `SESSION#7f3e8b2a...` | `CONTENT_DELIVERY` |
| Intervention | `SESSION#7f3e8b2a...` | `INTERVENTION#2025-10-23T14:34:30Z#1` |
| Baseline Test | `SESSION#7f3e8b2a...` | `ASSESSMENT#baseline#2025-10-23T14:30:00Z` |
| Final Test | `SESSION#7f3e8b2a...` | `ASSESSMENT#final#2025-10-23T15:00:00Z` |
| Survey | `SESSION#7f3e8b2a...` | `POST_SURVEY` |
| Stats | `STATS#CONDITION#on-site#2.5#dynamic` | `AGGREGATE#2025-10-01_2025-10-31` |

---

## GSI Usage Guide

### GSI1: Query by Experimental Condition
**Use when:** Comparing sessions within same condition

```python
GSI1PK = "CONDITION#on-site#2.5#dynamic"
GSI1SK = "2025-10-23T14:30:00Z"

# Returns: All sessions for on-site + 2.5min intervals + dynamic AI
```

**24 Possible Conditions:**
```
Locations (4):        Intervals (3):    Interventions (2):
├── on-site          ├── 2.5 min       ├── static
├── learning-space   ├── 5.0 min       └── dynamic
├── classroom        └── 10.0 min
└── home

Total: 4 × 3 × 2 = 24 conditions
```

---

### GSI2: Query by Student
**Use when:** Tracking individual student over time

```python
GSI2PK = "STUDENT#550e8400-e29b-41d4-a716-446655440000"
GSI2SK = "SESSION#2025-10-23T14:30:00Z"

# Returns: All sessions for this student, chronologically
```

---

### GSI3: Query by Location
**Use when:** Analyzing location impact

```python
GSI3PK = "LOCATION#on-site"
GSI3SK = "2025-10-23T14:30:00Z"

# Returns: All on-site sessions across all conditions
```

---

### GSI4: Query by Intervention Type
**Use when:** Comparing static vs dynamic interventions

```python
GSI4PK = "INTERVENTION#dynamic"
GSI4SK = "2025-10-23T14:34:30Z"

# Returns: All dynamic AI interventions
```

---

### GSI5: Query by Date
**Use when:** Daily/weekly/monthly reporting

```python
GSI5PK = "DATE#2025-10-23"
GSI5SK = "2025-10-23T14:30:00Z"

# Returns: All sessions on October 23, 2025
```

---

## Common Query Snippets

### 1. Get Complete Session Data
```python
# One query returns everything for a session
response = table.query(
    KeyConditionExpression='PK = :pk',
    ExpressionAttributeValues={
        ':pk': 'SESSION#7f3e8b2a-1c4d-4e9f-b2a1-9d8e7c6b5a4f'
    }
)

# Returns:
# - Session metadata
# - Location verification
# - Content delivery
# - All 4 interventions
# - Baseline + final assessments
# - Post-survey
```

---

### 2. Get All Interventions for Session
```python
response = table.query(
    KeyConditionExpression='PK = :pk AND begins_with(SK, :sk_prefix)',
    ExpressionAttributeValues={
        ':pk': 'SESSION#7f3e8b2a-1c4d-4e9f-b2a1-9d8e7c6b5a4f',
        ':sk_prefix': 'INTERVENTION#'
    }
)

# Returns: All intervention records sorted by timestamp
```

---

### 3. Compare Conditions
```python
# Get all sessions for Condition A
condition_a = table.query(
    IndexName='GSI1',
    KeyConditionExpression='GSI1PK = :condition',
    ExpressionAttributeValues={
        ':condition': 'CONDITION#on-site#2.5#dynamic'
    }
)

# Get all sessions for Condition B
condition_b = table.query(
    IndexName='GSI1',
    KeyConditionExpression='GSI1PK = :condition',
    ExpressionAttributeValues={
        ':condition': 'CONDITION#classroom#5.0#static'
    }
)

# Compare learning outcomes, engagement, etc.
```

---

### 4. Location Impact Analysis
```python
locations = ['on-site', 'learning-space', 'classroom', 'home']

results = {}
for location in locations:
    response = table.query(
        IndexName='GSI3',
        KeyConditionExpression='GSI3PK = :location',
        ExpressionAttributeValues={
            ':location': f'LOCATION#{location}'
        }
    )
    results[location] = response['Items']

# Analyze: Does physical presence at Tredegar improve outcomes?
```

---

### 5. Student Progress Over Time
```python
response = table.query(
    IndexName='GSI2',
    KeyConditionExpression='GSI2PK = :student',
    ExpressionAttributeValues={
        ':student': 'STUDENT#550e8400-e29b-41d4-a716-446655440000'
    },
    ScanIndexForward=True  # Chronological order
)

# Track: How does this student perform across different conditions?
```

---

### 6. Daily Dashboard
```python
# Get today's sessions
response = table.query(
    IndexName='GSI5',
    KeyConditionExpression='GSI5PK = :date',
    ExpressionAttributeValues={
        ':date': 'DATE#2025-10-23'
    }
)

# Dashboard metrics:
# - Total sessions today
# - Completion rate
# - Sessions by location
# - Sessions by condition
```

---

### 7. Intervention Quality Analysis
```python
# Get all dynamic interventions
dynamic = table.query(
    IndexName='GSI4',
    KeyConditionExpression='GSI4PK = :type',
    ExpressionAttributeValues={
        ':type': 'INTERVENTION#dynamic'
    }
)

# Get all static interventions
static = table.query(
    IndexName='GSI4',
    KeyConditionExpression='GSI4PK = :type',
    ExpressionAttributeValues={
        ':type': 'INTERVENTION#static'
    }
)

# Compare:
# - Average answer depth
# - Response times
# - Question quality (dynamic only)
```

---

## Data Integrity Rules

### Atomic Session Creation
```python
# Use transactions for related writes
table.meta.client.transact_write_items(
    TransactItems=[
        {
            'Put': {
                'TableName': 'SocraticBenchmarks',
                'Item': session_metadata,
                'ConditionExpression': 'attribute_not_exists(PK)'
            }
        },
        {
            'Put': {
                'TableName': 'SocraticBenchmarks',
                'Item': location_verification
            }
        },
        {
            'Update': {
                'TableName': 'SocraticBenchmarks',
                'Key': student_key,
                'UpdateExpression': 'ADD metadata.total_sessions :inc'
            }
        }
    ]
)
```

---

### Completion Status Tracking
```python
# Track partial completions
session.completion_status = {
    "completed": False,
    "location_verified": True,    # ✓
    "baseline_completed": True,   # ✓
    "content_completed": True,    # ✓
    "interventions_completed": 2, # Partial (need 4)
    "final_assessment_completed": False,  # ✗
    "post_survey_completed": False        # ✗
}

# Only mark completed=True when ALL steps done
```

---

## Data Flow

### Typical Session Flow

```
1. Student Profile
   └── Check existing or create new
       PK: STUDENT#<id>, SK: PROFILE

2. Session Initialization
   └── Create session metadata
       PK: SESSION#<id>, SK: METADATA

3. Location Verification
   └── Verify student location
       PK: SESSION#<id>, SK: LOCATION_VERIFICATION

4. Baseline Assessment
   └── Test prior knowledge
       PK: SESSION#<id>, SK: ASSESSMENT#baseline#<timestamp>

5. Content Delivery (10 minutes)
   ├── Segment 1 (0:00 - 2:30)
   ├── Segment 2 (2:30 - 5:00)
   ├── Segment 3 (5:00 - 7:30)
   └── Segment 4 (7:30 - 10:00)
       PK: SESSION#<id>, SK: CONTENT_DELIVERY

6. Interventions (based on condition)
   ├── 2.5 min: After each segment (4 interventions)
   ├── 5.0 min: After segments 2 & 4 (2 interventions)
   └── 10.0 min: After segment 4 (1 intervention)
       PK: SESSION#<id>, SK: INTERVENTION#<timestamp>#<segment>

7. Final Assessment
   └── Measure learning gain
       PK: SESSION#<id>, SK: ASSESSMENT#final#<timestamp>

8. Post-Survey
   └── Experience feedback
       PK: SESSION#<id>, SK: POST_SURVEY

9. Statistics Update (via DynamoDB Stream)
   └── Update condition aggregates
       PK: STATS#CONDITION#<...>, SK: AGGREGATE#<range>
```

---

## Condition Codes Reference

### Format: `L<location>-I<interval>-T<type>`

| Code | Location | Interval | Type |
|------|----------|----------|------|
| L1-I1-D | on-site | 2.5 min | dynamic |
| L1-I1-S | on-site | 2.5 min | static |
| L1-I2-D | on-site | 5.0 min | dynamic |
| L1-I2-S | on-site | 5.0 min | static |
| L1-I3-D | on-site | 10.0 min | dynamic |
| L1-I3-S | on-site | 10.0 min | static |
| L2-I1-D | learning-space | 2.5 min | dynamic |
| L2-I1-S | learning-space | 2.5 min | static |
| ... | ... | ... | ... |
| L4-I3-S | home | 10.0 min | static |

**Total:** 24 conditions

---

## Metrics & Analytics

### Learning Outcome Metrics
```python
# Absolute Gain
absolute_gain = final_score - baseline_score

# Normalized Gain (accounts for ceiling effect)
normalized_gain = (final_score - baseline_score) / (100 - baseline_score)

# Effect Size (Cohen's d)
effect_size = (mean_treatment - mean_control) / pooled_std_dev
```

---

### Intervention Quality Metrics

**Dynamic Interventions:**
- Question clarity (1-5)
- Question relevance (1-5)
- Answer depth (1-5)
- Answer accuracy (1-5)
- Progression quality (how well Q2/Q3 build on previous)
- Location integration (how well questions use physical context)

**Static Interventions:**
- Answer depth (1-5)
- Answer accuracy (1-5)
- Response time

---

### Engagement Metrics
- Content completion rate (%)
- Pause count
- Rewind count
- Time per segment
- Overall engagement score (0-1)

---

## Export & Analytics

### DynamoDB Streams → Lambda
```
New Item → Stream Event → Lambda Function
                             ├── Update aggregated stats
                             ├── Export to S3 (JSON)
                             └── Trigger notifications
```

---

### Batch Export to S3
```python
# Export condition data for analysis
aws dynamodb export-table-to-point-in-time \
    --table-arn arn:aws:dynamodb:us-east-1:123456789012:table/SocraticBenchmarks \
    --s3-bucket socratic-benchmarks-exports \
    --s3-prefix conditions/ \
    --export-format DYNAMODB_JSON
```

---

### Athena Queries
```sql
-- After exporting to S3, query with Athena
SELECT
    experimental_condition.location,
    experimental_condition.interval_minutes,
    experimental_condition.intervention_type,
    AVG(learning_gain.absolute_gain) as avg_gain,
    AVG(learning_gain.normalized_gain) as avg_normalized_gain,
    COUNT(*) as n
FROM sessions
WHERE completion_status.completed = true
GROUP BY
    experimental_condition.location,
    experimental_condition.interval_minutes,
    experimental_condition.intervention_type
ORDER BY avg_normalized_gain DESC;
```

---

## Cost Optimization

### Provisioned Capacity
```
Table:
- Read: 10 RCU
- Write: 10 WCU

GSI1-GSI5:
- Read: 5 RCU each
- Write: 5 WCU each
```

### Auto-Scaling
```python
# Scale based on utilization
Target: 70% capacity utilization
Min Capacity: 5 RCU/WCU
Max Capacity: 100 RCU/WCU
```

### Cost Estimates (per month)
```
Assumptions:
- 100 sessions/day
- 30 days/month
- 3,000 sessions total

Table Storage: ~$0.25/GB
- Estimated: 1 GB = $0.25

Provisioned Capacity:
- Table: $0.65/WCU/month × 10 = $6.50
- Table: $0.13/RCU/month × 10 = $1.30
- GSIs: ($0.65 × 25) + ($0.13 × 25) = $19.50

Estimated Total: ~$27/month
```

---

## Common Patterns Summary

| Need | GSI | Query Pattern |
|------|-----|---------------|
| All data for one session | Primary | `PK = SESSION#<id>` |
| Compare experimental conditions | GSI1 | `GSI1PK = CONDITION#...` |
| Track student over time | GSI2 | `GSI2PK = STUDENT#<id>` |
| Location impact analysis | GSI3 | `GSI3PK = LOCATION#<type>` |
| Static vs dynamic comparison | GSI4 | `GSI4PK = INTERVENTION#<type>` |
| Daily/weekly reporting | GSI5 | `GSI5PK = DATE#<YYYY-MM-DD>` |

---

## Timestamp Format

**Standard:** ISO 8601 with UTC timezone
```
2025-10-23T14:30:00Z
```

**Date-only keys:**
```
2025-10-23
```

**Date range keys:**
```
2025-10-01_2025-10-31
```

---

## Best Practices

### DO:
✓ Use transactions for related writes
✓ Include all GSI keys when creating sessions
✓ Track completion status granularly
✓ Validate data before writes
✓ Use consistent timestamp format (ISO 8601)
✓ Leverage DynamoDB Streams for real-time aggregation
✓ Export to S3 for long-term analysis

### DON'T:
✗ Write incomplete session data
✗ Skip location verification
✗ Forget to update student metadata
✗ Use inconsistent timestamp formats
✗ Store large binary data in items (use S3 references)
✗ Create hot partitions (GSI keys are well-distributed)

---

## Backup & Recovery

### Point-in-Time Recovery
```
Enabled: Yes
Retention: 35 days
```

### On-Demand Backups
```bash
aws dynamodb create-backup \
    --table-name SocraticBenchmarks \
    --backup-name socratic-benchmarks-$(date +%Y%m%d)
```

---

## Security

### IAM Permissions
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:UpdateItem",
        "dynamodb:Query"
      ],
      "Resource": [
        "arn:aws:dynamodb:*:*:table/SocraticBenchmarks",
        "arn:aws:dynamodb:*:*:table/SocraticBenchmarks/index/*"
      ]
    }
  ]
}
```

### Encryption
```
At Rest: AWS-managed KMS key
In Transit: TLS 1.2+
```

---

## Monitoring

### CloudWatch Metrics
- Read/Write Capacity Units consumed
- Throttled requests
- System errors
- User errors
- Conditional check failures

### Alarms
```python
# Alert if throttled requests > 0
cloudwatch.put_metric_alarm(
    AlarmName='SocraticBenchmarks-ThrottledReads',
    MetricName='UserErrors',
    Namespace='AWS/DynamoDB',
    Statistic='Sum',
    Period=60,
    EvaluationPeriods=1,
    Threshold=1,
    ComparisonOperator='GreaterThanThreshold'
)
```

---

This quick reference covers the essential patterns for working with the Socratic AI Benchmarks DynamoDB schema. For detailed examples and full schema definitions, see `DYNAMODB_SCHEMA.md`.
