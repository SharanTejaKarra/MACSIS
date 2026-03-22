# Week 3 Capstone: MultiAgent Customer Support Intelligence System

**Duration:** 72 hours (Friday Evening → Monday)
**Technology Stack:** LangGraph OR CrewAI + Langfuse
**Scope:** Pure Agentic AI (No Traditional ML, No DL, No Multimodal)

---

## 🏢 Business Problem

You are building an intelligent customer support system for **TechCorp**, a SaaS platform. The company receives complex customer queries that require investigation across multiple domains and intelligent decision-making about when to escalate to human agents.

Unlike traditional FAQ systems or single-agent chatbots, this system must:

- Investigate issues systematically across multiple sources
- Coordinate findings between specialized agents
- Maintain context throughout the entire investigation
- Synthesize conflicting information intelligently
- Make informed escalation decisions
- Provide transparent reasoning for all actions

---

## 🎯 Core Challenge

Build a multi-agent system that handles real-world customer support scenarios where:

1. **Problems are multi-domain** - answering requires checking customer account, feature availability, contract terms, and business rules
2. **Information can conflict** - customer documentation might say one thing, but their account shows another
3. **Context matters** - decisions from one agent should inform what other agents investigate
4. **Escalation is nuanced** - not all issues are simple, and some need human intervention based on specific criteria
5. **Reasoning must be observable** - you need to see why agents made specific decisions

---

## ⚙️ System Requirements

### 1. Multi-Agent Architecture

You must implement at least **5 agents**:

#### Agent 1: Orchestrator / Supervisor Agent

- Receives the initial customer query
- Analyzes the query to understand what information is needed
- Creates a plan for which agents to invoke and in what order
- Routes the query to appropriate specialized agents
- Synthesizes findings from multiple agents
- Makes the final decision (resolve or escalate)
- Coordinates agent interactions

#### Agent 2: Account Agent

- Investigates customer account information
- Retrieves subscription tier and plan details
- Looks up billing history
- Checks account status and features enabled
- Provides account context to other agents
- Must access account database tools

#### Agent 3: Feature Agent

- Checks feature availability across different plans
- Retrieves feature documentation
- Validates configuration and setup requirements
- Explains feature capabilities and limitations
- Compares feature entitlements vs. actual usage
- Must access feature matrix tools

#### Agent 4: Contract Agent

- Retrieves and reviews customer contracts
- Validates service level agreements (SLAs)
- Checks feature entitlements in contract
- Identifies contract terms and pricing
- Determines if violations have occurred
- Must access contract database tools

#### Agent 5: Escalation Agent

- Determines if human intervention is required
- Applies escalation logic (severity, SLA violations, special cases)
- Creates escalation tickets
- Routes to appropriate human team
- Provides clear reasoning for escalation decision
- Must integrate with escalation service

---

### 2. Shared Memory System

Implement a memory layer that agents share:

- **Conversation History** - maintain full chat history
- **Agent Findings** - each agent logs what it discovered
- **Decision State** - track key decisions and reasoning
- **Context Data** - shared information that multiple agents need
- **Investigation Progress** - what has been checked, what remains

**Requirements:**

- Agents can access findings from other agents
- Memory persists across multiple agent invocations
- Memory is efficiently managed (context windows have limits)
- State can be traced and understood

---

### 3. Tool Integration

Each agent must have realistic mock tools to call:

#### Account Agent Tools:

- `lookup_customer(customer_id)` - fetch customer profile
- `get_billing_history(customer_id)` - retrieve billing records
- `check_account_status(customer_id)` - verify account status
- `list_enabled_features(customer_id)` - get features enabled for customer

#### Feature Agent Tools:

- `get_feature_matrix()` - check availability per plan
- `get_feature_documentation(feature_name)` - fetch setup docs
- `validate_configuration(feature, customer_config)` - check if configured correctly
- `check_feature_limits(feature, plan)` - get rate limits and caps

