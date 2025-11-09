"""
DynamoDB Helper Functions for Socratic AI Benchmarks Platform

This module provides type-safe helper functions for interacting with the
DynamoDB schema defined in DYNAMODB_SCHEMA.md
"""

import boto3
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Literal
from decimal import Decimal
import uuid


# ============================================================================
# Type Definitions
# ============================================================================

LocationType = Literal["on-site", "learning-space", "classroom", "home"]
InterventionType = Literal["static", "dynamic"]
AssessmentType = Literal["baseline", "midpoint", "final"]


# ============================================================================
# DynamoDB Client Setup
# ============================================================================


class SocraticBenchmarksDB:
    """Main database interface for Socratic AI Benchmarks"""

    def __init__(
        self, table_name: str = "SocraticBenchmarks", region: str = "us-east-1"
    ):
        self.dynamodb = boto3.resource("dynamodb", region_name=region)
        self.table = self.dynamodb.Table(table_name)
        self.client = boto3.client("dynamodb", region_name=region)

    # ========================================================================
    # Utility Functions
    # ========================================================================

    @staticmethod
    def generate_id() -> str:
        """Generate a UUID for new entities"""
        return str(uuid.uuid4())

    @staticmethod
    def generate_timestamp() -> str:
        """Generate ISO 8601 timestamp with UTC timezone"""
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    @staticmethod
    def generate_date() -> str:
        """Generate date string in YYYY-MM-DD format"""
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")

    @staticmethod
    def convert_floats_to_decimal(obj: Any) -> Any:
        """Convert floats to Decimal for DynamoDB compatibility"""
        if isinstance(obj, float):
            return Decimal(str(obj))
        elif isinstance(obj, dict):
            return {
                k: SocraticBenchmarksDB.convert_floats_to_decimal(v)
                for k, v in obj.items()
            }
        elif isinstance(obj, list):
            return [
                SocraticBenchmarksDB.convert_floats_to_decimal(item) for item in obj
            ]
        return obj

    @staticmethod
    def convert_decimal_to_float(obj: Any) -> Any:
        """Convert Decimal to float for JSON serialization"""
        if isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, dict):
            return {
                k: SocraticBenchmarksDB.convert_decimal_to_float(v)
                for k, v in obj.items()
            }
        elif isinstance(obj, list):
            return [SocraticBenchmarksDB.convert_decimal_to_float(item) for item in obj]
        return obj

    # ========================================================================
    # Student Operations
    # ========================================================================

    def create_student(
        self,
        age: int,
        grade_level: int,
        school: str,
        richmond_resident: bool,
        depth_preference: Literal["surface", "moderate", "deep"],
        learning_style: str,
        prior_knowledge_topics: List[str],
        parent_consent: bool,
        student_assent: bool,
    ) -> Dict:
        """Create a new student profile"""
        student_id = self.generate_id()
        timestamp = self.generate_timestamp()

        student_profile = {
            "PK": f"STUDENT#{student_id}",
            "SK": "PROFILE",
            "GSI2PK": f"STUDENT#{student_id}",
            "GSI2SK": "PROFILE",
            "entity_type": "student_profile",
            "student_id": student_id,
            "demographics": {
                "age": age,
                "grade_level": grade_level,
                "school": school,
                "richmond_resident": richmond_resident,
            },
            "learning_profile": {
                "depth_preference": depth_preference,
                "learning_style": learning_style,
                "prior_knowledge_topics": prior_knowledge_topics,
            },
            "consent_data": {
                "parent_consent": parent_consent,
                "student_assent": student_assent,
                "irb_consent_date": timestamp,
                "data_sharing_consent": True,
            },
            "metadata": {
                "created_at": timestamp,
                "updated_at": timestamp,
                "total_sessions": 0,
                "conditions_completed": [],
            },
        }

        # Convert floats to Decimal
        student_profile = self.convert_floats_to_decimal(student_profile)

        # Write to DynamoDB
        self.table.put_item(Item=student_profile)

        return student_profile

    def get_student(self, student_id: str) -> Optional[Dict]:
        """Retrieve student profile"""
        response = self.table.get_item(
            Key={"PK": f"STUDENT#{student_id}", "SK": "PROFILE"}
        )
        return self.convert_decimal_to_float(response.get("Item"))

    def update_student_session_count(self, student_id: str, condition_code: str):
        """Increment student session count and track condition"""
        timestamp = self.generate_timestamp()

        self.table.update_item(
            Key={"PK": f"STUDENT#{student_id}", "SK": "PROFILE"},
            UpdateExpression="ADD metadata.total_sessions :inc SET metadata.updated_at = :now, metadata.conditions_completed = list_append(if_not_exists(metadata.conditions_completed, :empty_list), :condition)",
            ExpressionAttributeValues={
                ":inc": 1,
                ":now": timestamp,
                ":condition": [condition_code],
                ":empty_list": [],
            },
        )

    # ========================================================================
    # Session Operations
    # ========================================================================

    def create_session(
        self,
        student_id: str,
        location: LocationType,
        location_name: str,
        interval_minutes: Literal[2.5, 5.0, 10.0],
        intervention_type: InterventionType,
        student_age: int,
        student_grade: int,
        richmond_resident: bool,
        prior_knowledge_score: float,
    ) -> Dict:
        """Create a new experimental session"""
        session_id = self.generate_id()
        timestamp = self.generate_timestamp()
        date = self.generate_date()

        # Generate condition code
        location_codes = {
            "on-site": "L1",
            "learning-space": "L2",
            "classroom": "L3",
            "home": "L4",
        }
        interval_codes = {2.5: "I1", 5.0: "I2", 10.0: "I3"}
        intervention_codes = {"static": "S", "dynamic": "D"}

        condition_code = f"{location_codes[location]}-{interval_codes[interval_minutes]}-{intervention_codes[intervention_type]}"

        session = {
            "PK": f"SESSION#{session_id}",
            "SK": "METADATA",
            "GSI1PK": f"CONDITION#{location}#{interval_minutes}#{intervention_type}",
            "GSI1SK": timestamp,
            "GSI2PK": f"STUDENT#{student_id}",
            "GSI2SK": f"SESSION#{timestamp}",
            "GSI3PK": f"LOCATION#{location}",
            "GSI3SK": timestamp,
            "GSI4PK": f"INTERVENTION#{intervention_type}",
            "GSI4SK": timestamp,
            "GSI5PK": f"DATE#{date}",
            "GSI5SK": timestamp,
            "entity_type": "session",
            "session_id": session_id,
            "student_id": student_id,
            "experimental_condition": {
                "location": location,
                "location_name": location_name,
                "interval_minutes": interval_minutes,
                "intervention_type": intervention_type,
                "condition_code": condition_code,
            },
            "timeline": {
                "session_start": timestamp,
                "session_end": None,
                "total_duration_seconds": 0,
                "content_duration_seconds": 0,
                "intervention_duration_seconds": 0,
                "assessment_duration_seconds": 0,
            },
            "completion_status": {
                "completed": False,
                "location_verified": False,
                "baseline_completed": False,
                "content_completed": False,
                "interventions_completed": 0,
                "final_assessment_completed": False,
                "post_survey_completed": False,
            },
            "student_metadata": {
                "age": student_age,
                "grade": student_grade,
                "richmond_resident": richmond_resident,
                "prior_knowledge_score": prior_knowledge_score,
            },
            "metadata": {
                "created_at": timestamp,
                "updated_at": timestamp,
                "version": 1,
                "data_quality_flags": [],
            },
        }

        # Convert floats to Decimal
        session = self.convert_floats_to_decimal(session)

        # Write to DynamoDB
        self.table.put_item(Item=session)

        return session

    def get_session(self, session_id: str) -> Optional[Dict]:
        """Retrieve complete session data"""
        response = self.table.query(
            KeyConditionExpression="PK = :pk",
            ExpressionAttributeValues={":pk": f"SESSION#{session_id}"},
        )

        items = response.get("Items", [])
        if not items:
            return None

        # Organize items by type
        session_data = {
            "metadata": None,
            "location_verification": None,
            "content_delivery": None,
            "interventions": [],
            "assessments": {},
            "post_survey": None,
        }

        for item in items:
            item = self.convert_decimal_to_float(item)
            sk = item["SK"]

            if sk == "METADATA":
                session_data["metadata"] = item
            elif sk == "LOCATION_VERIFICATION":
                session_data["location_verification"] = item
            elif sk == "CONTENT_DELIVERY":
                session_data["content_delivery"] = item
            elif sk.startswith("INTERVENTION#"):
                session_data["interventions"].append(item)
            elif sk.startswith("ASSESSMENT#"):
                assessment_type = sk.split("#")[1]
                session_data["assessments"][assessment_type] = item
            elif sk == "POST_SURVEY":
                session_data["post_survey"] = item

        # Sort interventions by timestamp
        session_data["interventions"].sort(
            key=lambda x: x["intervention_metadata"]["timestamp"]
        )

        return session_data

    def update_session_status(self, session_id: str, status_updates: Dict):
        """Update session completion status"""
        timestamp = self.generate_timestamp()

        update_expressions = []
        expression_values = {":now": timestamp}

        for key, value in status_updates.items():
            update_expressions.append(f"completion_status.{key} = :{key}")
            expression_values[f":{key}"] = value

        update_expressions.append("metadata.updated_at = :now")

        self.table.update_item(
            Key={"PK": f"SESSION#{session_id}", "SK": "METADATA"},
            UpdateExpression=f"SET {', '.join(update_expressions)}",
            ExpressionAttributeValues=self.convert_floats_to_decimal(expression_values),
        )

    # ========================================================================
    # Location Verification Operations
    # ========================================================================

    def record_location_verification(
        self,
        session_id: str,
        student_id: str,
        location_type: LocationType,
        location_name: str,
        address: str,
        verification_method: Literal["GPS", "QR_code", "manual", "honor_system"],
        verified: bool,
        confidence: Literal["high", "medium", "low"],
        gps_data: Optional[Dict] = None,
        device_info: Optional[Dict] = None,
        ip_address: Optional[str] = None,
    ) -> Dict:
        """Record location verification for a session"""
        timestamp = self.generate_timestamp()

        location_verification = {
            "PK": f"SESSION#{session_id}",
            "SK": "LOCATION_VERIFICATION",
            "entity_type": "location_verification",
            "session_id": session_id,
            "student_id": student_id,
            "location_data": {
                "type": location_type,
                "name": location_name,
                "address": address,
            },
            "verification": {
                "method": verification_method,
                "verified": verified,
                "verification_timestamp": timestamp,
                "confidence": confidence,
            },
            "metadata": {
                "timestamp": timestamp,
                "ip_address": ip_address or "unknown",
                "session_token": "auto_generated",
            },
        }

        if gps_data:
            location_verification["gps_data"] = gps_data

        if device_info:
            location_verification["device_info"] = device_info

        # Convert and write
        location_verification = self.convert_floats_to_decimal(location_verification)
        self.table.put_item(Item=location_verification)

        # Update session status
        self.update_session_status(session_id, {"location_verified": verified})

        return location_verification

    # ========================================================================
    # Intervention Operations
    # ========================================================================

    def record_dynamic_intervention(
        self,
        session_id: str,
        student_id: str,
        sequence_number: int,
        segment_id: int,
        segment_summary: str,
        location_type: LocationType,
        location_name: str,
        socratic_sequence: List[Dict],
        ai_metadata: Dict,
    ) -> Dict:
        """Record a dynamic Socratic intervention"""
        timestamp = self.generate_timestamp()

        # Calculate summary metrics
        total_duration = sum(
            q["answer_metadata"]["response_time_seconds"]
            + (q["question_metadata"]["generation_time_ms"] / 1000)
            for q in socratic_sequence
        )

        avg_response_time = sum(
            q["answer_metadata"]["response_time_seconds"] for q in socratic_sequence
        ) / len(socratic_sequence)

        avg_question_quality = sum(
            q["quality_scores"].get("question_relevance", 0) for q in socratic_sequence
        ) / len(socratic_sequence)

        avg_answer_depth = sum(
            q["quality_scores"].get("answer_depth", 0) for q in socratic_sequence
        ) / len(socratic_sequence)

        intervention = {
            "PK": f"SESSION#{session_id}",
            "SK": f"INTERVENTION#{timestamp}#{segment_id}",
            "GSI4PK": "INTERVENTION#dynamic",
            "GSI4SK": timestamp,
            "entity_type": "intervention",
            "session_id": session_id,
            "student_id": student_id,
            "intervention_id": f"int_{self.generate_id()[:8]}",
            "intervention_metadata": {
                "type": "dynamic",
                "sequence_number": sequence_number,
                "timestamp": timestamp,
                "segment_id": segment_id,
                "segment_summary": segment_summary,
            },
            "location_context": {
                "location_type": location_type,
                "location_name": location_name,
                "location_aware_prompting": True,
            },
            "socratic_sequence": socratic_sequence,
            "intervention_summary": {
                "total_duration_seconds": total_duration,
                "questions_asked": len(socratic_sequence),
                "avg_response_time_seconds": avg_response_time,
                "avg_question_quality": avg_question_quality,
                "avg_answer_depth": avg_answer_depth,
                "progression_quality": 0.0,  # Calculate separately
                "location_awareness_utilized": True,
            },
            "ai_metadata": ai_metadata,
            "metadata": {
                "created_at": timestamp,
                "updated_at": timestamp,
                "version": 1,
            },
        }

        # Convert and write
        intervention = self.convert_floats_to_decimal(intervention)
        self.table.put_item(Item=intervention)

        # Update session intervention count
        self.update_session_status(
            session_id, {"interventions_completed": sequence_number}
        )

        return intervention

    def record_static_intervention(
        self,
        session_id: str,
        student_id: str,
        sequence_number: int,
        segment_id: int,
        segment_summary: str,
        location_type: LocationType,
        location_name: str,
        static_questions: List[Dict],
    ) -> Dict:
        """Record a static intervention"""
        timestamp = self.generate_timestamp()

        # Calculate summary metrics
        total_duration = sum(
            q["answer_metadata"]["response_time_seconds"] for q in static_questions
        )

        avg_response_time = total_duration / len(static_questions)

        avg_answer_depth = sum(
            q["quality_scores"].get("answer_depth", 0) for q in static_questions
        ) / len(static_questions)

        intervention = {
            "PK": f"SESSION#{session_id}",
            "SK": f"INTERVENTION#{timestamp}#{segment_id}",
            "GSI4PK": "INTERVENTION#static",
            "GSI4SK": timestamp,
            "entity_type": "intervention",
            "session_id": session_id,
            "student_id": student_id,
            "intervention_id": f"int_{self.generate_id()[:8]}",
            "intervention_metadata": {
                "type": "static",
                "sequence_number": sequence_number,
                "timestamp": timestamp,
                "segment_id": segment_id,
                "segment_summary": segment_summary,
            },
            "location_context": {
                "location_type": location_type,
                "location_name": location_name,
                "location_aware_prompting": False,
            },
            "static_questions": static_questions,
            "intervention_summary": {
                "total_duration_seconds": total_duration,
                "questions_asked": len(static_questions),
                "avg_response_time_seconds": avg_response_time,
                "avg_answer_depth": avg_answer_depth,
                "no_adaptive_followup": True,
            },
            "metadata": {
                "created_at": timestamp,
                "updated_at": timestamp,
                "version": 1,
            },
        }

        # Convert and write
        intervention = self.convert_floats_to_decimal(intervention)
        self.table.put_item(Item=intervention)

        # Update session intervention count
        self.update_session_status(
            session_id, {"interventions_completed": sequence_number}
        )

        return intervention

    # ========================================================================
    # Assessment Operations
    # ========================================================================

    def record_assessment(
        self,
        session_id: str,
        student_id: str,
        assessment_type: AssessmentType,
        questions: List[Dict],
        assessment_results: Dict,
        scoring_breakdown: Dict,
        duration_seconds: int,
        learning_gain: Optional[Dict] = None,
    ) -> Dict:
        """Record an assessment (baseline, midpoint, or final)"""
        timestamp = self.generate_timestamp()

        assessment = {
            "PK": f"SESSION#{session_id}",
            "SK": f"ASSESSMENT#{assessment_type}#{timestamp}",
            "entity_type": "assessment",
            "session_id": session_id,
            "student_id": student_id,
            "assessment_id": f"asmt_{assessment_type}_{self.generate_id()[:8]}",
            "assessment_metadata": {
                "type": assessment_type,
                "version": "v1.0",
                "timestamp": timestamp,
                "duration_seconds": duration_seconds,
                "content_topic": "tredegar-iron-works",
            },
            "questions": questions,
            "assessment_results": assessment_results,
            "scoring_breakdown": scoring_breakdown,
            "metadata": {
                "created_at": timestamp,
                "updated_at": timestamp,
                "grading_method": "automated_with_ai",
                "version": 1,
            },
        }

        if learning_gain:
            assessment["learning_gain"] = learning_gain

        # Convert and write
        assessment = self.convert_floats_to_decimal(assessment)
        self.table.put_item(Item=assessment)

        # Update session status
        status_key = (
            f"{assessment_type}_completed"
            if assessment_type != "midpoint"
            else "baseline_completed"
        )
        self.update_session_status(session_id, {status_key: True})

        return assessment

    # ========================================================================
    # Query Operations
    # ========================================================================

    def get_sessions_by_condition(
        self,
        location: LocationType,
        interval: Literal[2.5, 5.0, 10.0],
        intervention: InterventionType,
        limit: Optional[int] = None,
    ) -> List[Dict]:
        """Query all sessions for a specific experimental condition"""
        query_params = {
            "IndexName": "GSI1",
            "KeyConditionExpression": "GSI1PK = :condition",
            "ExpressionAttributeValues": {
                ":condition": f"CONDITION#{location}#{interval}#{intervention}"
            },
        }

        if limit:
            query_params["Limit"] = limit

        response = self.table.query(**query_params)
        return [
            self.convert_decimal_to_float(item) for item in response.get("Items", [])
        ]

    def get_sessions_by_student(self, student_id: str) -> List[Dict]:
        """Query all sessions for a specific student"""
        response = self.table.query(
            IndexName="GSI2",
            KeyConditionExpression="GSI2PK = :student",
            ExpressionAttributeValues={":student": f"STUDENT#{student_id}"},
        )

        return [
            self.convert_decimal_to_float(item) for item in response.get("Items", [])
        ]

    def get_sessions_by_location(self, location: LocationType) -> List[Dict]:
        """Query all sessions at a specific location"""
        response = self.table.query(
            IndexName="GSI3",
            KeyConditionExpression="GSI3PK = :location",
            ExpressionAttributeValues={":location": f"LOCATION#{location}"},
        )

        return [
            self.convert_decimal_to_float(item) for item in response.get("Items", [])
        ]

    def get_interventions_by_type(
        self, intervention_type: InterventionType
    ) -> List[Dict]:
        """Query all interventions of a specific type"""
        response = self.table.query(
            IndexName="GSI4",
            KeyConditionExpression="GSI4PK = :type",
            ExpressionAttributeValues={":type": f"INTERVENTION#{intervention_type}"},
        )

        return [
            self.convert_decimal_to_float(item) for item in response.get("Items", [])
        ]

    def get_sessions_by_date(self, date: str) -> List[Dict]:
        """Query all sessions on a specific date (YYYY-MM-DD)"""
        response = self.table.query(
            IndexName="GSI5",
            KeyConditionExpression="GSI5PK = :date",
            ExpressionAttributeValues={":date": f"DATE#{date}"},
        )

        return [
            self.convert_decimal_to_float(item) for item in response.get("Items", [])
        ]

    # ========================================================================
    # Analytics Operations
    # ========================================================================

    def calculate_learning_gains(
        self,
        location: LocationType,
        interval: Literal[2.5, 5.0, 10.0],
        intervention: InterventionType,
    ) -> Dict:
        """Calculate learning gains for a specific condition"""
        sessions = self.get_sessions_by_condition(location, interval, intervention)

        learning_gains = []

        for session_metadata in sessions:
            session_id = session_metadata["session_id"]
            session_data = self.get_session(session_id)

            if not session_data:
                continue

            assessments = session_data.get("assessments", {})
            baseline = assessments.get("baseline")
            final = assessments.get("final")

            if baseline and final:
                baseline_score = baseline["assessment_results"]["score_percentage"]
                final_score = final["assessment_results"]["score_percentage"]

                absolute_gain = final_score - baseline_score
                normalized_gain = (
                    absolute_gain / (100 - baseline_score)
                    if baseline_score < 100
                    else 0
                )

                learning_gains.append(
                    {
                        "session_id": session_id,
                        "student_id": session_metadata["student_id"],
                        "baseline": baseline_score,
                        "final": final_score,
                        "absolute_gain": absolute_gain,
                        "normalized_gain": normalized_gain,
                    }
                )

        if not learning_gains:
            return None

        # Calculate statistics
        n = len(learning_gains)
        avg_baseline = sum(g["baseline"] for g in learning_gains) / n
        avg_final = sum(g["final"] for g in learning_gains) / n
        avg_absolute_gain = sum(g["absolute_gain"] for g in learning_gains) / n
        avg_normalized_gain = sum(g["normalized_gain"] for g in learning_gains) / n

        return {
            "condition": {
                "location": location,
                "interval": interval,
                "intervention": intervention,
            },
            "n": n,
            "avg_baseline": avg_baseline,
            "avg_final": avg_final,
            "avg_absolute_gain": avg_absolute_gain,
            "avg_normalized_gain": avg_normalized_gain,
            "individual_gains": learning_gains,
        }


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    # Initialize database
    db = SocraticBenchmarksDB(table_name="SocraticBenchmarks")

    # Create a student
    student = db.create_student(
        age=16,
        grade_level=10,
        school="Richmond High School",
        richmond_resident=True,
        depth_preference="moderate",
        learning_style="visual-auditory",
        prior_knowledge_topics=["civil_war", "richmond_history"],
        parent_consent=True,
        student_assent=True,
    )
    print(f"Created student: {student['student_id']}")

    # Create a session
    session = db.create_session(
        student_id=student["student_id"],
        location="on-site",
        location_name="Tredegar Iron Works",
        interval_minutes=2.5,
        intervention_type="dynamic",
        student_age=16,
        student_grade=10,
        richmond_resident=True,
        prior_knowledge_score=2.5,
    )
    print(f"Created session: {session['session_id']}")

    # Record location verification
    db.record_location_verification(
        session_id=session["session_id"],
        student_id=student["student_id"],
        location_type="on-site",
        location_name="Tredegar Iron Works",
        address="500 Tredegar St, Richmond, VA 23219",
        verification_method="GPS",
        verified=True,
        confidence="high",
        gps_data={
            "latitude": 37.5316,
            "longitude": -77.4481,
            "accuracy_meters": 8.5,
            "geofence_validated": True,
            "distance_from_target_meters": 4.2,
        },
    )
    print("Recorded location verification")

    # Query sessions by condition
    condition_sessions = db.get_sessions_by_condition(
        location="on-site", interval=2.5, intervention="dynamic"
    )
    print(f"Found {len(condition_sessions)} sessions for this condition")
