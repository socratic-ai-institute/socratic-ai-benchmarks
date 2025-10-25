# Test Automation Strategy for Socratic AI Benchmarks Platform

## Executive Summary

This document defines the comprehensive test automation strategy for a location-aware educational research platform that orchestrates Socratic AI interventions across 24 experimental conditions (4 locations × 3 timing intervals × 2 intervention types).

**Key Testing Challenges:**
- Precise timing control (pause at exact 2.5, 5, 10 min marks)
- AI quality assurance (Socratic question generation)
- Location verification and geofencing
- Session state persistence across interruptions
- Concurrent multi-location session orchestration
- Experimental integrity and data quality

---

## 1. Test Orchestration Architecture

### 1.1 Recommended Orchestration: AWS Step Functions

**Decision: Use AWS Step Functions with Lambda for precision timing**

**Rationale:**
- Built-in state persistence and error handling
- Precise timing with Wait states (up to millisecond accuracy)
- Visual workflow monitoring
- Native integration with EventBridge for scheduling
- Automatic retry and compensation logic

**Architecture:**

```yaml
# Step Functions State Machine for Experiment Sessions
StateMachine: SocraticExperimentOrchestrator
States:

  1. InitializeSession:
     Type: Task
     Resource: arn:aws:lambda:${AWS::Region}:${AWS::AccountId}:function:InitSession
     Next: VerifyLocation

  2. VerifyLocation:
     Type: Task
     Resource: arn:aws:lambda:${AWS::Region}:${AWS::AccountId}:function:VerifyLocation
     Next: BaselineAssessment
     Catch:
       - ErrorEquals: ["LocationVerificationFailed"]
         Next: LocationFailureHandler

  3. BaselineAssessment:
     Type: Task
     Resource: arn:aws:lambda:${AWS::Region}:${AWS::AccountId}:function:BaselineTest
     Next: PlaySegment1

  4. PlaySegment1:
     Type: Wait
     Seconds: 150  # 2.5 minutes in seconds
     Next: CheckIntervention1

  5. CheckIntervention1:
     Type: Choice
     Choices:
       - Variable: $.condition.interval
         NumericEquals: 2.5
         Next: RunIntervention1
       - Variable: $.condition.interval
         NumericGreaterThan: 2.5
         Next: PlaySegment2
     Default: PlaySegment2

  6. RunIntervention1:
     Type: Task
     Resource: arn:aws:states:::lambda:invoke.waitForTaskToken
     Parameters:
       FunctionName: arn:aws:lambda:${AWS::Region}:${AWS::AccountId}:function:SocraticIntervention
       Payload:
         taskToken.$: $$.Task.Token
         segment: 1
         context.$: $
     TimeoutSeconds: 600  # 10 min max for intervention
     Next: PlaySegment2

  7. PlaySegment2:
     Type: Wait
     Seconds: 150
     Next: CheckIntervention2

  # ... Pattern repeats for segments 3 and 4

  8. FinalAssessment:
     Type: Task
     Resource: arn:aws:lambda:${AWS::Region}:${AWS::AccountId}:function:FinalTest
     Next: PostSurvey

  9. PostSurvey:
     Type: Task
     Resource: arn:aws:lambda:${AWS::Region}:${AWS::AccountId}:function:PostSurvey
     Next: StoreResults

  10. StoreResults:
      Type: Task
      Resource: arn:aws:lambda:${AWS::Region}:${AWS::AccountId}:function:StoreResults
      End: true
```

**Alternative Considered: ECS Tasks**
- Rejected for primary orchestration due to complexity in timing precision
- Used instead for background processing (data analysis, AI model inference batching)

**Hybrid Approach:**
```
Step Functions (Orchestration)
    → Lambda (Business Logic)
        → ECS Fargate (Heavy AI Processing)
            → Bedrock/OpenAI APIs
```

### 1.2 Timing Precision Implementation

**Requirements:**
- Content segments: 2.5, 5, 7.5, 10 minutes
- Intervention windows: Must pause exactly at boundary
- Resume exactly where paused
- Account for network latency

**Implementation:**

```python
# Lambda function: PlayContentSegment
import boto3
import time
from datetime import datetime, timedelta

class PrecisionTimingController:
    def __init__(self):
        self.cloudwatch = boto3.client('cloudwatch')
        self.dynamodb = boto3.resource('dynamodb')
        self.sessions_table = self.dynamodb.Table('ExperimentSessions')

    async def play_segment(self, session_id, segment_start, segment_end, intervention_time):
        """
        Orchestrate content delivery with precise timing

        Args:
            session_id: Unique session identifier
            segment_start: Start time in seconds (e.g., 0, 150, 300)
            segment_end: End time in seconds (e.g., 150, 300, 450)
            intervention_time: Target intervention time (2.5, 5, 10)
        """

        # Calculate actual play duration (accounting for buffer)
        play_duration = segment_end - segment_start

        # Record start timestamp with nanosecond precision
        start_time = time.perf_counter_ns()
        actual_start_wall_time = datetime.utcnow()

        # Update session state
        self.sessions_table.update_item(
            Key={'session_id': session_id},
            UpdateExpression='SET current_segment = :seg, segment_start_time = :start',
            ExpressionAttributeValues={
                ':seg': segment_start,
                ':start': actual_start_wall_time.isoformat()
            }
        )

        # Send CloudWatch metric for timing verification
        self.cloudwatch.put_metric_data(
            Namespace='SocraticExperiment',
            MetricData=[
                {
                    'MetricName': 'SegmentStartLatency',
                    'Value': (time.perf_counter_ns() - start_time) / 1_000_000,  # ms
                    'Unit': 'Milliseconds',
                    'Dimensions': [
                        {'Name': 'SessionId', 'Value': session_id},
                        {'Name': 'SegmentStart', 'Value': str(segment_start)}
                    ]
                }
            ]
        )

        # Return control to Step Functions with precise timing
        return {
            'segment_start': segment_start,
            'segment_end': segment_end,
            'started_at': actual_start_wall_time.isoformat(),
            'expected_completion': (actual_start_wall_time + timedelta(seconds=play_duration)).isoformat(),
            'next_intervention': intervention_time
        }

    async def verify_timing_accuracy(self, session_id):
        """
        Post-session validation of timing accuracy
        Returns: Report of timing deviations
        """

        session = self.sessions_table.get_item(Key={'session_id': session_id})['Item']

        timing_report = {
            'session_id': session_id,
            'expected_interventions': session['condition']['intervention_times'],
            'actual_interventions': [],
            'deviations': []
        }

        for intervention in session.get('interventions', []):
            expected = intervention['expected_timestamp']
            actual = intervention['actual_timestamp']

            expected_dt = datetime.fromisoformat(expected)
            actual_dt = datetime.fromisoformat(actual)

            deviation_ms = (actual_dt - expected_dt).total_seconds() * 1000

            timing_report['actual_interventions'].append(actual)
            timing_report['deviations'].append({
                'expected': expected,
                'actual': actual,
                'deviation_ms': deviation_ms,
                'within_tolerance': abs(deviation_ms) < 500  # 500ms tolerance
            })

        return timing_report
```

**Testing Timing Precision:**

```python
# tests/integration/test_timing_precision.py
import pytest
import asyncio
from datetime import datetime, timedelta

class TestTimingPrecision:

    @pytest.mark.asyncio
    async def test_segment_boundaries_2_5_min_interval(self):
        """
        Verify interventions occur at exactly 2.5, 5, 7.5, 10 min marks
        Tolerance: +/- 500ms
        """

        session_config = {
            'interval': 2.5,
            'intervention_type': 'dynamic'
        }

        start_time = datetime.utcnow()
        session_id = await self.start_test_session(session_config)

        # Monitor intervention timestamps
        intervention_times = await self.monitor_session(session_id, timeout=700)

        expected_times = [150, 300, 450, 600]  # seconds

        for i, (expected, actual) in enumerate(zip(expected_times, intervention_times)):
            actual_seconds = (actual - start_time).total_seconds()
            deviation = abs(actual_seconds - expected)

            assert deviation < 0.5, \
                f"Intervention {i+1} deviation: {deviation:.3f}s (expected: {expected}s, actual: {actual_seconds:.3f}s)"

    @pytest.mark.asyncio
    async def test_resume_after_intervention(self):
        """
        Verify content resumes exactly where it paused
        """

        session_id = await self.create_session()

        # Play to 2.5 min mark
        await self.play_until(session_id, 150)

        # Intervention takes 45 seconds
        intervention_start = datetime.utcnow()
        await self.run_intervention(session_id, duration=45)
        intervention_end = datetime.utcnow()

        # Resume should start at exactly 150 seconds of content
        resume_state = await self.get_resume_state(session_id)

        assert resume_state['content_position'] == 150, \
            f"Content position should be 150s, got {resume_state['content_position']}s"

        # Verify intervention time is NOT counted toward content time
        total_wall_time = (intervention_end - intervention_start).total_seconds()
        assert total_wall_time > 45, "Intervention took time"

        # But content time should remain at 150
        assert resume_state['content_elapsed'] == 150, \
            "Content time should not include intervention duration"
```

