"""Central AI access policy for subscription tiers."""


def get_ai_access_policy(role, tier, platform_pass_expired=False):
    """Return the AI access policy for the current user context."""
    effective_tier = tier or "free"
    if effective_tier == "platform_pass" and platform_pass_expired:
        effective_tier = "free"

    if role == "admin":
        return {
            "tier": effective_tier,
            "label": "Superadmin",
            "allow_vertex": False,
            "allow_byok": True,
            "provider_options": ["Gemini", "OpenRouter"],
            "default_provider": "OpenRouter",
            "default_model": "google/gemini-3.5-flash-lite",
            "platform_quota": None,
            "status_message": "Superadmin: Manual Key Override",
        }

    if effective_tier == "free":
        return {
            "tier": effective_tier,
            "label": "Free Tier",
            "allow_vertex": False,
            "allow_byok": False,
            "provider_options": ["OpenRouter"],
            "default_provider": "OpenRouter",
            "default_model": "google/gemini-3.5-flash-lite",
            "platform_quota": 5,
            "status_message": "Using Platform AI (Gemini Flash)",
        }

    if effective_tier == "platform_pass":
        return {
            "tier": effective_tier,
            "label": "Platform Pass",
            "allow_vertex": False,
            "allow_byok": True,
            "provider_options": ["Gemini", "OpenRouter"],
            "default_provider": "OpenRouter",
            "default_model": "google/gemini-3.5-flash-lite",
            "platform_quota": 0,
            "status_message": "Platform Pass: BYOK required for AI generation.",
        }

    if effective_tier == "lifetime":
        return {
            "tier": effective_tier,
            "label": "Lifetime",
            "allow_vertex": False,
            "allow_byok": True,
            "provider_options": ["Gemini", "OpenRouter"],
            "default_provider": "OpenRouter",
            "default_model": "google/gemini-3.5-flash-lite",
            "platform_quota": None,
            "status_message": "Lifetime Plan: BYOK preferred, unlimited platform fallback.",
        }

    if effective_tier == "enterprise":
        return {
            "tier": effective_tier,
            "label": "Enterprise",
            "allow_vertex": False,
            "allow_byok": True,
            "provider_options": ["Gemini", "OpenRouter"],
            "default_provider": "OpenRouter",
            "default_model": "google/gemini-3.5-flash-lite",
            "platform_quota": None,
            "status_message": "Enterprise Plan: BYOK or Org-billed AI.",
        }

    return {
        "tier": effective_tier,
        "label": effective_tier.title(),
        "allow_vertex": False,
        "allow_byok": False,
        "provider_options": ["OpenRouter"],
        "default_provider": "OpenRouter",
        "default_model": "google/gemini-3.5-flash-lite",
        "platform_quota": 5,
        "status_message": "Using Platform AI (Gemini Flash)",
    }