#### Contract Agent Tools:

- `lookup_contract(contract_id)` - fetch contract details
- `get_contract_terms(contract_id)` - retrieve specific terms
- `validate_sla_compliance(contract_id, issue_date)` - check SLA violations
- `get_included_features(contract_id)` - list contract entitlements

#### Escalation Agent Tools:

- `create_escalation_ticket(reason, priority, context)` - create ticket
- `get_escalation_routing(issue_type)` - determine routing
- `notify_support_team(ticket_id)` - alert team
- `log_escalation_reason(ticket_id, reason)` - document why

#### Tool Behavior Requirements:

- Tools have realistic latency (not instant)
- Tools can fail (database timeout, network error)
- Tools can return incomplete or ambiguous data
- Tools should log their calls for observability
- Agents must handle tool failures gracefully

---

### 4. Orchestration & Planning

The system must demonstrate sophisticated orchestration:

- **Intelligent Routing** - not simple if-else chains; agents are routed based on query analysis
- **Sequential vs. Parallel** - decide which agents can run in parallel vs. must be sequential
- **Dependency Management** - some agents depend on findings from others
- **Conflict Resolution** - when agents find conflicting information, system resolves it
- **Adaptive Planning** - if one agent fails or returns unexpected data, orchestrator adapts
- **Reason Tracking** - log why each agent was invoked and what triggered the routing decision

---

### 5. Memory & State Management

Implement sophisticated memory handling:

- **Conversation Persistence** - maintain chat history across calls
- **Context Optimization** - remember what matters, forget what doesn't
- **Cross-Agent State Sharing** - agents must access findings from other agents
- **Decision Tracking** - record what was decided and why
- **Recovery from Failure** - if an agent fails, memory should capture this
- **Memory Efficiency** - prevent context explosion in long conversations

---

### 6. Error Handling & Resilience

System must gracefully handle failures:

- **Tool Failures** - what happens if a database call fails?
- **Incomplete Data** - what if a tool returns partial results?
- **Contradictions** - what if agents find conflicting information?
- **Agent Failures** - what if an agent crashes or times out?
- **Retry Logic** - should you retry failed tools?
- **Fallback Strategies** - what's your backup plan?

---

### 7. Monitoring with Langfuse

Implement comprehensive observability:

- **Agent Invocation Traces** - see when/why each agent was called
- **Tool Call Logging** - record all tool invocations, inputs, outputs
- **Decision Point Tracking** - log key decisions and their reasoning
- **Error Context** - when something fails, log full context
- **Performance Metrics** - track latency, token usage, costs
- **Custom Events** - log domain-specific information (escalation triggers, conflicts, etc.)

#### Langfuse Requirements:

- All agent calls must be traced
- Tool invocations must be visible
- Decision points must be logged with reasoning
- Errors must be captured with context
- You must be able to reconstruct the full execution flow from traces

---

## 🧪 Test Scenarios

You will be evaluated on your system's ability to handle these real-world scenarios:

### Scenario 1: Basic Feature Question

**Query:** "How do I enable dark mode in my account?"

**Characteristics:**

- Straightforward question
- Single domain (features)
- Quick resolution expected
- Low complexity

**What Your System Should Do:**

- Route to Feature Agent
- Return configuration instructions
- No escalation needed

---

### Scenario 2: Plan-to-Feature Mismatch

**Query:** "I'm on the Starter plan, but I need to integrate with your API for my automation workflow. What are my options?"

**Characteristics:**

- Multiple domains (account + features)
- Requires plan checking
- May suggest upgrade
- Medium complexity

**What Your System Should Do:**

- Check current plan (Account Agent)
- Check feature availability (Feature Agent)
- Synthesize: API not available on Starter
- Suggest plan upgrade or recommend alternative
- No escalation unless customer has special agreement

---

### Scenario 3: Contradictory Information

