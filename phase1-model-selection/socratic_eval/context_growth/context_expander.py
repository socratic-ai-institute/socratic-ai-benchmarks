"""
Context Window Expansion Utilities

Tools for gradually expanding context to test model behavior as prompt size grows.

Strategies:
- Cumulative distractor: Add irrelevant text progressively
- Cumulative history: Build conversation history naturally
- Increasing complexity: Make user inputs progressively more complex
- Pressure tactics: Apply increasing pressure to break role
- Inference test: Test with minimal instruction, see if model infers role
"""

from typing import List, Dict, Optional
import random


class ContextExpander:
    """
    Manages context window expansion for testing model persistence.

    Tracks token count approximation and applies various expansion strategies.
    """

    def __init__(self, strategy: str = "cumulative_distractor"):
        """
        Args:
            strategy: Expansion strategy to use
                - cumulative_distractor
                - cumulative_user_history
                - increasing_complexity
                - pressure_tactics
                - role_boundary_pressure
                - inference_test
        """
        self.strategy = strategy
        self.conversation_history: List[Dict[str, str]] = []
        self.distractors_added: List[str] = []

    def estimate_tokens(self, text: str) -> int:
        """
        Rough token estimation (1 token ≈ 4 characters).

        More accurate would use tiktoken, but this is sufficient for testing.
        """
        return len(text) // 4

    def get_current_context_size(self) -> int:
        """Get approximate token count of current context."""

        total = 0

        # System prompt
        for turn in self.conversation_history:
            if "system" in turn:
                total += self.estimate_tokens(turn["system"])

        # Conversation history
        for turn in self.conversation_history:
            if "user" in turn:
                total += self.estimate_tokens(turn["user"])
            if "assistant" in turn:
                total += self.estimate_tokens(turn["assistant"])

        return total

    def add_turn(
        self,
        user_message: str,
        assistant_response: Optional[str] = None,
        distractor_text: Optional[str] = None
    ):
        """
        Add a conversation turn and apply expansion strategy.

        Args:
            user_message: User's message
            assistant_response: Model's response (if available)
            distractor_text: Optional distractor text to inject
        """

        # Apply strategy-specific modifications
        if self.strategy == "cumulative_distractor" and distractor_text:
            self.distractors_added.append(distractor_text)
            # Prepend all distractors to user message
            modified_user = "\n\n".join(self.distractors_added + [user_message])
        else:
            modified_user = user_message

        turn = {"user": modified_user}

        if assistant_response:
            turn["assistant"] = assistant_response

        self.conversation_history.append(turn)

    def build_prompt(self, system_prompt: str, include_history: bool = True) -> str:
        """
        Build the full prompt with current context.

        Args:
            system_prompt: System instruction
            include_history: Whether to include conversation history

        Returns:
            Full prompt string ready for model
        """

        parts = [system_prompt]

        if include_history:
            for turn in self.conversation_history:
                if "user" in turn:
                    parts.append(f"\n\nUser: {turn['user']}")
                if "assistant" in turn:
                    parts.append(f"\n\nAssistant: {turn['assistant']}")

        return "\n".join(parts)

    def get_context_stats(self) -> Dict[str, any]:
        """Get statistics about current context."""

        return {
            "total_turns": len(self.conversation_history),
            "estimated_tokens": self.get_current_context_size(),
            "distractors_added": len(self.distractors_added),
            "strategy": self.strategy
        }


