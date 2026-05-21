"""Trajectory collector — runs rollouts with an agent in an environment."""

from __future__ import annotations

import json
from typing import Any, Optional

from agenticrl.environment.base import Env
from agenticrl.reward.base import RewardFunction


class TrajectoryCollector:
    """Collects trajectories by running an agent in an environment.

    Each trajectory is a sequence of (observation, action, reward, done, info)
    transitions accumulated over a single episode.

    Args:
        env: The environment instance.
        reward_fn: Reward function for computing per-step rewards.
        max_steps: Maximum steps per episode (to prevent infinite loops).

    Example:
        >>> collector = TrajectoryCollector(env, reward_fn)
        >>> traj = collector.run_rollout(agent)
        >>> print(traj["total_reward"])
    """

    def __init__(
        self,
        env: Env,
        reward_fn: RewardFunction | None = None,
        max_steps: int = 100,
    ) -> None:
        self.env = env
        self.reward_fn = reward_fn
        self.max_steps = max_steps

    def run_rollout(
        self, agent: Any, seed: int | None = None
    ) -> dict[str, Any]:
        """Run a single rollout episode.

        Args:
            agent: Agent instance with an `act(obs) -> action` method.
            seed: Optional random seed for the environment.

        Returns:
            Dictionary with keys:
                - observations: list of observations
                - actions: list of actions
                - rewards: list of per-step rewards
                - dones: list of termination flags
                - infos: list of info dicts
                - total_reward: sum of all rewards
                - steps: number of steps taken
        """
        observations: list[Any] = []
        actions: list[Any] = []
        rewards: list[float] = []
        dones: list[bool] = []
        infos: list[dict[str, Any]] = []

        agent.reset()
        obs = self.env.reset(seed=seed)

        for _ in range(self.max_steps):
            action = agent.act(obs)
            next_obs, reward, terminated, truncated, info = self.env.step(action)
            done = terminated or truncated

            if self.reward_fn is not None:
                reward = self.reward_fn.compute(
                    obs, action, next_obs, done, info
                )

            observations.append(obs)
            actions.append(action)
            rewards.append(reward)
            dones.append(done)
            infos.append(info)

            if done:
                break
            obs = next_obs

        return {
            "observations": observations,
            "actions": actions,
            "rewards": rewards,
            "dones": dones,
            "infos": infos,
            "total_reward": sum(rewards),
            "steps": len(rewards),
        }

    def run_rollouts(
        self,
        agent: Any,
        num_rollouts: int = 1,
        seeds: list[int] | None = None,
    ) -> list[dict[str, Any]]:
        """Run multiple rollouts.

        Args:
            agent: Agent instance.
            num_rollouts: Number of rollouts to run.
            seeds: Optional per-rollout seeds.

        Returns:
            List of trajectory dictionaries.
        """
        if seeds is None or len(seeds) < num_rollouts:
            seeds = list(range(num_rollouts))

        trajectories = []
        for i in range(num_rollouts):
            traj = self.run_rollout(agent, seed=seeds[i])
            trajectories.append(traj)
        return trajectories

    def save_trajectories(
        self, trajectories: list[dict[str, Any]], filepath: str
    ) -> None:
        """Save trajectories to a JSON file.

        Args:
            trajectories: List of trajectory dicts.
            filepath: Output JSON path.
        """
        with open(filepath, "w") as f:
            json.dump(trajectories, f, indent=2, default=str)
