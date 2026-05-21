"""Base reward function interface for AgenticRL."""

from abc import ABC, abstractmethod
from typing import Any


class RewardFunction(ABC):
    """Abstract reward function.

    Subclasses define how to compute a scalar reward from environment transitions.
    """

    @abstractmethod
    def compute(
        self,
        observation: Any,
        action: Any,
        next_observation: Any,
        done: bool,
        info: dict[str, Any],
    ) -> float:
        """Compute the reward for a single transition.

        Args:
            observation: State before action.
            action: The action taken.
            next_observation: State after action.
            done: Whether the episode ended.
            info: Additional environment info.

        Returns:
            Scalar reward value.
        """
        ...

    def aggregate(self, rewards: list[float]) -> float:
        """Aggregate per-step rewards into an episode score.

        Default is sum. Override for alternative aggregation (e.g., mean, discounted).

        Args:
            rewards: Per-step reward list.

        Returns:
            Aggregated score.
        """
        return sum(rewards)

    def name(self) -> str:
        """Return a human-readable name for logging."""
        return self.__class__.__name__