---

## 2. AI Integration Testing

### 2.1 Socratic Question Quality Assurance

**Challenge:** How to test AI-generated questions are actually Socratic?

**Solution: Multi-Layer Quality Gates**

```python
# src/testing/ai_quality_gates.py

class SocraticQuestionValidator:
    """
    Validates AI-generated questions meet Socratic criteria
    """

    SOCRATIC_CRITERIA = {
        'open_ended': {
            'description': 'Question cannot be answered with yes/no',
            'weight': 0.25
        },
        'probing': {
            'description': 'Question challenges assumptions or probes deeper',
            'weight': 0.20
        },
        'builds_on_previous': {
            'description': 'Q2 and Q3 reference student answers',
            'weight': 0.25
        },
        'age_appropriate': {
            'description': 'Language matches student grade level',
            'weight': 0.15
        },
        'content_relevant': {
            'description': 'Directly relates to content segment',
            'weight': 0.15
        }
    }

    def __init__(self, llm_judge_model='claude-3-5-sonnet-20241022'):
        """
        Use LLM-as-judge pattern for quality scoring
        """
        self.anthropic = anthropic.Anthropic()
        self.judge_model = llm_judge_model

    async def validate_question_sequence(
        self,
        questions: list[str],
        answers: list[str],
        student_profile: dict,
        content_segment: dict
    ) -> dict:
        """
        Validates a 3-question Socratic sequence

        Returns:
            {
                'overall_score': float (0-1),
                'criteria_scores': dict,
                'feedback': str,
                'approved': bool
            }
        """

        evaluation_prompt = f"""
You are evaluating whether a sequence of 3 AI-generated questions follows the Socratic method effectively.

STUDENT CONTEXT:
- Age: {student_profile['age']}
- Grade: {student_profile['grade']}
- Content: {content_segment['summary']}

QUESTION SEQUENCE:
Q1: {questions[0]}
Student Answer: {answers[0]}

Q2: {questions[1]}
Student Answer: {answers[1]}

Q3: {questions[2]}

EVALUATION CRITERIA:
1. Open-ended (not yes/no): Score 0-1
2. Probing/challenging: Score 0-1
3. Builds on previous answers: Score 0-1
4. Age-appropriate language: Score 0-1
5. Content relevance: Score 0-1

Return JSON:
{{
    "open_ended": {{"score": 0.0-1.0, "reasoning": "..."}},
    "probing": {{"score": 0.0-1.0, "reasoning": "..."}},
    "builds_on_previous": {{"score": 0.0-1.0, "reasoning": "..."}},
    "age_appropriate": {{"score": 0.0-1.0, "reasoning": "..."}},
    "content_relevant": {{"score": 0.0-1.0, "reasoning": "..."}}
}}
"""

        response = await self.anthropic.messages.create(
            model=self.judge_model,
            max_tokens=1024,
            messages=[{"role": "user", "content": evaluation_prompt}]
        )

        evaluation = json.loads(response.content[0].text)

        # Calculate weighted score
        overall_score = sum(
            evaluation[criterion]['score'] * self.SOCRATIC_CRITERIA[criterion]['weight']
            for criterion in self.SOCRATIC_CRITERIA.keys()
        )

        return {
            'overall_score': overall_score,
            'criteria_scores': evaluation,
            'approved': overall_score >= 0.75,  # 75% threshold
            'feedback': self._generate_feedback(evaluation)
        }

    def _generate_feedback(self, evaluation: dict) -> str:
        """Generate actionable feedback for low-scoring questions"""

        weak_areas = [
            criterion for criterion, data in evaluation.items()
            if data['score'] < 0.6
        ]

        if not weak_areas:
            return "Question sequence meets Socratic standards."

        feedback_parts = ["Areas for improvement:"]
        for area in weak_areas:
            feedback_parts.append(
                f"- {self.SOCRATIC_CRITERIA[area]['description']}: {evaluation[area]['reasoning']}"
            )

        return "\n".join(feedback_parts)


# Automated quality gate in production pipeline
class AIGenerationPipeline:

    async def generate_with_quality_gate(self, context: dict) -> dict:
        """
        Generate questions with automatic quality validation
        Retry up to 3 times if quality gates fail
        """

        validator = SocraticQuestionValidator()
        max_attempts = 3

        for attempt in range(max_attempts):
            # Generate questions
            questions, answers = await self.generate_socratic_sequence(context)

            # Validate quality
            validation = await validator.validate_question_sequence(
                questions=questions,
                answers=answers,
                student_profile=context['student'],
                content_segment=context['content']
            )

            # Log quality metrics
            await self.log_quality_metrics(validation, attempt)

            if validation['approved']:
                return {
                    'questions': questions,
                    'answers': answers,
                    'quality_score': validation['overall_score'],
                    'attempts': attempt + 1
                }

            # If not approved and not final attempt, regenerate with feedback
            if attempt < max_attempts - 1:
                context['improvement_feedback'] = validation['feedback']

        # All attempts failed - fallback to static questions
        raise AIQualityGateFailure(
            f"Failed to generate quality questions after {max_attempts} attempts",
            last_validation=validation
        )
```

### 2.2 Mock AI Services for Unit Tests

```python
# tests/mocks/ai_service_mock.py

class MockAnthropicService:
    """
    Deterministic mock for unit testing
    """

    CANNED_RESPONSES = {
        'segment_1_q1': "What aspects of the founding of Tredegar Iron Works in 1837 do you find most significant?",
        'segment_1_q2': "You mentioned {student_answer}. How do you think that factor influenced Richmond's industrial development?",
        'segment_1_q3': "Considering your insights about {previous_answers}, what questions does this raise about the relationship between industry and the Civil War?",

        # ... more canned responses for each segment
    }

    RESPONSE_LATENCIES = {
        'fast': 0.3,      # 300ms
        'normal': 1.2,    # 1.2s
        'slow': 3.5,      # 3.5s
        'timeout': 30.0   # 30s (should trigger timeout)
    }

    def __init__(self, mode='normal', failure_rate=0.0):
        """
        Args:
            mode: Response latency mode
            failure_rate: Probability of API failure (0.0-1.0)
        """
        self.mode = mode
        self.failure_rate = failure_rate
        self.call_count = 0
        self.call_history = []

    async def messages_create(self, model, messages, max_tokens, **kwargs):
        """
        Mock Anthropic API call
        """

        self.call_count += 1

        # Simulate failure
        if random.random() < self.failure_rate:
            raise anthropic.APIError("Simulated API failure")

        # Simulate latency
        await asyncio.sleep(self.RESPONSE_LATENCIES[self.mode])

        # Extract context from prompt
        prompt = messages[0]['content']

        # Determine which canned response to use
        response_key = self._select_response(prompt)
        response_text = self.CANNED_RESPONSES.get(
            response_key,
            "What are your thoughts on this topic?"
        )

        # Record call for verification
        self.call_history.append({
            'model': model,
            'prompt': prompt,
            'response': response_text,
            'timestamp': datetime.utcnow()
        })

        # Return mock response in Anthropic format
        return type('Response', (), {
            'content': [type('Content', (), {'text': response_text})()],
            'model': model,
            'stop_reason': 'end_turn'
        })()

    def _select_response(self, prompt: str) -> str:
        """Determine which canned response matches the prompt"""

        if 'segment_id": 1' in prompt and 'question_number": 1' in prompt:
            return 'segment_1_q1'
        elif 'segment_id": 1' in prompt and 'question_number": 2' in prompt:
            return 'segment_1_q2'
        # ... more logic

        return 'default'


# Usage in tests
@pytest.fixture
def mock_anthropic(monkeypatch):
    """Fixture providing mocked Anthropic service"""

    mock_service = MockAnthropicService(mode='fast', failure_rate=0.0)
    monkeypatch.setattr('anthropic.Anthropic', lambda: mock_service)

    return mock_service


def test_socratic_intervention_with_mock(mock_anthropic):
    """
    Test intervention flow without real API calls
    """

    intervention = SocraticInterventionEngine(
        student_profile={'age': 16, 'grade': 10},
        content_segment={'segment_id': 1, 'summary': '...'},
        model_adapter=mock_anthropic
    )

    result = await intervention.generate_question_sequence()

    # Verify 3 questions generated
    assert len(result['questions']) == 3

    # Verify API was called 3 times
    assert mock_anthropic.call_count == 3

    # Verify questions build on each other
    assert '{student_answer}' in mock_anthropic.call_history[1]['prompt']
```

