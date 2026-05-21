"""Tests for the agent module."""

import pytest

from agenticrl.agent import BaseAgent, LLMAgent
from agenticrl.config import AgentConfig


class TestBaseAgent:
    """Test the BaseAgent abstract class."""

    def test_base_agent_learn_default(self) -> None:
        """Test that BaseAgent.learn returns empty dict by default."""

        class DummyAgent(BaseAgent):
            def act(self, obs):
                return "action"

        agent = DummyAgent()
        metrics = agent.learn([])
        assert metrics == {}

    def test_base_agent_reset(self) -> None:
        """Test BaseAgent.reset does nothing by default."""

        class DummyAgent(BaseAgent):
            def act(self, obs):
                return "action"

        agent = DummyAgent()
        agent.reset()  # Should not raise

    def test_abstract_act(self) -> None:
        """Test that BaseAgent cannot be instantiated without act()."""
        with pytest.raises(TypeError):
            BaseAgent()  # type: ignore[abstract]


class TestAgentConfig:
    """Test AgentConfig dataclass."""

    def test_defaults(self) -> None:
        """Test AgentConfig has sensible defaults."""
        cfg = AgentConfig()
        assert cfg.system_prompt == "You are a helpful AI assistant."
        assert cfg.temperature == 0.7
        assert cfg.max_new_tokens == 256
        assert cfg.tools == []

    def test_custom(self) -> None:
        """Test AgentConfig accepts custom values."""
        cfg = AgentConfig(
            system_prompt="Custom prompt",
            temperature=0.5,
            max_new_tokens=128,
            tools=["search"],
        )
        assert cfg.system_prompt == "Custom prompt"
        assert cfg.temperature == 0.5
        assert cfg.max_new_tokens == 128
        assert cfg.tools == ["search"]
