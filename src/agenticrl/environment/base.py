"""Abstract environment interface (gym-style) for AgenticRL."""

from abc import ABC, abstractmethod
from typing import Any

import gymnasium as gym


class Env(ABC):
    """Abstract base class for AgenticRL environments.

    Follows the gymnasium interface pattern: reset() → observation, step(action) → (obs, reward, done, info).
    Subclasses must implement reset, step, and provide action_space / observation_space.

    Unlike gymnasium.Env, this class is deliberately simpler and does not enforce
    the full gym protocol — it is designed for LLM agent training where observations
    and actions are often text-based.

    Example:
        >>> class MyEnv(Env):
        ...     @property
        ...     def action_space(self) -> gym.Space:
        ...         return gym.spaces.Discrete(4)
        ...     def reset(self, seed=None, options=None) -> Any:
        ...         return "initial state"
        ...     def step(self, action) -> tuple[Any, float, bool, bool, dict]:
        ...         return "next state", 1.0, True, False, {}
    """

    @property
    @abstractmethod
    def action_space(self) -> gym.Space:
        """Return the action space."""
        ...

    @property
    @abstractmethod
    def observation_space(self) -> gym.Space:
        """Return the observation space."""
        ...

    @abstractmethod
    def reset(self, seed: int | None = None, options: dict[str, Any] | None = None) -> Any:
        """Reset the environment and return the initial observation.

        Args:
            seed: Optional random seed.
            options: Optional additional information.

        Returns:
            The initial observation.
        """
        ...

    @abstractmethod
    def step(self, action: Any) -> tuple[Any, float, bool, bool, dict[str, Any]]:
        """Execute one step in the environment.

        Args:
            action: The action to execute.

        Returns:
            Tuple of (observation, reward, terminated, truncated, info).
        """
        ...

    def render(self) -> str | None:
        """Render the environment state (optional). Returns a string representation or None."""
        return None

    def close(self) -> None:
        """Clean up resources."""
        pass


class TextEnv(Env):
    """Convenience base class for text-based environments.

    Inherit from this when both observations and actions are strings.
    Provides default text-based action and observation spaces.
    """

    def __init__(self, max_obs_length: int = 4096, max_action_length: int = 2048):
        self._max_obs_length = max_obs_length
        self._max_action_length = max_action_length

    @property
    def action_space(self) -> gym.Space:
        return gym.spaces.Text(max_length=self._max_action_length)

    @property
    def observation_space(self) -> gym.Space:
        return gym.spaces.Text(max_length=self._max_obs_length)
