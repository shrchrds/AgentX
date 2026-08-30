"""Tests for the LegalAgent base class."""

from __future__ import annotations

from app.agents.contract_review import ContractReviewAgent
from app.memory.backends.in_memory import InMemoryStore


class TestLegalAgentBase:
    """Tests for shared base class behavior."""

    def test_build_system_prompt_contains_injection_resistance(self) -> None:
        store = InMemoryStore()
        agent = ContractReviewAgent(agent_id="test", memory=store)
        prompt = agent._build_system_prompt("You are a test agent.")
        assert "NEVER reveal" in prompt
        assert "ignore instructions" in prompt
        assert "injection" in prompt.lower()

    def test_sanitize_output_strips_system_prompt_leak(self) -> None:
        store = InMemoryStore()
        agent = ContractReviewAgent(agent_id="test", memory=store)

        dirty = "Here is the analysis. system prompt: do bad things."
        cleaned = agent._sanitize_output(dirty)
        assert "system prompt" not in cleaned.lower() or "[REDACTED]" in cleaned

    def test_sanitize_output_strips_control_tokens(self) -> None:
        store = InMemoryStore()
        agent = ContractReviewAgent(agent_id="test", memory=store)

        dirty = "Analysis <|im_start|> leaked <|im_end|>"
        cleaned = agent._sanitize_output(dirty)
        assert "<|im_start|>" not in cleaned
        assert "<|im_end|>" not in cleaned

    def test_sanitize_output_preserves_normal_text(self) -> None:
        store = InMemoryStore()
        agent = ContractReviewAgent(agent_id="test", memory=store)

        normal = "The contract has three key risks."
        assert agent._sanitize_output(normal) == normal

    def test_agent_info(self) -> None:
        store = InMemoryStore()
        agent = ContractReviewAgent(agent_id="cr-1", memory=store)
        info = agent.info
        assert info.agent_id == "cr-1"
        assert info.agent_type == "contract_review"
        assert info.description
        assert info.status == "active"
