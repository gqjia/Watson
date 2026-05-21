"""Built-in reward models for AgenticRL."""

from typing import Any, Callable

from agenticrl.reward.base import RewardFunction


class RuleReward(RewardFunction):
    """Reward computed by a user-supplied rule function.

    Args:
        rule_fn: Callable (obs, action, next_obs, done, info) → float.
        name: Human-readable name for logging.

    Example:
        >>> reward = RuleReward(
        ...     lambda obs, act, nxt, done, info: 1.0 if done else 0.0,
        ...     name="success_reward",
        ... )
    """

    def __init__(
        self, rule_fn: Callable[..., float], name: str = "rule_reward"
    ) -> None:
        self._rule_fn = rule_fn
        self._name = name

    def compute(
        self,
        observation: Any,
        action: Any,
        next_observation: Any,
        done: bool,
        info: dict[str, Any],
    ) -> float:
        return self._rule_fn(observation, action, next_observation, done, info)

    def name(self) -> str:
        return self._name


class LLMJudgeReward(RewardFunction):
    """Reward computed by an LLM-as-judge.

    Uses a separate LLM to evaluate the quality of agent actions.

    Args:
        judge_model_name: HuggingFace model for judging.
        rubric: Natural-language rubric describing what constitutes a good action.
        max_score: Maximum score the judge can assign.
    """

    def __init__(
        self,
        judge_model_name: str,
        rubric: str = "Rate the quality of the response from 1 (poor) to 10 (excellent).",
        max_score: float = 10.0,
    ) -> None:
        self.judge_model_name = judge_model_name
        self.rubric = rubric
        self.max_score = max_score
        self._judge = None  # Lazy-loaded

    def _load_judge(self) -> Any:
        """Lazy-load the judge model."""
        if self._judge is None:
            from transformers import AutoModelForCausalLM, AutoTokenizer  # noqa: F811

            import torch  # noqa: F811

            self._judge_tokenizer = AutoTokenizer.from_pretrained(
                self.judge_model_name, trust_remote_code=True
            )
            self._judge = AutoModelForCausalLM.from_pretrained(
                self.judge_model_name,
                torch_dtype=torch.bfloat16,
                device_map="auto",
                trust_remote_code=True,
            )
            self._judge.eval()
        return self._judge, self._judge_tokenizer

    def compute(
        self,
        observation: Any,
        action: Any,
        next_observation: Any,
        done: bool,
        info: dict[str, Any],
    ) -> float:
        """Use an LLM judge to score the action.

        Args:
            observation: The observation presented to the agent.
            action: The agent's response.
            next_observation: Resulting observation.
            done: Whether the episode ended.
            info: Additional info from the environment.

        Returns:
            Normalized score in [0, 1].
        """
        judge, tokenizer = self._load_judge()

        prompt = (
            f"Task:\n{str(observation)}\n\n"
            f"Agent response:\n{str(action)}\n\n"
            f"Outcome:\n{str(next_observation)}\n\n"
            f"Rubric: {self.rubric}\n"
            f"Please output ONLY a number between 1 and {int(self.max_score)}:"
        )

        inputs = tokenizer(prompt, return_tensors="pt").to(judge.device)
        with __import__("torch").no_grad():
            outputs = judge.generate(
                **inputs,
                max_new_tokens=10,
                temperature=0.0,
                pad_token_id=tokenizer.eos_token_id,
            )
        response = tokenizer.decode(
            outputs[0][inputs["input_ids"].shape[1] :], skip_special_tokens=True
        ).strip()

        try:
            score = float(response) / self.max_score
            return max(0.0, min(1.0, score))
        except ValueError:
            return 0.0

    def name(self) -> str:
        return "llm_judge"


class CompositeReward(RewardFunction):
    """Weighted sum of multiple reward functions.

    Args:
        rewards: List of (weight, RewardFunction) tuples.

    Example:
        >>> composite = CompositeReward([
        ...     (1.0, RuleReward(my_rule)),
        ...     (0.5, LLMJudgeReward("judge-model")),
        ... ])
    """

    def __init__(self, rewards: list[tuple[float, RewardFunction]]) -> None:
        self._rewards = rewards

    def compute(
        self,
        observation: Any,
        action: Any,
        next_observation: Any,
        done: bool,
        info: dict[str, Any],
    ) -> float:
        total = 0.0
        for weight, reward_fn in self._rewards:
            total += weight * reward_fn.compute(
                observation, action, next_observation, done, info
            )
        return total

    def name(self) -> str:
        parts = [f"{w}*{r.name()}" for w, r in self._rewards]
        return f"Composite({', '.join(parts)})"
