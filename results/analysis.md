# MACSIS Analysis

Post-run analysis template. Fill this in after running `python main.py --all-scenarios`.

## System Performance

### Token Usage Summary

| Metric | Value |
|--------|-------|
| Total tokens across all scenarios | |
| Total LLM calls | |
| Average tokens per scenario | |
| Most expensive scenario | |
| Cheapest scenario | |

### Per-Scenario Breakdown

#### Scenario 1: Basic Feature Question
- **Tokens used:**
- **Agents invoked:**
- **Escalation triggered:** No (expected)
- **Response quality:** Did the system correctly explain dark mode setup for a Pro user?

#### Scenario 2: Plan-to-Feature Mismatch
- **Tokens used:**
- **Agents invoked:**
- **Escalation triggered:**
- **Response quality:** Did it correctly identify that Starter plan lacks API access? Did it suggest upgrade options?

#### Scenario 3: Contradictory Information
- **Tokens used:**
- **Agents invoked:**
- **Escalation triggered:**
- **Response quality:** Did the system detect the contradiction between "unlimited API calls" in docs vs the actual 50k/month limit?

#### Scenario 4: SLA Violation
- **Tokens used:**
- **Agents invoked:**
- **Escalation triggered:** Yes (expected)
- **Response quality:** Did it calculate the SLA breach correctly? Did it reference the penalty clause? Was the escalation routed to the right team?

#### Scenario 5: Account Configuration Help
- **Tokens used:**
- **Agents invoked:**
- **Escalation triggered:**
- **Response quality:** Did it identify the seat capacity problem (10/10 used, needs 15)? Did it suggest how to add more seats?

## Key Findings

### Conflict Resolution (Scenario 3)

How did the system handle the API docs contradiction?

- Did the orchestrator classify this correctly as a "contradiction" type?
- Did both the feature agent and account agent get invoked?
- Did the synthesize step detect the conflict between public docs ("unlimited") and actual limits (50k/month)?
- Was the response honest about the discrepancy?

### Escalation Logic (Scenario 4)

How was the SLA violation detected and escalated?

- Did the contract agent correctly calculate the elapsed time vs SLA window?
- Was the penalty clause from special_terms surfaced?
- What severity did the escalation agent assign? (Expected: critical)
- Where was it routed? (Expected: legal_compliance or customer_success)
- Was a ticket ID generated?

### Agent Coordination

- How many agents were invoked per scenario on average?
- Did the orchestrator make reasonable routing decisions?
- Were there any cases where an unnecessary agent was invoked?
- Were there cases where a needed agent was skipped?

## What Worked Well

-
-
-

## What Could Be Improved

-
-
-

## Lessons Learned

-
-
-
