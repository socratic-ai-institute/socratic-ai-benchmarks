/**
 * TypeScript Type Definitions for Socratic AI Benchmarks DynamoDB Schema
 *
 * These types correspond to the DynamoDB schema defined in DYNAMODB_SCHEMA.md
 */

// ============================================================================
// Core Types
// ============================================================================

export type LocationType = 'on-site' | 'learning-space' | 'classroom' | 'home';
export type InterventionType = 'static' | 'dynamic';
export type AssessmentType = 'baseline' | 'midpoint' | 'final';
export type QuestionType = 'multiple_choice' | 'short_answer' | 'essay';
export type ContentFormat = 'audio' | 'text' | 'video';

// ============================================================================
// Student Profile
// ============================================================================

export interface StudentProfile {
  PK: string; // STUDENT#<student_id>
  SK: 'PROFILE';
  GSI2PK: string; // STUDENT#<student_id>
  GSI2SK: 'PROFILE';

  entity_type: 'student_profile';
  student_id: string;

  demographics: {
    age: number;
    grade_level: number;
    school: string;
    richmond_resident: boolean;
  };

  learning_profile: {
    depth_preference: 'surface' | 'moderate' | 'deep';
    learning_style: string;
    prior_knowledge_topics: string[];
  };

  consent_data: {
    parent_consent: boolean;
    student_assent: boolean;
    irb_consent_date: string; // ISO 8601
    data_sharing_consent: boolean;
  };

  metadata: {
    created_at: string; // ISO 8601
    updated_at: string; // ISO 8601
    total_sessions: number;
    conditions_completed: string[];
  };
}

// ============================================================================
// Experimental Session
// ============================================================================

export interface ExperimentalCondition {
  location: LocationType;
  location_name: string;
  interval_minutes: 2.5 | 5.0 | 10.0;
  intervention_type: InterventionType;
  condition_code: string; // e.g., "L1-I1-D"
}

export interface SessionTimeline {
  session_start: string; // ISO 8601
  session_end: string; // ISO 8601
  total_duration_seconds: number;
  content_duration_seconds: number;
  intervention_duration_seconds: number;
  assessment_duration_seconds: number;
}

export interface CompletionStatus {
  completed: boolean;
  location_verified: boolean;
  baseline_completed: boolean;
  content_completed: boolean;
  interventions_completed: number;
  final_assessment_completed: boolean;
  post_survey_completed: boolean;
}

export interface Session {
  PK: string; // SESSION#<session_id>
  SK: 'METADATA';

  GSI1PK: string; // CONDITION#<location>#<interval>#<intervention>
  GSI1SK: string; // timestamp
  GSI2PK: string; // STUDENT#<student_id>
  GSI2SK: string; // SESSION#<timestamp>
  GSI3PK: string; // LOCATION#<location_type>
  GSI3SK: string; // timestamp
  GSI4PK: string; // INTERVENTION#<type>
  GSI4SK: string; // timestamp
  GSI5PK: string; // DATE#<YYYY-MM-DD>
  GSI5SK: string; // timestamp

  entity_type: 'session';
  session_id: string;
  student_id: string;

  experimental_condition: ExperimentalCondition;
  timeline: SessionTimeline;
  completion_status: CompletionStatus;

  student_metadata: {
    age: number;
    grade: number;
    richmond_resident: boolean;
    prior_knowledge_score: number;
  };

  metadata: {
    created_at: string; // ISO 8601
    updated_at: string; // ISO 8601
    version: number;
    data_quality_flags: string[];
  };
}

// ============================================================================
// Location Verification
// ============================================================================

export interface GPSData {
  latitude: number;
  longitude: number;
  accuracy_meters: number;
  geofence_validated: boolean;
  distance_from_target_meters: number;
}

export interface DeviceInfo {
  device_type: 'mobile' | 'tablet' | 'desktop';
  os: string;
  browser: string;
  user_agent: string;
}