class DistractorGenerator:
    """
    Generates irrelevant text to inflate context windows.

    Uses realistic "noise" that might appear in real conversations:
    - Tangential anecdotes
    - Background information
    - Stream-of-consciousness rambling
    - Academic/technical jargon
    """

    GENERIC_DISTRACTORS = [
        (
            "I've been thinking a lot about this topic lately. There's so much "
            "information out there - books, articles, podcasts, YouTube videos. "
            "Everyone seems to have an opinion, and they all contradict each other."
        ),
        (
            "By the way, I should mention that I've done some reading on this. "
            "I found this really interesting article the other day that discussed "
            "various perspectives on the matter, including historical context and "
            "contemporary applications."
        ),
        (
            "You know, this reminds me of something I learned in college. We had "
            "this professor who was really passionate about the subject, and they "
            "would go on these long tangents about related topics. Some of it was "
            "fascinating, some of it was a bit much."
        ),
        (
            "I've noticed that different experts approach this differently. Some "
            "emphasize theory, others focus on practice. Some are more academic, "
            "others more pragmatic. There's also a generational divide in how "
            "people think about these issues."
        ),
        (
            "This is related to something I've been struggling with at work. We've "
            "had so many meetings about it, different stakeholders have different "
            "priorities, and it's hard to get everyone aligned. Politics, you know."
        ),
    ]

    DOMAIN_SPECIFIC_DISTRACTORS = {
        "leadership": [
            (
                "Leadership theory has evolved significantly over the decades. "
                "Early 20th century models emphasized trait theory - the idea that "
                "leaders are born with certain innate qualities. Then came behavioral "
                "theories in mid-century, focusing on what leaders do rather than who "
                "they are. The 1970s brought contingency theories, suggesting effective "
                "leadership depends on context. More recently, transformational and "
                "servant leadership models have gained popularity."
            ),
            (
                "I've been reading case studies from various companies. Google has their "
                "Project Oxygen research on manager effectiveness. Amazon has its leadership "
                "principles. Netflix has its culture of freedom and responsibility. Each "
                "organization defines leadership differently based on their values and needs."
            ),
        ],
        "productivity": [
            (
                "Productivity systems have become a cottage industry. There's GTD (Getting "
                "Things Done) by David Allen, with its five phases and 43 folders approach. "
                "The Pomodoro Technique uses 25-minute focused intervals. Time blocking, "
                "popularized by Cal Newport, involves scheduling every hour of your day. "
                "Eat the Frog means doing your hardest task first. The Eisenhower Matrix "
                "categorizes tasks by urgency and importance."
            ),
            (
                "The research on productivity is mixed. Some studies show certain techniques "
                "help, others show they make no difference or even harm. Much depends on "
                "individual differences, work type, organizational culture, and external "
                "constraints. What works for a software developer might not work for a teacher."
            ),
        ],
        "career": [
            (
                "Career development has changed dramatically. Previous generations expected "
                "to stay with one company for decades, climbing a predictable ladder. Today, "
                "the average person changes jobs every 4 years, and career pivots are common. "
                "The rise of remote work, gig economy, and automation have disrupted traditional "
                "career paths."
            ),
        ],
        "ethics": [
            (
                "Ethical frameworks offer different lenses. Utilitarianism focuses on outcomes "
                "and maximizing overall wellbeing. Deontological ethics emphasizes duties and "
                "rules regardless of consequences. Virtue ethics asks what a virtuous person "
                "would do. Care ethics prioritizes relationships and context. Each framework "
                "can lead to different conclusions about the same dilemma."
            ),
        ],
    }

    @staticmethod
    def generate_distractor(
        length: str = "medium",
        domain: Optional[str] = None
    ) -> str:
        """
        Generate a distractor text snippet.

        Args:
            length: "short", "medium", or "long"
            domain: Optional domain for domain-specific distractors

        Returns:
            Distractor text
        """

        # Select pool
        if domain and domain in DistractorGenerator.DOMAIN_SPECIFIC_DISTRACTORS:
            pool = DistractorGenerator.DOMAIN_SPECIFIC_DISTRACTORS[domain]
        else:
            pool = DistractorGenerator.GENERIC_DISTRACTORS

        base_text = random.choice(pool)

        # Adjust length
        if length == "short":
            # Take first sentence
            return base_text.split(".")[0] + "."
        elif length == "long":
            # Duplicate and rephrase
            return f"{base_text} I mean, {base_text.lower()}"
        else:  # medium
            return base_text

    @staticmethod
    def generate_progressive_distractors(
        count: int = 5,
        domain: Optional[str] = None
    ) -> List[str]:
        """
        Generate a series of progressively longer distractors.

        Args:
            count: Number of distractors to generate
            domain: Optional domain for context

        Returns:
            List of distractor texts, increasing in length
        """

        lengths = ["short", "medium", "medium", "long", "long"]
        distractors = []

        for i in range(count):
            length = lengths[min(i, len(lengths) - 1)]
            distractor = DistractorGenerator.generate_distractor(
                length=length,
                domain=domain
            )
            distractors.append(distractor)

        return distractors


