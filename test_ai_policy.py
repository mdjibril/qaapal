import unittest

from ai_policy import get_ai_access_policy


class AiPolicyTest(unittest.TestCase):
    def test_free_tier_policy(self):
        policy = get_ai_access_policy(role="assessor", tier="free")

        self.assertFalse(policy["allow_vertex"])
        self.assertFalse(policy["allow_byok"])
        self.assertEqual(policy["provider_options"], ["Gemini"])
        self.assertEqual(policy["default_provider"], "Gemini")
        self.assertEqual(policy["tier"], "free")
        self.assertEqual(policy["platform_quota"], 5)

    def test_platform_pass_policy(self):
        policy = get_ai_access_policy(role="assessor", tier="platform_pass")

        self.assertFalse(policy["allow_vertex"])
        self.assertTrue(policy["allow_byok"])
        self.assertNotIn("VertexAI", policy["provider_options"])
        self.assertEqual(policy["default_provider"], "Gemini")
        self.assertEqual(policy["platform_quota"], 0)

    def test_lifetime_policy(self):
        policy = get_ai_access_policy(role="assessor", tier="lifetime")

        self.assertFalse(policy["allow_vertex"])
        self.assertTrue(policy["allow_byok"])
        self.assertNotIn("VertexAI", policy["provider_options"])
        self.assertIn("OpenRouter", policy["provider_options"])
        self.assertEqual(policy["label"], "Lifetime")
        self.assertIsNone(policy["platform_quota"])

    def test_enterprise_policy_is_explicit(self):
        policy = get_ai_access_policy(role="assessor", tier="enterprise")

        self.assertFalse(policy["allow_vertex"])
        self.assertTrue(policy["allow_byok"])
        self.assertEqual(policy["label"], "Enterprise")
        self.assertEqual(policy["default_provider"], "Gemini")
        self.assertIsNone(policy["platform_quota"])

    def test_admin_policy(self):
        policy = get_ai_access_policy(role="admin", tier="free")

        self.assertFalse(policy["allow_vertex"])
        self.assertTrue(policy["allow_byok"])
        self.assertEqual(policy["label"], "Superadmin")
        self.assertEqual(policy["provider_options"], ["Gemini", "Groq", "OpenRouter"])
        self.assertIsNone(policy["platform_quota"])

    def test_expired_platform_pass_falls_back_to_free(self):
        policy = get_ai_access_policy(role="assessor", tier="platform_pass", platform_pass_expired=True)

        self.assertEqual(policy["tier"], "free")
        self.assertFalse(policy["allow_vertex"])
        self.assertFalse(policy["allow_byok"])
        self.assertEqual(policy["default_provider"], "Gemini")


if __name__ == "__main__":
    unittest.main()
