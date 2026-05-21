"""Example: GRPO training script.

Demonstrates the full training pipeline:
1. Define an environment
2. Create an LLM agent
3. Set up the GRPO trainer
4. Train and save
"""

from agenticrl import (
    AgenticRLConfig,
    AgentConfig,
    GRPOConfig,
    GRPOTrainer,
    LLMAgent,
    RuleReward,
)
from examples.math_env import MathEnv


def main() -> None:
    """Run a minimal GRPO training example."""

    # --- 1. Environment ---
    env = MathEnv(difficulty="easy", seed=42)

    # --- 2. Reward function ---
    # Use a simple rule: +1 for correct, check via environment info
    def math_reward(obs, action, next_obs, done, info):
        return 1.0 if info.get("correct", False) else -0.5

    reward_fn = RuleReward(math_reward, name="math_reward")

    # --- 3. Config ---
    cfg = AgenticRLConfig(
        model_name_or_path="Qwen/Qwen2.5-1.5B-Instruct",
        trainer_type="grpo",
        output_dir="./output/math-grpo",
        seed=42,
    )

    grpo_cfg = GRPOConfig(
        num_train_epochs=3,
        per_device_train_batch_size=2,
        gradient_accumulation_steps=2,
        learning_rate=1e-6,
        max_prompt_length=512,
        max_completion_length=128,
        num_generations=4,
        temperature=1.0,
        beta=0.04,
        logging_steps=5,
        save_steps=50,
    )

    agent_cfg = AgentConfig(
        system_prompt="You are a math expert. Provide only the numerical answer.",
        temperature=0.7,
        max_new_tokens=64,
    )

    # --- 4. Agent ---
    print("Loading agent...")
    agent = LLMAgent(
        model_name_or_path=cfg.model_name_or_path,
        config=agent_cfg,
    )

    # --- 5. Trainer ---
    print("Setting up GRPO trainer...")
    trainer = GRPOTrainer(
        model_name_or_path=cfg.model_name_or_path,
        env=env,
        config=grpo_cfg,
        reward_fn=reward_fn,
    )

    # --- 6. Train ---
    print("Starting training...")
    metrics = trainer.train_on_environment(
        agent=agent,
        num_episodes=64,  # Small number for demo
    )

    print(f"\nTraining complete! Metrics: {metrics}")

    # --- 7. Save ---
    trainer.save("./output/math-grpo/final")
    print("Model saved to ./output/math-grpo/final")


if __name__ == "__main__":
    main()
