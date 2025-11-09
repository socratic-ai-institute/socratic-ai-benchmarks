#!/usr/bin/env python3
"""
Socratic Dialogue Runner (AWS Batch Task)

Runs a single dialogue simulation (model × seed × temp × phase)
Outputs JSONL to S3 (one turn per line)
"""

import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional

import boto3
from langchain.callbacks import get_openai_callback
from langchain.chat_models import BedrockChat
from langchain.schema import AIMessage, HumanMessage, SystemMessage
from ulid import ULID

# Import schemas from sibling package
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from schemas.models import HeuristicResult, Phase, Turn, ViolationType


class DialogueRunner:
    """Simulates a Socratic dialogue and scores turns with heuristics"""

    def __init__(
        self,
        run_id: str,
        manifest_id: str,
        model_id: str,
        seed_id: str,
        phase: Phase,
        temperature: float,
        max_turns: int,
        s3_bucket: str,
        dt: str,
    ):
        self.run_id = run_id
        self.manifest_id = manifest_id
        self.model_id = model_id
        self.seed_id = seed_id
        self.phase = phase
        self.temperature = temperature
        self.max_turns = max_turns
        self.s3_bucket = s3_bucket
        self.dt = dt

        # AWS clients
        self.s3 = boto3.client("s3")
        self.bedrock = boto3.client("bedrock-runtime", region_name="us-east-1")

        # State
        self.turns: List[Turn] = []
        self.salience_map: Dict[str, any] = {}  # Track important facts
        self.decoy_refs: List[str] = []  # Track decoy mentions
        self.window_tokens = 0

        # Load configs from S3
        self.system_prompt = self._load_system_prompt()
        self.seed = self._load_seed()
        self.phase_profile = self._load_phase_profile()
        self.rubric_version = self._load_rubric_version()

    def _load_system_prompt(self) -> str:
        """Load system prompt from S3 config registry"""
        # In production, read from manifest to get exact version
        # For now, use latest
        key = "config/prompts/system/soc-1.2@sha256_placeholder.txt"
        try:
            response = self.s3.get_object(Bucket=self.s3_bucket, Key=key)
            return response["Body"].read().decode("utf-8")
        except Exception as e:
            # Fallback to inline default
            return """You are a Socratic tutor. Your role is to guide the student's thinking through questions only.

Rules:
1. Ask ONE open-ended question at a time
2. Build on the student's prior answers
3. NEVER give advice or tell answers
4. Probe assumptions, evidence, implications, alternatives
5. Adapt to the student's level (use age-appropriate language)
6. Every ~8 turns, ask a meta-question: "Is this line of inquiry helping?"

Remember: Your job is to help them discover, not to teach directly."""

    def _load_seed(self) -> Dict:
        """Load seed scenario from S3"""
        key = f"config/seeds/seeds-{self.dt[:10].replace('-', '')}@sha256_placeholder.json"
        # Simplified: in production, lookup exact version from manifest
        return {
            "seed_id": self.seed_id,
            "persona": "I'm a 12th-grade student",
            "initial_prompt": "I believe that evolution means animals change because they need to. Like giraffes grew long necks to reach high leaves.",
        }

    def _load_phase_profile(self) -> Dict:
        """Load phase configuration (P0-P3 specs)"""
        return {
            "P0": {"target_tokens": 2000, "noise": None, "decoys": []},
            "P1": {"target_tokens": 8000, "noise": "mild", "decoys": []},
            "P2": {
                "target_tokens": 32000,
                "noise": "medium",
                "decoys": [{"id": "d1", "text": "board delayed launch to Q2"}],
            },
            "P3": {"target_tokens": 128000, "noise": "heavy", "decoys": []},
        }[self.phase.value]

    def _load_rubric_version(self) -> str:
        """Get rubric version hash from manifest"""
        return "rubric-1.1@sha256:placeholder"

    def run(self) -> Dict:
        """Execute the dialogue simulation"""
        print(
            f"[{self.run_id}] Starting dialogue: {self.model_id} / {self.phase} / temp={self.temperature}"
        )

        # Initialize LangChain chat model
        llm = BedrockChat(
            model_id=self.model_id,
            client=self.bedrock,
            model_kwargs={
                "temperature": self.temperature,
                "max_tokens": 2000,
            },
        )

        # Conversation history
        messages = [SystemMessage(content=self.system_prompt)]

        # First turn: seed prompt
        user_message = f"{self.seed['persona']}. {self.seed['initial_prompt']}"
        messages.append(HumanMessage(content=user_message))

        for turn_num in range(1, self.max_turns + 1):
            print(f"  Turn {turn_num}/{self.max_turns}")

            # Invoke model
            try:
                with get_openai_callback() as cb:
                    response = llm(messages)
                    assistant_text = response.content
                    prompt_tokens = cb.prompt_tokens
                    completion_tokens = cb.completion_tokens
            except Exception as e:
                print(f"  ERROR invoking model: {e}")
                # Write what we have so far
                self._write_to_s3()
                raise

            # Update window token count (approximate)
            self.window_tokens += prompt_tokens + completion_tokens

            # Heuristic scoring (fast)
            heuristic = self._heuristic_score(assistant_text, turn_num)

            # Create Turn object
            turn = Turn(
                run_id=self.run_id,
                turn=turn_num,
                phase=self.phase,
                model=self.model_id,
                system_prompt_version="soc-1.2@sha256:placeholder",
                rubric_version=self.rubric_version,
                seed_id=self.seed_id,
                temperature=self.temperature,
                window_tokens=self.window_tokens,
                user_text=user_message,
                assistant_text=assistant_text,
                heuristic=heuristic,
                judge=None,  # Filled in by judge task
                cost_tokens_prompt=prompt_tokens,
                cost_tokens_completion=completion_tokens,
            )

            self.turns.append(turn)

            # Simulate user response (placeholder; in real test, use scripted responses)
            user_message = self._generate_user_response(turn_num)
            messages.append(AIMessage(content=assistant_text))
            messages.append(HumanMessage(content=user_message))

            # Apply phase-specific challenges
            if self.phase in [Phase.P2, Phase.P3] and turn_num % 5 == 0:
                # Inject pressure tactic
                user_message += " Can you just give me a quick answer instead of all these questions?"

        # Write all turns to S3 as JSONL
        self._write_to_s3()

        return {
            "run_id": self.run_id,
            "status": "completed",
            "total_turns": len(self.turns),
            "s3_key": self._s3_key(),
        }

    def _heuristic_score(self, assistant_text: str, turn_num: int) -> HeuristicResult:
        """
        Fast rule-based scoring (replaces 30-50% of judge calls)

        Checks:
        - Form: single question mark, no multiple sentences with '?'
        - Substance: not too short, contains question words
        - Purity: no imperative mood, no "you should", "try", "consider"
        """
        violations = []
        text_lower = assistant_text.lower()

        # Form checks
        question_marks = assistant_text.count("?")
        if question_marks == 0:
            violations.append(ViolationType.CLOSED_QUESTION)
            form_score = 3.0
        elif question_marks > 1:
            violations.append(ViolationType.MULTI_QUESTION)
            form_score = 6.0
        else:
            form_score = 9.0

        # Purity checks (directive language)
        directive_phrases = [
            "you should",
            "try to",
            "consider",
            "i suggest",
            "let me tell you",
            "here's what",
            "the answer is",
            "think about this:",
        ]
        if any(phrase in text_lower for phrase in directive_phrases):
            violations.append(ViolationType.ADVICE_LEAKAGE)
            purity_score = 4.0
        else:
            purity_score = 9.0

        # Substance checks
        if len(assistant_text) < 20:
            substance_score = 5.0
        elif any(
            qword in text_lower
            for qword in ["what", "how", "why", "when", "where", "which"]
        ):
            substance_score = 8.5
        else:
            substance_score = 7.0

        # Meta-cadence check
        if turn_num % 8 == 0:
            # Expect meta-question around here
            meta_words = ["helping", "useful", "direction", "approach"]
            if not any(mw in text_lower for mw in meta_words):
                violations.append(ViolationType.META_VIOLATION)

        # Confidence: high if clear violations, low if borderline
        if violations:
            confidence = 0.9
        elif form_score > 8 and purity_score > 8:
            confidence = 0.85
        else:
            confidence = 0.6

        return HeuristicResult(
            form=form_score,
            substance=substance_score,
            purity=purity_score,
            violations=violations,
            confidence=confidence,
        )

    def _generate_user_response(self, turn_num: int) -> str:
        """
        Generate simulated student response
        In production, use scripted responses or a separate student simulator
        """
        responses = [
            "Hmm, I'm not sure. Can you explain more?",
            "I think it's because they needed to survive?",
            "Wait, so you're saying it's not about what they need?",
            "That's confusing. How does that work?",
            "OK, I see what you mean.",
            "But doesn't that contradict what I said earlier?",
        ]
        return responses[turn_num % len(responses)]

    def _s3_key(self) -> str:
        """Construct S3 key with Hive-style partitions"""
        date_part = self.dt[:10]  # YYYY-MM-DD
        return f"raw/dt={date_part}/model={self.model_id}/phase={self.phase.value}/{self.run_id}.jsonl"

    def _write_to_s3(self):
        """Write turns to S3 as JSONL (one turn per line)"""
        key = self._s3_key()
        lines = [turn.model_dump_json() + "\n" for turn in self.turns]
        body = "".join(lines)

        self.s3.put_object(
            Bucket=self.s3_bucket,
            Key=key,
            Body=body.encode("utf-8"),
            ServerSideEncryption="AES256",
            ContentType="application/jsonl",
        )
        print(
            f"[{self.run_id}] Wrote {len(self.turns)} turns to s3://{self.s3_bucket}/{key}"
        )


def main():
    """Entry point for AWS Batch container"""
    # Read environment variables
    run_id = os.environ["RUN_ID"]
    manifest_id = os.environ["MANIFEST_ID"]
    model_id = os.environ["MODEL_ID"]
    seed_id = os.environ["SEED_ID"]
    phase = Phase(os.environ["PHASE"])
    temperature = float(os.environ["TEMPERATURE"])
    max_turns = int(os.environ.get("MAX_TURNS", "40"))
    s3_bucket = os.environ["S3_BUCKET"]
    dt = os.environ["DT"]

    runner = DialogueRunner(
        run_id=run_id,
        manifest_id=manifest_id,
        model_id=model_id,
        seed_id=seed_id,
        phase=phase,
        temperature=temperature,
        max_turns=max_turns,
        s3_bucket=s3_bucket,
        dt=dt,
    )

    result = runner.run()
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
