"""
MACSIS — MultiAgent Customer Support Intelligence System

Usage:
    python main.py --query "How do I enable dark mode?"
    python main.py --query "..." --customer-id CUST-002
    python main.py --scenario 3
    python main.py --all-scenarios
"""
import argparse
import json
import logging
import os
import sys
import time

import yaml
from dotenv import load_dotenv

from memory.state_schema import GraphState
from monitoring.langfuse_config import init_langfuse, flush as langfuse_flush
from monitoring.token_tracker import TokenTracker
from monitoring.metrics import log_scenario_complete
from graph.builder import build_graph
from agents.orchestrator import (
    orchestrator_analyze_node,
    orchestrator_synthesize_node,
    orchestrator_respond_node,
)
from agents.account_agent import account_agent_node
from agents.feature_agent import feature_agent_node
from agents.contract_agent import contract_agent_node
from agents.escalation_agent import escalation_agent_node


# predefined scenarios from the spec
SCENARIOS = {
    "1": {
        "name": "Basic Feature Question",
        "query": "How do I enable dark mode in my account?",
        "customer_id": "CUST-002",
    },
    "2": {
        "name": "Plan-to-Feature Mismatch",
        "query": (
            "I'm on the Starter plan, but I need to integrate with your API "
            "for my automation workflow. What are my options?"
        ),
        "customer_id": "CUST-001",
    },
    "3": {
        "name": "Contradictory Information",
        "query": (
            "Your documentation says the Pro plan includes unlimited API calls, "
            "but I'm seeing rate limit errors after 1000 calls/month. I've checked "
            "my account and it shows Pro. Is this a bug, or am I misunderstanding something?"
        ),
        "customer_id": "CUST-002",
    },
    "4": {
        "name": "SLA Violation",
        "query": (
            "I've been waiting for support response for 10 days on a critical "
            "production issue. My company has a contract with a 24-hour SLA guarantee. "
            "This is now costing us $500/day in lost revenue. I have my contract terms "
            "saved. Please verify if the SLA was violated and escalate this immediately."
        ),
        "customer_id": "CUST-003",
    },
    "5": {
        "name": "Account Configuration Help",
        "query": (
            "Our company just migrated from the competitor platform. We have 15 users, "
            "but the plan shows only 10 seats. Can you help me understand the licensing "
            "model and figure out how to set up all our users?"
        ),
        "customer_id": "CUST-004",
    },
}


def setup_logging(level: str = "INFO"):
    fmt = "%(asctime)s [%(name)s] %(levelname)s: %(message)s"
    logging.basicConfig(level=getattr(logging, level.upper(), logging.INFO), format=fmt)
    # shush noisy libs
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)


def build_initial_state(query: str, customer_id: str, scenario_id: str = "") -> dict:
    """Empty graph state with the query filled in."""
    return {
        "customer_query": query,
        "customer_id": customer_id,
        "scenario_id": scenario_id,
        "messages": [],
        "query_classification": "",
        "investigation_plan": [],
        "current_phase": "analyzing",
        "findings": [],
        "escalation_decision": None,
        "final_response": "",
        "internal_reasoning": "",
        "token_usage_log": [],
        "errors": [],
    }


def run_query(graph, query: str, customer_id: str, scenario_id: str = "") -> dict:
    """Run one query end-to-end and print results."""
    initial_state = build_initial_state(query, customer_id, scenario_id)
    start_time = time.time()

    print(f"\n{'=' * 70}")
    print(f"Query: {query}")
    print(f"Customer: {customer_id}")
    print(f"{'=' * 70}\n")

    final_state = graph.invoke(initial_state)
    elapsed = time.time() - start_time

    # customer-facing response
    print(f"\n{'─' * 70}")
    print("RESPONSE:")
    print(f"{'─' * 70}")
    print(final_state.get("final_response", "(no response generated)"))

    # internal reasoning
    reasoning = final_state.get("internal_reasoning", "")
    if reasoning:
        print(f"\n{'─' * 70}")
        print("INTERNAL REASONING:")
        print(f"{'─' * 70}")
        print(reasoning)

    # escalation info
    escalation = final_state.get("escalation_decision")
    if escalation and escalation.should_escalate:
        print(f"\n{'─' * 70}")
        print("ESCALATION:")
        print(f"{'─' * 70}")
        print(f"  Severity: {escalation.severity}")
        print(f"  Reason: {escalation.reason}")
        print(f"  Ticket: {escalation.ticket_id}")
        print(f"  Routed to: {escalation.routed_to}")

    # token breakdown
    tracker = TokenTracker(final_state.get("token_usage_log", []))
    print(f"\n{'─' * 70}")
    print("TOKEN USAGE:")
    print(f"{'─' * 70}")
    print(tracker.summary_table())
    print(f"\nTotal time: {elapsed:.2f}s")

    # monitoring
    log_scenario_complete(scenario_id, elapsed, tracker.to_dict())

    return final_state


