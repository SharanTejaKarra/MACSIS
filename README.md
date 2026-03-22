# MACSIS — MultiAgent Customer Support Intelligence System

A multi-agent system built on LangGraph that routes customer support queries through specialist agents, detects conflicts in information, and escalates issues when needed. Built as a practical demonstration of agent orchestration patterns for support automation.

## Architecture

The system uses a fan-out/fan-in graph where an orchestrator classifies the query, dispatches specialist agents in parallel, synthesizes their findings, and decides whether to escalate or respond directly.

```
                     ┌───────────┐
                     │   START   │
                     └─────┬─────┘
                           │
                ┌──────────▼──────────┐
                │ orchestrator_analyze │
                │  (classify + plan)  │
                └──────────┬──────────┘
                           │
           ┌───────────────┼───────────────┐
           │               │               │
  ┌────────▼────────┐ ┌───▼──────────┐ ┌──▼───────────┐
  │  account_agent  │ │ feature_agent│ │contract_agent│
  │ (profile/plan)  │ │ (docs/limits)│ │ (SLA/terms)  │
  └────────┬────────┘ └───┬──────────┘ └──┬───────────┘
           │               │               │
           └───────────────┼───────────────┘
                           │
              ┌────────────▼────────────┐
              │ orchestrator_synthesize │
              │ (merge + conflict check)│
              └────────────┬────────────┘
                           │
                needs escalation?
                    /          \
                  yes           no
                  /               \
    ┌────────────▼───────────┐     │
    │    escalation_agent    │     │
    │  (severity + route)    │     │
    └────────────┬───────────┘     │
                 │                 │
                 └────────┬────────┘
                          │
              ┌───────────▼───────────┐
              │  orchestrator_respond  │
              │    (final answer)      │
              └───────────┬───────────┘
                          │
                     ┌────▼────┐
                     │   END   │
                     └─────────┘
```

The orchestrator decides which agents to invoke based on query classification. Not every query needs all three specialists — a simple feature question might only trigger the feature agent, while an SLA complaint goes to the contract agent and account agent both.

## Setup

1. **Clone the repo**
   ```bash
   git clone <repo-url>
   cd MACSIS
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure your LLM provider**

   The system supports both cloud (OpenAI) and local (Ollama) backends. Edit `config.yaml`:

   **Option A — Local with Ollama (no API key needed):**
   ```bash
   brew install ollama
   ollama serve                # start the server
   ollama pull qwen3:8b        # download the model (~5GB)
   ```
   In `config.yaml`:
   ```yaml
   llm:
     provider: "ollama"
     model: "qwen3:8b"
   ```

   **Option B — OpenAI:**
   ```bash
   cp .env.example .env
   # Add your OPENAI_API_KEY to .env
   ```
   In `config.yaml`:
   ```yaml
   llm:
     provider: "openai"
     model: "gpt-4o-mini"
   ```

   Langfuse keys are optional — the system works fine without them.

5. **Run**
   ```bash
   python main.py --scenario 1
   ```

## Usage

```bash
# Run a single custom query
python main.py --query "How do I enable dark mode?" --customer-id CUST-002

# Run a specific test scenario (1-5)
python main.py --scenario 3

# Run all 5 scenarios and save results to results/query_results.json
python main.py --all-scenarios
```

## Running Tests

```bash
# All tests (no API key needed for unit tests)
pytest tests/ -v

# Just the tool tests
pytest tests/test_tools.py -v

# Include end-to-end tests (requires OPENAI_API_KEY)
OPENAI_API_KEY=sk-... pytest tests/ -v
```

## Project Structure

```
MACSIS/
├── main.py                     # CLI entry point, scenario definitions
├── config.yaml                 # LLM and tool configuration
├── requirements.txt
├── .env.example
│
├── agents/
│   ├── llm_factory.py          # LLM provider switch (OpenAI / Ollama)
│   ├── base_agent.py           # Base class with tool-calling loop
│   ├── orchestrator.py         # Analyze, synthesize, and respond nodes
│   ├── account_agent.py        # Customer profile and billing specialist
│   ├── feature_agent.py        # Feature availability and docs specialist
│   ├── contract_agent.py       # SLA and contract terms specialist
│   └── escalation_agent.py     # Severity assessment and routing
│
├── graph/
│   ├── builder.py              # Constructs and compiles the StateGraph
│   └── routing.py              # Conditional edge functions (fan-out, escalation)
│
├── memory/
│   ├── state_schema.py         # GraphState TypedDict and dataclasses
│   ├── state_manager.py        # Helpers for reading/querying state
│   └── shared_context.py       # Builds context strings for agent prompts
│
├── mock_data/
│   ├── customers.py            # 4 customer accounts (starter to enterprise)
│   ├── features.py             # Feature matrix, limits, docs, pricing
│   ├── contracts.py            # SLA terms for pro and enterprise
│   └── escalations.py          # Routing rules and ticket storage
│
├── tools/
│   ├── tool_base.py            # Failure simulation decorator
│   ├── account_tools.py        # 4 tools: lookup, billing, status, features
│   ├── feature_tools.py        # 4 tools: matrix, docs, config, limits
│   ├── contract_tools.py       # 4 tools: lookup, terms, SLA check, features
│   └── escalation_tools.py     # 4 tools: create ticket, routing, notify, log
│
├── monitoring/
│   ├── token_tracker.py        # Aggregation and reporting for token usage
│   ├── langfuse_config.py      # Optional Langfuse integration
│   ├── tracing_utils.py        # Trace decorators
│   └── metrics.py              # Scenario completion logging
│
├── tests/
│   ├── test_tools.py           # Unit tests for all 16 mock tools
│   ├── test_token_tracker.py   # TokenTracker aggregation tests
│   ├── test_agents.py          # Agent node tests with mocked LLM
│   ├── test_graph.py           # Graph compilation and execution tests
│   └── test_scenarios.py       # Scenario structure + optional E2E tests
│
└── results/
    └── analysis.md             # Post-run analysis template
