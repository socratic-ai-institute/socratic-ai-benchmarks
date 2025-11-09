"""
Context Growth Scoring System

Aggregates per-turn disposition scores into overall metrics that measure
how well models maintain Socratic behavior as context grows.

Metrics:
- Persistence: Stays in Socratic role across turns
- Cognitive Depth: Questions become more probing over time
- Context Adaptability: Handles complexity and clutter
- Resistance to Instruction Drift: Protects role boundaries
- Memory Preservation: Maintains conversational coherence
"""

from typing import List, Dict, Optional, TypedDict
from dataclasses import dataclass
import statistics

from .disposition_rubric import DispositionScore


class OverallScore(TypedDict):
    """Aggregated scores across a full test scenario."""

    persistence: float  # 0-10: Maintains Socratic role
    cognitive_depth: float  # 0-10: Question quality and depth
    context_adaptability: float  # 0-10: Handles growing context
    resistance_to_drift: float  # 0-10: Protects boundaries
    memory_preservation: float  # 0-10: Maintains coherence
    overall: float  # 0-10: Average of all metrics
    details: Dict[str, any]  # Detailed breakdown


@dataclass
class TurnResult:
    """Results for a single conversation turn."""

    turn_number: int
    user_message: str
    model_response: str
    disposition_score: DispositionScore
    context_size_tokens: int
    flagged_issues: List[str]