export interface LocationVerification {
  PK: string; // SESSION#<session_id>
  SK: 'LOCATION_VERIFICATION';

  entity_type: 'location_verification';
  session_id: string;
  student_id: string;

  location_data: {
    type: LocationType;
    name: string;
    address: string;
  };

  verification: {
    method: 'GPS' | 'QR_code' | 'manual' | 'honor_system';
    verified: boolean;
    verification_timestamp: string; // ISO 8601
    confidence: 'high' | 'medium' | 'low';
  };

  gps_data?: GPSData;
  device_info: DeviceInfo;

  metadata: {
    timestamp: string; // ISO 8601
    ip_address: string;
    session_token: string;
  };
}

// ============================================================================
// Content Delivery
// ============================================================================

export interface SegmentTracking {
  segment_id: number;
  start_time: string; // ISO 8601
  end_time: string; // ISO 8601
  duration_seconds: number;
  completed: boolean;
  engagement_score: number; // 0-1
}

export interface ContentDelivery {
  PK: string; // SESSION#<session_id>
  SK: 'CONTENT_DELIVERY';

  entity_type: 'content_delivery';
  session_id: string;
  student_id: string;

  content_metadata: {
    content_id: string;
    content_version: string;
    topic: string;
    duration_seconds: number;
    difficulty_level: string;
  };

  delivery_preferences: {
    format_chosen: ContentFormat;
    playback_speed: number;
    captions_enabled: boolean;
    language: string;
  };

  engagement_metrics: {
    start_time: string; // ISO 8601
    end_time: string; // ISO 8601
    total_play_time_seconds: number;
    total_elapsed_time_seconds: number;
    pause_count: number;
    rewind_count: number;
    segments_completed: number;
    completion_percentage: number;
  };

  segment_tracking: SegmentTracking[];

  metadata: {
    created_at: string; // ISO 8601
    updated_at: string; // ISO 8601
  };
}

// ============================================================================
// Intervention Record - Dynamic
// ============================================================================

export interface QuestionMetadata {
  model: string;
  prompt_tokens: number;
  completion_tokens: number;
  generation_time_ms: number;
  temperature: number;
  incorporates_previous_answer?: boolean;
  synthesis_question?: boolean;
}

export interface AnswerMetadata {
  timestamp: string; // ISO 8601
  response_time_seconds: number;
  word_count: number;
  character_count: number;
}

export interface QualityScores {
  question_clarity: number;
  question_relevance: number;
  answer_depth: number;
  answer_accuracy: number;
  engagement_level: number;
  builds_on_previous?: number;
  synthesis_quality?: number;
  location_integration?: number;
}

export interface SocraticQuestion {
  question_number: 1 | 2 | 3;
  timestamp: string; // ISO 8601
  question: string;
  question_metadata: QuestionMetadata;
  answer: string;
  answer_metadata: AnswerMetadata;
  quality_scores: QualityScores;
}

export interface DynamicIntervention {
  PK: string; // SESSION#<session_id>
  SK: string; // INTERVENTION#<timestamp>#<segment_id>

  GSI4PK: string; // INTERVENTION#dynamic
  GSI4SK: string; // timestamp

  entity_type: 'intervention';
  session_id: string;
  student_id: string;
  intervention_id: string;

  intervention_metadata: {
    type: 'dynamic';
    sequence_number: number;
    timestamp: string; // ISO 8601
    segment_id: number;
    segment_summary: string;
  };

  location_context: {
    location_type: LocationType;
    location_name: string;
    location_aware_prompting: boolean;
  };

  socratic_sequence: SocraticQuestion[];

  intervention_summary: {
    total_duration_seconds: number;
    questions_asked: number;
    avg_response_time_seconds: number;
    avg_question_quality: number;
    avg_answer_depth: number;
    progression_quality: number;
    location_awareness_utilized: boolean;
  };

  ai_metadata: {
    model_version: string;
    total_prompt_tokens: number;
    total_completion_tokens: number;
    total_cost_usd: number;
    avg_generation_time_ms: number;
  };