def run_all_scenarios(graph) -> list[dict]:
    """Run all test scenarios and dump results to JSON."""
    results = []

    for scenario_id, scenario in SCENARIOS.items():
        print(f"\n\n{'#' * 70}")
        print(f"  SCENARIO {scenario_id}: {scenario['name']}")
        print(f"{'#' * 70}")

        final_state = run_query(
            graph,
            query=scenario["query"],
            customer_id=scenario["customer_id"],
            scenario_id=f"scenario_{scenario_id}",
        )

        tracker = TokenTracker(final_state.get("token_usage_log", []))
        escalation = final_state.get("escalation_decision")

        result = {
            "scenario_id": scenario_id,
            "scenario_name": scenario["name"],
            "query": scenario["query"],
            "customer_id": scenario["customer_id"],
            "query_classification": final_state.get("query_classification", ""),
            "final_response": final_state.get("final_response", ""),
            "internal_reasoning": final_state.get("internal_reasoning", ""),
            "escalation": {
                "triggered": escalation.should_escalate if escalation else False,
                "severity": escalation.severity if escalation else None,
                "ticket_id": escalation.ticket_id if escalation else None,
                "routed_to": escalation.routed_to if escalation else None,
                "reason": escalation.reason if escalation else None,
            },
            "agents_invoked": list({
                f.agent_name for f in final_state.get("findings", [])
            }),
            "token_usage": tracker.to_dict(),
        }
        results.append(result)

    # save results
    os.makedirs("results", exist_ok=True)
    output_path = "results/query_results.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n\nResults saved to {output_path}")

    # print grand summary
    print(f"\n\n{'=' * 70}")
    print("GRAND SUMMARY")
    print(f"{'=' * 70}")
    for r in results:
        tokens = r["token_usage"]["total"]
        esc = "YES" if r["escalation"]["triggered"] else "no"
        print(
            f"  Scenario {r['scenario_id']} ({r['scenario_name']}): "
            f"{tokens['total_tokens']} tokens, "
            f"{tokens['num_llm_calls']} LLM calls, "
            f"escalation={esc}"
        )

    return results


def main():
    load_dotenv()

    # load config
    with open("config.yaml") as f:
        config = yaml.safe_load(f)

    setup_logging(config.get("logging", {}).get("level", "INFO"))
    logger = logging.getLogger("macsis.main")

    # langfuse (graceful fallback if not configured)
    init_langfuse()

    # build the graph
    graph = build_graph(
        orchestrator_analyze_fn=orchestrator_analyze_node,
        orchestrator_synthesize_fn=orchestrator_synthesize_node,
        orchestrator_respond_fn=orchestrator_respond_node,
        account_agent_fn=account_agent_node,
        feature_agent_fn=feature_agent_node,
        contract_agent_fn=contract_agent_node,
        escalation_agent_fn=escalation_agent_node,
    )

    # parse CLI args
    parser = argparse.ArgumentParser(description="MACSIS Customer Support System")
    parser.add_argument("--query", type=str, help="Customer query to process")
    parser.add_argument("--customer-id", type=str, default="CUST-002", help="Customer ID")
    parser.add_argument("--scenario", type=str, choices=["1", "2", "3", "4", "5"],
                        help="Run a predefined test scenario")
    parser.add_argument("--all-scenarios", action="store_true",
                        help="Run all 5 test scenarios and save results")
    args = parser.parse_args()

    if args.all_scenarios:
        run_all_scenarios(graph)
    elif args.scenario:
        scenario = SCENARIOS[args.scenario]
        run_query(
            graph,
            query=scenario["query"],
            customer_id=scenario["customer_id"],
            scenario_id=f"scenario_{args.scenario}",
        )
    elif args.query:
        run_query(graph, query=args.query, customer_id=args.customer_id)
    else:
        parser.print_help()
        sys.exit(1)

    # flush langfuse
    langfuse_flush()


if __name__ == "__main__":
    main()