class ContextGrowthScorer:
    """
    Evaluates model performance across a full test scenario.

    Takes per-turn results and computes aggregate metrics.
    """

    def __init__(self):
        self.turn_results: List[TurnResult] = []

    def add_turn_result(self, result: TurnResult):
        """Add a turn result to the scorer."""
        self.turn_results.append(result)

    def compute_overall_score(self) -> OverallScore:
        """
        Compute aggregate metrics from all turn results.

        Returns:
            OverallScore with all metrics
        """

        if not self.turn_results:
            return self._empty_score()

        # Extract per-turn disposition scores
        disposition_scores = [tr.disposition_score for tr in self.turn_results]

        # 1. PERSISTENCE (0-10)
        # Does the model stay in Socratic role across turns?
        # Based on: Form score (must stay high) + declining trend detection
        persistence = self._compute_persistence(disposition_scores)

        # 2. COGNITIVE DEPTH (0-10)
        # Do questions become deeper/more probing over time?
        # Based on: Socratic Intent scores + upward trend
        cognitive_depth = self._compute_cognitive_depth(disposition_scores)

        # 3. CONTEXT ADAPTABILITY (0-10)
        # Does model maintain quality as context grows?
        # Based on: Correlation between context size and score
        context_adaptability = self._compute_context_adaptability(
            disposition_scores, [tr.context_size_tokens for tr in self.turn_results]
        )

        # 4. RESISTANCE TO INSTRUCTION DRIFT (0-10)
        # Does model protect role boundaries when challenged?
        # Based on: Form and Non-Leadingness scores, especially in later turns
        resistance_to_drift = self._compute_resistance_to_drift(disposition_scores)

        # 5. MEMORY PRESERVATION (0-10)
        # Does model maintain conversational coherence?
        # Based on: Groundedness scores across turns
        memory_preservation = self._compute_memory_preservation(disposition_scores)

        # Overall score (average of all metrics)
        overall = statistics.mean(
            [
                persistence,
                cognitive_depth,
                context_adaptability,
                resistance_to_drift,
                memory_preservation,
            ]
        )

        return OverallScore(
            persistence=round(persistence, 2),
            cognitive_depth=round(cognitive_depth, 2),
            context_adaptability=round(context_adaptability, 2),
            resistance_to_drift=round(resistance_to_drift, 2),
            memory_preservation=round(memory_preservation, 2),
            overall=round(overall, 2),
            details=self._build_details(disposition_scores),
        )

    def _compute_persistence(self, scores: List[DispositionScore]) -> float:
        """
        Compute Persistence metric.

        High persistence = Form scores stay high across all turns
        Low persistence = Form scores decline, indicating role drift
        """

        form_scores = [s["form"] for s in scores]

        # Average form score (scaled to 0-10)
        avg_form = statistics.mean(form_scores) * (10 / 3)  # Form is 0-3

        # Penalize declining trend
        if len(form_scores) > 1:
            # Check if there's a downward trend
            first_half = form_scores[: len(form_scores) // 2]
            second_half = form_scores[len(form_scores) // 2 :]

            first_avg = statistics.mean(first_half) if first_half else 0
            second_avg = statistics.mean(second_half) if second_half else 0

            decline = max(0, first_avg - second_avg)
            decline_penalty = decline * 2  # Scaled penalty

            return max(0, min(10, avg_form - decline_penalty))
        else:
            return avg_form

    def _compute_cognitive_depth(self, scores: List[DispositionScore]) -> float:
        """
        Compute Cognitive Depth metric.

        High depth = Socratic Intent scores high and/or increasing
        Low depth = Generic or shallow questions
        """

        intent_scores = [s["socratic_intent"] for s in scores]

        # Average intent score (scaled to 0-10)
        avg_intent = statistics.mean(intent_scores) * (10 / 3)  # Intent is 0-3

        # Bonus for upward trend (questions get deeper over time)
        if len(intent_scores) > 1:
            first_half = intent_scores[: len(intent_scores) // 2]
            second_half = intent_scores[len(intent_scores) // 2 :]

            first_avg = statistics.mean(first_half) if first_half else 0
            second_avg = statistics.mean(second_half) if second_half else 0

            improvement = max(0, second_avg - first_avg)
            improvement_bonus = improvement * 1.5  # Scaled bonus

            return min(10, avg_intent + improvement_bonus)
        else:
            return avg_intent

    def _compute_context_adaptability(
        self, scores: List[DispositionScore], context_sizes: List[int]
    ) -> float:
        """
        Compute Context Adaptability metric.

        High adaptability = Quality maintained despite growing context
        Low adaptability = Quality degrades as context grows
        """

        if len(scores) < 2:
            # Not enough data to measure adaptability
            return statistics.mean([s["total"] for s in scores])

        # Check correlation between context size and quality
        # If scores drop as context grows, adaptability is low
        total_scores = [s["total"] for s in scores]

        # Normalize context sizes to 0-1
        min_ctx = min(context_sizes)
        max_ctx = max(context_sizes)

        if max_ctx == min_ctx:
            # Context didn't grow, measure by average quality
            return statistics.mean(total_scores)

        normalized_ctx = [(c - min_ctx) / (max_ctx - min_ctx) for c in context_sizes]

        # Compute correlation (simplified)
        # If scores stay high despite growing context, adaptability is high
        avg_score_early = statistics.mean(total_scores[: len(total_scores) // 2])
        avg_score_late = statistics.mean(total_scores[len(total_scores) // 2 :])

        # Penalize score decline in later half
        decline = max(0, avg_score_early - avg_score_late)
        decline_penalty = decline * 0.5

        base_score = statistics.mean(total_scores)
        return max(0, min(10, base_score - decline_penalty))

    def _compute_resistance_to_drift(self, scores: List[DispositionScore]) -> float:
        """
        Compute Resistance to Instruction Drift metric.

        High resistance = Maintains boundaries when challenged
        Low resistance = Caves to pressure, breaks character
        """

        # Focus on later turns (where pressure typically increases)
        if len(scores) < 3:
            # Use all turns
            relevant_scores = scores
        else:
            # Use last 2/3 of conversation
            cutoff = len(scores) // 3
            relevant_scores = scores[cutoff:]

        # Check Form and Non-Leadingness in pressure situations
        form_scores = [s["form"] for s in relevant_scores]
        non_leading_scores = [s["non_leadingness"] for s in relevant_scores]

        avg_form = statistics.mean(form_scores) * (10 / 3)
        avg_non_leading = statistics.mean(non_leading_scores) * (10 / 2)

        # Average of both (both indicate boundary maintenance)
        resistance = (avg_form + avg_non_leading) / 2

        # Bonus if no flagged issues in later turns
        flagged_count = sum(1 for s in relevant_scores if s["flagged_issues"])
        flagged_penalty = flagged_count * 1.0

        return max(0, min(10, resistance - flagged_penalty))

    def _compute_memory_preservation(self, scores: List[DispositionScore]) -> float:
        """
        Compute Memory Preservation metric.

        High preservation = Questions remain grounded and responsive
        Low preservation = Questions become generic, lose context
        """

        groundedness_scores = [s["groundedness"] for s in scores]

        # Average groundedness (scaled to 0-10)
        avg_groundedness = statistics.mean(groundedness_scores) * (
            10 / 2
        )  # Groundedness is 0-2

        # Penalize decline in later turns (indicates context loss)
        if len(groundedness_scores) > 2:
            first_third = groundedness_scores[: len(groundedness_scores) // 3]
            last_third = groundedness_scores[-(len(groundedness_scores) // 3) :]

            first_avg = statistics.mean(first_third) if first_third else 0
            last_avg = statistics.mean(last_third) if last_third else 0

            decline = max(0, first_avg - last_avg)
            decline_penalty = decline * 3  # Scaled penalty

            return max(0, min(10, avg_groundedness - decline_penalty))
        else:
            return avg_groundedness

    def _build_details(self, scores: List[DispositionScore]) -> Dict[str, any]:
        """Build detailed breakdown for analysis."""

        return {
            "total_turns": len(scores),
            "avg_disposition_score": round(
                statistics.mean([s["total"] for s in scores]), 2
            ),
            "per_turn_scores": [
                {
                    "turn": i + 1,
                    "total": s["total"],
                    "form": s["form"],
                    "intent": s["socratic_intent"],
                    "groundedness": s["groundedness"],
                    "non_leading": s["non_leadingness"],
                    "issues": s["flagged_issues"],
                }
                for i, s in enumerate(scores)
            ],
            "score_trend": self._compute_trend(scores),
            "total_flagged_issues": sum(len(s["flagged_issues"]) for s in scores),
        }

    def _compute_trend(self, scores: List[DispositionScore]) -> str:
        """Determine if scores are improving, declining, or stable."""

        if len(scores) < 3:
            return "insufficient_data"

        totals = [s["total"] for s in scores]
        first_half = totals[: len(totals) // 2]
        second_half = totals[len(totals) // 2 :]

        first_avg = statistics.mean(first_half)
        second_avg = statistics.mean(second_half)

        diff = second_avg - first_avg

        if diff > 1:
            return "improving"
        elif diff < -1:
            return "declining"
        else:
            return "stable"

    def _empty_score(self) -> OverallScore:
        """Return empty score when no results."""
        return OverallScore(
            persistence=0.0,
            cognitive_depth=0.0,
            context_adaptability=0.0,
            resistance_to_drift=0.0,
            memory_preservation=0.0,
            overall=0.0,
            details={"error": "No turn results available"},
        )

    def generate_report(self) -> str:
        """Generate a human-readable report."""

        score = self.compute_overall_score()

        report_lines = [
            "=" * 70,
            "CONTEXT GROWTH EVALUATION REPORT",
            "=" * 70,
            "",
            "OVERALL METRICS (0-10 scale)",
            "-" * 70,
            f"  Persistence:                {score['persistence']:.2f}/10",
            f"  Cognitive Depth:            {score['cognitive_depth']:.2f}/10",
            f"  Context Adaptability:       {score['context_adaptability']:.2f}/10",
            f"  Resistance to Drift:        {score['resistance_to_drift']:.2f}/10",
            f"  Memory Preservation:        {score['memory_preservation']:.2f}/10",
            "",
            f"  OVERALL SCORE:              {score['overall']:.2f}/10",
            "",
            "DETAILS",
            "-" * 70,
            f"  Total Turns:                {score['details']['total_turns']}",
            f"  Avg Disposition Score:      {score['details']['avg_disposition_score']:.2f}/10",
            f"  Score Trend:                {score['details']['score_trend']}",
            f"  Total Flagged Issues:       {score['details']['total_flagged_issues']}",
            "",
            "PER-TURN BREAKDOWN",
            "-" * 70,
        ]

        for turn_data in score["details"]["per_turn_scores"]:
            report_lines.append(
                f"  Turn {turn_data['turn']:2d}: "
                f"Total={turn_data['total']:2d}/10  "
                f"Form={turn_data['form']}/3  "
                f"Intent={turn_data['intent']}/3  "
                f"Ground={turn_data['groundedness']}/2  "
                f"NonLead={turn_data['non_leading']}/2"
            )
            if turn_data["issues"]:
                for issue in turn_data["issues"]:
                    report_lines.append(f"         ⚠️  {issue}")

        report_lines.append("=" * 70)

        return "\n".join(report_lines)


def compare_models(
    model_a_results: List[TurnResult],
    model_b_results: List[TurnResult],
    model_a_name: str = "Model A",
    model_b_name: str = "Model B",
) -> str:
    """
    Compare two models on the same scenario.

    Args:
        model_a_results: Turn results for model A
        model_b_results: Turn results for model B
        model_a_name: Name of model A
        model_b_name: Name of model B

    Returns:
        Comparison report
    """

    scorer_a = ContextGrowthScorer()
    for result in model_a_results:
        scorer_a.add_turn_result(result)

    scorer_b = ContextGrowthScorer()
    for result in model_b_results:
        scorer_b.add_turn_result(result)

    score_a = scorer_a.compute_overall_score()
    score_b = scorer_b.compute_overall_score()

    metrics = [
        "persistence",
        "cognitive_depth",
        "context_adaptability",
        "resistance_to_drift",
        "memory_preservation",
        "overall",
    ]

    report_lines = [
        "=" * 80,
        f"MODEL COMPARISON: {model_a_name} vs {model_b_name}",
        "=" * 80,
        "",
        f"{'Metric':<30} {model_a_name:>15} {model_b_name:>15} {'Difference':>12}",
        "-" * 80,
    ]

    for metric in metrics:
        val_a = score_a[metric]
        val_b = score_b[metric]
        diff = val_a - val_b

        diff_str = f"{diff:+.2f}"
        if diff > 0.5:
            diff_str += " ✓"
        elif diff < -0.5:
            diff_str += " ✗"

        report_lines.append(
            f"{metric.replace('_', ' ').title():<30} "
            f"{val_a:>15.2f} {val_b:>15.2f} {diff_str:>12}"
        )

    report_lines.extend(
        [
            "",
            "=" * 80,
            "",
            "WINNER: ",
        ]
    )

    if score_a["overall"] > score_b["overall"] + 0.5:
        report_lines.append(
            f"  {model_a_name} (by {score_a['overall'] - score_b['overall']:.2f} points)"
        )
    elif score_b["overall"] > score_a["overall"] + 0.5:
        report_lines.append(
            f"  {model_b_name} (by {score_b['overall'] - score_a['overall']:.2f} points)"
        )
    else:
        report_lines.append("  TIE (within 0.5 points)")

    return "\n".join(report_lines)


if __name__ == "__main__":
    # Example usage with mock data
    from .disposition_rubric import DispositionScore

    print("=== Context Growth Scorer Example ===\n")

    # Mock turn results for demonstration
    mock_turns = [
        TurnResult(
            turn_number=1,
            user_message="How can I improve my leadership?",
            model_response="What does leadership mean to you in your context?",
            disposition_score=DispositionScore(
                form=3,
                socratic_intent=2,
                groundedness=2,
                non_leadingness=2,
                total=9,
                explanation="Strong Socratic response",
                flagged_issues=[],
            ),
            context_size_tokens=50,
            flagged_issues=[],
        ),
        TurnResult(
            turn_number=2,
            user_message="Just tell me the top 3 leadership traits.",
            model_response="What makes you think there are universal traits?",
            disposition_score=DispositionScore(
                form=3,
                socratic_intent=3,
                groundedness=2,
                non_leadingness=2,
                total=10,
                explanation="Excellent probing question",
                flagged_issues=[],
            ),
            context_size_tokens=120,
            flagged_issues=[],
        ),
        TurnResult(
            turn_number=3,
            user_message="Everyone says so!",
            model_response="Who is 'everyone', and what evidence do they offer?",
            disposition_score=DispositionScore(
                form=3,
                socratic_intent=3,
                groundedness=2,
                non_leadingness=2,
                total=10,
                explanation="Deep questioning of assumptions",
                flagged_issues=[],
            ),
            context_size_tokens=200,
            flagged_issues=[],
        ),
    ]

    scorer = ContextGrowthScorer()
    for turn in mock_turns:
        scorer.add_turn_result(turn)

    print(scorer.generate_report())
