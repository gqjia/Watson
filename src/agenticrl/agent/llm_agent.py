"""LLM-based agent for AgenticRL.

Wraps a HuggingFace transformers model as an agent that can interact with
text-based environments. Supports optional tool calling via a simple
function-calling format.
"""

from __future__ import annotations

import textwrap
from typing import Any, Callable, Optional

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, PreTrainedTokenizerBase

from agenticrl.agent.base import BaseAgent
from agenticrl.config import AgentConfig


class LLMAgent(BaseAgent):
    """An agent powered by a HuggingFace causal language model.

    The agent converts environment observations into prompts, generates
    actions via the LLM, and parses the output.

    Args:
        model_name_or_path: HuggingFace model identifier or local path.
        config: Agent configuration for prompt, temperature, etc.
        torch_dtype: Data type for model weights (default: bfloat16 if available).
        device_map: Device placement strategy (default: "auto").

    Example:
        >>> from agenticrl.agent import LLMAgent
        >>> agent = LLMAgent("Qwen/Qwen2.5-1.5B-Instruct")
        >>> action = agent.act("What is 2 + 2?")
    """

    def __init__(
        self,
        model_name_or_path: str,
        config: AgentConfig | None = None,
        torch_dtype: torch.dtype | None = None,
        device_map: str = "auto",
    ) -> None:
        self.model_name_or_path = model_name_or_path
        self.config = config or AgentConfig()

        if torch_dtype is None:
            torch_dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16

        self.tokenizer: PreTrainedTokenizerBase = AutoTokenizer.from_pretrained(
            model_name_or_path, trust_remote_code=True
        )
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name_or_path,
            torch_dtype=torch_dtype,
            device_map=device_map,
            trust_remote_code=True,
        )
        self.model.eval()

        # Tool registry: name → callable
        self._tools: dict[str, Callable[..., str]] = {}

    def register_tool(self, name: str, fn: Callable[..., str]) -> None:
        """Register a tool that the agent can invoke.

        Args:
            name: Tool name (used in function-calling prompts).
            fn: A callable that takes string arguments and returns a string result.
        """
        self._tools[name] = fn

    def act(self, observation: Any) -> str:
        """Generate an action given an observation.

        Args:
            observation: Environment observation (converted to string).

        Returns:
            Generated action string.
        """
        prompt = self._build_prompt(str(observation))
        inputs = self.tokenizer(
            prompt, return_tensors="pt", truncation=True, max_length=2048
        ).to(self.model.device)

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=self.config.max_new_tokens,
                temperature=self.config.temperature,
                top_p=self.config.top_p,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id,
            )

        response = self.tokenizer.decode(
            outputs[0][inputs["input_ids"].shape[1] :], skip_special_tokens=True
        )
        return response.strip()

    def _build_prompt(self, observation: str) -> str:
        """Build a chat-format prompt from the observation.

        Args:
            observation: The current environment observation.

        Returns:
            Formatted prompt string ready for tokenization.
        """
        messages = [
            {"role": "system", "content": self.config.system_prompt},
            {"role": "user", "content": observation},
        ]
        return self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )

    def learn(self, trajectories: list[dict[str, Any]]) -> dict[str, float]:
        base_agent_learn = super().learn(trajectories)
        return {"loss": 0.0, **base_agent_learn}

    def save(self, path: str) -> None:
        """Save model and tokenizer to disk."""
        self.model.save_pretrained(path)
        self.tokenizer.save_pretrained(path)

    def load(self, path: str) -> None:
        """Load model and tokenizer from disk."""
        self.model = AutoModelForCausalLM.from_pretrained(path, trust_remote_code=True)
        self.tokenizer = AutoTokenizer.from_pretrained(path, trust_remote_code=True)

    def to(self, device: str | torch.device) -> "LLMAgent":
        """Move the model to a device."""
        self.model.to(device)
        return self
