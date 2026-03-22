"""
Account Agent — digs into customer profile, plan, billing, and enabled features.
"""
from __future__ import annotations

from agents.base_agent import BaseAgent
from agents.llm_factory import get_llm
from memory.state_schema import GraphState
from tools.account_tools import account_tools


class AccountAgent(BaseAgent):

    def get_system_prompt(self, state: GraphState) -> str:
        return (
            "You are the Account Agent for TechCorp customer support.\n"
            "Your job is to investigate the customer's account details.\n"
            "Use your tools to look up their profile, billing history, "
            "account status, and which features they have enabled.\n\n"
            "Focus on facts that are relevant to the customer's query. "
            "If a tool call fails, note the error and keep going with "
            "whatever data you have — partial info is better than nothing.\n\n"
            "Summarize your findings clearly at the end."
        )


def account_agent_node(state: GraphState) -> dict:
    llm = get_llm()
    agent = AccountAgent(llm=llm, tools=account_tools, agent_name="account_agent")
    return agent.invoke(state)