### 2.3 Integration Tests with Real AI Models

```python
# tests/integration/test_ai_integration.py

@pytest.mark.integration
@pytest.mark.slow
class TestRealAIIntegration:
    """
    Integration tests using real Anthropic API
    Run in CI/CD with rate limiting
    """

    @pytest.mark.parametrize('student_age,grade', [
        (13, 7),
        (16, 10),
        (18, 12)
    ])
    async def test_age_appropriate_language(self, student_age, grade):
        """
        Verify questions are age-appropriate across different grades
        """

        real_service = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

        intervention = SocraticInterventionEngine(
            student_profile={'age': student_age, 'grade': grade},
            content_segment=TEST_CONTENT_SEGMENTS['segment_1'],
            model_adapter=real_service
        )

        result = await intervention.generate_question_sequence()

        # Analyze reading level
        for question in result['questions']:
            reading_level = textstat.flesch_kincaid_grade(question)

            # Reading level should be within 2 grades of student
            assert abs(reading_level - grade) <= 2, \
                f"Question reading level {reading_level} inappropriate for grade {grade}: {question}"

    @pytest.mark.parametrize('model', [
        'claude-3-5-sonnet-20241022',
        'claude-3-haiku-20240307'
    ])
    async def test_model_comparison(self, model):
        """
        Compare quality across different Claude models
        """

        validator = SocraticQuestionValidator()

        results = []
        for i in range(10):  # 10 trials per model
            intervention = SocraticInterventionEngine(
                student_profile=TEST_STUDENT_PROFILES['grade_10'],
                content_segment=TEST_CONTENT_SEGMENTS['segment_2'],
                model=model
            )

            questions, answers = await intervention.generate_question_sequence()

            validation = await validator.validate_question_sequence(
                questions, answers,
                student_profile=TEST_STUDENT_PROFILES['grade_10'],
                content_segment=TEST_CONTENT_SEGMENTS['segment_2']
            )

            results.append({
                'model': model,
                'quality_score': validation['overall_score'],
                'latency': intervention.last_call_latency,
                'cost': intervention.calculate_cost()
            })

        # Generate comparison report
        avg_quality = np.mean([r['quality_score'] for r in results])
        avg_latency = np.mean([r['latency'] for r in results])
        total_cost = sum([r['cost'] for r in results])

        print(f"\nModel: {model}")
        print(f"Avg Quality: {avg_quality:.3f}")
        print(f"Avg Latency: {avg_latency:.2f}s")
        print(f"Total Cost: ${total_cost:.4f}")

        # Quality threshold
        assert avg_quality >= 0.75, f"Model {model} avg quality {avg_quality} below threshold"
```

### 2.4 Prompt Regression Testing

```python
# tests/regression/test_prompt_changes.py

class PromptRegressionSuite:
    """
    Detect when prompt changes affect output quality
    """

    def __init__(self):
        self.baseline_db = 'test_data/prompt_baselines.db'
        self.conn = sqlite3.connect(self.baseline_db)
        self._init_db()

    def _init_db(self):
        """Create baseline storage"""

        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS prompt_baselines (
                id INTEGER PRIMARY KEY,
                prompt_version TEXT,
                test_case TEXT,
                input_hash TEXT,
                expected_response TEXT,
                quality_score REAL,
                created_at TIMESTAMP
            )
        """)

    async def record_baseline(self, prompt_version: str):
        """
        Record baseline responses for current prompt version
        """

        for test_case in STANDARD_TEST_CASES:
            response = await self.generate_with_prompt(
                prompt_version,
                test_case
            )

            quality = await self.evaluate_quality(response, test_case)

            self.conn.execute("""
                INSERT INTO prompt_baselines
                (prompt_version, test_case, input_hash, expected_response, quality_score, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                prompt_version,
                test_case['name'],
                hashlib.sha256(json.dumps(test_case).encode()).hexdigest(),
                json.dumps(response),
                quality['overall_score'],
                datetime.utcnow()
            ))

        self.conn.commit()

    async def test_against_baseline(self, new_prompt_version: str, baseline_version: str):
        """
        Test new prompt against baseline
        Alert if quality regresses
        """

        baselines = self.conn.execute("""
            SELECT test_case, expected_response, quality_score
            FROM prompt_baselines
            WHERE prompt_version = ?
        """, (baseline_version,)).fetchall()

        regressions = []
        improvements = []

        for test_case_name, expected_response, baseline_quality in baselines:
            test_case = STANDARD_TEST_CASES[test_case_name]

            new_response = await self.generate_with_prompt(
                new_prompt_version,
                test_case
            )

            new_quality = await self.evaluate_quality(new_response, test_case)

            quality_delta = new_quality['overall_score'] - baseline_quality

            if quality_delta < -0.05:  # 5% regression
                regressions.append({
                    'test_case': test_case_name,
                    'baseline': baseline_quality,
                    'new': new_quality['overall_score'],
                    'delta': quality_delta
                })
            elif quality_delta > 0.05:  # 5% improvement
                improvements.append({
                    'test_case': test_case_name,
                    'baseline': baseline_quality,
                    'new': new_quality['overall_score'],
                    'delta': quality_delta
                })

        # Generate report
        report = {
            'baseline_version': baseline_version,
            'new_version': new_prompt_version,
            'total_tests': len(baselines),
            'regressions': regressions,
            'improvements': improvements,
            'regression_rate': len(regressions) / len(baselines)
        }

        # Fail if > 10% regression rate
        assert report['regression_rate'] <= 0.1, \
            f"Prompt regression detected: {len(regressions)} test cases degraded"

        return report
```

---

## 3. Location Testing Strategy

### 3.1 GPS Verification and Geofencing

```python
# src/location/geofence_validator.py

from typing import Tuple
from geopy.distance import geodesic
import numpy as np

class GeofenceValidator:
    """
    Validates student location against approved experiment sites
    """

    APPROVED_LOCATIONS = {
        'on-site': {
            'name': 'Tredegar Iron Works',
            'center': (37.5316, -77.4481),
            'radius_meters': 100,
            'verification_method': 'GPS'
        },
        'learning-space': {
            'name': 'Lost Office Collaborative',
            'center': (37.5407, -77.4360),
            'radius_meters': 50,
            'verification_method': 'GPS'
        },
        'classroom': {
            'name': 'Richmond Classroom',
            'center': None,  # Multiple valid classrooms
            'approved_addresses': [
                '1234 School St, Richmond, VA',
                '5678 Education Ave, Richmond, VA'
            ],
            'verification_method': 'QR_CODE'
        },
        'home': {
            'name': 'Home Environment',
            'verification_method': 'HONOR_SYSTEM'
        }
    }

    def verify_location(
        self,
        claimed_location_type: str,
        gps_coords: Tuple[float, float] = None,
        qr_code: str = None
    ) -> dict:
        """
        Verify student is at approved location

        Returns:
            {
                'verified': bool,
                'location_type': str,
                'verification_method': str,
                'distance_from_center': float (meters),
                'accuracy_estimate': float (meters)
            }
        """

        location_config = self.APPROVED_LOCATIONS[claimed_location_type]

        if location_config['verification_method'] == 'GPS':
            return self._verify_gps(gps_coords, location_config)

        elif location_config['verification_method'] == 'QR_CODE':
            return self._verify_qr_code(qr_code, location_config)

        elif location_config['verification_method'] == 'HONOR_SYSTEM':
            return {
                'verified': True,
                'location_type': claimed_location_type,
                'verification_method': 'HONOR_SYSTEM',
                'note': 'Home location uses self-reporting'
            }

    def _verify_gps(self, gps_coords: Tuple[float, float], config: dict) -> dict:
        """
        Verify GPS coordinates within geofence
        """

        if not gps_coords:
            return {
                'verified': False,
                'error': 'GPS coordinates required for this location type'
            }

        # Calculate distance from approved center
        distance = geodesic(gps_coords, config['center']).meters

        # Check if within radius
        within_geofence = distance <= config['radius_meters']

        return {
            'verified': within_geofence,
            'location_type': config['name'],
            'verification_method': 'GPS',
            'distance_from_center': distance,
            'geofence_radius': config['radius_meters'],
            'coordinates': gps_coords
        }

    def _verify_qr_code(self, qr_code: str, config: dict) -> dict:
        """
        Verify QR code matches approved classroom
        """

        # QR codes are signed tokens with location data
        try:
            payload = jwt.decode(
                qr_code,
                public_key=self.get_public_key(),
                algorithms=['RS256']
            )

            # Verify timestamp (QR codes expire after 24 hours)
            issued_at = datetime.fromisoformat(payload['iat'])
            age_hours = (datetime.utcnow() - issued_at).total_seconds() / 3600

            if age_hours > 24:
                return {
                    'verified': False,
                    'error': 'QR code expired'
                }

            # Verify location
            if payload['location'] in config['approved_addresses']:
                return {
                    'verified': True,
                    'location_type': config['name'],
                    'verification_method': 'QR_CODE',
                    'classroom_id': payload['location']
                }
            else:
                return {
                    'verified': False,
                    'error': 'QR code not from approved classroom'
                }

        except jwt.InvalidTokenError as e:
            return {
                'verified': False,
                'error': f'Invalid QR code: {str(e)}'
            }


# tests/unit/test_geofencing.py

class TestGeofencing:

    def test_on_site_within_radius(self):
        """Student at Tredegar Iron Works - should verify"""

        validator = GeofenceValidator()

        # Coordinates 50 meters from center
        test_coords = (37.5320, -77.4485)

        result = validator.verify_location('on-site', gps_coords=test_coords)

        assert result['verified'] == True
        assert result['distance_from_center'] < 100

    def test_on_site_outside_radius(self):
        """Student too far from Tredegar - should fail"""

        validator = GeofenceValidator()

        # Coordinates 500 meters away
        test_coords = (37.5360, -77.4481)

        result = validator.verify_location('on-site', gps_coords=test_coords)

        assert result['verified'] == False
        assert result['distance_from_center'] > 100

    def test_gps_spoofing_detection(self):
        """Detect impossible GPS movements (teleportation)"""

        validator = GeofenceValidator()
        session_id = 'test-session-123'

        # First check-in at Tredegar
        check_in_1 = validator.verify_location('on-site', gps_coords=(37.5316, -77.4481))
        validator.record_location(session_id, check_in_1, timestamp=datetime.utcnow())

        # 30 seconds later, claim to be at learning space (2km away)
        check_in_2 = validator.verify_location('learning-space', gps_coords=(37.5407, -77.4360))

        # Validate movement is plausible
        is_plausible = validator.validate_movement_plausibility(
            session_id,
            new_location=check_in_2,
            timestamp=datetime.utcnow()
        )

        assert is_plausible == False, "Should detect impossible 2km movement in 30 seconds"
```

