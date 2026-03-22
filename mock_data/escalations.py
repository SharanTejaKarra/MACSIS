"""Routing rules and runtime ticket storage (mutable — tools write here)."""

ROUTING_RULES = {
    "billing": {
        "team": "billing_support",
        "default_priority": "medium",
        "description": "Payment failures, invoice disputes, refund requests",
    },
    "technical": {
        "team": "engineering_support",
        "default_priority": "high",
        "description": "API errors, integration failures, platform bugs",
    },
    "account": {
        "team": "account_management",
        "default_priority": "medium",
        "description": "Plan changes, seat adjustments, account access issues",
    },
    "sla_violation": {
        "team": "customer_success",
        "default_priority": "critical",
        "description": "Breached SLA terms, uptime failures, missed response targets",
    },
    "feature_request": {
        "team": "product",
        "default_priority": "low",
        "description": "New feature requests and enhancement suggestions",
    },
    "security": {
        "team": "security_ops",
        "default_priority": "critical",
        "description": "Suspected breaches, access anomalies, compliance concerns",
    },
    "migration": {
        "team": "onboarding",
        "default_priority": "high",
        "description": "Data migration, platform onboarding, bulk user provisioning",
    },
    "documentation_error": {
        "team": "product",
        "default_priority": "medium",
        "description": "Incorrect or misleading documentation that needs correction",
    },
}

# Runtime storage — gets populated by escalation tools during a session
ESCALATION_TICKETS = {}
