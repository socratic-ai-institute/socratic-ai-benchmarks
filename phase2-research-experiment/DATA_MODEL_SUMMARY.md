# Complete DynamoDB Data Model Summary
## Socratic AI Benchmarks Platform

---

## Overview

This data model supports a research platform studying the effectiveness of Socratic AI interventions for learning comprehension across 24 experimental conditions (4 locations × 3 intervals × 2 intervention types).

---

## Files in This Package

1. **DYNAMODB_SCHEMA.md** (51,000+ words)
   - Complete table structure with all entity schemas
   - Detailed attribute definitions and examples
   - Query patterns and DynamoDB code examples
   - Analytics pipeline architecture
   - Cost optimization strategies

2. **types.ts** (1,500+ lines)
   - TypeScript type definitions for all entities
   - Helper types and constants
   - Key builders for DynamoDB operations
   - Validation functions
   - Constants for locations, segments, questions

3. **SCHEMA_QUICK_REFERENCE.md** (14,000+ words)
   - Quick-reference patterns for common operations
   - GSI usage guide with examples
   - Common query snippets
   - Condition codes reference
   - Metrics and analytics formulas

4. **dynamodb_helpers.py** (800+ lines)
   - Python library for database operations
   - Type-safe CRUD operations
   - Query helper functions
   - Analytics calculations
   - Example usage code

5. **ENTITY_RELATIONSHIPS.md** (10,000+ words)
   - Visual entity relationship diagrams
   - Data flow diagrams
   - Intervention flow comparisons
   - Assessment flow charts
   - Session state machine
   - Research question query patterns

6. **DATA_MODEL_SUMMARY.md** (this file)
   - High-level overview
   - Design decisions rationale
   - Implementation checklist

---

## Design Philosophy

### Single-Table Design
**Decision:** All entities in one DynamoDB table with 5 GSIs

**Rationale:**
- Atomic writes for session creation (student + session + location)
- Reduced costs (1 table vs 8+ tables)
- Efficient cross-entity queries
- Simplified backup/restore
- Better performance for hierarchical data (session → interventions → assessments)

**Trade-offs:**
- More complex key design
- Requires careful GSI planning
- Harder to understand initially

---

### Key Structure Strategy

**Pattern:**
```
PK = <ENTITY_TYPE>#<ID>
SK = <RECORD_TYPE>#<OPTIONAL_TIMESTAMP>
```

**Benefits:**
- Single query returns all session data
- Hierarchical relationships preserved
- Flexible sorting by timestamp
- Easy to add new entity types

**Example:**
```
Student:      PK=STUDENT#550e8400,     SK=PROFILE
Session:      PK=SESSION#7f3e8b2a,     SK=METADATA
Intervention: PK=SESSION#7f3e8b2a,     SK=INTERVENTION#2025-10-23T14:34:30Z#1
Assessment:   PK=SESSION#7f3e8b2a,     SK=ASSESSMENT#baseline#2025-10-23T14:30:00Z
```

---

### GSI Strategy

#### GSI1: Experimental Condition
```
GSI1PK = CONDITION#<location>#<interval>#<intervention>
GSI1SK = <timestamp>

Purpose: Compare sessions within same condition
Example: All on-site + 2.5min + dynamic sessions
```

#### GSI2: Student Tracking
```
GSI2PK = STUDENT#<student_id>
GSI2SK = SESSION#<timestamp>

Purpose: Longitudinal student tracking
Example: All sessions for one student over time
```

#### GSI3: Location Analysis
```
GSI3PK = LOCATION#<location_type>
GSI3SK = <timestamp>

Purpose: Location impact analysis
Example: All on-site sessions across conditions
```

#### GSI4: Intervention Type
```
GSI4PK = INTERVENTION#<type>
GSI4SK = <timestamp>

Purpose: Static vs dynamic comparison
Example: All dynamic interventions across all sessions
```

#### GSI5: Time-Series
```
GSI5PK = DATE#<YYYY-MM-DD>
GSI5SK = <timestamp>

Purpose: Daily/weekly/monthly reporting
Example: All sessions on 2025-10-23
```

---

## Entity Summary

### 1. Student Profile
**Purpose:** Store student demographics and consent information

**Key Attributes:**
- Demographics (age, grade, school)
- Learning profile (depth preference, style)
- Consent data (IRB, parent, student)
- Session tracking (total sessions, conditions completed)

