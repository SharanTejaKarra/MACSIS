"""Mock customer records — four accounts across different plan tiers."""

CUSTOMERS = {
    "CUST-001": {
        "customer_id": "CUST-001",
        "name": "Alice Johnson",
        "company": "Acme Corp",
        "email": "alice.johnson@acmecorp.com",
        "plan": "starter",
        "account_status": "active",
        "created_at": "2025-06-15T10:30:00Z",
        "seats_purchased": 5,
        "seats_used": 3,
        "contract_id": None,
        "features_enabled": ["dashboard", "basic_reports", "email_support"],
        "billing_history": [
            {
                "date": "2026-03-01",
                "amount": 149.95,
                "status": "paid",
                "description": "Starter plan - 5 seats (March 2026)",
            },
            {
                "date": "2026-02-01",
                "amount": 149.95,
                "status": "paid",
                "description": "Starter plan - 5 seats (February 2026)",
            },
            {
                "date": "2026-01-01",
                "amount": 149.95,
                "status": "paid",
                "description": "Starter plan - 5 seats (January 2026)",
            },
        ],
    },

    "CUST-002": {
        "customer_id": "CUST-002",
        "name": "Bob Martinez",
        "company": "DataFlow Inc",
        "email": "bob.martinez@dataflow.io",
        "plan": "pro",
        "account_status": "active",
        "created_at": "2024-11-01T14:00:00Z",
        "seats_purchased": 25,
        "seats_used": 20,
        "contract_id": "CONTRACT-002",
        "features_enabled": [
            "dashboard", "basic_reports", "advanced_reports",
            "api_access", "dark_mode", "sso", "priority_support",
            "email_support",
        ],
        "billing_history": [
            {
                "date": "2026-03-01",
                "amount": 4999.75,
                "status": "paid",
                "description": "Pro plan - 25 seats (March 2026)",
            },
            {
                "date": "2026-02-01",
                "amount": 4999.75,
                "status": "paid",
                "description": "Pro plan - 25 seats (February 2026)",
            },
            {
                "date": "2026-01-01",
                "amount": 4999.75,
                "status": "paid",
                "description": "Pro plan - 25 seats (January 2026)",
            },
        ],
    },

    "CUST-003": {
        "customer_id": "CUST-003",
        "name": "Carol Chen",
        "company": "Enterprise Solutions Ltd",
        "email": "carol.chen@enterprise-solutions.com",
        "plan": "enterprise",
        "account_status": "active",
        "created_at": "2024-03-10T09:00:00Z",
        "seats_purchased": 100,
        "seats_used": 85,
        "contract_id": "CONTRACT-003",
        "features_enabled": [
            "dashboard", "basic_reports", "advanced_reports",
            "api_access", "dark_mode", "custom_integrations", "sso",
            "priority_support", "email_support", "dedicated_support",
            "audit_log", "custom_branding",
        ],
        "billing_history": [
            {
                "date": "2026-03-01",
                "amount": 99999.00,
                "status": "paid",
                "description": "Enterprise plan - 100 seats (March 2026)",
            },
            {
                "date": "2026-02-01",
                "amount": 99999.00,
                "status": "paid",
                "description": "Enterprise plan - 100 seats (February 2026)",
            },
            {
                "date": "2026-01-01",
                "amount": 99999.00,
                "status": "paid",
                "description": "Enterprise plan - 100 seats (January 2026)",
            },
        ],
    },

    # Recently onboarded migration customer — all seats filled
    "CUST-004": {
        "customer_id": "CUST-004",
        "name": "David Park",
        "company": "MigrateCo",
        "email": "david.park@migrateco.com",
        "plan": "professional",
        "account_status": "active",
        "created_at": "2026-02-20T16:45:00Z",
        "seats_purchased": 10,
        "seats_used": 10,
        "contract_id": None,
        "features_enabled": [
            "dashboard", "basic_reports", "advanced_reports",
            "api_access", "email_support", "priority_support",
        ],
        "billing_history": [
            {
                "date": "2026-03-01",
                "amount": 1499.90,
                "status": "paid",
                "description": "Professional plan - 10 seats (March 2026)",
            },
        ],
    },
}
