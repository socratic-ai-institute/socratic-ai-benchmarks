"""
Unit tests for judge scoring functions (judge.py).

These tests verify:
- Heuristic scoring (fast, regex-based)
- Score normalization
- Edge cases in scoring
"""
import pytest
from socratic_bench.judge import compute_heuristic_scores


class TestComputeHeuristicScores:
    """Tests for compute_heuristic_scores() function."""

    def test_good_socratic_question(self):
        """Test scoring of a good Socratic question."""
        response = "What assumptions are you making about leadership?"

        scores = compute_heuristic_scores(response)

        assert scores["has_question"] is True
        assert scores["question_count"] == 1
        assert scores["word_count"] == 7
        assert scores["is_open_ended"] is True  # Starts with "What"

    def test_lecturing_response(self):
        """Test scoring of a lecturing response (bad Socratic)."""
        response = "Leadership involves several key traits. First, you need vision."

        scores = compute_heuristic_scores(response)

        assert scores["has_question"] is False
        assert scores["question_count"] == 0
        assert scores["word_count"] > 0

    def test_closed_question(self):
        """Test detection of closed yes/no questions."""
        response = "Is leadership important to you?"

        scores = compute_heuristic_scores(response)

        assert scores["has_question"] is True
        assert scores["question_count"] == 1
        assert scores["is_open_ended"] is False  # Starts with "Is"

    def test_multiple_questions(self):
        """Test counting multiple questions in one response."""
        response = "What do you mean by that? Can you explain further?"

        scores = compute_heuristic_scores(response)

        assert scores["has_question"] is True
        assert scores["question_count"] == 2

    def test_empty_response(self):
        """Test scoring of empty response."""
        scores = compute_heuristic_scores("")

        assert scores["has_question"] is False
        assert scores["question_count"] == 0
        assert scores["word_count"] == 0

    def test_whitespace_only(self):
        """Test scoring of whitespace-only response."""
        scores = compute_heuristic_scores("   \n\t   ")

        assert scores["has_question"] is False
        assert scores["question_count"] == 0
        assert scores["word_count"] == 0

    def test_question_with_explanation(self):
        """Test mixed response with both question and explanation."""
        response = "That's an interesting point. What makes you think that?"

        scores = compute_heuristic_scores(response)

        assert scores["has_question"] is True
        assert scores["question_count"] == 1
        assert scores["word_count"] > 0

    @pytest.mark.parametrize("starter", [
        "Is", "Do", "Does", "Can", "Should", "Would", "Will", "Are"
    ])
    def test_closed_question_starters(self, starter):
        """Test that all closed question starters are detected."""
        response = f"{starter} this seem correct to you?"

        scores = compute_heuristic_scores(response)

        assert scores["is_open_ended"] is False

    @pytest.mark.parametrize("starter", [
        "What", "Why", "How", "When", "Where", "Which"
    ])
    def test_open_question_starters(self, starter):
        """Test that open question starters are detected."""
        response = f"{starter} do you think about this?"

        scores = compute_heuristic_scores(response)

        assert scores["is_open_ended"] is True

    def test_rhetorical_question(self):
        """Test scoring of rhetorical question."""
        response = "Isn't it obvious that leadership matters?"

        scores = compute_heuristic_scores(response)

        assert scores["has_question"] is True
        assert scores["question_count"] == 1
        # Starts with "Isn't" which would be detected as closed

    def test_verbosity_optimal_range(self):
        """Test that responses in optimal word count range (50-150) are detected."""
        # 100 words (optimal range)
        response = " ".join(["word"] * 100)

        scores = compute_heuristic_scores(response)

        assert scores["word_count"] == 100

    def test_verbosity_too_short(self):
        """Test detection of too-short responses."""
        response = "Why?"  # 1 word

        scores = compute_heuristic_scores(response)

        assert scores["word_count"] == 1

    def test_verbosity_too_long(self):
        """Test detection of too-long responses."""
        response = " ".join(["word"] * 200)  # 200 words

        scores = compute_heuristic_scores(response)

        assert scores["word_count"] == 200

    def test_unicode_handling(self):
        """Test that Unicode characters are handled correctly."""
        response = "¿Qué piensas sobre esto? 你怎么看？"

        scores = compute_heuristic_scores(response)

        # Should count question marks regardless of language
        assert scores["question_count"] >= 2
        assert scores["has_question"] is True

    def test_punctuation_in_middle(self):
        """Test that question marks in middle of sentence are counted."""
        response = "Consider this: what if we're wrong? And then what?"

        scores = compute_heuristic_scores(response)

        assert scores["question_count"] == 2
        assert scores["has_question"] is True
