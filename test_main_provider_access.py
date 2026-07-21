import pathlib
import unittest


class MainProviderAccessTest(unittest.TestCase):
    def test_main_uses_ai_policy_helper(self):
        source = pathlib.Path(__file__).with_name("main.py").read_text(encoding="utf-8")

        self.assertIn("from ai_policy import get_ai_access_policy", source)
        self.assertIn("ai_policy = get_ai_access_policy(role, tier, is_platform_pass_expired)", source)
        self.assertIn("show_byok = ai_policy[\"allow_byok\"]", source)
        self.assertIn("providers = ai_policy[\"provider_options\"]", source)
        self.assertIn("st.session_state.ai_provider = ai_policy[\"default_provider\"]", source)
        self.assertIn("st.session_state.target_model = ai_policy[\"default_model\"]", source)


if __name__ == "__main__":
    unittest.main()
