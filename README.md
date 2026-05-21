# Watson → AgenticRL 🧠⚔️

**Train LLM Agents with Reinforcement Learning.**

AgenticRL lets you train LLM-based agents in arbitrary environments using two complementary approaches:

| Method | What it optimizes | When to use |
|--------|-------------------|-------------|
| **GRPO** (TRL-based) | Model weights | You want to fine-tune the model |
| **Prompt Optimization** (DSPy-style) | System prompt | You want to keep the model frozen |

## Architecture

```
 Agent  ──act──▶  Environment
   ▲                │
   │     reward     │  obs
   │                ▼
   └── learn ── Trajectory ──▶  Buffer  ──▶  Trainer
```

## Quick Start

```python
from agenticrl import LLMAgent, GRPOTrainer, RuleReward
from examples.math_env import MathEnv

# 1. Environment
env = MathEnv(difficulty="easy")

# 2. Reward
reward = RuleReward(lambda o,a,n,d,i: 1.0 if i.get("correct") else -0.5)

# 3. Agent + Train
agent = LLMAgent("Qwen/Qwen2.5-1.5B-Instruct")
trainer = GRPOTrainer("Qwen/Qwen2.5-1.5B-Instruct", env=env, reward_fn=reward)
trainer.train_on_environment(agent, num_episodes=100)
```

## Install

```bash
git clone git@github.com:gqjia/Watson.git
cd Watson
uv sync
```

## Project Structure

```
src/agenticrl/
├── agent/          # BaseAgent + LLMAgent (HF transformers)
├── environment/    # Env interface (gym-style) + registry
├── trainer/        # GRPOTrainer (TRL) + PromptOptimizer (evolutionary)
├── reward/         # RewardFunction + RuleReward + LLMJudgeReward
├── trajectory/     # TrajectoryCollector + TrajectoryBuffer
└── utils/          # Logging
examples/           # math_env.py, train_grpo.py
tests/              # 18 tests covering environment + trajectory
```