```

## Design Decisions

**LangGraph over CrewAI** — LangGraph gives fine-grained control over the execution graph. We needed conditional edges (the orchestrator decides which agents to invoke), fan-out/fan-in parallelism, and typed state that flows through every node. CrewAI abstracts too much of this away.

**Fan-out/fan-in for parallel execution** — When the orchestrator determines multiple specialists are needed, they run in parallel. A query about SLA violations might trigger both the account agent (to check the customer's tier) and the contract agent (to look up SLA terms) simultaneously.

**Append-only findings with reducers** — Each agent appends its findings to a shared list using LangGraph's reducer pattern. No agent can overwrite another's work. This makes the data flow predictable and easy to debug.

**TokenTracker for observability** — Every LLM call records input/output tokens tagged with the agent name. The tracker aggregates this into per-agent breakdowns and totals, printed after every run.

**Graceful Langfuse fallback** — Langfuse integration is nice-to-have, not a hard dependency. If the keys aren't set or the service is down, the system logs a warning and keeps running.

**Intentional data contradictions** — The mock data has a deliberate inconsistency: the API access feature documentation claims "unlimited API calls" for the Pro plan, but the actual limits are 50,000/month. This tests whether the system can detect and surface conflicts between different data sources.

## Test Scenarios

| # | Name | Customer | What It Tests |
|---|------|----------|---------------|
| 1 | Basic Feature Question | CUST-002 (Pro) | Simple feature lookup — dark mode setup |
| 2 | Plan-to-Feature Mismatch | CUST-001 (Starter) | Customer wants API access but their plan doesn't include it |
| 3 | Contradictory Information | CUST-002 (Pro) | Docs say unlimited API calls, actual limit is 50k/mo |
| 4 | SLA Violation | CUST-003 (Enterprise) | 10-day wait on a 24-hour SLA with penalty clauses |
| 5 | Account Configuration Help | CUST-004 (Professional) | Migration from competitor, all seats used, needs more |

## Token Tracking

Every node in the graph logs its token usage. After each run, you get a table like:

```
+------------------------+-------+--------+-------+-------+
| Agent                  | Input | Output | Total | Calls |
+------------------------+-------+--------+-------+-------+
| account_agent          |  1200 |    350 |  1550 |     2 |
| feature_agent          |   900 |    280 |  1180 |     1 |
| orchestrator_analyze   |   500 |    120 |   620 |     1 |
| orchestrator_respond   |  1800 |    450 |  2250 |     1 |
| orchestrator_synthesize|  1400 |    200 |  1600 |     1 |
+------------------------+-------+--------+-------+-------+
| TOTAL                  |  5800 |   1400 |  7200 |     6 |
+------------------------+-------+--------+-------+-------+
```

Use `--all-scenarios` to get a full breakdown saved to `results/query_results.json`.

## Known Limitations

- **Mock tools with simulated data** — The tools return hardcoded data from the mock_data modules. In production these would hit real databases and APIs.
- **Single-phase investigation** — Each specialist agent runs once. There's no multi-round loop where agents can ask follow-up questions or request more data from each other.
- **No persistent conversation memory** — Each query is stateless. The system doesn't remember past interactions with the same customer.
- **Fixed "now" timestamp** — SLA compliance checks use a hardcoded current time (2026-03-22T12:00:00) for deterministic behavior. A real system would use the actual clock.
- **Random tool failures** — Tools have a 5% simulated failure rate. This is good for testing resilience but means runs aren't perfectly reproducible unless you mock `random`.
