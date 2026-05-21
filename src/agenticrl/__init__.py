"""AgenticRL — Train LLM Agents with Reinforcement Learning.

AgenticRL provides a unified framework for training LLM-based agents
in general-purpose environments using two approaches:

1. **GRPO** (Group Relative Policy Optimization): Fine-tune LLM weights via TRL.
2. **Prompt Optimization** (DSPy-style): Search for optimal prompts without weight updates.

Quick Start:
    >>> from agenticrl import AgenticRLConfig, GRPOTrainer, LLMAgent
    >>> from agenticrl.environment import Env
    >>> 
    >>> # 1. Define your environment
    >>> class MyEnv(Env):
    ...     ...
    >>> 
    >>> # 2. Create agent
    >>> agent = LLMAgent("Qwen/Qwen2.5-1.5B-Instruct")
    >>> 
    >>> # 3. Train
    >>> trainer = GRPOTrainer("Qwen/Qwen2.5-1.5B-Instruct", env=MyEnv())
    >>> trainer.train_on_environment(agent, num_episodes=100)
"""

__version__ = "0.2.0"

from agenticrl.config import AgenticRLConfig, GRPOConfig, PromptOptConfig, AgentConfig
from agenticrl.agent import BaseAgent, LLMAgent
from agenticrl.environment import Env, TextEnv, register as register_env, get as get_env
from agenticrl.reward import RewardFunction, RuleReward, LLMJudgeReward, CompositeReward
from agenticrl.trajectory import TrajectoryCollector, TrajectoryBuffer
from agenticrl.trainer import GRPOTrainer, PromptOptimizer, PromptCandidate
from agenticrl.utils import setup_logger

__all__ = [
    "__version__",
    # Config
    "AgenticRLConfig",
    "GRPOConfig",
    "PromptOptConfig",
    "AgentConfig",
    # Agent
    "BaseAgent",
    "LLMAgent",
    # Environment
    "Env",
    "TextEnv",
    "register_env",
    "get_env",
    # Reward
    "RewardFunction",
    "RuleReward",
    "LLMJudgeReward",
    "CompositeReward",
    # Trajectory
    "TrajectoryCollector",
    "TrajectoryBuffer",
    # Trainer
    "GRPOTrainer",
    "PromptOptimizer",
    "PromptCandidate",
    # Utils
    "setup_logger",
]