**Query:** "Your documentation says the Pro plan includes unlimited API calls, but I'm seeing rate limit errors after 1000 calls/month. I've checked my account and it shows Pro. Is this a bug, or am I misunderstanding something?"

**Characteristics:**

- Contradictory information (docs vs. actual behavior)
- Multiple domains (account + features + contract)
- Requires investigation
- Needs conflict resolution
- High complexity

**What Your System Should Do:**

- Verify account is actually Pro (Account Agent)
- Check documentation and feature limits (Feature Agent)
- Review contract for actual entitlements (Contract Agent)
- Identify the contradiction
- Determine root cause (bug, misconfiguration, documentation error, special terms)
- Either resolve with accurate information or escalate if it's a real bug

---

### Scenario 4: SLA Violation

**Query:** "I've been waiting for support response for 10 days on a critical production issue. My company has a contract with a 24-hour SLA guarantee. This is now costing us $500/day in lost revenue. I have my contract terms saved. Please verify if the SLA was violated and escalate this immediately."

**Characteristics:**

- Contract validation needed
- SLA compliance check
- Clear escalation trigger
- High severity
- Requires contract review
- High complexity

**What Your System Should Do:**

- Retrieve and validate contract (Contract Agent)
- Check SLA terms and dates
- Calculate if SLA was violated
- Determine escalation priority (urgent)
- Create escalation ticket immediately
- Log clear reasoning for escalation

---

### Scenario 5: Account Configuration Help

**Query:** "Our company just migrated from the competitor platform. We have 15 users, but the plan shows only 10 seats. Can you help me understand the licensing model and figure out how to set up all our users?"

**Characteristics:**

- Account analysis
- Feature explanation
- Potential upgrade suggestion
- Configuration guidance
- Medium complexity

**What Your System Should Do:**

- Review current plan and seat allocation (Account Agent)
- Explain licensing model (Feature Agent)
- Identify seat shortage
- Suggest upgrade path
- Provide setup guidance
- May offer to escalate to onboarding specialist

---

## 📦 Expected Deliverables

```
your_submission/
│
├── main.py (or main entry point)
│   Entry point that demonstrates your system
│   Should be runnable: python main.py --query "sample query"
│
├── README.md
│   Explain your approach and architecture
│   How to setup and run your system
│   Key design decisions and why you made them
│   Known limitations or areas for improvement
│
├── agents/
│   ├── orchestrator.py (or orchestrator_agent.py)
│   ├── account_agent.py
│   ├── feature_agent.py
│   ├── contract_agent.py
│   ├── escalation_agent.py
│   └── base_agent.py (shared base class/interface)
│
├── tools/
│   ├── account_tools.py (mock customer database)
│   ├── feature_tools.py (mock feature matrix)
│   ├── contract_tools.py (mock contract service)
│   ├── escalation_tools.py (mock escalation service)
│   └── tool_base.py (shared tool interface)
│
├── memory/
│   ├── conversation_memory.py
│   ├── state_manager.py
│   └── shared_context.py
│
├── monitoring/
│   ├── langfuse_config.py (setup and configuration)
│   ├── tracing_utils.py (helper functions)
│   └── metrics.py (custom metrics/events)
│
├── config.yaml (or config.json)
│   Configuration settings
│   LLM model choice
│   API keys/configuration
│
├── requirements.txt
│   Python dependencies
│   Include: langchain, langgraph (or crewai), langfuse, etc.
│
├── tests/ (optional but encouraged)
│   Unit tests or integration tests
│   Shows your testing approach
│
└── results/
    ├── query_results.json
    │   Results from running 5 test scenarios
    │   Show what your system outputs
    │
    ├── langfuse_export.json (or traces folder)
    │   Export of your Langfuse traces
    │   Shows how your system executed
    │
    └── analysis.md
        Your analysis of what you built
        Key findings about your system
        What you'd improve
        Learnings from the process
```