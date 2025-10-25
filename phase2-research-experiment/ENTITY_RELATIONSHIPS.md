# Entity Relationships and Data Flow
## Socratic AI Benchmarks Platform

---

## Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         STUDENT PROFILE                             │
│  PK: STUDENT#<id>  SK: PROFILE                                     │
│                                                                      │
│  • Demographics (age, grade, school)                                │
│  • Learning Profile (depth preference, style)                       │
│  • Consent Data (parent, student, IRB)                             │
│  • Metadata (total_sessions, conditions_completed)                  │
└────────────────┬────────────────────────────────────────────────────┘
                 │
                 │ 1:N (student can have multiple sessions)
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      EXPERIMENTAL SESSION                           │
│  PK: SESSION#<id>  SK: METADATA                                    │
│                                                                      │
│  • Experimental Condition (location, interval, type)               │
│  • Timeline (start, end, durations)                                │
│  • Completion Status (flags for each step)                         │
│  • Student Metadata (denormalized)                                 │
│                                                                      │
│  GSIs:                                                              │
│  • GSI1: CONDITION#location#interval#intervention                  │
│  • GSI2: STUDENT#<id>                                              │
│  • GSI3: LOCATION#<type>                                           │
│  • GSI4: INTERVENTION#<type>                                       │
│  • GSI5: DATE#<YYYY-MM-DD>                                         │
└───┬─────────┬─────────┬─────────┬─────────┬─────────────────────────┘
    │         │         │         │         │
    │         │         │         │         │
    ▼         ▼         ▼         ▼         ▼
┌────────┐ ┌────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│Location│ │Content │ │Interven- │ │Assess-   │ │Post      │
│Verify  │ │Delivery│ │tion (×N) │ │ment (×2-3)│ │Survey    │
└────────┘ └────────┘ └──────────┘ └──────────┘ └──────────┘
    │         │         │             │             │
    │         │         │             │             │
    │         │         │             │             │
    │         │         │             │             │
    ▼         ▼         ▼             ▼             ▼
┌─────────────────────────────────────────────────────────────────┐
│            All children share SESSION#<id> as PK                │
│                                                                  │
│  SK: LOCATION_VERIFICATION                                      │
│  SK: CONTENT_DELIVERY                                           │
│  SK: INTERVENTION#<timestamp>#<segment_id>                      │
│  SK: ASSESSMENT#<type>#<timestamp>                              │
│  SK: POST_SURVEY                                                │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Flow Diagram

```
┌─────────────────┐
│  1. Student     │
│  Registration   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌──────────────────┐
│  2. Condition   │─────▶│  Random          │
│  Assignment     │      │  Assignment      │
└────────┬────────┘      │  to 1 of 24      │
         │               │  Conditions      │
         ▼               └──────────────────┘
┌─────────────────┐
│  3. Create      │
│  Session        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌──────────────────┐
│  4. Location    │─────▶│  GPS/QR/Manual   │
│  Verification   │      │  Verification    │
└────────┬────────┘      └──────────────────┘
         │
         │ If verified = false, terminate session
         ▼
┌─────────────────┐
│  5. Baseline    │
│  Assessment     │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│                6. Content Delivery (10 minutes)                 │
│                                                                  │
│  Segment 1 (0:00 - 2:30) ──► Intervention? ──┐                 │
│                                                │                 │
│  Segment 2 (2:30 - 5:00) ──► Intervention? ──┤                 │
│                                                │                 │
│  Segment 3 (5:00 - 7:30) ──► Intervention? ──┤                 │
│                                                │                 │
│  Segment 4 (7:30 - 10:00) ─► Intervention? ──┘                 │
│                                                                  │
│  Intervention Schedule:                                         │
│  • 2.5 min interval: After each segment (4 interventions)      │
│  • 5.0 min interval: After segments 2 & 4 (2 interventions)   │
│  • 10.0 min interval: After segment 4 only (1 intervention)    │
└────────┬────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────┐
│  7. Final       │
│  Assessment     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  8. Post-Session│
│  Survey         │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌──────────────────────────┐
│  9. Calculate   │─────▶│  Learning Gain           │
│  Outcomes       │      │  = Final - Baseline      │
└────────┬────────┘      │                          │
         │               │  Normalized Gain         │
         │               │  = Gain / (100-Baseline) │
         ▼               └──────────────────────────┘
┌─────────────────┐
│ 10. Update      │
│ Aggregated      │
│ Statistics      │
│ (via Stream)    │
└─────────────────┘
```

---

## Intervention Flow (Dynamic vs Static)

### Dynamic Socratic Intervention