**Access:**
- Direct: `PK=STUDENT#<id>, SK=PROFILE`
- All sessions: `GSI2PK=STUDENT#<id>`

---

### 2. Experimental Session
**Purpose:** Core session metadata and condition assignment

**Key Attributes:**
- Experimental condition (location, interval, intervention type)
- Timeline (start, end, durations)
- Completion status (flags for each step)
- Denormalized student metadata

**Access:**
- Direct: `PK=SESSION#<id>, SK=METADATA`
- By condition: `GSI1PK=CONDITION#...`
- By student: `GSI2PK=STUDENT#<id>`
- By location: `GSI3PK=LOCATION#<type>`
- By date: `GSI5PK=DATE#<date>`

---

### 3. Location Verification
**Purpose:** Verify student is in correct location for condition

**Key Attributes:**
- Location data (type, name, address)
- Verification method (GPS, QR, manual, honor system)
- GPS coordinates (if GPS verification)
- Device info (OS, browser, IP)

**Access:**
- Direct: `PK=SESSION#<id>, SK=LOCATION_VERIFICATION`

---

### 4. Content Delivery
**Purpose:** Track student engagement with content

**Key Attributes:**
- Content metadata (ID, version, duration)
- Delivery preferences (format, speed, captions)
- Engagement metrics (pauses, rewinds, completion)
- Segment tracking (4 segments, 2.5 min each)

**Access:**
- Direct: `PK=SESSION#<id>, SK=CONTENT_DELIVERY`

---

### 5. Intervention Record
**Purpose:** Store intervention questions, answers, and quality metrics

**Two Types:**

**5a. Dynamic Intervention:**
- 3 adaptive Socratic questions
- Each question builds on previous answer
- Location-aware prompting
- Quality scores (question clarity, answer depth, progression)
- AI metadata (model, tokens, cost)

**5b. Static Intervention:**
- 3 pre-written reflection questions
- No adaptive follow-up
- Same questions for all students
- Answer quality scores only

**Access:**
- All for session: `PK=SESSION#<id>, SK begins_with INTERVENTION#`
- By type: `GSI4PK=INTERVENTION#<type>`

---

### 6. Assessment Record
**Purpose:** Measure learning gain (baseline vs final)

**Key Attributes:**
- Type (baseline, midpoint, final)
- Questions (mix of multiple choice + short answer)
- Student responses
- AI-graded scoring
- Learning gain metrics (only in final assessment)

**Access:**
- All for session: `PK=SESSION#<id>, SK begins_with ASSESSMENT#`
- Specific: `PK=SESSION#<id>, SK=ASSESSMENT#baseline#<timestamp>`

---

### 7. Post-Session Survey
**Purpose:** Collect subjective experience feedback

**Key Attributes:**
- Location experience (impact rating, enhancement, distraction)
- Intervention experience (helpfulness, engagement, appropriateness)
- Learning experience (difficulty, interest, pacing, overall rating)
- Technical experience (usability, quality, issues)
- Open-ended feedback

**Access:**
- Direct: `PK=SESSION#<id>, SK=POST_SURVEY`

---

### 8. Aggregated Statistics
**Purpose:** Pre-computed condition-level statistics (updated via Streams)

**Key Attributes:**
- Sample statistics (N, completion rate, avg duration)
- Learning outcomes (baseline, final, gains, effect size)
- Intervention metrics (quality, depth, response times)
- Engagement metrics (completion, pauses, rewinds)
- Survey results (avg ratings)

**Access:**
- Direct: `PK=STATS#CONDITION#..., SK=AGGREGATE#<date_range>`

---

## 24 Experimental Conditions

```
Location (4)           Interval (3)      Intervention (2)
──────────────────     ──────────────    ────────────────
1. on-site            × 2.5 minutes    × static
2. learning-space     × 5.0 minutes    × dynamic
3. classroom          × 10.0 minutes
4. home

Total: 4 × 3 × 2 = 24 conditions
```

**Condition Codes:**
```
L1-I1-D: on-site, 2.5min, dynamic
L1-I1-S: on-site, 2.5min, static
L1-I2-D: on-site, 5.0min, dynamic
...
L4-I3-S: home, 10.0min, static
```

---

## Research Questions Supported

### 1. Does physical location affect learning?
**Query:** Compare learning gains across 4 locations
**GSI:** GSI3 (by location)
**Analysis:** One-way ANOVA on learning gains

### 2. Does intervention frequency matter?
**Query:** Compare learning gains across 3 interval types
**GSI:** Filter sessions by interval
**Analysis:** One-way ANOVA on learning gains