  metadata: {
    created_at: string; // ISO 8601
    updated_at: string; // ISO 8601
    version: number;
  };
}

// ============================================================================
// Intervention Record - Static
// ============================================================================

export interface StaticQuestion {
  question_number: 1 | 2 | 3;
  timestamp: string; // ISO 8601
  question: string;
  question_source: string;
  answer: string;
  answer_metadata: AnswerMetadata;
  quality_scores: {
    answer_depth: number;
    answer_accuracy: number;
    engagement_level: number;
  };
}

export interface StaticIntervention {
  PK: string; // SESSION#<session_id>
  SK: string; // INTERVENTION#<timestamp>#<segment_id>

  GSI4PK: string; // INTERVENTION#static
  GSI4SK: string; // timestamp

  entity_type: 'intervention';
  session_id: string;
  student_id: string;
  intervention_id: string;

  intervention_metadata: {
    type: 'static';
    sequence_number: number;
    timestamp: string; // ISO 8601
    segment_id: number;
    segment_summary: string;
  };

  location_context: {
    location_type: LocationType;
    location_name: string;
    location_aware_prompting: false;
  };

  static_questions: StaticQuestion[];

  intervention_summary: {
    total_duration_seconds: number;
    questions_asked: number;
    avg_response_time_seconds: number;
    avg_answer_depth: number;
    no_adaptive_followup: true;
  };

  metadata: {
    created_at: string; // ISO 8601
    updated_at: string; // ISO 8601
    version: number;
  };
}

export type Intervention = DynamicIntervention | StaticIntervention;

// ============================================================================
// Assessment Record
// ============================================================================

export interface MultipleChoiceQuestion {
  question_id: string;
  question_text: string;
  question_type: 'multiple_choice';
  options: string[];
  correct_answer: string;
  student_answer: string;
  is_correct: boolean;
  points: number;
  points_earned: number;
  response_time_seconds: number;
  difficulty: 'easy' | 'medium' | 'hard';
}

export interface AIScoring {
  model: string;
  raw_score: number;
  rubric_breakdown: Record<string, number>;
  feedback: string;
}

export interface ShortAnswerQuestion {
  question_id: string;
  question_text: string;
  question_type: 'short_answer';
  rubric_points: number;
  student_answer: string;
  ai_scoring: AIScoring;
  points: number;
  points_earned: number;
  response_time_seconds: number;
  difficulty: 'easy' | 'medium' | 'hard';
}

export type AssessmentQuestion = MultipleChoiceQuestion | ShortAnswerQuestion;

export interface AssessmentResults {
  total_questions: number;
  questions_answered: number;
  correct_answers: number;
  total_points: number;
  points_earned: number;
  score_percentage: number;
  avg_response_time_seconds: number;
}

export interface ScoringBreakdown {
  multiple_choice_score: number;
  multiple_choice_possible: number;
  short_answer_score: number;
  short_answer_possible: number;
  mc_percentage: number;
  sa_percentage: number;
}

export interface LearningGain {
  baseline_score: number;
  final_score: number;
  absolute_gain: number;
  relative_gain: number;
  normalized_gain: number;
}

export interface Assessment {
  PK: string; // SESSION#<session_id>
  SK: string; // ASSESSMENT#<type>#<timestamp>

  entity_type: 'assessment';
  session_id: string;
  student_id: string;
  assessment_id: string;

  assessment_metadata: {
    type: AssessmentType;
    version: string;
    timestamp: string; // ISO 8601
    duration_seconds: number;
    content_topic: string;
  };

  questions: AssessmentQuestion[];

  assessment_results: AssessmentResults;
  scoring_breakdown: ScoringBreakdown;
  learning_gain?: LearningGain; // Only present in final assessment

  metadata: {
    created_at: string; // ISO 8601
    updated_at: string; // ISO 8601
    grading_method: 'automated' | 'automated_with_ai' | 'manual';
    version: number;
  };
}

