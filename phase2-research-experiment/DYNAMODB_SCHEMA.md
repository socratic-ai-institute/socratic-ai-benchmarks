# DynamoDB Schema Design
## Socratic AI Benchmarks Research Platform

---

## Table of Contents
1. [Design Philosophy](#design-philosophy)
2. [Table Structure](#table-structure)
3. [Entity Schemas](#entity-schemas)
4. [Access Patterns](#access-patterns)
5. [Query Examples](#query-examples)
6. [Data Integrity](#data-integrity)
7. [Analytics Pipeline](#analytics-pipeline)

---

## Design Philosophy

### Single-Table Design
Using DynamoDB single-table design pattern for optimal performance and cost efficiency. All entities share one table with strategic use of GSIs for flexible querying.

**Benefits:**
- Atomic writes for related entities
- Reduced costs (one table vs many)
- Efficient cross-entity queries via GSIs
- Simplified backup/restore
- Better performance for hierarchical data

### Key Design Decisions
1. **Single table** with overloaded GSIs for flexible access patterns
2. **Composite keys** to support hierarchical relationships
3. **Time-series optimization** for intervention and assessment data
4. **Denormalization** of frequently accessed student metadata
5. **Event sourcing** for tracking intervention progression

---

## Table Structure

### Primary Table: `SocraticBenchmarks`

**Primary Key:**
- **PK** (Partition Key): String - Entity identifier with hierarchical prefix
- **SK** (Sort Key): String - Entity type or timestamp-based sorting

**Global Secondary Indexes (GSIs):**

#### GSI1: Query by Condition
- **GSI1PK**: Condition composite (location#interval#intervention)
- **GSI1SK**: Session timestamp
- **Purpose**: Aggregate all sessions for a specific experimental condition

#### GSI2: Query by Student
- **GSI2PK**: Student ID
- **GSI2SK**: Session timestamp
- **Purpose**: Retrieve all sessions for a student (longitudinal tracking)

#### GSI3: Query by Location
- **GSI3PK**: Location type
- **GSI3SK**: Session timestamp
- **Purpose**: Location-specific analytics and comparisons

#### GSI4: Query by Intervention Type
- **GSI4PK**: Intervention type (static/dynamic)
- **GSI4SK**: Session timestamp
- **Purpose**: Compare intervention effectiveness across conditions

#### GSI5: Time-Series Analytics
- **GSI5PK**: Date (YYYY-MM-DD)
- **GSI5SK**: Session timestamp
- **Purpose**: Daily/weekly/monthly aggregations and reporting

---

## Entity Schemas

### 1. Student Profile

**Keys:**
```
PK: STUDENT#<student_id>
SK: PROFILE
```

**GSI Keys:**
```
GSI2PK: STUDENT#<student_id>
GSI2SK: PROFILE
```

**Attributes:**
```json
{
  "PK": "STUDENT#550e8400-e29b-41d4-a716-446655440000",
  "SK": "PROFILE",
  "GSI2PK": "STUDENT#550e8400-e29b-41d4-a716-446655440000",
  "GSI2SK": "PROFILE",

  "entity_type": "student_profile",
  "student_id": "550e8400-e29b-41d4-a716-446655440000",

  "demographics": {
    "age": 16,
    "grade_level": 10,
    "school": "Richmond High School",
    "richmond_resident": true
  },

  "learning_profile": {
    "depth_preference": "moderate",
    "learning_style": "visual-auditory",
    "prior_knowledge_topics": ["civil_war", "richmond_history"]
  },

  "consent_data": {
    "parent_consent": true,
    "student_assent": true,
    "irb_consent_date": "2025-10-01T10:30:00Z",
    "data_sharing_consent": true
  },

  "metadata": {
    "created_at": "2025-10-01T10:30:00Z",
    "updated_at": "2025-10-23T14:20:00Z",
    "total_sessions": 0,
    "conditions_completed": []
  }
}
```

---

### 2. Experimental Session

**Keys:**
```
PK: SESSION#<session_id>
SK: METADATA
```

**GSI Keys:**
```
GSI1PK: CONDITION#<location>#<interval>#<intervention>
GSI1SK: <timestamp>
GSI2PK: STUDENT#<student_id>
GSI2SK: SESSION#<timestamp>
GSI3PK: LOCATION#<location_type>
GSI3SK: <timestamp>
GSI4PK: INTERVENTION#<type>
GSI4SK: <timestamp>
GSI5PK: DATE#<YYYY-MM-DD>
GSI5SK: <timestamp>
```

**Attributes:**
```json
{
  "PK": "SESSION#7f3e8b2a-1c4d-4e9f-b2a1-9d8e7c6b5a4f",
  "SK": "METADATA",

  "GSI1PK": "CONDITION#on-site#2.5#dynamic",
  "GSI1SK": "2025-10-23T14:30:00Z",
  "GSI2PK": "STUDENT#550e8400-e29b-41d4-a716-446655440000",
  "GSI2SK": "SESSION#2025-10-23T14:30:00Z",
  "GSI3PK": "LOCATION#on-site",
  "GSI3SK": "2025-10-23T14:30:00Z",
  "GSI4PK": "INTERVENTION#dynamic",
  "GSI4SK": "2025-10-23T14:30:00Z",
  "GSI5PK": "DATE#2025-10-23",
  "GSI5SK": "2025-10-23T14:30:00Z",

  "entity_type": "session",
  "session_id": "7f3e8b2a-1c4d-4e9f-b2a1-9d8e7c6b5a4f",
  "student_id": "550e8400-e29b-41d4-a716-446655440000",

  "experimental_condition": {
    "location": "on-site",
    "location_name": "Tredegar Iron Works",
    "interval_minutes": 2.5,
    "intervention_type": "dynamic",
    "condition_code": "L1-I1-D"
  },

  "timeline": {
    "session_start": "2025-10-23T14:30:00Z",
    "session_end": "2025-10-23T15:12:00Z",
    "total_duration_seconds": 2520,
    "content_duration_seconds": 600,
    "intervention_duration_seconds": 380,
    "assessment_duration_seconds": 540
  },

  "completion_status": {
    "completed": true,
    "location_verified": true,
    "baseline_completed": true,
    "content_completed": true,
    "interventions_completed": 4,
    "final_assessment_completed": true,
    "post_survey_completed": true
  },

  "student_metadata": {
    "age": 16,
    "grade": 10,
    "richmond_resident": true,
    "prior_knowledge_score": 2.5
  },

  "metadata": {
    "created_at": "2025-10-23T14:30:00Z",
    "updated_at": "2025-10-23T15:12:00Z",
    "version": 1,
    "data_quality_flags": []
  }
}
```

---

### 3. Location Verification

**Keys:**
```
PK: SESSION#<session_id>
SK: LOCATION_VERIFICATION
```

**Attributes:**
```json
{
  "PK": "SESSION#7f3e8b2a-1c4d-4e9f-b2a1-9d8e7c6b5a4f",
  "SK": "LOCATION_VERIFICATION",

  "entity_type": "location_verification",
  "session_id": "7f3e8b2a-1c4d-4e9f-b2a1-9d8e7c6b5a4f",
  "student_id": "550e8400-e29b-41d4-a716-446655440000",

  "location_data": {
    "type": "on-site",
    "name": "Tredegar Iron Works",
    "address": "500 Tredegar St, Richmond, VA 23219"
  },

  "verification": {
    "method": "GPS",
    "verified": true,
    "verification_timestamp": "2025-10-23T14:28:00Z",
    "confidence": "high"
  },

  "gps_data": {
    "latitude": 37.5316,
    "longitude": -77.4481,
    "accuracy_meters": 8.5,
    "geofence_validated": true,
    "distance_from_target_meters": 4.2
  },

  "device_info": {
    "device_type": "mobile",
    "os": "iOS 17.1",
    "browser": "Safari 17.0",
    "user_agent": "Mozilla/5.0..."
  },

  "metadata": {
    "timestamp": "2025-10-23T14:28:00Z",
    "ip_address": "192.168.1.100",
    "session_token": "eyJhbGc..."
  }
}
```

---

### 4. Content Delivery

**Keys:**
```
PK: SESSION#<session_id>
SK: CONTENT_DELIVERY
```

**Attributes:**
```json
{
  "PK": "SESSION#7f3e8b2a-1c4d-4e9f-b2a1-9d8e7c6b5a4f",
  "SK": "CONTENT_DELIVERY",

  "entity_type": "content_delivery",
  "session_id": "7f3e8b2a-1c4d-4e9f-b2a1-9d8e7c6b5a4f",
  "student_id": "550e8400-e29b-41d4-a716-446655440000",

  "content_metadata": {
    "content_id": "tredegar-iron-works-v1",
    "content_version": "1.0",
    "topic": "Tredegar Iron Works History",
    "duration_seconds": 600,
    "difficulty_level": "grade_9-12"
  },

  "delivery_preferences": {
    "format_chosen": "audio",
    "playback_speed": 1.0,
    "captions_enabled": false,
    "language": "en-US"
  },

  "engagement_metrics": {
    "start_time": "2025-10-23T14:32:00Z",
    "end_time": "2025-10-23T14:48:35Z",
    "total_play_time_seconds": 600,
    "total_elapsed_time_seconds": 995,
    "pause_count": 4,
    "rewind_count": 2,
    "segments_completed": 4,
    "completion_percentage": 100
  },

  "segment_tracking": [
    {
      "segment_id": 1,
      "start_time": "2025-10-23T14:32:00Z",
      "end_time": "2025-10-23T14:34:30Z",
      "duration_seconds": 150,
      "completed": true,
      "engagement_score": 0.95
    },
    {
      "segment_id": 2,
      "start_time": "2025-10-23T14:37:45Z",
      "end_time": "2025-10-23T14:40:15Z",
      "duration_seconds": 150,
      "completed": true,
      "engagement_score": 0.88
    },
    {
      "segment_id": 3,
      "start_time": "2025-10-23T14:43:20Z",
      "end_time": "2025-10-23T14:45:50Z",
      "duration_seconds": 150,
      "completed": true,
      "engagement_score": 0.92
    },
    {
      "segment_id": 4,
      "start_time": "2025-10-23T14:46:05Z",
      "end_time": "2025-10-23T14:48:35Z",
      "duration_seconds": 150,
      "completed": true,
      "engagement_score": 0.90
    }
  ],

  "metadata": {
    "created_at": "2025-10-23T14:32:00Z",
    "updated_at": "2025-10-23T14:48:35Z"
  }
}
```

---

### 5. Intervention Record

**Keys:**
```
PK: SESSION#<session_id>
SK: INTERVENTION#<timestamp>#<segment_id>
```

**GSI Keys:**
```
GSI4PK: INTERVENTION#<type>
GSI4SK: <timestamp>
```

**Attributes - Dynamic Intervention:**
```json
{
  "PK": "SESSION#7f3e8b2a-1c4d-4e9f-b2a1-9d8e7c6b5a4f",
  "SK": "INTERVENTION#2025-10-23T14:34:30Z#1",

  "GSI4PK": "INTERVENTION#dynamic",
  "GSI4SK": "2025-10-23T14:34:30Z",

  "entity_type": "intervention",
  "session_id": "7f3e8b2a-1c4d-4e9f-b2a1-9d8e7c6b5a4f",
  "student_id": "550e8400-e29b-41d4-a716-446655440000",
  "intervention_id": "int_001",

  "intervention_metadata": {
    "type": "dynamic",
    "sequence_number": 1,
    "timestamp": "2025-10-23T14:34:30Z",
    "segment_id": 1,
    "segment_summary": "Introduction to Tredegar Iron Works and its founding"
  },

  "location_context": {
    "location_type": "on-site",
    "location_name": "Tredegar Iron Works",
    "location_aware_prompting": true
  },

  "socratic_sequence": [
    {
      "question_number": 1,
      "timestamp": "2025-10-23T14:34:30Z",
      "question": "Looking around at the physical space where you're standing, what features suggest this was an industrial site during the 1800s?",
      "question_metadata": {
        "model": "claude-3-5-sonnet-20241022",
        "prompt_tokens": 450,
        "completion_tokens": 42,
        "generation_time_ms": 850,
        "temperature": 0.7
      },
      "answer": "The brick buildings and the proximity to the river. I can see where machinery would have been placed based on the foundation marks.",
      "answer_metadata": {
        "timestamp": "2025-10-23T14:35:15Z",
        "response_time_seconds": 45,
        "word_count": 25,
        "character_count": 142
      },
      "quality_scores": {
        "question_clarity": 4.5,
        "question_relevance": 4.8,
        "answer_depth": 3.2,
        "answer_accuracy": 4.0,
        "engagement_level": 4.3
      }
    },
    {
      "question_number": 2,
      "timestamp": "2025-10-23T14:35:20Z",
      "question": "You mentioned the river proximity. How might the James River have been essential for iron production, given what you just learned about the founding of Tredegar?",
      "question_metadata": {
        "model": "claude-3-5-sonnet-20241022",
        "prompt_tokens": 520,
        "completion_tokens": 38,
        "generation_time_ms": 920,
        "temperature": 0.7,
        "incorporates_previous_answer": true
      },
      "answer": "For transportation of raw materials and finished products, and probably for water power to run the machinery. The river would connect Richmond to other markets.",
      "answer_metadata": {
        "timestamp": "2025-10-23T14:36:05Z",
        "response_time_seconds": 45,
        "word_count": 28,
        "character_count": 168
      },
      "quality_scores": {
        "question_clarity": 4.7,
        "question_relevance": 4.9,
        "answer_depth": 4.1,
        "answer_accuracy": 4.5,
        "engagement_level": 4.6,
        "builds_on_previous": 4.8
      }
    },
    {
      "question_number": 3,
      "timestamp": "2025-10-23T14:36:10Z",
      "question": "You've identified both physical features and the river's role in transportation and power. How does standing here at the actual site change your understanding of why Richmond became such a crucial industrial center during the Civil War?",
      "question_metadata": {
        "model": "claude-3-5-sonnet-20241022",
        "prompt_tokens": 680,
        "completion_tokens": 48,
        "generation_time_ms": 1050,
        "temperature": 0.7,
        "incorporates_previous_answer": true,
        "synthesis_question": true
      },
      "answer": "Being here makes it obvious - it's not just about having an iron works, but about the whole geographic advantage. Richmond had water, transportation, and was far enough south to be protected. The physical reality of the location explains why the Confederacy relied on it so heavily.",
      "answer_metadata": {
        "timestamp": "2025-10-23T14:37:20Z",
        "response_time_seconds": 70,
        "word_count": 52,
        "character_count": 312
      },
      "quality_scores": {
        "question_clarity": 4.9,
        "question_relevance": 5.0,
        "answer_depth": 4.8,
        "answer_accuracy": 4.7,
        "engagement_level": 4.9,
        "synthesis_quality": 4.8,
        "location_integration": 5.0
      }
    }
  ],

  "intervention_summary": {
    "total_duration_seconds": 170,
    "questions_asked": 3,
    "avg_response_time_seconds": 53.3,
    "avg_question_quality": 4.70,
    "avg_answer_depth": 4.03,
    "progression_quality": 4.8,
    "location_awareness_utilized": true
  },

  "ai_metadata": {
    "model_version": "claude-3-5-sonnet-20241022",
    "total_prompt_tokens": 1650,
    "total_completion_tokens": 128,
    "total_cost_usd": 0.0089,
    "avg_generation_time_ms": 940
  },

  "metadata": {
    "created_at": "2025-10-23T14:34:30Z",
    "updated_at": "2025-10-23T14:37:20Z",
    "version": 1
  }
}
```

**Attributes - Static Intervention:**
```json
{
  "PK": "SESSION#8a2f9c3b-2d5e-4f0a-c3b2-0e9f8d7c6b5a",
  "SK": "INTERVENTION#2025-10-23T15:34:30Z#1",

  "GSI4PK": "INTERVENTION#static",
  "GSI4SK": "2025-10-23T15:34:30Z",

  "entity_type": "intervention",
  "session_id": "8a2f9c3b-2d5e-4f0a-c3b2-0e9f8d7c6b5a",
  "student_id": "660f9511-f30c-42e5-b827-557766551111",
  "intervention_id": "int_002",

  "intervention_metadata": {
    "type": "static",
    "sequence_number": 1,
    "timestamp": "2025-10-23T15:34:30Z",
    "segment_id": 1,
    "segment_summary": "Introduction to Tredegar Iron Works and its founding"
  },

  "location_context": {
    "location_type": "classroom",
    "location_name": "Richmond Classroom",
    "location_aware_prompting": false
  },

  "static_questions": [
    {
      "question_number": 1,
      "timestamp": "2025-10-23T15:34:30Z",
      "question": "What stood out to you most about the founding of Tredegar Iron Works?",
      "question_source": "predefined_set_v1",
      "answer": "The fact that it was founded in 1837 and became so important so quickly.",
      "answer_metadata": {
        "timestamp": "2025-10-23T15:35:10Z",
        "response_time_seconds": 40,
        "word_count": 15,
        "character_count": 82
      },
      "quality_scores": {
        "answer_depth": 2.5,
        "answer_accuracy": 3.5,
        "engagement_level": 3.0
      }
    },
    {
      "question_number": 2,
      "timestamp": "2025-10-23T15:35:15Z",
      "question": "Why do you think Richmond became an important industrial center?",
      "question_source": "predefined_set_v1",
      "answer": "Because of the James River and its location in Virginia.",
      "answer_metadata": {
        "timestamp": "2025-10-23T15:35:45Z",
        "response_time_seconds": 30,
        "word_count": 11,
        "character_count": 62
      },
      "quality_scores": {
        "answer_depth": 2.8,
        "answer_accuracy": 3.8,
        "engagement_level": 3.2
      }
    },
    {
      "question_number": 3,
      "timestamp": "2025-10-23T15:35:50Z",
      "question": "What questions do you have about this time period?",
      "question_source": "predefined_set_v1",
      "answer": "How many people worked there and what were the working conditions like?",
      "answer_metadata": {
        "timestamp": "2025-10-23T15:36:30Z",
        "response_time_seconds": 40,
        "word_count": 13,
        "character_count": 73
      },
      "quality_scores": {
        "answer_depth": 3.5,
        "answer_accuracy": 4.0,
        "engagement_level": 3.8
      }
    }
  ],

  "intervention_summary": {
    "total_duration_seconds": 120,
    "questions_asked": 3,
    "avg_response_time_seconds": 36.7,
    "avg_answer_depth": 2.93,
    "no_adaptive_followup": true
  },

  "metadata": {
    "created_at": "2025-10-23T15:34:30Z",
    "updated_at": "2025-10-23T15:36:30Z",
    "version": 1
  }
}
```

---

### 6. Assessment Record

**Keys:**
```
PK: SESSION#<session_id>
SK: ASSESSMENT#<type>#<timestamp>
```

**Attributes - Baseline Assessment:**
```json
{
  "PK": "SESSION#7f3e8b2a-1c4d-4e9f-b2a1-9d8e7c6b5a4f",
  "SK": "ASSESSMENT#baseline#2025-10-23T14:30:00Z",

  "entity_type": "assessment",
  "session_id": "7f3e8b2a-1c4d-4e9f-b2a1-9d8e7c6b5a4f",
  "student_id": "550e8400-e29b-41d4-a716-446655440000",
  "assessment_id": "asmt_baseline_001",

  "assessment_metadata": {
    "type": "baseline",
    "version": "v1.0",
    "timestamp": "2025-10-23T14:30:00Z",
    "duration_seconds": 180,
    "content_topic": "tredegar-iron-works"
  },

  "questions": [
    {
      "question_id": "q1",
      "question_text": "What was the primary industry of Tredegar before the Civil War?",
      "question_type": "multiple_choice",
      "options": [
        "Textile manufacturing",
        "Iron production",
        "Tobacco processing",
        "Shipbuilding"
      ],
      "correct_answer": "Iron production",
      "student_answer": "Iron production",
      "is_correct": true,
      "points": 1,
      "points_earned": 1,
      "response_time_seconds": 12,
      "difficulty": "easy"
    },
    {
      "question_id": "q2",
      "question_text": "During the Civil War, what role did Tredegar Iron Works play for the Confederacy?",
      "question_type": "multiple_choice",
      "options": [
        "Produced uniforms and supplies",
        "Manufactured cannons and munitions",
        "Served as a military headquarters",
        "Processed food for troops"
      ],
      "correct_answer": "Manufactured cannons and munitions",
      "student_answer": "Served as a military headquarters",
      "is_correct": false,
      "points": 1,
      "points_earned": 0,
      "response_time_seconds": 18,
      "difficulty": "medium"
    },
    {
      "question_id": "q3",
      "question_text": "Explain why Richmond's geographic location made it ideal for industrial development.",
      "question_type": "short_answer",
      "rubric_points": 3,
      "student_answer": "Richmond is on a river which helped with transportation.",
      "ai_scoring": {
        "model": "claude-3-5-sonnet-20241022",
        "raw_score": 1.5,
        "rubric_breakdown": {
          "mentions_james_river": 1.0,
          "mentions_transportation": 0.5,
          "mentions_water_power": 0.0,
          "mentions_fall_line": 0.0,
          "mentions_proximity_to_resources": 0.0
        },
        "feedback": "Answer identifies the river and transportation but misses key factors like the fall line, water power, and proximity to coal/iron resources."
      },
      "points": 3,
      "points_earned": 1.5,
      "response_time_seconds": 45,
      "difficulty": "hard"
    }
  ],

  "assessment_results": {
    "total_questions": 10,
    "questions_answered": 10,
    "correct_answers": 6,
    "total_points": 15,
    "points_earned": 9.5,
    "score_percentage": 63.3,
    "avg_response_time_seconds": 18.0
  },

  "scoring_breakdown": {
    "multiple_choice_score": 6.0,
    "multiple_choice_possible": 7.0,
    "short_answer_score": 3.5,
    "short_answer_possible": 8.0,
    "mc_percentage": 85.7,
    "sa_percentage": 43.8
  },

  "metadata": {
    "created_at": "2025-10-23T14:30:00Z",
    "updated_at": "2025-10-23T14:33:00Z",
    "grading_method": "automated_with_ai",
    "version": 1
  }
}
```

**Attributes - Final Assessment:**
```json
{
  "PK": "SESSION#7f3e8b2a-1c4d-4e9f-b2a1-9d8e7c6b5a4f",
  "SK": "ASSESSMENT#final#2025-10-23T15:00:00Z",

  "entity_type": "assessment",
  "session_id": "7f3e8b2a-1c4d-4e9f-b2a1-9d8e7c6b5a4f",
  "student_id": "550e8400-e29b-41d4-a716-446655440000",
  "assessment_id": "asmt_final_001",

  "assessment_metadata": {
    "type": "final",
    "version": "v1.0",
    "timestamp": "2025-10-23T15:00:00Z",
    "duration_seconds": 175,
    "content_topic": "tredegar-iron-works"
  },

  "questions": [
    {
      "question_id": "q1",
      "question_text": "What was the primary industry of Tredegar before the Civil War?",
      "question_type": "multiple_choice",
      "options": [
        "Textile manufacturing",
        "Iron production",
        "Tobacco processing",
        "Shipbuilding"
      ],
      "correct_answer": "Iron production",
      "student_answer": "Iron production",
      "is_correct": true,
      "points": 1,
      "points_earned": 1,
      "response_time_seconds": 8,
      "difficulty": "easy"
    },
    {
      "question_id": "q2",
      "question_text": "During the Civil War, what role did Tredegar Iron Works play for the Confederacy?",
      "question_type": "multiple_choice",
      "options": [
        "Produced uniforms and supplies",
        "Manufactured cannons and munitions",
        "Served as a military headquarters",
        "Processed food for troops"
      ],
      "correct_answer": "Manufactured cannons and munitions",
      "student_answer": "Manufactured cannons and munitions",
      "is_correct": true,
      "points": 1,
      "points_earned": 1,
      "response_time_seconds": 10,
      "difficulty": "medium"
    },
    {
      "question_id": "q3",
      "question_text": "Explain why Richmond's geographic location made it ideal for industrial development.",
      "question_type": "short_answer",
      "rubric_points": 3,
      "student_answer": "Richmond is located on the fall line of the James River, which provided both water power for machinery and transportation for raw materials like coal and iron ore. The river also connected Richmond to ocean ports for shipping finished products. Being far enough south but still accessible made it strategically important.",
      "ai_scoring": {
        "model": "claude-3-5-sonnet-20241022",
        "raw_score": 3.0,
        "rubric_breakdown": {
          "mentions_james_river": 1.0,
          "mentions_transportation": 1.0,
          "mentions_water_power": 1.0,
          "mentions_fall_line": 1.0,
          "mentions_proximity_to_resources": 1.0
        },
        "feedback": "Excellent answer that demonstrates comprehensive understanding of geographic advantages including the fall line, water power, transportation networks, and resource proximity."
      },
      "points": 3,
      "points_earned": 3.0,
      "response_time_seconds": 75,
      "difficulty": "hard"
    }
  ],

  "assessment_results": {
    "total_questions": 10,
    "questions_answered": 10,
    "correct_answers": 9,
    "total_points": 15,
    "points_earned": 14.0,
    "score_percentage": 93.3,
    "avg_response_time_seconds": 17.5
  },

  "scoring_breakdown": {
    "multiple_choice_score": 7.0,
    "multiple_choice_possible": 7.0,
    "short_answer_score": 7.0,
    "short_answer_possible": 8.0,
    "mc_percentage": 100.0,
    "sa_percentage": 87.5
  },

  "learning_gain": {
    "baseline_score": 63.3,
    "final_score": 93.3,
    "absolute_gain": 30.0,
    "relative_gain": 47.4,
    "normalized_gain": 0.82
  },

  "metadata": {
    "created_at": "2025-10-23T15:00:00Z",
    "updated_at": "2025-10-23T15:03:00Z",
    "grading_method": "automated_with_ai",
    "version": 1
  }
}
```

---

### 7. Post-Session Survey

**Keys:**
```
PK: SESSION#<session_id>
SK: POST_SURVEY
```

**Attributes:**
```json
{
  "PK": "SESSION#7f3e8b2a-1c4d-4e9f-b2a1-9d8e7c6b5a4f",
  "SK": "POST_SURVEY",

  "entity_type": "post_survey",
  "session_id": "7f3e8b2a-1c4d-4e9f-b2a1-9d8e7c6b5a4f",
  "student_id": "550e8400-e29b-41d4-a716-446655440000",

  "survey_metadata": {
    "version": "v1.0",
    "timestamp": "2025-10-23T15:10:00Z",
    "duration_seconds": 120
  },

  "location_experience": {
    "location_impact_rating": 5,
    "location_enhanced_understanding": true,
    "location_was_distracting": false,
    "would_recommend_location": true,
    "location_feedback": "Being at the actual site made everything click. I could visualize the processes and understand the geography in a way I never could from just reading about it."
  },

  "intervention_experience": {
    "intervention_helpful_rating": 5,
    "questions_were_engaging": true,
    "questions_were_appropriate": true,
    "questions_promoted_thinking": true,
    "preferred_intervention_type": "dynamic",
    "intervention_feedback": "The questions built on each other really well and made me think deeper about the connections."
  },

  "learning_experience": {
    "content_difficulty_rating": 3,
    "content_interest_rating": 5,
    "pacing_rating": 4,
    "overall_experience_rating": 5,
    "would_recommend_experience": true,
    "general_feedback": "This was way more engaging than just watching a video. The questions made me really think about what I was learning."
  },

  "technical_experience": {
    "interface_easy_to_use": true,
    "audio_quality_rating": 5,
    "technical_issues_encountered": false,
    "technical_feedback": "Everything worked smoothly."
  },

  "open_ended_responses": {
    "most_valuable_aspect": "Being able to connect the physical space to the historical events. The questions helped me see patterns I wouldn't have noticed.",
    "least_valuable_aspect": "Nothing really - it was all helpful.",
    "suggestions_for_improvement": "Maybe add some primary source images during the content segments?",
    "additional_comments": "I learned more in this 10-minute experience than I did in a full class period on this topic."
  },

  "metadata": {
    "created_at": "2025-10-23T15:10:00Z",
    "updated_at": "2025-10-23T15:12:00Z"
  }
}
```

---

### 8. Aggregated Condition Statistics (Materialized View)

**Keys:**
```
PK: STATS#CONDITION#<location>#<interval>#<intervention>
SK: AGGREGATE#<date_range>
```

**Attributes:**
```json
{
  "PK": "STATS#CONDITION#on-site#2.5#dynamic",
  "SK": "AGGREGATE#2025-10-01_2025-10-31",

  "entity_type": "condition_statistics",
  "condition": {
    "location": "on-site",
    "interval": 2.5,
    "intervention": "dynamic"
  },

  "date_range": {
    "start_date": "2025-10-01",
    "end_date": "2025-10-31",
    "days_elapsed": 30
  },

  "sample_statistics": {
    "total_sessions": 45,
    "completed_sessions": 42,
    "completion_rate": 93.3,
    "unique_students": 45,
    "avg_session_duration_seconds": 2485
  },

  "learning_outcomes": {
    "baseline_assessment": {
      "mean_score": 58.3,
      "median_score": 59.0,
      "std_dev": 12.4,
      "min_score": 33.3,
      "max_score": 86.7,
      "n": 42
    },
    "final_assessment": {
      "mean_score": 84.7,
      "median_score": 86.7,
      "std_dev": 8.9,
      "min_score": 60.0,
      "max_score": 100.0,
      "n": 42
    },
    "learning_gain": {
      "mean_absolute_gain": 26.4,
      "median_absolute_gain": 26.7,
      "mean_normalized_gain": 0.65,
      "effect_size_cohens_d": 2.31,
      "students_with_gains": 40,
      "students_with_no_change": 1,
      "students_with_losses": 1
    }
  },

  "intervention_metrics": {
    "avg_interventions_per_session": 4.0,
    "avg_intervention_duration_seconds": 168.5,
    "avg_questions_per_intervention": 3.0,
    "avg_response_time_seconds": 51.2,
    "avg_question_quality_score": 4.58,
    "avg_answer_depth_score": 3.87,
    "avg_progression_quality": 4.62
  },

  "engagement_metrics": {
    "avg_content_completion_rate": 98.7,
    "avg_pause_count": 4.1,
    "avg_rewind_count": 1.8,
    "avg_engagement_score": 0.91
  },

  "survey_results": {
    "avg_location_impact": 4.73,
    "avg_intervention_helpful": 4.81,
    "avg_overall_experience": 4.69,
    "would_recommend_pct": 95.2
  },

  "metadata": {
    "last_updated": "2025-10-31T23:59:59Z",
    "aggregation_version": "v1.0",
    "auto_generated": true
  }
}
```

---

## Access Patterns

### Pattern 1: Retrieve Complete Session Data
**Use Case:** View all data for a single experimental session

```
Query: PK = SESSION#<session_id>
Returns: Session metadata, location verification, content delivery, all interventions, all assessments, post-survey
```

**Example DynamoDB Query:**
```python
response = dynamodb.query(
    TableName='SocraticBenchmarks',
    KeyConditionExpression='PK = :pk',
    ExpressionAttributeValues={
        ':pk': 'SESSION#7f3e8b2a-1c4d-4e9f-b2a1-9d8e7c6b5a4f'
    }
)
```

---

### Pattern 2: Get All Sessions for a Condition
**Use Case:** Compare sessions within same experimental condition

```
Query: GSI1PK = CONDITION#<location>#<interval>#<intervention>
Sort by: GSI1SK (timestamp)
Returns: All session metadata for that condition
```

**Example DynamoDB Query:**
```python
response = dynamodb.query(
    TableName='SocraticBenchmarks',
    IndexName='GSI1',
    KeyConditionExpression='GSI1PK = :condition',
    ExpressionAttributeValues={
        ':condition': 'CONDITION#on-site#2.5#dynamic'
    }
)
```

---

### Pattern 3: Get All Sessions for a Student
**Use Case:** Longitudinal tracking of individual student

```
Query: GSI2PK = STUDENT#<student_id>
Sort by: GSI2SK (timestamp)
Returns: All sessions for that student across conditions
```

**Example DynamoDB Query:**
```python
response = dynamodb.query(
    TableName='SocraticBenchmarks',
    IndexName='GSI2',
    KeyConditionExpression='GSI2PK = :student',
    ExpressionAttributeValues={
        ':student': 'STUDENT#550e8400-e29b-41d4-a716-446655440000'
    }
)
```

---

### Pattern 4: Compare All Locations
**Use Case:** Location-based effectiveness analysis

```
Query: GSI3PK = LOCATION#<location_type>
Sort by: GSI3SK (timestamp)
Returns: All sessions at specific location
```

**Example DynamoDB Query:**
```python
# Get all on-site sessions
response = dynamodb.query(
    TableName='SocraticBenchmarks',
    IndexName='GSI3',
    KeyConditionExpression='GSI3PK = :location',
    ExpressionAttributeValues={
        ':location': 'LOCATION#on-site'
    }
)
```

---

### Pattern 5: Compare Intervention Types
**Use Case:** Static vs Dynamic intervention analysis

```
Query: GSI4PK = INTERVENTION#<type>
Sort by: GSI4SK (timestamp)
Returns: All interventions of specific type
```

**Example DynamoDB Query:**
```python
response = dynamodb.query(
    TableName='SocraticBenchmarks',
    IndexName='GSI4',
    KeyConditionExpression='GSI4PK = :intervention_type',
    ExpressionAttributeValues={
        ':intervention_type': 'INTERVENTION#dynamic'
    }
)
```

---

### Pattern 6: Time-Based Analytics
**Use Case:** Daily/weekly/monthly aggregations

```
Query: GSI5PK = DATE#<YYYY-MM-DD>
Sort by: GSI5SK (timestamp)
Returns: All sessions on specific date
```

**Example DynamoDB Query:**
```python
# Get all sessions from October 23, 2025
response = dynamodb.query(
    TableName='SocraticBenchmarks',
    IndexName='GSI5',
    KeyConditionExpression='GSI5PK = :date',
    ExpressionAttributeValues={
        ':date': 'DATE#2025-10-23'
    }
)
```

---

### Pattern 7: Get Interventions for Session by Time Range
**Use Case:** Analyze intervention progression within session

```
Query: PK = SESSION#<session_id> AND SK BETWEEN INTERVENTION#<start> AND INTERVENTION#<end>
Returns: All interventions in time range
```

**Example DynamoDB Query:**
```python
response = dynamodb.query(
    TableName='SocraticBenchmarks',
    KeyConditionExpression='PK = :pk AND begins_with(SK, :sk_prefix)',
    ExpressionAttributeValues={
        ':pk': 'SESSION#7f3e8b2a-1c4d-4e9f-b2a1-9d8e7c6b5a4f',
        ':sk_prefix': 'INTERVENTION#'
    }
)
```

---

### Pattern 8: Get Baseline vs Final Assessment
**Use Case:** Learning gain calculation

```
Query: PK = SESSION#<session_id> AND SK IN (ASSESSMENT#baseline, ASSESSMENT#final)
Returns: Baseline and final assessments
```

**Example DynamoDB Query:**
```python
response = dynamodb.batch_get_item(
    RequestItems={
        'SocraticBenchmarks': {
            'Keys': [
                {
                    'PK': 'SESSION#7f3e8b2a-1c4d-4e9f-b2a1-9d8e7c6b5a4f',
                    'SK': 'ASSESSMENT#baseline#2025-10-23T14:30:00Z'
                },
                {
                    'PK': 'SESSION#7f3e8b2a-1c4d-4e9f-b2a1-9d8e7c6b5a4f',
                    'SK': 'ASSESSMENT#final#2025-10-23T15:00:00Z'
                }
            ]
        }
    }
)
```

---

## Query Examples

### Example 1: Calculate Average Learning Gain by Condition

```python
import boto3
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('SocraticBenchmarks')

def calculate_learning_gains_by_condition(location, interval, intervention):
    """
    Calculate average learning gains for a specific experimental condition
    """
    # Query all sessions for this condition
    response = table.query(
        IndexName='GSI1',
        KeyConditionExpression='GSI1PK = :condition',
        ExpressionAttributeValues={
            ':condition': f'CONDITION#{location}#{interval}#{intervention}'
        }
    )

    sessions = response['Items']
    learning_gains = []

    # For each session, get baseline and final assessments
    for session in sessions:
        session_id = session['session_id']

        # Get assessments
        assessment_response = table.query(
            KeyConditionExpression='PK = :pk AND begins_with(SK, :sk_prefix)',
            ExpressionAttributeValues={
                ':pk': f'SESSION#{session_id}',
                ':sk_prefix': 'ASSESSMENT#'
            }
        )

        assessments = {a['assessment_metadata']['type']: a
                      for a in assessment_response['Items']}

        if 'baseline' in assessments and 'final' in assessments:
            baseline_score = assessments['baseline']['assessment_results']['score_percentage']
            final_score = assessments['final']['assessment_results']['score_percentage']

            absolute_gain = final_score - baseline_score
            normalized_gain = absolute_gain / (100 - baseline_score) if baseline_score < 100 else 0

            learning_gains.append({
                'session_id': session_id,
                'student_id': session['student_id'],
                'baseline': baseline_score,
                'final': final_score,
                'absolute_gain': absolute_gain,
                'normalized_gain': normalized_gain
            })

    # Calculate statistics
    if learning_gains:
        avg_baseline = sum(g['baseline'] for g in learning_gains) / len(learning_gains)
        avg_final = sum(g['final'] for g in learning_gains) / len(learning_gains)
        avg_absolute_gain = sum(g['absolute_gain'] for g in learning_gains) / len(learning_gains)
        avg_normalized_gain = sum(g['normalized_gain'] for g in learning_gains) / len(learning_gains)

        return {
            'condition': {
                'location': location,
                'interval': interval,
                'intervention': intervention
            },
            'n': len(learning_gains),
            'avg_baseline': avg_baseline,
            'avg_final': avg_final,
            'avg_absolute_gain': avg_absolute_gain,
            'avg_normalized_gain': avg_normalized_gain,
            'individual_gains': learning_gains
        }

    return None

# Example usage
results = calculate_learning_gains_by_condition('on-site', 2.5, 'dynamic')
print(f"Average learning gain: {results['avg_absolute_gain']:.2f} points")
print(f"Normalized gain: {results['avg_normalized_gain']:.2f}")
```

---

### Example 2: Compare Intervention Quality Across Types

```python
def compare_intervention_quality(start_date, end_date):
    """
    Compare question quality and answer depth between static and dynamic interventions
    """
    results = {
        'static': {'questions': [], 'answer_depths': [], 'response_times': []},
        'dynamic': {'questions': [], 'answer_depths': [], 'response_times': []}
    }

    # Query dynamic interventions
    dynamic_response = table.query(
        IndexName='GSI4',
        KeyConditionExpression='GSI4PK = :intervention AND GSI4SK BETWEEN :start AND :end',
        ExpressionAttributeValues={
            ':intervention': 'INTERVENTION#dynamic',
            ':start': start_date,
            ':end': end_date
        }
    )

    for intervention in dynamic_response['Items']:
        summary = intervention['intervention_summary']
        results['dynamic']['questions'].append(summary.get('avg_question_quality', 0))
        results['dynamic']['answer_depths'].append(summary.get('avg_answer_depth', 0))
        results['dynamic']['response_times'].append(summary.get('avg_response_time_seconds', 0))

    # Query static interventions
    static_response = table.query(
        IndexName='GSI4',
        KeyConditionExpression='GSI4PK = :intervention AND GSI4SK BETWEEN :start AND :end',
        ExpressionAttributeValues={
            ':intervention': 'INTERVENTION#static',
            ':start': start_date,
            ':end': end_date
        }
    )

    for intervention in static_response['Items']:
        summary = intervention['intervention_summary']
        results['static']['answer_depths'].append(summary.get('avg_answer_depth', 0))
        results['static']['response_times'].append(summary.get('avg_response_time_seconds', 0))

    # Calculate averages
    comparison = {
        'dynamic': {
            'avg_question_quality': sum(results['dynamic']['questions']) / len(results['dynamic']['questions']) if results['dynamic']['questions'] else 0,
            'avg_answer_depth': sum(results['dynamic']['answer_depths']) / len(results['dynamic']['answer_depths']) if results['dynamic']['answer_depths'] else 0,
            'avg_response_time': sum(results['dynamic']['response_times']) / len(results['dynamic']['response_times']) if results['dynamic']['response_times'] else 0,
            'n': len(results['dynamic']['answer_depths'])
        },
        'static': {
            'avg_answer_depth': sum(results['static']['answer_depths']) / len(results['static']['answer_depths']) if results['static']['answer_depths'] else 0,
            'avg_response_time': sum(results['static']['response_times']) / len(results['static']['response_times']) if results['static']['response_times'] else 0,
            'n': len(results['static']['answer_depths'])
        }
    }

    # Calculate effect size (Cohen's d) for answer depth
    if comparison['dynamic']['n'] > 0 and comparison['static']['n'] > 0:
        import math
        pooled_std = math.sqrt(
            (sum((x - comparison['dynamic']['avg_answer_depth'])**2 for x in results['dynamic']['answer_depths']) +
             sum((x - comparison['static']['avg_answer_depth'])**2 for x in results['static']['answer_depths'])) /
            (comparison['dynamic']['n'] + comparison['static']['n'] - 2)
        )

        cohens_d = (comparison['dynamic']['avg_answer_depth'] - comparison['static']['avg_answer_depth']) / pooled_std
        comparison['effect_size_cohens_d'] = cohens_d

    return comparison

# Example usage
results = compare_intervention_quality('2025-10-01', '2025-10-31')
print(f"Dynamic intervention avg answer depth: {results['dynamic']['avg_answer_depth']:.2f}")
print(f"Static intervention avg answer depth: {results['static']['avg_answer_depth']:.2f}")
print(f"Effect size (Cohen's d): {results.get('effect_size_cohens_d', 'N/A'):.2f}")
```

---

### Example 3: Location Impact Analysis

```python
def analyze_location_impact():
    """
    Compare learning outcomes across all four location types
    """
    locations = ['on-site', 'learning-space', 'classroom', 'home']
    results = {}

    for location in locations:
        # Query all sessions for this location
        response = table.query(
            IndexName='GSI3',
            KeyConditionExpression='GSI3PK = :location',
            ExpressionAttributeValues={
                ':location': f'LOCATION#{location}'
            }
        )

        sessions = response['Items']
        learning_gains = []
        location_ratings = []

        for session in sessions:
            session_id = session['session_id']

            # Get assessments
            assessment_response = table.query(
                KeyConditionExpression='PK = :pk AND begins_with(SK, :sk_prefix)',
                ExpressionAttributeValues={
                    ':pk': f'SESSION#{session_id}',
                    ':sk_prefix': 'ASSESSMENT#'
                }
            )

            assessments = {a['assessment_metadata']['type']: a
                          for a in assessment_response['Items']}

            # Get post-survey
            survey_response = table.get_item(
                Key={
                    'PK': f'SESSION#{session_id}',
                    'SK': 'POST_SURVEY'
                }
            )

            if 'Item' in survey_response:
                survey = survey_response['Item']
                location_ratings.append(survey['location_experience']['location_impact_rating'])

            if 'baseline' in assessments and 'final' in assessments:
                baseline = assessments['baseline']['assessment_results']['score_percentage']
                final = assessments['final']['assessment_results']['score_percentage']
                learning_gains.append(final - baseline)

        results[location] = {
            'n': len(sessions),
            'avg_learning_gain': sum(learning_gains) / len(learning_gains) if learning_gains else 0,
            'avg_location_rating': sum(location_ratings) / len(location_ratings) if location_ratings else 0,
            'std_learning_gain': None  # Calculate if needed
        }

    return results

# Example usage
location_results = analyze_location_impact()
for location, data in location_results.items():
    print(f"{location}: Avg gain = {data['avg_learning_gain']:.2f}, "
          f"Avg rating = {data['avg_location_rating']:.2f}, N = {data['n']}")
```

---

### Example 4: Real-Time Dashboard Query

```python
def get_dashboard_stats(date):
    """
    Get real-time statistics for dashboard display
    """
    # Query all sessions for today
    response = table.query(
        IndexName='GSI5',
        KeyConditionExpression='GSI5PK = :date',
        ExpressionAttributeValues={
            ':date': f'DATE#{date}'
        }
    )

    sessions = response['Items']

    # Calculate stats
    total_sessions = len(sessions)
    completed_sessions = sum(1 for s in sessions if s['completion_status']['completed'])

    conditions = {}
    for session in sessions:
        condition_code = session['experimental_condition']['condition_code']
        if condition_code not in conditions:
            conditions[condition_code] = 0
        conditions[condition_code] += 1

    locations = {}
    for session in sessions:
        location = session['experimental_condition']['location']
        if location not in locations:
            locations[location] = 0
        locations[location] += 1

    return {
        'date': date,
        'total_sessions': total_sessions,
        'completed_sessions': completed_sessions,
        'completion_rate': (completed_sessions / total_sessions * 100) if total_sessions > 0 else 0,
        'sessions_by_condition': conditions,
        'sessions_by_location': locations
    }

# Example usage
dashboard = get_dashboard_stats('2025-10-23')
print(f"Today's sessions: {dashboard['total_sessions']}")
print(f"Completion rate: {dashboard['completion_rate']:.1f}%")
print(f"By location: {dashboard['sessions_by_location']}")
```

---

## Data Integrity

### Atomic Writes

Use DynamoDB transactions to ensure all session data is written atomically:

```python
def create_session_with_verification(session_data, location_data):
    """
    Atomically create session and location verification
    """
    session_id = session_data['session_id']
    timestamp = session_data['timeline']['session_start']

    try:
        table.meta.client.transact_write_items(
            TransactItems=[
                {
                    'Put': {
                        'TableName': 'SocraticBenchmarks',
                        'Item': {
                            'PK': f'SESSION#{session_id}',
                            'SK': 'METADATA',
                            **session_data
                        },
                        'ConditionExpression': 'attribute_not_exists(PK)'
                    }
                },
                {
                    'Put': {
                        'TableName': 'SocraticBenchmarks',
                        'Item': {
                            'PK': f'SESSION#{session_id}',
                            'SK': 'LOCATION_VERIFICATION',
                            **location_data
                        }
                    }
                },
                {
                    'Update': {
                        'TableName': 'SocraticBenchmarks',
                        'Key': {
                            'PK': f'STUDENT#{session_data["student_id"]}',
                            'SK': 'PROFILE'
                        },
                        'UpdateExpression': 'SET metadata.total_sessions = metadata.total_sessions + :inc, metadata.updated_at = :now',
                        'ExpressionAttributeValues': {
                            ':inc': 1,
                            ':now': timestamp
                        }
                    }
                }
            ]
        )
        return True
    except Exception as e:
        print(f"Transaction failed: {e}")
        return False
```

---

### Handling Partial Completions

Track session state with status flags:

```python
def update_session_status(session_id, status_updates):
    """
    Update session completion status atomically
    """
    update_expressions = []
    expression_values = {}

    for key, value in status_updates.items():
        update_expressions.append(f'completion_status.{key} = :{key}')
        expression_values[f':{key}'] = value

    update_expressions.append('metadata.updated_at = :now')
    expression_values[':now'] = datetime.now().isoformat()

    table.update_item(
        Key={
            'PK': f'SESSION#{session_id}',
            'SK': 'METADATA'
        },
        UpdateExpression=f'SET {", ".join(update_expressions)}',
        ExpressionAttributeValues=expression_values
    )

# Example usage
update_session_status(
    'session_123',
    {
        'baseline_completed': True,
        'content_completed': True,
        'interventions_completed': 2  # Partial completion
    }
)
```

---

### Timestamping Strategy

All entities include:
- `created_at`: When entity was first created
- `updated_at`: Last modification timestamp
- Entity-specific timestamps (e.g., intervention timestamp, assessment timestamp)

```python
import datetime

def generate_timestamps():
    """
    Generate consistent timestamp format
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    return {
        'timestamp': now.isoformat(),
        'unix_timestamp': int(now.timestamp()),
        'date': now.strftime('%Y-%m-%d'),
        'time': now.strftime('%H:%M:%S')
    }

# Example usage
timestamps = generate_timestamps()
# Returns: {
#   'timestamp': '2025-10-23T14:30:00Z',
#   'unix_timestamp': 1729692600,
#   'date': '2025-10-23',
#   'time': '14:30:00'
# }
```

---

### Data Validation

Implement validation before writes:

```python
def validate_intervention_data(intervention):
    """
    Validate intervention data before writing to DynamoDB
    """
    required_fields = [
        'session_id',
        'student_id',
        'intervention_metadata',
        'intervention_summary'
    ]

    for field in required_fields:
        if field not in intervention:
            raise ValueError(f"Missing required field: {field}")

    # Validate intervention type
    if intervention['intervention_metadata']['type'] not in ['static', 'dynamic']:
        raise ValueError("Invalid intervention type")

    # Validate dynamic intervention has required fields
    if intervention['intervention_metadata']['type'] == 'dynamic':
        if 'socratic_sequence' not in intervention:
            raise ValueError("Dynamic intervention missing socratic_sequence")

        if len(intervention['socratic_sequence']) != 3:
            raise ValueError("Dynamic intervention must have exactly 3 questions")

    # Validate timestamps
    try:
        datetime.datetime.fromisoformat(intervention['intervention_metadata']['timestamp'].replace('Z', '+00:00'))
    except ValueError:
        raise ValueError("Invalid timestamp format")

    return True
```

---

## Analytics Pipeline

### DynamoDB Streams → Lambda → S3

Configure DynamoDB Streams to trigger Lambda for real-time aggregation and long-term storage:

```python
# Lambda function triggered by DynamoDB Streams
import json
import boto3
from datetime import datetime

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    """
    Process DynamoDB stream events and:
    1. Update aggregated statistics
    2. Export to S3 for long-term analysis
    """

    for record in event['Records']:
        if record['eventName'] == 'INSERT':
            new_item = record['dynamodb']['NewImage']

            # Check entity type
            entity_type = new_item.get('entity_type', {}).get('S', '')

            if entity_type == 'session':
                # Update condition statistics
                update_condition_stats(new_item)

                # Export to S3
                export_to_s3(new_item, 'sessions')

            elif entity_type == 'intervention':
                # Update intervention analytics
                update_intervention_stats(new_item)

                # Export to S3
                export_to_s3(new_item, 'interventions')

            elif entity_type == 'assessment':
                # Update learning outcome stats
                update_assessment_stats(new_item)

                # Export to S3
                export_to_s3(new_item, 'assessments')

    return {
        'statusCode': 200,
        'body': json.dumps('Processing complete')
    }

def update_condition_stats(session_item):
    """
    Update aggregated statistics for the condition
    """
    # Extract condition from GSI1PK
    condition = session_item['GSI1PK']['S']  # e.g., "CONDITION#on-site#2.5#dynamic"

    # Get current month
    month = datetime.now().strftime('%Y-%m')

    table = dynamodb.Table('SocraticBenchmarks')

    # Increment session count
    table.update_item(
        Key={
            'PK': f'STATS#{condition}',
            'SK': f'AGGREGATE#{month}'
        },
        UpdateExpression='ADD sample_statistics.total_sessions :inc SET metadata.last_updated = :now',
        ExpressionAttributeValues={
            ':inc': 1,
            ':now': datetime.now().isoformat()
        }
    )

def export_to_s3(item, entity_type):
    """
    Export item to S3 for long-term storage and analysis
    """
    date = datetime.now().strftime('%Y-%m-%d')
    timestamp = datetime.now().isoformat()

    # Create file key
    key = f'socratic-benchmarks/{entity_type}/date={date}/{timestamp}.json'

    # Convert DynamoDB item to JSON
    item_json = json.dumps(item, default=str)

    # Upload to S3
    s3.put_object(
        Bucket='socratic-benchmarks-data-lake',
        Key=key,
        Body=item_json,
        ContentType='application/json'
    )
```

---

### Batch Export to S3

For analysis in tools like Athena, Glue, or Python notebooks:

```python
def export_condition_to_s3(location, interval, intervention, date_range):
    """
    Export all sessions for a condition to S3 in Parquet format
    """
    import pandas as pd
    import pyarrow.parquet as pq

    # Query all sessions
    response = table.query(
        IndexName='GSI1',
        KeyConditionExpression='GSI1PK = :condition AND GSI1SK BETWEEN :start AND :end',
        ExpressionAttributeValues={
            ':condition': f'CONDITION#{location}#{interval}#{intervention}',
            ':start': date_range['start'],
            ':end': date_range['end']
        }
    )

    sessions = []

    for session_item in response['Items']:
        session_id = session_item['session_id']

        # Get all related entities
        session_response = table.query(
            KeyConditionExpression='PK = :pk',
            ExpressionAttributeValues={
                ':pk': f'SESSION#{session_id}'
            }
        )

        # Flatten data for analysis
        flattened = flatten_session_data(session_response['Items'])
        sessions.append(flattened)

    # Convert to DataFrame
    df = pd.DataFrame(sessions)

    # Export to S3 as Parquet
    output_path = f's3://socratic-benchmarks-analytics/conditions/{location}_{interval}_{intervention}.parquet'
    df.to_parquet(output_path, engine='pyarrow', compression='snappy')

    return output_path

def flatten_session_data(items):
    """
    Flatten hierarchical DynamoDB items into flat structure for analytics
    """
    flattened = {}

    for item in items:
        if item['SK'] == 'METADATA':
            # Session metadata
            flattened.update({
                'session_id': item['session_id'],
                'student_id': item['student_id'],
                'location': item['experimental_condition']['location'],
                'interval': item['experimental_condition']['interval_minutes'],
                'intervention_type': item['experimental_condition']['intervention_type'],
                'session_start': item['timeline']['session_start'],
                'total_duration': item['timeline']['total_duration_seconds'],
                'completed': item['completion_status']['completed']
            })

        elif item['SK'].startswith('ASSESSMENT#baseline'):
            # Baseline assessment
            flattened.update({
                'baseline_score': item['assessment_results']['score_percentage'],
                'baseline_mc_score': item['scoring_breakdown']['mc_percentage'],
                'baseline_sa_score': item['scoring_breakdown']['sa_percentage']
            })

        elif item['SK'].startswith('ASSESSMENT#final'):
            # Final assessment
            flattened.update({
                'final_score': item['assessment_results']['score_percentage'],
                'final_mc_score': item['scoring_breakdown']['mc_percentage'],
                'final_sa_score': item['scoring_breakdown']['sa_percentage'],
                'learning_gain': item['learning_gain']['absolute_gain'],
                'normalized_gain': item['learning_gain']['normalized_gain']
            })

        elif item['SK'].startswith('INTERVENTION#'):
            # Aggregate intervention metrics
            if 'interventions_total' not in flattened:
                flattened['interventions_total'] = 0
                flattened['avg_question_quality'] = []
                flattened['avg_answer_depth'] = []

            flattened['interventions_total'] += 1

            if 'intervention_summary' in item:
                summary = item['intervention_summary']
                if 'avg_question_quality' in summary:
                    flattened['avg_question_quality'].append(summary['avg_question_quality'])
                if 'avg_answer_depth' in summary:
                    flattened['avg_answer_depth'].append(summary['avg_answer_depth'])

        elif item['SK'] == 'POST_SURVEY':
            # Post-survey data
            flattened.update({
                'location_impact_rating': item['location_experience']['location_impact_rating'],
                'intervention_helpful_rating': item['intervention_experience']['intervention_helpful_rating'],
                'overall_experience_rating': item['learning_experience']['overall_experience_rating']
            })

    # Calculate averages for intervention metrics
    if 'avg_question_quality' in flattened and flattened['avg_question_quality']:
        flattened['avg_question_quality'] = sum(flattened['avg_question_quality']) / len(flattened['avg_question_quality'])
    if 'avg_answer_depth' in flattened and flattened['avg_answer_depth']:
        flattened['avg_answer_depth'] = sum(flattened['avg_answer_depth']) / len(flattened['avg_answer_depth'])

    return flattened
```

---

### GSI Design Summary

| GSI | Partition Key | Sort Key | Use Case |
|-----|--------------|----------|----------|
| GSI1 | CONDITION#location#interval#intervention | timestamp | Condition-level analysis |
| GSI2 | STUDENT#student_id | SESSION#timestamp | Student longitudinal tracking |
| GSI3 | LOCATION#type | timestamp | Location comparison |
| GSI4 | INTERVENTION#type | timestamp | Intervention effectiveness |
| GSI5 | DATE#YYYY-MM-DD | timestamp | Time-series analytics |

---

### Cost Optimization

**Provisioned Capacity Recommendations:**
- **Primary Table**: 10 RCU, 10 WCU (adjust based on usage)
- **GSI1-GSI5**: 5 RCU each (read-heavy for analytics)

**Auto-scaling Configuration:**
```python
autoscaling = boto3.client('application-autoscaling')

# Configure auto-scaling for table
autoscaling.register_scalable_target(
    ServiceNamespace='dynamodb',
    ResourceId='table/SocraticBenchmarks',
    ScalableDimension='dynamodb:table:WriteCapacityUnits',
    MinCapacity=5,
    MaxCapacity=100
)

autoscaling.put_scaling_policy(
    PolicyName='WriteAutoScaling',
    ServiceNamespace='dynamodb',
    ResourceId='table/SocraticBenchmarks',
    ScalableDimension='dynamodb:table:WriteCapacityUnits',
    PolicyType='TargetTrackingScaling',
    TargetTrackingScalingPolicyConfiguration={
        'TargetValue': 70.0,
        'PredefinedMetricSpecification': {
            'PredefinedMetricType': 'DynamoDBWriteCapacityUtilization'
        }
    }
)
```

---

## Table Creation

### DynamoDB Table Definition (CloudFormation/CDK)

```yaml
Resources:
  SocraticBenchmarksTable:
    Type: AWS::DynamoDB::Table
    Properties:
      TableName: SocraticBenchmarks
      BillingMode: PROVISIONED
      ProvisionedThroughput:
        ReadCapacityUnits: 10
        WriteCapacityUnits: 10

      AttributeDefinitions:
        - AttributeName: PK
          AttributeType: S
        - AttributeName: SK
          AttributeType: S
        - AttributeName: GSI1PK
          AttributeType: S
        - AttributeName: GSI1SK
          AttributeType: S
        - AttributeName: GSI2PK
          AttributeType: S
        - AttributeName: GSI2SK
          AttributeType: S
        - AttributeName: GSI3PK
          AttributeType: S
        - AttributeName: GSI3SK
          AttributeType: S
        - AttributeName: GSI4PK
          AttributeType: S
        - AttributeName: GSI4SK
          AttributeType: S
        - AttributeName: GSI5PK
          AttributeType: S
        - AttributeName: GSI5SK
          AttributeType: S

      KeySchema:
        - AttributeName: PK
          KeyType: HASH
        - AttributeName: SK
          KeyType: RANGE

      GlobalSecondaryIndexes:
        - IndexName: GSI1
          KeySchema:
            - AttributeName: GSI1PK
              KeyType: HASH
            - AttributeName: GSI1SK
              KeyType: RANGE
          Projection:
            ProjectionType: ALL
          ProvisionedThroughput:
            ReadCapacityUnits: 5
            WriteCapacityUnits: 5

        - IndexName: GSI2
          KeySchema:
            - AttributeName: GSI2PK
              KeyType: HASH
            - AttributeName: GSI2SK
              KeyType: RANGE
          Projection:
            ProjectionType: ALL
          ProvisionedThroughput:
            ReadCapacityUnits: 5
            WriteCapacityUnits: 5

        - IndexName: GSI3
          KeySchema:
            - AttributeName: GSI3PK
              KeyType: HASH
            - AttributeName: GSI3SK
              KeyType: RANGE
          Projection:
            ProjectionType: ALL
          ProvisionedThroughput:
            ReadCapacityUnits: 5
            WriteCapacityUnits: 5

        - IndexName: GSI4
          KeySchema:
            - AttributeName: GSI4PK
              KeyType: HASH
            - AttributeName: GSI4SK
              KeyType: RANGE
          Projection:
            ProjectionType: ALL
          ProvisionedThroughput:
            ReadCapacityUnits: 5
            WriteCapacityUnits: 5

        - IndexName: GSI5
          KeySchema:
            - AttributeName: GSI5PK
              KeyType: HASH
            - AttributeName: GSI5SK
              KeyType: RANGE
          Projection:
            ProjectionType: ALL
          ProvisionedThroughput:
            ReadCapacityUnits: 5
            WriteCapacityUnits: 5

      StreamSpecification:
        StreamViewType: NEW_AND_OLD_IMAGES

      PointInTimeRecoverySpecification:
        PointInTimeRecoveryEnabled: true

      Tags:
        - Key: Project
          Value: SocraticBenchmarks
        - Key: Environment
          Value: Production
```

---

## Summary

This DynamoDB schema provides:

1. **Single-table design** for atomic operations and cost efficiency
2. **5 GSIs** for flexible querying across all research dimensions
3. **Hierarchical key structure** supporting all access patterns
4. **Complete entity schemas** for students, sessions, interventions, assessments
5. **Real-time analytics** via DynamoDB Streams
6. **Long-term storage** integration with S3
7. **Data integrity** through transactions and validation
8. **Scalability** with auto-scaling configuration

The schema supports all 24 experimental conditions (4 locations × 3 intervals × 2 intervention types) and enables comprehensive research analytics including:
- Learning gain calculations
- Condition comparisons
- Location impact analysis
- Intervention effectiveness measurement
- Longitudinal student tracking
- Real-time dashboard queries

All query patterns are optimized for DynamoDB's strengths while maintaining flexibility for research analysis needs.
