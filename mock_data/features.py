"""Feature catalog — plan matrix, limits, and docs."""

# plan -> feature availability
FEATURE_MATRIX = {
    "dark_mode": {
        "starter": False,
        "professional": True,
        "pro": True,
        "enterprise": True,
    },
    "dashboard": {
        "starter": True,
        "professional": True,
        "pro": True,
        "enterprise": True,
    },
    "basic_reports": {
        "starter": True,
        "professional": True,
        "pro": True,
        "enterprise": True,
    },
    "advanced_reports": {
        "starter": False,
        "professional": True,
        "pro": True,
        "enterprise": True,
    },
    "api_access": {
        "starter": False,
        "professional": True,
        "pro": True,
        "enterprise": True,
    },
    "custom_integrations": {
        "starter": False,
        "professional": False,
        "pro": False,
        "enterprise": True,
    },
    "sso": {
        "starter": False,
        "professional": False,
        "pro": True,
        "enterprise": True,
    },
    "priority_support": {
        "starter": False,
        "professional": True,
        "pro": True,
        "enterprise": True,
    },
    "email_support": {
        "starter": True,
        "professional": True,
        "pro": True,
        "enterprise": True,
    },
    "dedicated_support": {
        "starter": False,
        "professional": False,
        "pro": False,
        "enterprise": True,
    },
    "audit_log": {
        "starter": False,
        "professional": False,
        "pro": False,
        "enterprise": True,
    },
    "custom_branding": {
        "starter": False,
        "professional": False,
        "pro": False,
        "enterprise": True,
    },
}

# per-plan rate limits and caps
FEATURE_LIMITS = {
    "api_access": {
        "starter": None,  # not available
        "professional": {
            "monthly_limit": 5000,
            "rate_limit_per_minute": 60,
            "concurrent_connections": 5,
        },
        "pro": {
            "monthly_limit": 50000,
            "rate_limit_per_minute": 300,
            "concurrent_connections": 25,
        },
        "enterprise": {
            "monthly_limit": "unlimited",
            "rate_limit_per_minute": 1000,
            "concurrent_connections": 100,
        },
    },
    "advanced_reports": {
        "starter": None,
        "professional": {"max_scheduled_reports": 10, "export_formats": ["csv", "pdf"]},
        "pro": {"max_scheduled_reports": 50, "export_formats": ["csv", "pdf", "xlsx"]},
        "enterprise": {"max_scheduled_reports": "unlimited", "export_formats": ["csv", "pdf", "xlsx", "json"]},
    },
    "custom_integrations": {
        "starter": None,
        "professional": None,
        "pro": None,
        "enterprise": {"max_integrations": 50, "webhook_limit": 100},
    },
}