// ============================================================================
// Post-Session Survey
// ============================================================================

export interface PostSessionSurvey {
  PK: string; // SESSION#<session_id>
  SK: 'POST_SURVEY';

  entity_type: 'post_survey';
  session_id: string;
  student_id: string;

  survey_metadata: {
    version: string;
    timestamp: string; // ISO 8601
    duration_seconds: number;
  };

  location_experience: {
    location_impact_rating: 1 | 2 | 3 | 4 | 5;
    location_enhanced_understanding: boolean;
    location_was_distracting: boolean;
    would_recommend_location: boolean;
    location_feedback: string;
  };

  intervention_experience: {
    intervention_helpful_rating: 1 | 2 | 3 | 4 | 5;
    questions_were_engaging: boolean;
    questions_were_appropriate: boolean;
    questions_promoted_thinking: boolean;
    preferred_intervention_type: InterventionType;
    intervention_feedback: string;
  };

  learning_experience: {
    content_difficulty_rating: 1 | 2 | 3 | 4 | 5;
    content_interest_rating: 1 | 2 | 3 | 4 | 5;
    pacing_rating: 1 | 2 | 3 | 4 | 5;
    overall_experience_rating: 1 | 2 | 3 | 4 | 5;
    would_recommend_experience: boolean;
    general_feedback: string;
  };

  technical_experience: {
    interface_easy_to_use: boolean;
    audio_quality_rating: 1 | 2 | 3 | 4 | 5;
    technical_issues_encountered: boolean;
    technical_feedback: string;
  };

  open_ended_responses: {
    most_valuable_aspect: string;
    least_valuable_aspect: string;
    suggestions_for_improvement: string;
    additional_comments: string;
  };

  metadata: {
    created_at: string; // ISO 8601
    updated_at: string; // ISO 8601
  };
}

// ============================================================================
// Aggregated Statistics
// ============================================================================

export interface StatisticsRange {
  mean_score: number;
  median_score: number;
  std_dev: number;
  min_score: number;
  max_score: number;
  n: number;
}

export interface LearningGainStatistics {
  mean_absolute_gain: number;
  median_absolute_gain: number;
  mean_normalized_gain: number;
  effect_size_cohens_d: number;
  students_with_gains: number;
  students_with_no_change: number;
  students_with_losses: number;
}

export interface ConditionStatistics {
  PK: string; // STATS#CONDITION#<location>#<interval>#<intervention>
  SK: string; // AGGREGATE#<date_range>

  entity_type: 'condition_statistics';

  condition: {
    location: LocationType;
    interval: 2.5 | 5.0 | 10.0;
    intervention: InterventionType;
  };

  date_range: {
    start_date: string; // YYYY-MM-DD
    end_date: string; // YYYY-MM-DD
    days_elapsed: number;
  };

  sample_statistics: {
    total_sessions: number;
    completed_sessions: number;
    completion_rate: number;
    unique_students: number;
    avg_session_duration_seconds: number;
  };

  learning_outcomes: {
    baseline_assessment: StatisticsRange;
    final_assessment: StatisticsRange;
    learning_gain: LearningGainStatistics;
  };

  intervention_metrics: {
    avg_interventions_per_session: number;
    avg_intervention_duration_seconds: number;
    avg_questions_per_intervention: number;
    avg_response_time_seconds: number;
    avg_question_quality_score: number;
    avg_answer_depth_score: number;
    avg_progression_quality: number;
  };

  engagement_metrics: {
    avg_content_completion_rate: number;
    avg_pause_count: number;
    avg_rewind_count: number;
    avg_engagement_score: number;
  };

  survey_results: {
    avg_location_impact: number;
    avg_intervention_helpful: number;
    avg_overall_experience: number;
    would_recommend_pct: number;
  };

  metadata: {
    last_updated: string; // ISO 8601
    aggregation_version: string;
    auto_generated: boolean;
  };
}

// ============================================================================
// Helper Types for Queries
// ============================================================================