### 3.2 Mock Location Services for Dev/Test

```python
# tests/mocks/location_service_mock.py

class MockLocationService:
    """
    Simulates GPS and location services for testing
    """

    def __init__(self, mode='accurate'):
        """
        Modes:
            - accurate: Returns exact coordinates
            - noisy: Adds realistic GPS noise (+/- 10m)
            - spoofed: Returns wrong coordinates
            - unavailable: Simulates GPS unavailable
        """
        self.mode = mode
        self.location_history = []

    def get_current_location(self, claimed_type: str) -> dict:
        """
        Mock getting device GPS coordinates
        """

        if self.mode == 'unavailable':
            raise LocationServiceUnavailable("GPS signal not available")

        # Base coordinates for claimed type
        base_coords = self._get_base_coordinates(claimed_type)

        if self.mode == 'accurate':
            coords = base_coords
            accuracy = 5.0  # meters

        elif self.mode == 'noisy':
            # Add realistic GPS noise
            noise = np.random.normal(0, 0.00005, size=2)  # ~5-10m noise
            coords = (
                base_coords[0] + noise[0],
                base_coords[1] + noise[1]
            )
            accuracy = np.random.uniform(5, 15)  # 5-15m accuracy

        elif self.mode == 'spoofed':
            # Return coordinates from wrong location
            wrong_location = self._get_wrong_location(claimed_type)
            coords = self._get_base_coordinates(wrong_location)
            accuracy = 5.0

        result = {
            'latitude': coords[0],
            'longitude': coords[1],
            'accuracy': accuracy,
            'timestamp': datetime.utcnow().isoformat(),
            'provider': 'mock_gps'
        }

        self.location_history.append(result)
        return result

    def _get_base_coordinates(self, location_type: str) -> Tuple[float, float]:
        """Get center coordinates for each location type"""

        coords_map = {
            'on-site': (37.5316, -77.4481),
            'learning-space': (37.5407, -77.4360),
            'classroom': (37.5450, -77.4400),  # Example classroom
            'home': (37.5500, -77.4500)  # Example home
        }

        return coords_map.get(location_type, (0, 0))


# Usage in tests
@pytest.fixture
def mock_gps():
    return MockLocationService(mode='accurate')


def test_location_verification_with_mock_gps(mock_gps):
    """
    Test location verification using mocked GPS
    """

    validator = GeofenceValidator()

    # Get mock GPS coordinates
    gps_data = mock_gps.get_current_location('on-site')

    # Verify location
    result = validator.verify_location(
        claimed_location_type='on-site',
        gps_coords=(gps_data['latitude'], gps_data['longitude'])
    )

    assert result['verified'] == True
```

---

## 4. Session State Management Testing

### 4.1 State Persistence Across Interruptions

```python
# src/session/state_manager.py

class SessionStateManager:
    """
    Manages experiment session state with persistence
    """

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table('ExperimentSessions')
        self.state_cache = {}

    async def save_checkpoint(self, checkpoint_data: dict):
        """
        Save session state checkpoint
        Atomically updates DynamoDB with versioning
        """

        checkpoint = {
            'session_id': self.session_id,
            'checkpoint_time': datetime.utcnow().isoformat(),
            'state': checkpoint_data,
            'version': self._get_next_version()
        }

        # Atomic write with optimistic locking
        try:
            self.table.put_item(
                Item=checkpoint,
                ConditionExpression='attribute_not_exists(session_id) OR version < :new_version',
                ExpressionAttributeValues={
                    ':new_version': checkpoint['version']
                }
            )
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                # Concurrent write detected - merge and retry
                await self._handle_concurrent_write(checkpoint)
            else:
                raise

    async def restore_session(self) -> dict:
        """
        Restore session from last checkpoint
        """

        response = self.table.get_item(Key={'session_id': self.session_id})

        if 'Item' not in response:
            raise SessionNotFound(f"No session found: {self.session_id}")

        checkpoint = response['Item']

        # Verify checkpoint integrity
        if not self._verify_checkpoint_integrity(checkpoint):
            raise CorruptedCheckpoint(f"Session checkpoint corrupted: {self.session_id}")

        return checkpoint['state']

    def _verify_checkpoint_integrity(self, checkpoint: dict) -> bool:
        """
        Verify checkpoint has not been corrupted
        """

        required_fields = [
            'session_id',
            'checkpoint_time',
            'state',
            'version'
        ]

        # Check required fields present
        if not all(field in checkpoint for field in required_fields):
            return False

        # Verify state structure
        state = checkpoint['state']
        required_state_fields = [
            'current_segment',
            'content_position',
            'interventions_completed',
            'student_responses'
        ]

        if not all(field in state for field in required_state_fields):
            return False

        # Verify data consistency
        if state['current_segment'] not in [0, 150, 300, 450, 600]:
            return False

        if state['content_position'] > 600:  # 10 minutes max
            return False

        return True


# tests/integration/test_session_persistence.py

class TestSessionPersistence:

    @pytest.mark.asyncio
    async def test_resume_after_network_interruption(self):
        """
        Simulate network interruption and verify resume works
        """

        session_id = str(uuid.uuid4())
        state_mgr = SessionStateManager(session_id)

        # Start session and progress to 2.5 minutes
        await self.start_session(session_id)
        await self.progress_to(session_id, content_position=150)

        # Complete first intervention
        await self.complete_intervention(session_id, intervention_num=1)

        # Checkpoint state
        checkpoint_before = {
            'current_segment': 150,
            'content_position': 150,
            'interventions_completed': 1,
            'student_responses': ['Answer 1', 'Answer 2', 'Answer 3']
        }
        await state_mgr.save_checkpoint(checkpoint_before)

        # Simulate network interruption (kill connection)
        await self.simulate_network_failure()

        # Wait 30 seconds
        await asyncio.sleep(30)

        # Restore network
        await self.restore_network()

        # Restore session
        restored_state = await state_mgr.restore_session()

        # Verify state matches checkpoint
        assert restored_state == checkpoint_before

        # Verify can continue from exact point
        next_segment = await self.get_next_segment(session_id)
        assert next_segment['start'] == 150, "Should resume at exactly 150 seconds"

    @pytest.mark.asyncio
    async def test_resume_after_app_crash(self):
        """
        Verify resume works after complete app crash
        """

        session_id = str(uuid.uuid4())

        # Run session until crash point
        process = await self.start_session_process(session_id)
        await self.progress_to(session_id, content_position=375)  # 6.25 minutes

        # Simulate crash (kill process)
        process.kill()
        await asyncio.sleep(2)

        # Restart app
        new_process = await self.start_session_process(session_id, resume=True)

        # Verify resumed at correct position
        state = await self.get_session_state(session_id)

        assert state['content_position'] == 375
        assert state['interventions_completed'] == 2  # Should have completed 2.5 and 5 min

    @pytest.mark.asyncio
    async def test_concurrent_state_updates(self):
        """
        Handle race conditions in state updates
        """

        session_id = str(uuid.uuid4())
        state_mgr = SessionStateManager(session_id)

        # Simulate two concurrent processes trying to update state
        async def update_worker(worker_id: int):
            for i in range(10):
                current_state = await state_mgr.restore_session()
                current_state['worker_updates'] = current_state.get('worker_updates', [])
                current_state['worker_updates'].append(f'worker_{worker_id}_update_{i}')

                await state_mgr.save_checkpoint(current_state)
                await asyncio.sleep(0.01)  # Small delay to trigger race conditions

        # Run two workers concurrently
        await asyncio.gather(
            update_worker(1),
            update_worker(2)
        )

        # Verify all updates preserved (no lost writes)
        final_state = await state_mgr.restore_session()
        assert len(final_state['worker_updates']) == 20, "All 20 updates should be preserved"
```

