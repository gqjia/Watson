"""Experience buffer for storing and sampling trajectories."""

from __future__ import annotations

import random
from typing import Any


class TrajectoryBuffer:
    """A simple replay buffer for trajectory data.

    Stores trajectories in memory and supports sampling for training.

    Args:
        capacity: Maximum number of trajectories to store (FIFO).
        seed: Random seed for sampling.

    Example:
        >>> buffer = TrajectoryBuffer(capacity=1000)
        >>> buffer.add(trajectory)
        >>> batch = buffer.sample(32)
    """

    def __init__(self, capacity: int = 10000, seed: int | None = None) -> None:
        self.capacity = capacity
        self._buffer: list[dict[str, Any]] = []
        self._rng = random.Random(seed)

    def add(self, trajectory: dict[str, Any]) -> None:
        """Add a trajectory to the buffer.

        Args:
            trajectory: Trajectory dict from TrajectoryCollector.
        """
        if len(self._buffer) >= self.capacity:
            self._buffer.pop(0)
        self._buffer.append(trajectory)

    def add_batch(self, trajectories: list[dict[str, Any]]) -> None:
        """Add multiple trajectories at once."""
        for traj in trajectories:
            self.add(traj)

    def sample(self, batch_size: int) -> list[dict[str, Any]]:
        """Sample a random batch of trajectories.

        Args:
            batch_size: Number of trajectories to sample.

        Returns:
            List of sampled trajectory dicts (may be fewer than batch_size
            if the buffer has fewer trajectories).
        """
        n = min(batch_size, len(self._buffer))
        return self._rng.sample(self._buffer, n)

    def get_all(self) -> list[dict[str, Any]]:
        """Return all trajectories in the buffer."""
        return list(self._buffer)

    def clear(self) -> None:
        """Empty the buffer."""
        self._buffer.clear()

    def __len__(self) -> int:
        return len(self._buffer)

    def to_trl_format(self) -> list[dict[str, Any]]:
        """Convert buffer contents to TRL-compatible format.

        TRL's GRPOTrainer expects a dataset where each example has at minimum
        a "prompt" field. We concatenate the observation and the agent's
        responses into a conversation format.

        Returns:
            List of dicts with "prompt", "completion", and "reward" keys.
        """
        examples = []
        for traj in self._buffer:
            for i, (obs, act, reward) in enumerate(
                zip(traj["observations"], traj["actions"], traj["rewards"])
            ):
                examples.append({
                    "prompt": str(obs),
                    "completion": str(act),
                    "reward": reward,
                })
        return examples

    def stats(self) -> dict[str, float]:
        """Compute summary statistics over the buffer.

        Returns:
            Dict with mean_reward, max_reward, min_reward, mean_episode_length.
        """
        if not self._buffer:
            return {
                "mean_reward": 0.0,
                "max_reward": 0.0,
                "min_reward": 0.0,
                "mean_episode_length": 0.0,
                "num_episodes": 0,
            }
        total_rewards = [t["total_reward"] for t in self._buffer]
        lengths = [t["steps"] for t in self._buffer]
        return {
            "mean_reward": sum(total_rewards) / len(total_rewards),
            "max_reward": max(total_rewards),
            "min_reward": min(total_rewards),
            "mean_episode_length": sum(lengths) / len(lengths),
            "num_episodes": len(self._buffer),
        }