export interface QueryOptions {
  limit?: number;
  startKey?: Record<string, any>;
  filterExpression?: string;
  expressionAttributeValues?: Record<string, any>;
}

export interface SessionQueryResult {
  items: Session[];
  lastEvaluatedKey?: Record<string, any>;
  count: number;
}

export interface InterventionQueryResult {
  items: Intervention[];
  lastEvaluatedKey?: Record<string, any>;
  count: number;
}

export interface AssessmentQueryResult {
  items: Assessment[];
  lastEvaluatedKey?: Record<string, any>;
  count: number;
}

// ============================================================================
// Condition Builder Types
// ============================================================================

export interface ExperimentalDesign {
  locations: LocationType[];
  intervals: Array<2.5 | 5.0 | 10.0>;
  interventions: InterventionType[];
  totalConditions: number; // Should be 24 (4 × 3 × 2)
}

export const EXPERIMENTAL_DESIGN: ExperimentalDesign = {
  locations: ['on-site', 'learning-space', 'classroom', 'home'],
  intervals: [2.5, 5.0, 10.0],
  interventions: ['static', 'dynamic'],
  totalConditions: 24,
};

// ============================================================================
// DynamoDB Key Builders
// ============================================================================

export const KeyBuilder = {
  student: (studentId: string) => ({
    PK: `STUDENT#${studentId}`,
    SK: 'PROFILE',
  }),

  session: (sessionId: string) => ({
    PK: `SESSION#${sessionId}`,
    SK: 'METADATA',
  }),

  locationVerification: (sessionId: string) => ({
    PK: `SESSION#${sessionId}`,
    SK: 'LOCATION_VERIFICATION',
  }),

  contentDelivery: (sessionId: string) => ({
    PK: `SESSION#${sessionId}`,
    SK: 'CONTENT_DELIVERY',
  }),

  intervention: (sessionId: string, timestamp: string, segmentId: number) => ({
    PK: `SESSION#${sessionId}`,
    SK: `INTERVENTION#${timestamp}#${segmentId}`,
  }),

  assessment: (sessionId: string, type: AssessmentType, timestamp: string) => ({
    PK: `SESSION#${sessionId}`,
    SK: `ASSESSMENT#${type}#${timestamp}`,
  }),

  postSurvey: (sessionId: string) => ({
    PK: `SESSION#${sessionId}`,
    SK: 'POST_SURVEY',
  }),

  conditionStats: (
    location: LocationType,
    interval: number,
    intervention: InterventionType,
    dateRange: string
  ) => ({
    PK: `STATS#CONDITION#${location}#${interval}#${intervention}`,
    SK: `AGGREGATE#${dateRange}`,
  }),
};

// ============================================================================
// GSI Key Builders
// ============================================================================

export const GSIKeyBuilder = {
  byCondition: (
    location: LocationType,
    interval: number,
    intervention: InterventionType,
    timestamp: string
  ) => ({
    GSI1PK: `CONDITION#${location}#${interval}#${intervention}`,
    GSI1SK: timestamp,
  }),

  byStudent: (studentId: string, timestamp: string) => ({
    GSI2PK: `STUDENT#${studentId}`,
    GSI2SK: `SESSION#${timestamp}`,
  }),

  byLocation: (location: LocationType, timestamp: string) => ({
    GSI3PK: `LOCATION#${location}`,
    GSI3SK: timestamp,
  }),

  byInterventionType: (type: InterventionType, timestamp: string) => ({
    GSI4PK: `INTERVENTION#${type}`,
    GSI4SK: timestamp,
  }),

  byDate: (date: string, timestamp: string) => ({
    GSI5PK: `DATE#${date}`,
    GSI5SK: timestamp,
  }),
};

// ============================================================================
// Validation Schemas
// ============================================================================

