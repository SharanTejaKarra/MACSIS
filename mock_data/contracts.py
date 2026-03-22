"""Mock contracts — pro and enterprise SLA terms."""

CONTRACTS = {
    "CONTRACT-002": {
        "contract_id": "CONTRACT-002",
        "customer_id": "CUST-002",
        "plan": "pro",
        "start_date": "2024-11-01",
        "end_date": "2026-10-31",
        "auto_renew": True,
        "sla": {
            "response_time_hours": 48,
            "resolution_time_hours": 120,
            "uptime_guarantee_percent": 99.5,
        },
        "included_features": [
            "dashboard", "basic_reports", "advanced_reports",
            "api_access", "dark_mode", "sso", "priority_support",
            "email_support",
        ],
        "special_terms": [],
        "monthly_cost": 4999.75,
        "seat_limit": 25,
    },

    "CONTRACT-003": {
        "contract_id": "CONTRACT-003",
        "customer_id": "CUST-003",
        "plan": "enterprise",
        "start_date": "2024-03-10",
        "end_date": "2027-03-09",
        "auto_renew": True,
        "sla": {
            "response_time_hours": 24,
            "resolution_time_hours": 72,
            "uptime_guarantee_percent": 99.9,
        },
        "included_features": [
            "dashboard", "basic_reports", "advanced_reports",
            "api_access", "dark_mode", "custom_integrations", "sso",
            "priority_support", "email_support", "dedicated_support",
            "audit_log", "custom_branding",
        ],
        "special_terms": [
            "Quarterly business reviews with product team",
            "Early access to beta features",
            "Custom SLA penalty: 5% credit per SLA breach, up to 25% monthly",
        ],
        "monthly_cost": 99999.00,
        "seat_limit": 100,
    },
}
