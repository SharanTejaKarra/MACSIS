"""
Contract Agent — reviews contracts, SLA terms, and compliance.
"""
from __future__ import annotations

from agents.base_agent import BaseAgent
from agents.llm_factory import get_llm
from memory.state_schema import GraphState
from tools.contract_tools import contract_tools


class ContractAgent(BaseAgent):

    def get_system_prompt(self, state: GraphState) -> str:
        return (
            "You are the Contract Agent for TechCorp customer support.\n"
            "Your job is to investigate contract and SLA-related questions.\n\n"
            "Use your tools to:\n"
            "- Look up the customer's contract (if they have one)\n"
            "- Review specific contract terms\n"
            "- Validate SLA compliance — check uptime, response time guarantees\n"
            "- List features that are contractually included\n\n"
            "Pay attention to the difference between what's in the contract "
            "vs what's actually enabled. Flag any discrepancies.\n\n"
            "Customers without a contract_id are on self-serve plans and "
            "don't have custom SLA terms — note this if relevant.\n\n"
            "If a tool fails, note the error and keep working."
        )


def contract_agent_node(state: GraphState) -> dict:
    llm = get_llm()
    agent = ContractAgent(llm=llm, tools=contract_tools, agent_name="contract_agent")
    return agent.invoke(state)