```
┌───────────────────────────────────────────────────────┐
│              Dynamic Intervention Flow                │
└───────────────────────────────────────────────────────┘

Input Context:
├── Content segment summary
├── Student profile (age, grade, depth preference)
├── Location context (on-site, learning-space, etc.)
└── Conversation history (for Q2, Q3)

         │
         ▼
┌─────────────────────────────────────┐
│  Question 1: Opening Inquiry        │
│                                      │
│  • Generate based on content         │
│  • Incorporate location context      │
│  • Match student level               │
│  • Open-ended, thought-provoking     │
└────────────┬────────────────────────┘
             │
             ▼ Student Answer A1
             │
┌────────────┴────────────────────────┐
│  Question 2: Adaptive Follow-up     │
│                                      │
│  • Build directly on A1              │
│  • Probe deeper into understanding   │
│  • Identify gaps or assumptions      │
│  • Challenge or extend thinking      │
└────────────┬────────────────────────┘
             │
             ▼ Student Answer A2
             │
┌────────────┴────────────────────────┐
│  Question 3: Synthesis              │
│                                      │
│  • Connect A1 and A2                 │
│  • Push toward deeper insight        │
│  • Help see patterns/implications    │
│  • Location-integrated conclusion    │
└────────────┬────────────────────────┘
             │
             ▼
         Complete

Store:
├── All 3 questions + answers
├── Quality scores (clarity, depth, accuracy)
├── Timing metrics (response times, generation times)
├── AI metadata (model, tokens, cost)
└── Progression quality (how well Q2/Q3 built on previous)
```

### Static Intervention

```
┌───────────────────────────────────────────────────────┐
│               Static Intervention Flow                │
└───────────────────────────────────────────────────────┘

Input Context:
└── Segment ID (determines which pre-written questions)

         │
         ▼
┌─────────────────────────────────────┐
│  Question 1: Pre-written            │
│  "What stood out most about..."     │
└────────────┬────────────────────────┘
             │
             ▼ Student Answer A1
             │
┌────────────┴────────────────────────┐
│  Question 2: Pre-written            │
│  "Why do you think..."               │
└────────────┬────────────────────────┘
             │
             ▼ Student Answer A2
             │
┌────────────┴────────────────────────┐
│  Question 3: Pre-written            │
│  "What questions do you have..."     │
└────────────┬────────────────────────┘
             │
             ▼
         Complete

Store:
├── All 3 questions + answers
├── Quality scores (answer depth, accuracy only)
├── Timing metrics (response times)
└── Note: No adaptive follow-up
```

---

## Assessment Flow

```
┌─────────────────────────────────────────────────────┐
│               Baseline Assessment                   │
│  (Before any content/interventions)                 │
└────────────┬────────────────────────────────────────┘
             │
             ▼
┌────────────────────────────────────────────────────┐
│  • 10 questions (mix of MC + short answer)         │
│  • Tests prior knowledge                            │
│  • Establishes baseline score                       │
│  • AI-graded short answers                          │
└────────────┬───────────────────────────────────────┘
             │
             ▼ Store baseline score
             │
┌────────────┴────────────────────────────────────────┐
│         Content + Interventions                     │
│         (experimental manipulation)                 │
└────────────┬────────────────────────────────────────┘
             │
             ▼
┌────────────────────────────────────────────────────┐
│               Final Assessment                      │
│  (Same questions as baseline)                       │
└────────────┬───────────────────────────────────────┘
             │
             ▼
┌────────────────────────────────────────────────────┐
│  • Compare final vs baseline                        │
│  • Calculate learning gain                          │
│  • Generate quality scores                          │
│  • Store complete results                           │
└─────────────────────────────────────────────────────┘

Learning Gain Metrics:
├── Absolute Gain = Final - Baseline
├── Normalized Gain = (Final - Baseline) / (100 - Baseline)
├── Relative Gain = (Final - Baseline) / Baseline × 100
└── Effect Size = (Mean_treatment - Mean_control) / Pooled_SD
```

---

## DynamoDB Access Patterns by Research Question

### Research Question 1: "Does location matter?"
**Query Pattern:**
```
Compare learning gains across 4 locations:
├── GSI3: Get all sessions for "on-site"
├── GSI3: Get all sessions for "learning-space"
├── GSI3: Get all sessions for "classroom"
└── GSI3: Get all sessions for "home"

Analysis:
└── ANOVA on learning gains by location
```

---

### Research Question 2: "Does intervention frequency matter?"
**Query Pattern:**
```
Compare learning gains across 3 intervals:
├── Filter sessions with interval = 2.5 min
├── Filter sessions with interval = 5.0 min
└── Filter sessions with interval = 10.0 min

Analysis:
└── ANOVA on learning gains by interval
```

---

### Research Question 3: "Is dynamic AI better than static questions?"
**Query Pattern:**
```
Compare intervention effectiveness:
├── GSI4: Get all "dynamic" interventions
└── GSI4: Get all "static" interventions

Analysis:
├── Compare answer depth scores
├── Compare response times
├── Compare learning gains
└── Calculate effect size (Cohen's d)
```

---

