"""GRPO (Group Relative Policy Optimization) trainer.

Wraps TRL's GRPOTrainer to train LLM agents in arbitrary environments.
The training loop alternates between collecting rollout trajectories from
the environment and performing gradient updates on the policy.
"""

from __future__ import annotations

import os
from typing import Any

import torch
from datasets import Dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    PreTrainedModel,
    PreTrainedTokenizerBase,
    TrainingArguments,
)

from agenticrl.config import GRPOConfig
from agenticrl.environment.base import Env
from agenticrl.reward.base import RewardFunction
from agenticrl.trajectory.buffer import TrajectoryBuffer
from agenticrl.trajectory.collector import TrajectoryCollector


def _reward_func(prompts: list[list[dict[str, str]]], completions: list[str]) -> list[float]:
    """Default reward function for GRPOTrainer — simple length-based reward."""
    return [min(1.0, len(c) / 200.0) for c in completions]


class GRPOTrainer:
    """GRPO trainer that trains an LLM agent in an environment.

    The trainer manages the full training lifecycle:
    1. Run rollouts with the current model → collect trajectories
    2. Format trajectories for TRL's GRPOTrainer
    3. Perform GRPO gradient updates
    4. Repeat

    Args:
        model_name_or_path: HuggingFace model ID or path.
        env: Environment instance for rollouts.
        config: GRPO configuration.
        reward_fn: Optional reward function for per-step scoring.

    Example:
        >>> from agenticrl.trainer import GRPOTrainer
        >>> from agenticrl.config import GRPOConfig
        >>> 
        >>> trainer = GRPOTrainer(
        ...     "Qwen/Qwen2.5-1.5B-Instruct",
        ...     env=my_env,
        ...     config=GRPOConfig(num_train_epochs=3),
        ... )
        >>> trainer.train(agent=my_agent)
    """

    def __init__(
        self,
        model_name_or_path: str,
        env: Env,
        config: GRPOConfig | None = None,
        reward_fn: RewardFunction | None = None,
    ) -> None:
        self.model_name_or_path = model_name_or_path
        self.env = env
        self.config = config or GRPOConfig()
        self.reward_fn = reward_fn

        # Internal state
        self._trl_trainer: Any = None
        self._buffer = TrajectoryBuffer(capacity=10000)
        self._collector = TrajectoryCollector(env, reward_fn=reward_fn)

        # Model and tokenizer
        self.tokenizer: PreTrainedTokenizerBase = AutoTokenizer.from_pretrained(
            model_name_or_path, trust_remote_code=True
        )
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        self.model: PreTrainedModel = AutoModelForCausalLM.from_pretrained(
            model_name_or_path,
            torch_dtype=torch.bfloat16,
            device_map="auto",
            trust_remote_code=True,
        )

    def _prepare_dataset(self, agent: Any, num_episodes: int = 32) -> Dataset:
        """Collect rollouts and prepare a TRL-compatible dataset.

        Args:
            agent: Agent to run rollouts with.
            num_episodes: Number of episodes to collect.

        Returns:
            A HuggingFace Dataset with "prompt" and "reward" columns.
        """
        trajectories = self._collector.run_rollouts(agent, num_rollouts=num_episodes)
        self._buffer.add_batch(trajectories)

        # Convert to TRL format: list of {prompt, completion, reward}
        examples = self._buffer.to_trl_format()
        return Dataset.from_list(examples)

    def _create_trl_trainer(self, train_dataset: Dataset) -> Any:
        """Create the underlying TRL GRPOTrainer.

        Args:
            train_dataset: Dataset with prompts and rewards.

        Returns:
            Configured GRPOTrainer instance.
        """
        from trl import GRPOConfig as TRLGRPOConfig
        from trl import GRPOTrainer as TRLGRPOTrainer

        training_args = TrainingArguments(
            output_dir=self.config.output_dir if hasattr(self.config, 'output_dir') else "./grpo_output",
            num_train_epochs=self.config.num_train_epochs,
            per_device_train_batch_size=self.config.per_device_train_batch_size,
            gradient_accumulation_steps=self.config.gradient_accumulation_steps,
            learning_rate=self.config.learning_rate,
            warmup_ratio=self.config.warmup_ratio,
            logging_steps=self.config.logging_steps,
            save_steps=self.config.save_steps,
            eval_strategy="steps",
            eval_steps=self.config.eval_steps,
            bf16=torch.cuda.is_bf16_supported(),
            remove_unused_columns=False,
            report_to=["wandb"],
        )

        trl_config = TRLGRPOConfig(
            max_prompt_length=self.config.max_prompt_length,
            max_completion_length=self.config.max_completion_length,
            num_generations=self.config.num_generations,
            temperature=self.config.temperature,
            beta=self.config.beta,
        )

        trainer = TRLGRPOTrainer(
            model=self.model,
            processing_class=self.tokenizer,
            args=training_args,
            train_dataset=train_dataset,
            reward_funcs=_reward_func,
            **trl_config.to_dict() if hasattr(trl_config, 'to_dict') else {},
        )
        return trainer

    def train(
        self,
        agent: Any,
        num_iterations: int = 10,
        rollouts_per_iteration: int = 32,
    ) -> dict[str, Any]:
        """Run the full training loop.

        Args:
            agent: Agent to collect rollouts from (should be the same model).
            num_iterations: Number of collect→train cycles.
            rollouts_per_iteration: Number of episodes to collect each iteration.

        Returns:
            Dict with training metrics (final_loss, total_steps, buffer_stats).
        """
        total_steps = 0
        final_metrics: dict[str, Any] = {}

        for iteration in range(num_iterations):
            # Phase 1: Collect rollouts
            dataset = self._prepare_dataset(agent, num_episodes=rollouts_per_iteration)
            buffer_stats = self._buffer.stats()
            print(
                f"[Iter {iteration+1}/{num_iterations}] "
                f"Buffer: {buffer_stats['num_episodes']} episodes, "
                f"mean_reward={buffer_stats['mean_reward']:.3f}"
            )

            # Phase 2: Create trainer (re-create per iteration to use fresh data)
            trl_trainer = self._create_trl_trainer(dataset)
            self._trl_trainer = trl_trainer

            # Phase 3: Train
            train_result = trl_trainer.train()
            total_steps += train_result.global_step if hasattr(train_result, 'global_step') else 0
            final_metrics = {
                "iteration": iteration + 1,
                "total_steps": total_steps,
                "buffer_stats": buffer_stats,
            }
            print(f"[Iter {iteration+1}/{num_iterations}] Steps: {total_steps}")

            # Update agent's model weights
            if hasattr(agent, 'model'):
                agent.model.load_state_dict(self.model.state_dict())

        return final_metrics

    def save(self, path: str) -> None:
        """Save the trained model and tokenizer."""
        os.makedirs(path, exist_ok=True)
        self.model.save_pretrained(path)
        self.tokenizer.save_pretrained(path)

    def train_on_environment(
        self,
        agent: Any,
        num_episodes: int = 100,
    ) -> dict[str, Any]:
        """High-level API: train an agent on an environment.

        This is the recommended entry point. It handles the full pipeline:
        collect → train → save.

        Args:
            agent: Agent instance (should have `act()` method).
            num_episodes: Total number of episodes to use.

        Returns:
            Training metrics dict.
        """
        num_iterations = max(1, num_episodes // 32)
        rollouts_per_iteration = max(1, num_episodes // num_iterations)

        return self.train(
            agent=agent,
            num_iterations=num_iterations,
            rollouts_per_iteration=rollouts_per_iteration,
        )