### 4.2 Data Consistency Validation

```python
# src/validation/data_consistency.py

class DataConsistencyValidator:
    """
    Validates experimental data meets integrity requirements
    """

    def validate_session_data(self, session_data: dict) -> dict:
        """
        Run comprehensive data consistency checks

        Returns:
            {
                'valid': bool,
                'errors': list[str],
                'warnings': list[str]
            }
        """

        errors = []
        warnings = []

        # Check 1: Timing consistency
        timing_check = self._validate_timing_consistency(session_data)
        if not timing_check['valid']:
            errors.extend(timing_check['errors'])

        # Check 2: Intervention completeness
        intervention_check = self._validate_interventions(session_data)
        if not intervention_check['valid']:
            errors.extend(intervention_check['errors'])

        # Check 3: Assessment scores in valid range
        assessment_check = self._validate_assessments(session_data)
        if not assessment_check['valid']:
            errors.extend(assessment_check['errors'])

        # Check 4: Location verification
        location_check = self._validate_location_data(session_data)
        if not location_check['valid']:
            warnings.extend(location_check['warnings'])

        # Check 5: Student response quality
        response_check = self._validate_responses(session_data)
        if not response_check['valid']:
            warnings.extend(response_check['warnings'])

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }

    def _validate_timing_consistency(self, session_data: dict) -> dict:
        """
        Verify timing makes sense
        """

        errors = []

        # Interventions should occur at expected times
        expected_times = {
            2.5: [150],
            5.0: [300],
            10.0: [600]
        }

        interval = session_data['condition']['interval']
        expected = []

        if interval == 2.5:
            expected = [150, 300, 450, 600]
        elif interval == 5.0:
            expected = [300, 600]
        else:
            expected = [600]

        actual_times = [i['timestamp'] for i in session_data.get('interventions', [])]

        for exp_time in expected:
            # Find closest actual time
            if actual_times:
                closest = min(actual_times, key=lambda x: abs(x - exp_time))
                deviation = abs(closest - exp_time)

                if deviation > 5:  # More than 5 seconds off
                    errors.append(
                        f"Intervention timing off by {deviation}s (expected {exp_time}s, got {closest}s)"
                    )

        # Total session time should be ~600s + intervention time
        total_time = session_data['content_delivery']['actual_completion_time']
        expected_min = 600
        expected_max = 600 + (len(expected) * 180)  # 3 min max per intervention

        if not (expected_min <= total_time <= expected_max):
            errors.append(
                f"Total session time {total_time}s outside expected range {expected_min}-{expected_max}s"
            )

        return {
            'valid': len(errors) == 0,
            'errors': errors
        }

    def _validate_interventions(self, session_data: dict) -> dict:
        """
        Verify all interventions completed properly
        """

        errors = []

        for i, intervention in enumerate(session_data.get('interventions', [])):
            # Each intervention should have 3 questions
            if len(intervention.get('questions', [])) != 3:
                errors.append(
                    f"Intervention {i+1} has {len(intervention['questions'])} questions (expected 3)"
                )

            # Each question should have an answer
            if len(intervention.get('answers', [])) != 3:
                errors.append(
                    f"Intervention {i+1} has {len(intervention['answers'])} answers (expected 3)"
                )

            # Answers should not be empty
            for j, answer in enumerate(intervention.get('answers', [])):
                if not answer or len(answer.strip()) < 5:
                    errors.append(
                        f"Intervention {i+1}, Answer {j+1} appears invalid or too short"
                    )

        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
```

---

## 5. Performance Testing

### 5.1 Load Testing for Concurrent Sessions

```python
# tests/performance/test_load.py

import locust
from locust import HttpUser, task, between

class ExperimentSessionUser(locust.HttpUser):
    """
    Simulates a student going through an experiment session
    """

    wait_time = between(1, 3)  # Wait 1-3 seconds between requests

    def on_start(self):
        """Initialize session"""

        # Authenticate (if needed)
        self.client.post("/api/auth/login", json={
            "student_id": f"test_student_{self.environment.runner.user_count}",
            "password": "test_password"
        })

        # Start experiment session
        response = self.client.post("/api/sessions/start", json={
            "condition": {
                "location": "on-site",
                "interval": 2.5,
                "intervention": "dynamic"
            }
        })

        self.session_id = response.json()['session_id']

    @task(1)
    def complete_intervention(self):
        """Simulate completing a Socratic intervention"""

        # Request intervention
        response = self.client.post(
            f"/api/sessions/{self.session_id}/intervention",
            json={"timestamp": 150}
        )

        questions = response.json()['questions']

        # Answer each question
        for i, question in enumerate(questions):
            self.client.post(
                f"/api/sessions/{self.session_id}/answer",
                json={
                    "question_num": i + 1,
                    "answer": f"This is my thoughtful answer to question {i+1}"
                },
                name="/api/sessions/[id]/answer"  # Group in locust stats
            )

    @task(2)
    def update_progress(self):
        """Report content progress"""

        self.client.post(
            f"/api/sessions/{self.session_id}/progress",
            json={"content_position": 150},
            name="/api/sessions/[id]/progress"
        )


# Run load test
# locust -f tests/performance/test_load.py --users 100 --spawn-rate 10 --host https://api.socratic-experiment.com

# Expected results:
# - 100 concurrent sessions
# - < 2s response time for intervention requests (p95)
# - < 500ms for progress updates (p95)
# - 0% error rate
```

### 5.2 AI Response Time SLAs

