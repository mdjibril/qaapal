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
            "allow_vertex": True,
            "allow_byok": True,
            "provider_options": ["VertexAI", "Gemini", "Groq", "OpenRouter"],
            "default_provider": "VertexAI",
            "default_model": "gemini-3.5-flash",
            "status_message": "Superadmin: Manual Key Override",
        }

    if effective_tier == "free":
        return {
            "tier": effective_tier,
            "label": "Free Tier",
            "allow_vertex": True,
            "allow_byok": False,
            "provider_options": ["VertexAI"],
            "default_provider": "VertexAI",
            "default_model": "gemini-3.5-flash",
            "status_message": "Using Platform AI (Free Tier)",
        }

    if effective_tier == "platform_pass":
        return {
            "tier": effective_tier,
            "label": "Platform Pass",
            "allow_vertex": False,
            "allow_byok": True,
            "provider_options": ["Gemini", "Groq", "OpenRouter"],
            "default_provider": "Gemini",
            "default_model": "gemini-3.5-flash",
            "status_message": "Platform Pass: BYOK is available.",
        }

    if effective_tier == "lifetime":
        return {
            "tier": effective_tier,
            "label": "Lifetime",
            "allow_vertex": True,
            "allow_byok": True,
            "provider_options": ["VertexAI", "Gemini", "Groq", "OpenRouter"],
            "default_provider": "VertexAI",
            "default_model": "gemini-3.5-flash",
            "status_message": "Lifetime Plan: BYOK and Vertex AI are available.",
        }

    if effective_tier == "enterprise":
        return {
            "tier": effective_tier,
            "label": "Enterprise",
            "allow_vertex": True,
            "allow_byok": True,
            "provider_options": ["VertexAI", "Gemini", "Groq", "OpenRouter"],
            "default_provider": "VertexAI",
            "default_model": "gemini-3.5-flash",
            "status_message": "Enterprise Plan: BYOK and Vertex AI are available.",
        }

    return {
        "tier": effective_tier,
        "label": effective_tier.title(),
        "allow_vertex": True,
        "allow_byok": False,
        "provider_options": ["VertexAI"],
        "default_provider": "VertexAI",
        "default_model": "gemini-3.5-flash",
        "status_message": "Using Platform AI (Free Tier)",
    }
