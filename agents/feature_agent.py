"""
Feature Agent — checks feature availability, docs, configuration, and limits.
"""
from __future__ import annotations

from agents.base_agent import BaseAgent
from agents.llm_factory import get_llm
from memory.state_schema import GraphState


class FeatureAgent(BaseAgent):

    def get_system_prompt(self, state: GraphState) -> str:
        return (
            "You are the Feature Agent for TechCorp customer support.\n"
            "Your job is to investigate feature-related questions.\n\n"
            "Use your tools to:\n"
            "- Check the feature matrix to see what's available per plan\n"
            "- Pull up feature documentation for details\n"
            "- Validate any configuration the customer mentions\n"
            "- Check feature limits (quotas, rate limits, etc.)\n\n"
            "Be specific about which plan tiers include which features. "
            "If something isn't available on the customer's plan, say so "
            "clearly and mention which plan they'd need.\n\n"
            "If a tool fails, note the error and keep working."
        )


def feature_agent_node(state: GraphState) -> dict:
    from tools.feature_tools import feature_tools

    llm = get_llm()
    agent = FeatureAgent(llm=llm, tools=feature_tools, agent_name="feature_agent")
    return agent.invoke(state)
