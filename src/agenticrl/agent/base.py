"""Abstract base class for agents in AgenticRL."""

from abc import ABC, abstractmethod
from typing import Any


class BaseAgent(ABC):
    """Abstract agent that interacts with environments.

    An agent observes environment state, produces actions, and (optionally) learns
    from experience. Subclasses implement act() and learn().
    """

    @abstractmethod
    def act(self, observation: Any) -> Any:
        """Produce an action given the current observation.

        Args:
            observation: Current environment observation.

        Returns:
            An action to execute in the environment.
        """
        ...

    def learn(self, trajectories: list[dict[str, Any]]) -> dict[str, float]:
        """Update the agent from collected trajectories.

        Args:
            trajectories: List of trajectory dictionaries, each containing
                "observations", "actions", "rewards", "dones", "infos".

        Returns:
            Dictionary of training metrics (e.g., {"loss": 0.5, "reward_mean": 2.3}).
        """
        return {}

    def reset(self) -> None:
        """Reset agent state for a new episode."""
        pass

    def save(self, path: str) -> None:
        """Save agent state to disk."""
        raise NotImplementedError

    def load(self, path: str) -> None:
        """Load agent state from disk."""
        raise NotImplementedError