### 3. Is dynamic AI better than static questions?
**Query:** Compare intervention effectiveness
**GSI:** GSI4 (by intervention type)
**Analysis:** Independent t-test, effect size (Cohen's d)

### 4. What are interaction effects?
**Query:** 4×3×2 factorial analysis
**GSI:** GSI1 (by condition)
**Analysis:** Factorial ANOVA, interaction plots

### 5. Does on-site amplify dynamic interventions?
**Query:** Specific 2×2 comparison
**GSI:** GSI1 for specific conditions
**Analysis:** 2×2 interaction test

---

## Key Metrics

### Learning Outcomes
```python
# Absolute Gain
absolute_gain = final_score - baseline_score

# Normalized Gain (accounts for ceiling effect)
normalized_gain = (final_score - baseline_score) / (100 - baseline_score)

# Effect Size (Cohen's d)
pooled_sd = sqrt(((n1-1)*sd1² + (n2-1)*sd2²) / (n1+n2-2))
cohens_d = (mean1 - mean2) / pooled_sd

# Interpretation:
# d = 0.2 : small effect
# d = 0.5 : medium effect
# d = 0.8 : large effect
```

### Intervention Quality
```python
# Dynamic Interventions
- Question clarity (1-5)
- Question relevance (1-5)
- Answer depth (1-5)
- Answer accuracy (1-5)
- Progression quality (1-5)
- Location integration (1-5)

# Static Interventions
- Answer depth (1-5)
- Answer accuracy (1-5)
```

### Engagement
```python
- Content completion rate (%)
- Pause count
- Rewind count
- Segment engagement scores (0-1)
- Overall engagement score (0-1)
```

---

## Implementation Checklist

### Phase 1: Infrastructure Setup
- [ ] Create DynamoDB table with CloudFormation/CDK
- [ ] Configure 5 GSIs
- [ ] Enable DynamoDB Streams
- [ ] Set up Lambda for stream processing
- [ ] Create S3 bucket for exports
- [ ] Configure auto-scaling
- [ ] Enable point-in-time recovery
- [ ] Set up CloudWatch alarms

### Phase 2: Core Functionality
- [ ] Implement student registration
- [ ] Implement condition assignment (balanced randomization)
- [ ] Build location verification (GPS/QR/manual)
- [ ] Create baseline assessment system
- [ ] Build content delivery player (audio/text)
- [ ] Implement intervention pause logic (2.5/5/10 min)
- [ ] Create static question display
- [ ] Build dynamic Socratic AI question generator
- [ ] Implement final assessment
- [ ] Create post-session survey

### Phase 3: Data Collection
- [ ] Test student profile creation
- [ ] Test session initialization
- [ ] Test location verification flows
- [ ] Test assessment scoring (AI-graded)
- [ ] Test intervention recording (static)
- [ ] Test intervention recording (dynamic)
- [ ] Test completion status tracking
- [ ] Test DynamoDB Stream → Lambda → S3 pipeline

### Phase 4: Analytics
- [ ] Build query functions for each GSI
- [ ] Implement learning gain calculations
- [ ] Build condition comparison queries
- [ ] Create aggregated statistics updater
- [ ] Build export to S3 functionality
- [ ] Set up Athena for SQL queries
- [ ] Create QuickSight dashboards
- [ ] Build statistical analysis notebooks

### Phase 5: Quality Assurance
- [ ] Validate data integrity (transactions)
- [ ] Test partial session handling
- [ ] Verify timestamp consistency
- [ ] Test GSI query performance
- [ ] Verify AI grading accuracy
- [ ] Test concurrent session handling
- [ ] Verify backup/restore procedures
- [ ] Load test with expected throughput

---

## Cost Estimates

### DynamoDB Costs (per month)
```
Assumptions:
- 100 sessions/day
- 30 days = 3,000 sessions/month
- 10 items per session average
- 30,000 items/month written
- 100,000 reads/month

Provisioned Capacity:
- Table: 10 WCU × $0.65 = $6.50
- Table: 10 RCU × $0.13 = $1.30
- GSI1-5: 25 WCU × $0.65 = $16.25
- GSI1-5: 25 RCU × $0.13 = $3.25

Storage:
- 1 GB × $0.25 = $0.25

Total: ~$27.55/month
```

### Lambda Costs
```
Streams processing:
- 30,000 invocations/month
- 256 MB memory
- 2 second avg duration

Cost: ~$1.50/month
```

### S3 Costs
```
Storage:
- 5 GB/month × $0.023 = $0.12

Requests:
- 30,000 PUTs × $0.005/1000 = $0.15

Total: ~$0.27/month
```

### Total Platform Cost
```
DynamoDB: $27.55
Lambda: $1.50
S3: $0.27
CloudWatch: $2.00
─────────────────
Total: ~$31.32/month

Per session: $0.01
```

---

## Security & Compliance

### Data Protection
- Encryption at rest (AWS-managed KMS)
- Encryption in transit (TLS 1.2+)
- Point-in-time recovery (35 days)
- On-demand backups before major changes

### Access Control
- IAM roles for least-privilege access
- Separate roles for read/write operations
- Lambda execution roles scoped to specific actions
- S3 bucket policies for analytics access

### Privacy & Compliance
- Student data anonymized (UUIDs, no PII)
- IRB consent tracking (parent + student)
- Data retention policies
- FERPA compliance considerations
- Right to deletion (remove student + sessions)

### Audit Trail
- CloudTrail for all API calls
- DynamoDB Streams capture all changes
- S3 versioning for exported data
- CloudWatch logs for Lambda processing

---

## Monitoring & Alerts

### CloudWatch Metrics
- Read/write capacity consumption
- Throttled requests (alert if > 0)
- System errors
- User errors
- Conditional check failures
- Lambda invocation errors
- S3 upload failures

### Custom Metrics
- Sessions created per hour
- Session completion rate
- Average session duration
- Intervention completion rate
- Assessment scoring errors

### Alerts
```python
# Example: Alert if throttled reads
Alarm: ThrottledReads
Metric: UserErrors
Threshold: > 0
Period: 1 minute
Action: SNS notification to ops team
```

---

## Performance Optimization

### Read Optimization
- Use GSIs for all common query patterns
- Batch reads where possible
- Project only needed attributes in GSIs
- Use consistent reads only when necessary

### Write Optimization
- Batch writes for related items
- Use transactions for atomic operations
- Compress large attributes (surveys, AI metadata)
- Denormalize frequently accessed data

### Cost Optimization
- Auto-scaling for variable load
- Use provisioned capacity (cheaper than on-demand)
- Archive old sessions to S3 (cheaper storage)
- Use Athena for historical analysis (query S3, not DynamoDB)

---

## Next Steps

1. **Review all documentation files** in this package
2. **Deploy infrastructure** (CloudFormation/CDK)
3. **Implement core application** using helper libraries
4. **Pilot test** with 10 students across 2-3 conditions
5. **Validate data integrity** and query patterns
6. **Launch full study** with balanced assignment
7. **Monitor performance** and costs
8. **Export data** for statistical analysis
9. **Publish findings** in research journals

---

## Support & Documentation

### File Reference
```
/DYNAMODB_SCHEMA.md          → Detailed schema documentation
/types.ts                     → TypeScript type definitions
/SCHEMA_QUICK_REFERENCE.md   → Quick query patterns
/dynamodb_helpers.py         → Python helper library
/ENTITY_RELATIONSHIPS.md     → Visual diagrams and flows
/DATA_MODEL_SUMMARY.md       → This file
```

### Example Queries
See `SCHEMA_QUICK_REFERENCE.md` for 20+ example queries covering:
- Session retrieval
- Condition comparisons
- Student tracking
- Location analysis
- Intervention comparisons
- Learning gain calculations
- Daily dashboards

### Helper Functions
See `dynamodb_helpers.py` for ready-to-use functions:
- `create_student()`
- `create_session()`
- `record_location_verification()`
- `record_dynamic_intervention()`
- `record_static_intervention()`
- `record_assessment()`
- `get_sessions_by_condition()`
- `calculate_learning_gains()`

---

## Summary

This DynamoDB data model provides:

✅ **Complete schema** for all 8 entity types
✅ **5 GSIs** supporting all research questions
✅ **Atomic operations** via transactions
✅ **Real-time aggregation** via DynamoDB Streams
✅ **Long-term analysis** via S3 exports
✅ **Type safety** via TypeScript definitions
✅ **Helper libraries** in Python
✅ **Cost efficiency** (~$31/month for 3,000 sessions)
✅ **Scalability** to 100,000+ sessions
✅ **Security** with encryption and access controls
✅ **Compliance** with IRB and FERPA

Ready for immediate implementation and deployment.
