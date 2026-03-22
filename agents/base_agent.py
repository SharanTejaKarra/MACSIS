"""Base agent — LLM + tool loop + token tracking."""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

from langchain_core.messages import SystemMessage, HumanMessage
from memory.state_schema import GraphState, AgentFinding, TokenUsage, InvestigationStep
from memory.shared_context import build_context_for_agent, get_customer_id

logger = logging.getLogger("macsis.agents")


class BaseAgent(ABC):

    def __init__(self, llm, tools: list, agent_name: str):
        self.llm = llm
        self.tools = tools
        self.agent_name = agent_name
        # bind tools so the LLM can call them
        self.llm_with_tools = llm.bind_tools(tools) if tools else llm

    @abstractmethod
    def get_system_prompt(self, state: GraphState) -> str:
        """Subclasses define their own system prompt."""
        ...

    def invoke(self, state: GraphState) -> dict:
        """Run the agent: prompt -> tool loop -> return state delta."""
        context = build_context_for_agent(state, self.agent_name)
        system_prompt = self.get_system_prompt(state)
        customer_id = get_customer_id(state)

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=(
                f"Customer ID: {customer_id}\n"
                f"Query: {state['customer_query']}\n\n"
                f"Context from other agents:\n{context}"
            )),
        ]

        # tool loop — keep going until the LLM stops requesting tools
        all_tool_calls = []
        tool_results = {}
        total_input_tokens = 0
        total_output_tokens = 0
        model_name = ""
        max_iterations = 6

        for _ in range(max_iterations):
            response = self.llm_with_tools.invoke(messages)

            # track tokens
            usage = getattr(response, "usage_metadata", None) or {}
            total_input_tokens += usage.get("input_tokens", 0)
            total_output_tokens += usage.get("output_tokens", 0)
            model_name = (
                getattr(response, "response_metadata", {}).get("model_name", "")
                or model_name
            )

            # if no tool calls, we're done
            if not response.tool_calls:
                break

            messages.append(response)

            # execute each tool call
            for tc in response.tool_calls:
                tool_name = tc["name"]
                tool_args = tc["args"]
                all_tool_calls.append(tool_name)

                result = self._run_tool(tool_name, tool_args)
                tool_results[tool_name] = result

                # feed tool result back to the LLM
                from langchain_core.messages import ToolMessage
                messages.append(
                    ToolMessage(content=str(result), tool_call_id=tc["id"])
                )
        else:
            logger.warning(f"[{self.agent_name}] hit max iterations in tool loop")

        # build the finding
        finding = AgentFinding(
            agent_name=self.agent_name,
            summary=response.content if hasattr(response, "content") else str(response),
            raw_data=tool_results,
            tool_calls_made=all_tool_calls,
        )

        # mark step done
        updated_step = InvestigationStep(
            agent_name=self.agent_name,
            reason="completed",
            status="completed",
        )

        token_record = TokenUsage(
            agent_name=self.agent_name,
            input_tokens=total_input_tokens,
            output_tokens=total_output_tokens,
            model=model_name,
        )

        return {
            "findings": [finding],
            "investigation_plan": [updated_step],
            "token_usage_log": [token_record],
        }

    def _run_tool(self, tool_name: str, tool_args: dict) -> Any:
        """Look up and call a tool by name."""
        for tool in self.tools:
            if tool.name == tool_name:
                try:
                    return tool.invoke(tool_args)
                except Exception as e:
                    logger.error(f"[{self.agent_name}] tool {tool_name} failed: {e}")
                    return f"Error: {e}"

        return f"Error: tool '{tool_name}' not found"
