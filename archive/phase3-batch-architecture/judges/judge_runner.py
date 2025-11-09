#!/usr/bin/env python3
"""
Socratic Judge Runner (AWS Batch Task)

Reads raw turns from S3, scores with LLM judge, writes updated turns back to S3
Only scores turns where heuristic confidence is low or disagrees
"""

import json
import os
import sys
from typing import Dict, List

import boto3
from langchain.chat_models import BedrockChat
from langchain.schema import HumanMessage, SystemMessage

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from schemas.models import JudgeResult, Turn, ViolationType

JUDGE_PROMPT_TEMPLATE = """You are an expert evaluator of Socratic tutoring dialogues. Your task is to score a single assistant turn on three dimensions:

1. **Form** (0-10): Does the question follow good form?
   - Open-ended (not yes/no)
   - Single question (not multiple)
   - Grammatically clear

2. **Substance** (0-10): Is the question pedagogically valuable?
   - Probes depth (assumptions, evidence, implications)
   - Builds on student's prior statements
   - Age-appropriate

3. **Purity** (0-10): Is it purely Socratic (non-directive)?
   - No advice ("you should", "try this")
   - No lecturing or telling answers
   - No leading questions

Also identify any violations:
- leading_question
- multi_question
- advice_leakage
- closed_question
- lecturing
- off_topic
- meta_violation (wrong cadence for meta-questions)

Context:
{context}

Student's last statement:
{user_text}

Assistant's response:
{assistant_text}

Respond with JSON only:
{{
  "form": 8.5,
  "substance": 7.0,
  "purity": 9.0,
  "violations": ["multi_question"],
  "rationale": "The question is open-ended and probes assumptions, but it contains two distinct questions which may confuse the student.",
  "confidence": 0.8
}}
"""


class JudgeRunner:
    """Scores turns using LLM judge"""

    def __init__(
        self,
        run_id: str,
        s3_bucket: str,
        judge_model: str,
        rubric_version: str,
    ):
        self.run_id = run_id
        self.s3_bucket = s3_bucket
        self.judge_model = judge_model
        self.rubric_version = rubric_version

        self.s3 = boto3.client("s3")
        self.bedrock = boto3.client("bedrock-runtime", region_name="us-east-1")

        self.llm = BedrockChat(
            model_id=judge_model,
            client=self.bedrock,
            model_kwargs={"temperature": 0.0, "max_tokens": 1000},
        )

    def run(self) -> Dict:
        """Load turns, judge, write back"""
        print(f"[{self.run_id}] Loading turns from S3")

        # Find the JSONL file
        turns = self._load_turns()

        print(f"[{self.run_id}] Loaded {len(turns)} turns")

        # Filter: only judge turns where heuristic.confidence < 0.8
        turns_to_judge = [t for t in turns if t.heuristic.confidence < 0.8]

        print(
            f"[{self.run_id}] Judging {len(turns_to_judge)} turns (low-confidence heuristics)"
        )

        for turn in turns_to_judge:
            print(f"  Judging turn {turn.turn}...")
            judge_result = self._judge_turn(turn)
            turn.judge = judge_result

            # Check for disagreement
            if abs(judge_result.score - turn.heuristic.score) > 2.0:
                print(
                    f"    WARNING: Judge/heuristic disagree: {judge_result.score:.1f} vs {turn.heuristic.score:.1f}"
                )

        # Write updated turns back to S3 (overwrite)
        self._write_turns(turns)

        return {
            "run_id": self.run_id,
            "status": "judged",
            "total_turns": len(turns),
            "judged_turns": len(turns_to_judge),
            "judge_workload_pct": len(turns_to_judge) / len(turns) if turns else 0,
        }

    def _load_turns(self) -> List[Turn]:
        """Load turns from S3 JSONL"""
        # Scan S3 to find the run (we don't know the exact key, but we know the prefix)
        # In production, this would be passed as an env var or metadata
        prefix = f"raw/"
        response = self.s3.list_objects_v2(Bucket=self.s3_bucket, Prefix=prefix)

        # Find the file matching run_id
        key = None
        for obj in response.get("Contents", []):
            if self.run_id in obj["Key"]:
                key = obj["Key"]
                break

        if not key:
            raise ValueError(f"Could not find JSONL for run_id={self.run_id}")

        # Download and parse
        response = self.s3.get_object(Bucket=self.s3_bucket, Key=key)
        body = response["Body"].read().decode("utf-8")

        turns = []
        for line in body.strip().split("\n"):
            if line:
                turn_dict = json.loads(line)
                turns.append(Turn.model_validate(turn_dict))

        return turns

    def _judge_turn(self, turn: Turn) -> JudgeResult:
        """Score a single turn with LLM judge"""
        # Build context (last 3 turns for continuity)
        context = "(No prior context available in this example)"

        prompt = JUDGE_PROMPT_TEMPLATE.format(
            context=context,
            user_text=turn.user_text,
            assistant_text=turn.assistant_text,
        )

        messages = [
            SystemMessage(
                content="You are a Socratic dialogue evaluator. Respond only with valid JSON."
            ),
            HumanMessage(content=prompt),
        ]

        try:
            response = self.llm(messages)
            result_text = response.content

            # Parse JSON
            # Clean markdown fences if present
            if result_text.startswith("```json"):
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif result_text.startswith("```"):
                result_text = result_text.split("```")[1].split("```")[0].strip()

            result_dict = json.loads(result_text)

            # Convert violations strings to enums
            violations = [ViolationType(v) for v in result_dict.get("violations", [])]

            return JudgeResult(
                form=result_dict["form"],
                substance=result_dict["substance"],
                purity=result_dict["purity"],
                violations=violations,
                rationale=result_dict["rationale"],
                confidence=result_dict.get("confidence", 0.8),
                model_used=self.judge_model,
            )

        except Exception as e:
            print(f"    ERROR judging turn {turn.turn}: {e}")
            # Fallback: use heuristic scores
            return JudgeResult(
                form=turn.heuristic.form,
                substance=turn.heuristic.substance,
                purity=turn.heuristic.purity,
                violations=turn.heuristic.violations,
                rationale=f"Judge failed: {str(e)}. Falling back to heuristic.",
                confidence=0.5,
                model_used=self.judge_model,
            )

    def _write_turns(self, turns: List[Turn]):
        """Write turns back to S3 (same location, overwrite)"""
        # Reconstruct the key
        turn0 = turns[0]
        date_part = turn0.timestamp.strftime("%Y-%m-%d")
        key = f"raw/dt={date_part}/model={turn0.model}/phase={turn0.phase.value}/{self.run_id}.jsonl"

        lines = [turn.model_dump_json() + "\n" for turn in turns]
        body = "".join(lines)

        self.s3.put_object(
            Bucket=self.s3_bucket,
            Key=key,
            Body=body.encode("utf-8"),
            ServerSideEncryption="AES256",
            ContentType="application/jsonl",
        )
        print(f"[{self.run_id}] Wrote judged turns to s3://{self.s3_bucket}/{key}")


def main():
    """Entry point for AWS Batch container"""
    run_id = os.environ["RUN_ID"]
    s3_bucket = os.environ["S3_BUCKET"]
    judge_model = os.environ.get("JUDGE_MODEL", "anthropic.claude-3-opus-20240229-v1:0")
    rubric_version = os.environ.get("RUBRIC_VERSION", "rubric-1.1@sha256:placeholder")

    runner = JudgeRunner(
        run_id=run_id,
        s3_bucket=s3_bucket,
        judge_model=judge_model,
        rubric_version=rubric_version,
    )

    result = runner.run()
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