```python
# tests/performance/test_ai_latency.py

class AILatencySLATest:
    """
    Verify AI response times meet SLA requirements
    """

    SLA_TARGETS = {
        'question_generation': {
            'p50': 1.5,   # 50th percentile: 1.5s
            'p95': 3.0,   # 95th percentile: 3.0s
            'p99': 5.0    # 99th percentile: 5.0s
        },
        'question_evaluation': {
            'p50': 1.0,
            'p95': 2.0,
            'p99': 3.0
        }
    }

    async def test_question_generation_latency(self):
        """
        Measure AI question generation latency distribution
        """

        latencies = []

        # Generate 1000 questions
        for i in range(1000):
            start = time.perf_counter()

            question = await self.generate_socratic_question(
                student_profile=TEST_PROFILES['grade_10'],
                content_segment=TEST_SEGMENTS['segment_1']
            )

            latency = time.perf_counter() - start
            latencies.append(latency)

        # Calculate percentiles
        p50 = np.percentile(latencies, 50)
        p95 = np.percentile(latencies, 95)
        p99 = np.percentile(latencies, 99)

        # Verify SLAs
        assert p50 <= self.SLA_TARGETS['question_generation']['p50'], \
            f"P50 latency {p50:.2f}s exceeds SLA {self.SLA_TARGETS['question_generation']['p50']}s"

        assert p95 <= self.SLA_TARGETS['question_generation']['p95'], \
            f"P95 latency {p95:.2f}s exceeds SLA {self.SLA_TARGETS['question_generation']['p95']}s"

        assert p99 <= self.SLA_TARGETS['question_generation']['p99'], \
            f"P99 latency {p99:.2f}s exceeds SLA {self.SLA_TARGETS['question_generation']['p99']}s"

        # Generate latency distribution report
        self._generate_latency_report('question_generation', latencies)

    def _generate_latency_report(self, test_name: str, latencies: list):
        """Generate detailed latency analysis"""

        report = {
            'test': test_name,
            'samples': len(latencies),
            'percentiles': {
                'p50': np.percentile(latencies, 50),
                'p75': np.percentile(latencies, 75),
                'p90': np.percentile(latencies, 90),
                'p95': np.percentile(latencies, 95),
                'p99': np.percentile(latencies, 99),
                'p999': np.percentile(latencies, 99.9)
            },
            'statistics': {
                'mean': np.mean(latencies),
                'median': np.median(latencies),
                'std_dev': np.std(latencies),
                'min': np.min(latencies),
                'max': np.max(latencies)
            },
            'sla_compliance': {
                'p50': np.percentile(latencies, 50) <= self.SLA_TARGETS[test_name]['p50'],
                'p95': np.percentile(latencies, 95) <= self.SLA_TARGETS[test_name]['p95'],
                'p99': np.percentile(latencies, 99) <= self.SLA_TARGETS[test_name]['p99']
            }
        }

        # Save to file
        with open(f'performance_reports/{test_name}_latency.json', 'w') as f:
            json.dump(report, f, indent=2)

        # Generate histogram
        plt.figure(figsize=(10, 6))
        plt.hist(latencies, bins=50, edgecolor='black')
        plt.axvline(report['percentiles']['p50'], color='green', linestyle='--', label='P50')
        plt.axvline(report['percentiles']['p95'], color='orange', linestyle='--', label='P95')
        plt.axvline(report['percentiles']['p99'], color='red', linestyle='--', label='P99')
        plt.xlabel('Latency (seconds)')
        plt.ylabel('Frequency')
        plt.title(f'{test_name} Latency Distribution')
        plt.legend()
        plt.savefig(f'performance_reports/{test_name}_histogram.png')
```

### 5.3 Database Throughput Validation

```python
# tests/performance/test_database_throughput.py

class DatabaseThroughputTest:
    """
    Validate database can handle concurrent session writes
    """

    async def test_concurrent_checkpoint_writes(self):
        """
        Verify DynamoDB can handle 100 concurrent sessions
        Each session writes checkpoints every 30 seconds
        """

        num_sessions = 100
        test_duration_seconds = 300  # 5 minutes
        checkpoint_interval = 30

        sessions = [str(uuid.uuid4()) for _ in range(num_sessions)]

        async def session_worker(session_id: str):
            """Simulate one session's checkpoint writes"""

            state_mgr = SessionStateManager(session_id)
            writes_completed = 0
            write_latencies = []

            for i in range(test_duration_seconds // checkpoint_interval):
                checkpoint_data = {
                    'current_segment': i * 30,
                    'content_position': i * 30,
                    'interventions_completed': i // 5,
                    'student_responses': [f'Answer {j}' for j in range(i * 3)]
                }

                start = time.perf_counter()
                await state_mgr.save_checkpoint(checkpoint_data)
                latency = time.perf_counter() - start

                write_latencies.append(latency)
                writes_completed += 1

                await asyncio.sleep(checkpoint_interval)

            return {
                'session_id': session_id,
                'writes_completed': writes_completed,
                'latencies': write_latencies
            }

        # Run all sessions concurrently
        results = await asyncio.gather(*[session_worker(sid) for sid in sessions])

        # Aggregate metrics
        total_writes = sum(r['writes_completed'] for r in results)
        all_latencies = [lat for r in results for lat in r['latencies']]

        writes_per_second = total_writes / test_duration_seconds
        p95_latency = np.percentile(all_latencies, 95)
        error_rate = sum(1 for r in results if r['writes_completed'] < test_duration_seconds // checkpoint_interval) / num_sessions

        print(f"\nDatabase Throughput Test Results:")
        print(f"Total writes: {total_writes}")
        print(f"Writes/second: {writes_per_second:.2f}")
        print(f"P95 latency: {p95_latency:.3f}s")
        print(f"Error rate: {error_rate:.2%}")

        # SLA assertions
        assert writes_per_second >= 50, f"Throughput {writes_per_second:.2f} writes/s below minimum 50 writes/s"
        assert p95_latency <= 0.5, f"P95 latency {p95_latency:.3f}s exceeds 500ms SLA"
        assert error_rate == 0, f"Error rate {error_rate:.2%} should be 0%"
```

---

## 6. Validation Framework for Experimental Integrity

### 6.1 Condition Randomization Validation

```python
# src/validation/randomization_validator.py

class RandomizationValidator:
    """
    Ensures students are truly randomly assigned to conditions
    Tests for bias in assignment algorithm
    """

    def validate_assignment_distribution(self, assignments: list[dict]) -> dict:
        """
        Verify condition assignments are balanced

        Args:
            assignments: List of {student_id, condition} dicts

        Returns:
            Statistical test results for randomization quality
        """

        # Count assignments to each condition
        condition_counts = {}

        for assignment in assignments:
            condition_key = self._condition_to_key(assignment['condition'])
            condition_counts[condition_key] = condition_counts.get(condition_key, 0) + 1

        total_assignments = len(assignments)
        num_conditions = 24  # 4 locations × 3 intervals × 2 interventions

        expected_per_condition = total_assignments / num_conditions

        # Chi-square test for uniform distribution
        observed = list(condition_counts.values())
        expected = [expected_per_condition] * num_conditions

        chi2, p_value = stats.chisquare(observed, expected)

        # Calculate Cramér's V (effect size)
        cramers_v = np.sqrt(chi2 / (total_assignments * (num_conditions - 1)))

        # Detect underrepresented conditions
        underrepresented = [
            (cond, count) for cond, count in condition_counts.items()
            if count < expected_per_condition * 0.8  # Less than 80% of expected
        ]

        # Detect overrepresented conditions
        overrepresented = [
            (cond, count) for cond, count in condition_counts.items()
            if count > expected_per_condition * 1.2  # More than 120% of expected
        ]

        return {
            'balanced': p_value > 0.05,  # Not significantly different from uniform
            'chi_square': chi2,
            'p_value': p_value,
            'cramers_v': cramers_v,
            'total_assignments': total_assignments,
            'expected_per_condition': expected_per_condition,
            'condition_counts': condition_counts,
            'underrepresented': underrepresented,
            'overrepresented': overrepresented,
            'recommendation': self._generate_recommendation(p_value, cramers_v)
        }

    def _condition_to_key(self, condition: dict) -> str:
        """Convert condition dict to unique key"""
        return f"{condition['location']}_{condition['interval']}_{condition['intervention']}"

    def _generate_recommendation(self, p_value: float, cramers_v: float) -> str:
        """Generate actionable recommendation"""

        if p_value > 0.05 and cramers_v < 0.1:
            return "Randomization is well-balanced. No action needed."
        elif p_value > 0.05:
            return "Randomization is statistically balanced but shows moderate effect size. Monitor for drift."
        else:
            return "Randomization is significantly imbalanced. Review assignment algorithm and consider rebalancing."

    def test_for_temporal_bias(self, assignments: list[dict]) -> dict:
        """
        Test if certain conditions are more likely at certain times
        (e.g., all 'home' conditions assigned in evenings)
        """

        # Group by hour of day
        hour_condition_map = {}

        for assignment in assignments:
            timestamp = datetime.fromisoformat(assignment['assigned_at'])
            hour = timestamp.hour
            condition = self._condition_to_key(assignment['condition'])

            if hour not in hour_condition_map:
                hour_condition_map[hour] = []

            hour_condition_map[hour].append(condition)

        # Test for independence (time vs condition)
        # If truly random, condition assignment should be independent of time

        # Create contingency table
        all_conditions = list(set(self._condition_to_key(a['condition']) for a in assignments))
        contingency_table = []

        for hour in range(24):
            row = []
            hour_assignments = hour_condition_map.get(hour, [])

            for condition in all_conditions:
                count = hour_assignments.count(condition)
                row.append(count)

            contingency_table.append(row)

        # Chi-square test for independence
        chi2, p_value, dof, expected = stats.chi2_contingency(contingency_table)

        return {
            'temporally_independent': p_value > 0.05,
            'chi_square': chi2,
            'p_value': p_value,
            'degrees_of_freedom': dof,
            'recommendation': "No temporal bias detected" if p_value > 0.05
                            else "WARNING: Condition assignments show temporal bias"
        }


# tests/validation/test_randomization.py

class TestRandomization:

    def test_balanced_assignment_across_conditions(self):
        """
        Simulate 1000 student assignments and verify balance
        """

        validator = RandomizationValidator()

        # Simulate assignments
        assignments = []
        for i in range(1000):
            condition = self.random_assignment_algorithm()
            assignments.append({
                'student_id': f'student_{i}',
                'condition': condition,
                'assigned_at': (datetime.utcnow() + timedelta(hours=i % 24)).isoformat()
            })

        # Validate distribution
        result = validator.validate_assignment_distribution(assignments)

        print(f"\nRandomization Test Results:")
        print(f"Chi-square: {result['chi_square']:.2f}")
        print(f"P-value: {result['p_value']:.4f}")
        print(f"Balanced: {result['balanced']}")
        print(f"Recommendation: {result['recommendation']}")

        assert result['balanced'], "Assignment distribution is significantly imbalanced"

        # No condition should be severely underrepresented
        assert len(result['underrepresented']) == 0, \
            f"Underrepresented conditions detected: {result['underrepresented']}"

    def test_no_temporal_bias(self):
        """
        Verify assignments don't cluster by time of day
        """

        validator = RandomizationValidator()

        # Simulate assignments spread across different times
        assignments = []
        for i in range(2400):  # 100 per hour
            hour = i % 24
            condition = self.random_assignment_algorithm()

            assignments.append({
                'student_id': f'student_{i}',
                'condition': condition,
                'assigned_at': datetime(2025, 10, 23, hour, 0, 0).isoformat()
            })

        result = validator.test_for_temporal_bias(assignments)

        assert result['temporally_independent'], \
            "Temporal bias detected in condition assignments"
```