export const Validators = {
  isValidLocationVerification: (data: LocationVerification): boolean => {
    return (
      data.verification.verified === true &&
      data.verification.confidence !== 'low' &&
      (data.verification.method === 'GPS' ? data.gps_data !== undefined : true)
    );
  },

  isSessionComplete: (session: Session): boolean => {
    const status = session.completion_status;
    return (
      status.completed &&
      status.location_verified &&
      status.baseline_completed &&
      status.content_completed &&
      status.final_assessment_completed &&
      status.post_survey_completed
    );
  },

  isValidIntervention: (intervention: Intervention): boolean => {
    if (intervention.intervention_metadata.type === 'dynamic') {
      return (
        'socratic_sequence' in intervention &&
        intervention.socratic_sequence.length === 3
      );
    } else {
      return (
        'static_questions' in intervention &&
        intervention.static_questions.length === 3
      );
    }
  },

  isValidAssessment: (assessment: Assessment): boolean => {
    return (
      assessment.questions.length > 0 &&
      assessment.assessment_results.total_questions > 0 &&
      assessment.assessment_results.score_percentage >= 0 &&
      assessment.assessment_results.score_percentage <= 100
    );
  },
};

// ============================================================================
// Constants
// ============================================================================

export const LOCATION_NAMES: Record<LocationType, string> = {
  'on-site': 'Tredegar Iron Works',
  'learning-space': 'Lost Office Collaborative',
  classroom: 'Richmond Classroom',
  home: 'Home Environment',
};

export const LOCATION_ADDRESSES: Record<LocationType, string | null> = {
  'on-site': '500 Tredegar St, Richmond, VA 23219',
  'learning-space': 'Lost Office Collaborative, Richmond, VA',
  classroom: null,
  home: null,
};

export const LOCATION_COORDINATES: Record<
  LocationType,
  { lat: number; lng: number } | null
> = {
  'on-site': { lat: 37.5316, lng: -77.4481 },
  'learning-space': { lat: 37.5407, lng: -77.436 },
  classroom: null,
  home: null,
};

export const CONTENT_SEGMENTS = [
  {
    segment_id: 1,
    start_time: 0,
    end_time: 150,
    summary: 'Introduction to Tredegar Iron Works and its founding',
    key_concepts: ["industrial revolution", "Richmond's role", "1837 founding"],
    difficulty_level: 'introductory',
  },
  {
    segment_id: 2,
    start_time: 150,
    end_time: 300,
    summary: 'Civil War era production and significance',
    key_concepts: [
      'Confederate munitions',
      'industrial capacity',
      'labor force',
    ],
    difficulty_level: 'intermediate',
  },
  {
    segment_id: 3,
    start_time: 300,
    end_time: 450,
    summary: 'Post-war transformation and labor history',
    key_concepts: ['reconstruction', 'labor movements', 'economic changes'],
    difficulty_level: 'intermediate',
  },
  {
    segment_id: 4,
    start_time: 450,
    end_time: 600,
    summary: 'Modern preservation and historical memory',
    key_concepts: [
      'American Civil War Museum',
      'historical interpretation',
      'public memory',
    ],
    difficulty_level: 'advanced',
  },
] as const;

export const INTERVENTION_INTERVALS = [2.5, 5.0, 7.5, 10.0] as const;

export const STATIC_REFLECTION_QUESTIONS: Record<string, string[]> = {
  segment_1: [
    'What stood out to you most about the founding of Tredegar Iron Works?',
    'Why do you think Richmond became an important industrial center?',
    'What questions do you have about this time period?',
  ],
  segment_2: [
    "How did Tredegar's role change during the Civil War?",
    'What surprised you about the production capacity described?',
    'What do you wonder about the people who worked there?',
  ],
  segment_3: [
    'How did Reconstruction affect industrial sites like Tredegar?',
    'What connections can you make between labor movements then and now?',
    'What would you want to know more about regarding this era?',
  ],
  segment_4: [
    'Why is preserving historical sites like Tredegar important?',
    'How does learning local history change your perspective on Richmond?',
    'What aspects of this story do you think should be remembered?',
  ],
};
