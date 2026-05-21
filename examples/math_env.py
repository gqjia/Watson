"""Example: Math problem-solving environment.

A simple text-based environment where the agent must solve math problems.
The environment presents a math question and evaluates the agent's answer.
"""

import random
from typing import Any

import gymnasium as gym

from agenticrl.environment.base import TextEnv


class MathEnv(TextEnv):
    """A math problem-solving environment.

    Each episode presents a randomly selected math problem. The agent
    must output the correct numerical answer. Reward: +1 for correct, -0.5 for wrong.

    Args:
        difficulty: Problem difficulty level ("easy", "medium", "hard").
        seed: Random seed for reproducibility.
    """

    PROBLEMS = {
        "easy": [
            ("What is 15 + 27?", "42"),
            ("What is 100 - 37?", "63"),
            ("What is 8 × 7?", "56"),
            ("What is 144 ÷ 12?", "12"),
            ("What is 2^5?", "32"),
            ("What is the square root of 64?", "8"),
        ],
        "medium": [
            ("If x + 5 = 12, what is x?", "7"),
            ("What is 15% of 200?", "30"),
            ("If a triangle has base 10 and height 6, what is its area?", "30"),
            ("What is the value of 3! + 4!?", "30"),
            ("Solve: 2x - 7 = 11. What is x?", "9"),
            ("What is the sum of the angles in a hexagon?", "720"),
        ],
        "hard": [
            ("If f(x) = x² + 3x - 4, what is f(5)?", "36"),
            ("What is the derivative of x³ at x = 2?", "12"),
            ("If a circle has area 100π, what is its radius?", "10"),
            ("What is the 10th Fibonacci number?", "55"),
            ("Solve for x: log₂(x) = 5. What is x?", "32"),
            ("If P(A)=0.3 and P(B)=0.4, and A,B are independent, what is P(A∩B)?", "0.12"),
        ],
    }

    def __init__(
        self,
        difficulty: str = "easy",
        seed: int | None = None,
        max_obs_length: int = 4096,
        max_action_length: int = 2048,
    ) -> None:
        super().__init__(max_obs_length, max_action_length)
        if difficulty not in self.PROBLEMS:
            raise ValueError(f"Unknown difficulty: {difficulty}. Choose from {list(self.PROBLEMS.keys())}")
        self.difficulty = difficulty
        self._rng = random.Random(seed)
        self._current_problem: tuple[str, str] = ("", "")
        self._steps: int = 0

    @property
    def action_space(self) -> gym.Space:
        return gym.spaces.Text(max_length=self._max_action_length)

    @property
    def observation_space(self) -> gym.Space:
        return gym.spaces.Text(max_length=self._max_obs_length)

    def reset(
        self, seed: int | None = None, options: dict[str, Any] | None = None
    ) -> str:
        """Reset and sample a new problem.

        Args:
            seed: Optional seed for reproducibility.
            options: Unused.

        Returns:
            The math problem as a string.
        """
        if seed is not None:
            self._rng = random.Random(seed)
        self._steps = 0
        problems = self.PROBLEMS[self.difficulty]
        self._current_problem = self._rng.choice(problems)
        return f"Problem: {self._current_problem[0]}\nPlease provide only the numerical answer."

    def step(self, action: str) -> tuple[str, float, bool, bool, dict[str, Any]]:
        """Evaluate the agent's answer.

        Args:
            action: The agent's answer string.

        Returns:
            (observation, reward, terminated, truncated, info).
        """
        self._steps += 1
        question, answer = self._current_problem

        # Extract numeric answer from action
        action_clean = action.strip().rstrip(".")
        is_correct = action_clean == answer

        reward = 1.0 if is_correct else -0.5
        done = is_correct or self._steps >= 3
        info = {"correct": is_correct, "expected": answer, "got": action_clean}

        if is_correct:
            obs = f"Correct! The answer is {answer}."
        elif done:
            obs = f"Wrong. The correct answer was {answer}. You answered: {action_clean}"
        else:
            obs = f"That's not correct. Try again.\nProblem: {question}\nProvide only the numerical answer."

        return obs, reward, done, False, info

    def render(self) -> str:
        """Show the current problem."""
        return f"[MathEnv:{self.difficulty}] {self._current_problem[0]} (answer: {self._current_problem[1]})"