### 6.2 Intervention Timing Accuracy Validation

```python
# src/validation/timing_validator.py

class InterventionTimingValidator:
    """
    Validates interventions occurred at precisely the correct times
    """

    TOLERANCE_MS = 500  # +/- 500ms acceptable

    def validate_session_timing(self, session_data: dict) -> dict:
        """
        Comprehensive timing validation for a session
        """

        condition = session_data['condition']
        interval = condition['interval']

        # Expected intervention times
        expected_times = self._calculate_expected_times(interval)

        # Actual intervention times
        actual_interventions = session_data.get('interventions', [])

        timing_errors = []

        for expected_time in expected_times:
            # Find matching intervention
            matching = [
                i for i in actual_interventions
                if abs(i['timestamp'] - expected_time) < 10  # within 10 seconds
            ]

            if not matching:
                timing_errors.append({
                    'type': 'missing_intervention',
                    'expected_time': expected_time,
                    'error': 'No intervention found within 10 seconds of expected time'
                })
                continue

            # Check precision
            intervention = matching[0]
            deviation_ms = abs(intervention['timestamp'] - expected_time) * 1000

            if deviation_ms > self.TOLERANCE_MS:
                timing_errors.append({
                    'type': 'timing_deviation',
                    'expected_time': expected_time,
                    'actual_time': intervention['timestamp'],
                    'deviation_ms': deviation_ms,
                    'tolerance_ms': self.TOLERANCE_MS
                })

        return {
            'valid': len(timing_errors) == 0,
            'timing_errors': timing_errors,
            'expected_interventions': len(expected_times),
            'actual_interventions': len(actual_interventions),
            'precision_score': 1.0 - (len(timing_errors) / len(expected_times)) if expected_times else 1.0
        }

    def _calculate_expected_times(self, interval: float) -> list[float]:
        """Calculate expected intervention times based on interval"""

        if interval == 2.5:
            return [150, 300, 450, 600]  # 2.5, 5, 7.5, 10 minutes
        elif interval == 5.0:
            return [300, 600]  # 5, 10 minutes
        else:  # 10.0
            return [600]  # 10 minutes

    def generate_timing_report(self, all_sessions: list[dict]) -> dict:
        """
        Aggregate timing validation across all sessions
        """

        total_sessions = len(all_sessions)
        sessions_with_errors = 0
        all_errors = []
        precision_scores = []

        for session in all_sessions:
            validation = self.validate_session_timing(session)

            if not validation['valid']:
                sessions_with_errors += 1
                all_errors.extend(validation['timing_errors'])

            precision_scores.append(validation['precision_score'])

        return {
            'total_sessions': total_sessions,
            'sessions_with_timing_errors': sessions_with_errors,
            'error_rate': sessions_with_errors / total_sessions,
            'total_timing_errors': len(all_errors),
            'avg_precision_score': np.mean(precision_scores),
            'min_precision_score': np.min(precision_scores),
            'error_breakdown': self._breakdown_errors(all_errors),
            'recommendation': self._timing_recommendation(sessions_with_errors / total_sessions)
        }

    def _breakdown_errors(self, errors: list[dict]) -> dict:
        """Categorize timing errors"""

        breakdown = {
            'missing_intervention': 0,
            'timing_deviation': 0
        }

        for error in errors:
            breakdown[error['type']] = breakdown.get(error['type'], 0) + 1

        return breakdown

    def _timing_recommendation(self, error_rate: float) -> str:
        """Generate recommendation based on error rate"""

        if error_rate < 0.01:  # Less than 1%
            return "Timing accuracy excellent (<1% error rate)"
        elif error_rate < 0.05:  # 1-5%
            return "Timing accuracy acceptable but monitor for trends"
        else:
            return "WARNING: High timing error rate. Investigate orchestration system"
```

---

## 7. CI/CD Integration

### 7.1 Testing Pipeline

```yaml
# .github/workflows/test-pipeline.yml

name: Test Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:

  unit-tests:
    runs-on: ubuntu-latest
    timeout-minutes: 10

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Cache dependencies
        uses: actions/cache@v3
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-test.txt

      - name: Run unit tests
        run: |
          pytest tests/unit/ \
            --cov=src \
            --cov-report=xml \
            --cov-report=html \
            --junitxml=test-results/unit-tests.xml \
            -v

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
          flags: unit-tests

  integration-tests:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    needs: unit-tests

    services:
      dynamodb-local:
        image: amazon/dynamodb-local
        ports:
          - 8000:8000

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-test.txt

      - name: Set up test database
        run: |
          python scripts/setup_test_db.py

      - name: Run integration tests
        env:
          AWS_ENDPOINT_URL: http://localhost:8000
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_TEST_API_KEY }}
        run: |
          pytest tests/integration/ \
            --junitxml=test-results/integration-tests.xml \
            -v \
            -m "not slow"

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: integration-test-results
          path: test-results/

  ai-quality-tests:
    runs-on: ubuntu-latest
    timeout-minutes: 45
    needs: integration-tests
    if: github.event_name == 'pull_request'

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-test.txt

      - name: Run AI quality validation
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_TEST_API_KEY }}
        run: |
          pytest tests/ai_quality/ \
            --junitxml=test-results/ai-quality-tests.xml \
            -v

      - name: Generate quality report
        run: |
          python scripts/generate_ai_quality_report.py \
            --output reports/ai-quality-${{ github.sha }}.html

      - name: Upload quality report
        uses: actions/upload-artifact@v3
        with:
          name: ai-quality-report
          path: reports/

      - name: Comment PR with quality metrics
        uses: actions/github-script@v6
        with:
          script: |
            const fs = require('fs');
            const report = JSON.parse(fs.readFileSync('reports/ai-quality-summary.json'));

            const comment = `
            ## 🤖 AI Quality Report

            **Overall Score:** ${report.overall_score.toFixed(2)}/1.00

            **Criteria Breakdown:**
            - Open-ended: ${report.open_ended.toFixed(2)}
            - Probing: ${report.probing.toFixed(2)}
            - Builds on previous: ${report.builds_on_previous.toFixed(2)}
            - Age-appropriate: ${report.age_appropriate.toFixed(2)}
            - Content relevant: ${report.content_relevant.toFixed(2)}

            ${report.overall_score >= 0.75 ? '✅ Quality gate passed' : '❌ Quality gate failed'}
            `;

            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: comment
            });

  performance-tests:
    runs-on: ubuntu-latest
    timeout-minutes: 60
    needs: integration-tests
    if: github.ref == 'refs/heads/main'

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-test.txt
          pip install locust

      - name: Run performance tests
        env:
          TEST_ENVIRONMENT: staging
        run: |
          # Run load test
          locust -f tests/performance/test_load.py \
            --headless \
            --users 100 \
            --spawn-rate 10 \
            --run-time 10m \
            --host https://staging-api.socratic-experiment.com \
            --html reports/load-test-report.html \
            --csv reports/load-test

          # Run latency tests
          pytest tests/performance/ \
            --junitxml=test-results/performance-tests.xml \
            -v

      - name: Validate SLAs
        run: |
          python scripts/validate_slas.py \
            --load-test-csv reports/load-test_stats.csv \
            --latency-report reports/latency-report.json

      - name: Upload performance reports
        uses: actions/upload-artifact@v3
        with:
          name: performance-reports
          path: reports/

  experimental-integrity-tests:
    runs-on: ubuntu-latest
    timeout-minutes: 20
    needs: integration-tests

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-test.txt

      - name: Test randomization algorithm
        run: |
          pytest tests/validation/test_randomization.py -v

      - name: Test timing precision
        run: |
          pytest tests/validation/test_timing_precision.py -v

      - name: Test data consistency
        run: |
          pytest tests/validation/test_data_consistency.py -v

      - name: Generate validation report
        run: |
          python scripts/generate_validation_report.py \
            --output reports/experimental-integrity-${{ github.sha }}.pdf

      - name: Upload validation report
        uses: actions/upload-artifact@v3
        with:
          name: validation-report
          path: reports/
```