# per-feature help docs
FEATURE_DOCUMENTATION = {
    "dark_mode": {
        "description": "Switches the UI to a dark color scheme. Easier on the eyes for late-night sessions.",
        "setup_instructions": (
            "Go to Settings > Appearance > Theme and select 'Dark'. "
            "Changes apply immediately, no reload needed."
        ),
        "requirements": ["professional plan or higher"],
        "known_issues": [
            "Some third-party embedded charts may not respect dark mode colors.",
            "PDF exports always use light theme regardless of UI setting.",
        ],
    },
    "dashboard": {
        "description": "Main analytics dashboard with real-time metrics and customizable widgets.",
        "setup_instructions": "Available by default on all plans. Visit the Dashboard tab to get started.",
        "requirements": [],
        "known_issues": [],
    },
    "basic_reports": {
        "description": "Pre-built reports covering usage, performance, and billing summaries.",
        "setup_instructions": "Navigate to Reports > Basic to access standard report templates.",
        "requirements": [],
        "known_issues": [],
    },
    "advanced_reports": {
        "description": "Custom report builder with drag-and-drop fields, scheduled delivery, and multiple export formats.",
        "setup_instructions": (
            "Go to Reports > Advanced. Use the report builder to select data sources "
            "and configure filters. Schedule via the clock icon in the top-right."
        ),
        "requirements": ["professional plan or higher"],
        "known_issues": [
            "Scheduled reports occasionally deliver 1-2 minutes late during peak hours.",
        ],
    },
    "api_access": {
        "description": "RESTful API for programmatic access to your TechCorp data and configuration.",
        "setup_instructions": (
            "Generate an API key at Settings > API > Keys. Use the base URL "
            "https://api.techcorp.com/v2/ with your key in the Authorization header."
        ),
        "requirements": ["professional plan or higher", "admin role on the account"],
        "known_issues": [
            "Rate limit headers (X-RateLimit-Remaining) may be off by 1 during high concurrency.",
            "The /bulk endpoint has a 10MB payload cap that isn't documented in the OpenAPI spec yet.",
        ],
        # NOTE: this is intentionally wrong — the actual pro limit is 50,000/month.
        # Public-facing copy hasn't been updated since the limit was added.
        "public_docs_note": "Pro plan includes unlimited API calls with priority throughput.",
    },
    "custom_integrations": {
        "description": "Build and deploy custom integrations with third-party services using webhooks and the integration SDK.",
        "setup_instructions": (
            "Access the Integration Builder at Settings > Integrations > Custom. "
            "Use the SDK docs at docs.techcorp.com/integrations for reference."
        ),
        "requirements": ["enterprise plan"],
        "known_issues": [
            "OAuth refresh token rotation can cause brief auth failures if the integration doesn't handle 401 retries.",
        ],
    },
    "sso": {
        "description": "SAML 2.0 and OIDC single sign-on integration for centralized authentication.",
        "setup_instructions": (
            "Configure your IdP in Settings > Security > SSO. "
            "We support Okta, Azure AD, Google Workspace, and generic SAML/OIDC providers."
        ),
        "requirements": ["pro plan or higher", "domain verification completed"],
        "known_issues": [
            "SCIM user deprovisioning can take up to 15 minutes to propagate.",
        ],
    },
    "priority_support": {
        "description": "Faster response times and dedicated support queue for your tickets.",
        "setup_instructions": "Automatically enabled on eligible plans. Submit tickets as usual — they'll be routed to the priority queue.",
        "requirements": ["professional plan or higher"],
        "known_issues": [],
    },
    "email_support": {
        "description": "Standard email-based support. Reach us at support@techcorp.com.",
        "setup_instructions": "Email support@techcorp.com with your account ID in the subject line.",
        "requirements": [],
        "known_issues": [],
    },
    "dedicated_support": {
        "description": "Named account manager and direct Slack channel for your team.",
        "setup_instructions": "Your account manager will reach out within 48 hours of enterprise activation.",
        "requirements": ["enterprise plan"],
        "known_issues": [],
    },
    "audit_log": {
        "description": "Comprehensive audit trail of all user actions, API calls, and configuration changes.",
        "setup_instructions": "Go to Settings > Security > Audit Log. Logs are retained for 1 year by default.",
        "requirements": ["enterprise plan"],
        "known_issues": [
            "Bulk API operations log as a single event rather than individual entries.",
        ],
    },
    "custom_branding": {
        "description": "White-label the platform with your company's logo, colors, and custom domain.",
        "setup_instructions": (
            "Upload assets at Settings > Branding. Custom domain setup requires "
            "a CNAME record pointing to brand.techcorp.com."
        ),
        "requirements": ["enterprise plan"],
        "known_issues": [
            "Custom favicon may not update in some browsers without a hard refresh.",
        ],
    },
}

PLAN_PRICING = {
    "starter": {"monthly_per_seat": 29.99, "annual_discount_percent": 10},
    "professional": {"monthly_per_seat": 149.99, "annual_discount_percent": 15},
    "pro": {"monthly_per_seat": 199.99, "annual_discount_percent": 15},
    "enterprise": {"monthly_per_seat": 999.99, "annual_discount_percent": 20},
}