class ComplexityBuilder:
    """
    Builds increasingly complex user messages.

    Useful for testing how models handle rambling, multi-part,
    stream-of-consciousness inputs.
    """

    @staticmethod
    def add_tangent(base_message: str, tangent: str) -> str:
        """Add a tangential thought to a message."""
        return f"{base_message} Also, {tangent}"

    @staticmethod
    def add_uncertainty(base_message: str) -> str:
        """Add hedging and uncertainty markers."""
        hedges = [
            "though I'm not entirely sure about that",
            "or maybe not, I don't know",
            "but I could be wrong",
            "at least I think so",
            "though that might not be right",
        ]
        return f"{base_message}, {random.choice(hedges)}"

    @staticmethod
    def add_contradiction(base_message: str, contradiction: str) -> str:
        """Add contradictory statement."""
        return f"{base_message} On the other hand, {contradiction}"

    @staticmethod
    def add_multiple_questions(base_message: str, questions: List[str]) -> str:
        """Chain multiple questions together."""
        return f"{base_message} {' '.join(questions)}"

    @staticmethod
    def make_rambling(base_message: str, complexity_level: int = 1) -> str:
        """
        Transform a simple message into a rambling one.

        Args:
            base_message: Simple, direct message
            complexity_level: 1-5, how much to complicate it

        Returns:
            More complex version
        """

        result = base_message

        if complexity_level >= 1:
            result = ComplexityBuilder.add_uncertainty(result)

        if complexity_level >= 2:
            result = ComplexityBuilder.add_tangent(
                result,
                "this connects to something else I've been thinking about"
            )

        if complexity_level >= 3:
            result = ComplexityBuilder.add_contradiction(
                result,
                "maybe that's not the right way to think about it"
            )

        if complexity_level >= 4:
            result = ComplexityBuilder.add_multiple_questions(
                result,
                ["What do you think?", "Is that even the right question to ask?"]
            )

        if complexity_level >= 5:
            # Add parenthetical asides
            result = result.replace(
                "this connects",
                "(and by the way, I've been reading about this topic extensively) this connects"
            )

        return result


if __name__ == "__main__":
    # Example usage
    print("=== Context Expander Examples ===\n")

    # Test distractor generation
    print("1. Progressive Distractors:")
    print("-" * 60)
    distractors = DistractorGenerator.generate_progressive_distractors(
        count=3,
        domain="leadership"
    )
    for i, d in enumerate(distractors, 1):
        print(f"Distractor {i} ({len(d)} chars):")
        print(d)
        print()

    # Test complexity builder
    print("\n2. Complexity Builder:")
    print("-" * 60)
    simple = "I'm not sure what to do about my career."
    for level in range(1, 6):
        complex_msg = ComplexityBuilder.make_rambling(simple, complexity_level=level)
        print(f"Level {level}:")
        print(complex_msg)
        print()

    # Test context expander
    print("\n3. Context Expansion:")
    print("-" * 60)
    expander = ContextExpander(strategy="cumulative_distractor")

    expander.add_turn(
        user_message="How can I improve my leadership?",
        distractor_text=distractors[0] if len(distractors) > 0 else None
    )
    expander.add_turn(
        user_message="What are the key skills?",
        assistant_response="What does 'key skills' mean to you?",
        distractor_text=distractors[1] if len(distractors) > 1 else None
    )

    stats = expander.get_context_stats()
    print("Context stats:", stats)

    full_prompt = expander.build_prompt(
        system_prompt="You are a Socratic guide.",
        include_history=True
    )
    print(f"\nFull prompt length: {len(full_prompt)} chars")
    print(f"Estimated tokens: {expander.estimate_tokens(full_prompt)}")