### 7.2 Deployment Gates

```yaml
# .github/workflows/deploy.yml

name: Deploy to Production

on:
  push:
    tags:
      - 'v*'

jobs:

  pre-deployment-validation:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Validate all tests passed
        run: |
          # Require all test jobs to have passed
          echo "Checking test status..."

      - name: Run security scan
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
          format: 'sarif'
          output: 'trivy-results.sarif'

      - name: Validate AI quality baseline
        run: |
          python scripts/validate_ai_quality_baseline.py \
            --min-score 0.75

      - name: Check performance benchmarks
        run: |
          python scripts/validate_performance_benchmarks.py \
            --p95-latency-max 3.0 \
            --throughput-min 50

  deploy-staging:
    runs-on: ubuntu-latest
    needs: pre-deployment-validation
    environment: staging

    steps:
      - uses: actions/checkout@v3

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1

      - name: Deploy to staging
        run: |
          # Deploy Lambda functions
          aws lambda update-function-code \
            --function-name socratic-intervention-staging \
            --zip-file fileb://deployment-package.zip

          # Update Step Functions
          aws stepfunctions update-state-machine \
            --state-machine-arn ${{ secrets.STAGING_STATE_MACHINE_ARN }} \
            --definition file://step-functions/experiment-orchestrator.json

      - name: Run smoke tests
        run: |
          pytest tests/smoke/ \
            --base-url https://staging-api.socratic-experiment.com \
            -v

  production-validation:
    runs-on: ubuntu-latest
    needs: deploy-staging

    steps:
      - name: Run end-to-end tests on staging
        run: |
          pytest tests/e2e/ \
            --base-url https://staging-api.socratic-experiment.com \
            -v

      - name: Validate experimental integrity
        run: |
          # Run 10 full sessions and validate data
          python scripts/run_validation_sessions.py \
            --num-sessions 10 \
            --environment staging

      - name: Manual approval gate
        uses: trstringer/manual-approval@v1
        with:
          secret: ${{ github.TOKEN }}
          approvers: research-team-leads
          minimum-approvals: 2
          issue-title: "Deploy to Production"

  deploy-production:
    runs-on: ubuntu-latest
    needs: production-validation
    environment: production

    steps:
      - uses: actions/checkout@v3

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1

      - name: Deploy to production
        run: |
          # Blue/green deployment
          python scripts/blue_green_deploy.py \
            --environment production \
            --health-check-retries 10

      - name: Post-deployment monitoring
        run: |
          # Monitor for 15 minutes
          python scripts/monitor_deployment.py \
            --duration 900 \
            --alert-on-error-rate 0.01
```

---

## 8. Testing Tools and Frameworks

### 8.1 Recommended Stack

```python
# requirements-test.txt

# Unit testing
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
pytest-mock==3.12.0

# Integration testing
pytest-docker==2.0.1
moto==4.2.9  # AWS service mocking
boto3-stubs[dynamodb,lambda,stepfunctions]==1.29.0

# AI testing
anthropic==0.7.1
openai==1.3.7

# Performance testing
locust==2.17.0
pytest-benchmark==4.0.0

# Data validation
pydantic==2.5.0
jsonschema==4.20.0

# Statistical testing
scipy==1.11.4
numpy==1.26.2
statsmodels==0.14.0

# Location testing
geopy==2.4.1

# Report generation
pytest-html==4.1.1
allure-pytest==2.13.2

# Code quality
ruff==0.1.6
mypy==1.7.1
black==23.11.0
```

### 8.2 Test Directory Structure

```
tests/
├── unit/
│   ├── test_socratic_engine.py
│   ├── test_location_validator.py
│   ├── test_session_manager.py
│   └── test_content_delivery.py
│
├── integration/
│   ├── test_step_functions.py
│   ├── test_ai_integration.py
│   ├── test_database_operations.py
│   └── test_timing_precision.py
│
├── e2e/
│   ├── test_full_session_flow.py
│   ├── test_multi_condition.py
│   └── test_location_scenarios.py
│
├── performance/
│   ├── test_load.py
│   ├── test_ai_latency.py
│   └── test_database_throughput.py
│
├── ai_quality/
│   ├── test_socratic_validation.py
│   ├── test_prompt_regression.py
│   └── test_age_appropriateness.py
│
├── validation/
│   ├── test_randomization.py
│   ├── test_timing_accuracy.py
│   └── test_data_consistency.py
│
├── mocks/
│   ├── ai_service_mock.py
│   ├── location_service_mock.py
│   └── aws_service_mocks.py
│
├── fixtures/
│   ├── student_profiles.py
│   ├── content_segments.py
│   └── test_sessions.py
│
└── conftest.py
```

---

## 9. Metrics and Success Criteria

### 9.1 Test Coverage Targets

```yaml
Coverage Targets:
  Unit Tests:
    - Overall: >= 85%
    - Critical paths (intervention, timing): >= 95%

  Integration Tests:
    - API endpoints: 100%
    - Step Functions states: 100%
    - Database operations: >= 90%

  E2E Tests:
    - All 24 conditions: 100%
    - Error scenarios: >= 80%
```

### 9.2 Performance Benchmarks

```yaml
Performance SLAs:

  AI Response Time:
    - P50: <= 1.5s
    - P95: <= 3.0s
    - P99: <= 5.0s

  Database Operations:
    - Checkpoint writes P95: <= 500ms
    - Session reads P95: <= 200ms
    - Throughput: >= 50 writes/second

  Timing Precision:
    - Intervention timing deviation: <= 500ms
    - Error rate: < 1%

  Load Capacity:
    - Concurrent sessions: >= 100
    - Error rate under load: < 0.1%
```

### 9.3 Quality Gates

```yaml
Quality Gates (must pass for deployment):

  Code Quality:
    - Ruff linting: 0 errors
    - Type coverage: >= 90%
    - Security scan: 0 critical/high vulnerabilities

  Test Success:
    - Unit tests: 100% pass
    - Integration tests: 100% pass
    - E2E tests: >= 95% pass

  AI Quality:
    - Socratic question score: >= 0.75
    - Age-appropriateness: >= 0.80
    - Content relevance: >= 0.85

  Experimental Integrity:
    - Randomization balance: p-value > 0.05
    - Timing precision: >= 99% within tolerance
    - Data consistency: 100% valid
```

---

## 10. Implementation Phases

### Phase 1: Foundation (Weeks 1-2)
- Set up test infrastructure
- Implement mock services
- Create test fixtures
- Build CI/CD pipeline

### Phase 2: Core Testing (Weeks 3-4)
- Unit tests for all components
- Integration tests for AWS services
- Location testing framework
- Session state management tests

### Phase 3: AI Quality (Weeks 5-6)
- AI quality validation framework
- LLM-as-judge implementation
- Prompt regression testing
- Model comparison tests

### Phase 4: Performance (Week 7)
- Load testing setup
- Latency benchmarking
- Database throughput tests
- SLA validation

### Phase 5: Experimental Integrity (Week 8)
- Randomization validation
- Timing precision tests
- Data consistency framework
- End-to-end validation

### Phase 6: Production Readiness (Week 9-10)
- Deploy staging environment
- Run validation sessions
- Performance tuning
- Documentation

---

## Summary

This comprehensive test automation strategy provides:

1. **Precision Timing**: Step Functions orchestration with < 500ms deviation
2. **AI Quality Assurance**: Multi-layer validation using LLM-as-judge
3. **Location Verification**: GPS geofencing with mock services for testing
4. **State Resilience**: Checkpoint-based persistence with corruption detection
5. **Performance Validation**: Load testing for 100+ concurrent sessions
6. **Experimental Integrity**: Statistical validation of randomization and timing
7. **CI/CD Integration**: Automated quality gates and deployment pipeline

The strategy balances comprehensive testing with practical implementation timelines, ensuring the platform delivers rigorous, reproducible experimental results.