### Research Question 4: "What are interaction effects?"
**Query Pattern:**
```
2×2×2 factorial design:
├── Location (4 levels)
├── Interval (3 levels)
└── Intervention Type (2 levels)

For each of 24 conditions:
└── GSI1: Get sessions for specific condition
    Example: CONDITION#on-site#2.5#dynamic

Analysis:
└── Factorial ANOVA to detect interaction effects
```

---

### Research Question 5: "Does being on-site amplify dynamic interventions?"
**Query Pattern:**
```
Specific condition comparison:
├── GSI1: on-site + 2.5min + dynamic
├── GSI1: on-site + 2.5min + static
├── GSI1: classroom + 2.5min + dynamic
└── GSI1: classroom + 2.5min + static

Analysis:
└── 2×2 interaction: Location × Intervention Type
```

---

## Data Aggregation Pipeline

```
┌────────────────────────────────────────────────┐
│         DynamoDB Streams                       │
│  (captures all item changes in real-time)     │
└────────────┬───────────────────────────────────┘
             │
             ▼
┌────────────────────────────────────────────────┐
│         Lambda Function                        │
│  • Triggered on new session completion         │
│  • Calculate session-level metrics             │
│  • Update aggregated statistics                │
└────────────┬───────────────────────────────────┘
             │
             ├──────► Update Condition Stats
             │        (STATS#CONDITION#...)
             │
             ├──────► Export to S3 (JSON)
             │        s3://bucket/sessions/date=2025-10-23/
             │
             └──────► Send to Analytics Pipeline
                      (for real-time dashboards)

S3 Data Lake Structure:
├── sessions/
│   └── date=2025-10-23/
│       ├── session_001.json
│       ├── session_002.json
│       └── ...
│
├── interventions/
│   └── date=2025-10-23/
│       ├── intervention_001.json
│       └── ...
│
└── assessments/
    └── date=2025-10-23/
        ├── assessment_001.json
        └── ...

Analysis Tools:
├── AWS Athena (SQL queries on S3)
├── AWS Glue (ETL for data transformations)
├── QuickSight (dashboards)
├── Python/R (statistical analysis)
└── Jupyter Notebooks (exploratory analysis)
```

---

## Session State Machine

```
┌─────────────┐
│  CREATED    │ ──► Session record created
└──────┬──────┘     completion_status.completed = false
       │
       ▼
┌─────────────┐
│  VERIFIED   │ ──► Location verified
└──────┬──────┘     completion_status.location_verified = true
       │
       ▼
┌─────────────┐
│  BASELINE   │ ──► Baseline assessment completed
└──────┬──────┘     completion_status.baseline_completed = true
       │
       ▼
┌─────────────┐
│  IN_CONTENT │ ──► Content delivery in progress
└──────┬──────┘     Interventions being recorded
       │            completion_status.interventions_completed = N
       ▼
┌─────────────┐
│  CONTENT_OK │ ──► All content segments completed
└──────┬──────┘     completion_status.content_completed = true
       │
       ▼
┌─────────────┐
│  FINAL_TEST │ ──► Final assessment completed
└──────┬──────┘     completion_status.final_assessment_completed = true
       │
       ▼
┌─────────────┐
│  SURVEYED   │ ──► Post-survey completed
└──────┬──────┘     completion_status.post_survey_completed = true
       │
       ▼
┌─────────────┐
│  COMPLETED  │ ──► All steps done
└─────────────┘     completion_status.completed = true
                    Timeline.session_end = timestamp
```

---

## Condition Assignment Strategy

### Balanced Random Assignment

```python
def assign_condition(student_id: str) -> Dict:
    """
    Randomly assign student to one of 24 conditions
    with balancing to ensure equal distribution
    """

    # Get current counts per condition
    condition_counts = get_condition_counts()

    # Find conditions with lowest counts
    min_count = min(condition_counts.values())
    available_conditions = [
        cond for cond, count in condition_counts.items()
        if count == min_count
    ]

    # Randomly select from available conditions
    condition = random.choice(available_conditions)

    return {
        'location': condition['location'],
        'interval': condition['interval'],
        'intervention': condition['intervention']
    }
```

### Stratified Assignment (Alternative)

```python
def assign_condition_stratified(
    student_id: str,
    age: int,
    prior_knowledge_score: float
) -> Dict:
    """
    Assign to condition while balancing on student characteristics
    """

    # Stratify by age group and prior knowledge
    stratum = f"{age // 2}_{int(prior_knowledge_score)}"

    # Get conditions needing students in this stratum
    available = get_undersampled_conditions_for_stratum(stratum)

    return random.choice(available)
```

---

This entity relationship model ensures:
- **Data integrity** through hierarchical keys
- **Flexible querying** via 5 GSIs
- **Research analytics** support for all experimental comparisons
- **Real-time tracking** via DynamoDB Streams
- **Long-term analysis** via S3 exports
- **Scalability** through single-table design
