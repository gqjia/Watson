"""Configuration dataclasses for AgenticRL."""

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class AgenticRLConfig:
    """Top-level configuration for AgenticRL.

    Attributes:
        model_name_or_path: HuggingFace model identifier or local path.
        trainer_type: Training mode, either "grpo" or "prompt_opt".
        output_dir: Directory for checkpoints and logs.
        seed: Random seed for reproducibility.
        use_vllm: Whether to use vLLM for fast rollout inference.
        vllm_gpu_memory_utilization: GPU memory fraction for vLLM.
    """

    model_name_or_path: str = "Qwen/Qwen2.5-1.5B-Instruct"
    trainer_type: str = "grpo"  # "grpo" or "prompt_opt"
    output_dir: str = "./output"
    seed: int = 42
    use_vllm: bool = False
    vllm_gpu_memory_utilization: float = 0.6

    def __post_init__(self) -> None:
        if self.trainer_type not in ("grpo", "prompt_opt"):
            raise ValueError(f"trainer_type must be 'grpo' or 'prompt_opt', got '{self.trainer_type}'")


@dataclass
class GRPOConfig:
    """Configuration for GRPO training.

    Attributes:
        num_train_epochs: Number of training epochs.
        per_device_train_batch_size: Batch size per device.
        gradient_accumulation_steps: Gradient accumulation steps.
        learning_rate: Peak learning rate.
        warmup_ratio: Fraction of steps for linear warmup.
        max_prompt_length: Maximum prompt token length.
        max_completion_length: Maximum completion token length.
        num_generations: Number of completions to sample per prompt (group size).
        temperature: Sampling temperature for rollouts.
        beta: KL penalty coefficient.
        reward_weights: Weight multipliers per reward function name.
        logging_steps: Log metrics every N steps.
        save_steps: Save checkpoint every N steps.
        eval_steps: Run evaluation every N steps.
    """

    num_train_epochs: int = 3
    per_device_train_batch_size: int = 4
    gradient_accumulation_steps: int = 2
    learning_rate: float = 1e-6
    warmup_ratio: float = 0.1
    max_prompt_length: int = 1024
    max_completion_length: int = 512
    num_generations: int = 4
    temperature: float = 1.0
    beta: float = 0.04
    reward_weights: dict[str, float] = field(default_factory=dict)
    logging_steps: int = 10
    save_steps: int = 100
    eval_steps: int = 200


@dataclass
class PromptOptConfig:
    """Configuration for prompt-level optimization (DSPy-style).

    Attributes:
        population_size: Number of prompt candidates.
        num_iterations: Number of evolutionary iterations.
        top_k: Number of top-performing prompts to retain each generation.
        mutation_rate: Probability of mutating each prompt component.
        crossover_rate: Probability of performing crossover between two prompts.
        num_rollouts_per_prompt: Rollouts to evaluate each prompt candidate.
        max_prompt_length: Maximum token length for generated prompts.
        initial_prompts: Seed prompts for the population.
    """

    population_size: int = 10
    num_iterations: int = 20
    top_k: int = 3
    mutation_rate: float = 0.3
    crossover_rate: float = 0.5
    num_rollouts_per_prompt: int = 5
    max_prompt_length: int = 512
    initial_prompts: list[str] = field(default_factory=list)


@dataclass
class AgentConfig:
    """Configuration for LLM Agent.

    Attributes:
        system_prompt: System prompt prepended to every conversation.
        tools: List of tool names available to the agent.
        max_tool_calls: Maximum tool calls per turn.
        temperature: Sampling temperature for generation.
        top_p: Nucleus sampling parameter.
        max_new_tokens: Maximum generation tokens per turn.
    """

    system_prompt: str = "You are a helpful AI assistant."
    tools: list[str] = field(default_factory=list)
    max_tool_calls: int = 5
    temperature: float = 0.7
    top_p: float = 0.95
    max_new_tokens: int = 256
