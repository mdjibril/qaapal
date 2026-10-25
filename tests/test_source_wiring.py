# Static source-level checks that modules are wired to the expected helpers and prompt builders.
import pathlib
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]


class SourceWiringTest(unittest.TestCase):
    def test_main_uses_ai_policy_helper(self):
        source = (REPO_ROOT / "main.py").read_text(encoding="utf-8")

        self.assertIn("from ai_policy import get_ai_access_policy", source)
        self.assertIn("ai_policy = get_ai_access_policy(role, tier, is_platform_pass_expired)", source)
        self.assertIn("show_byok = ai_policy[\"allow_byok\"]", source)
        self.assertIn("providers = ai_policy[\"provider_options\"]", source)
        self.assertIn("st.session_state.ai_provider = ai_policy[\"default_provider\"]", source)
        self.assertIn("st.session_state.target_model = ai_policy[\"default_model\"]", source)
        self.assertIn("tier in ('platform_pass', 'lifetime', 'enterprise')", source)

    def test_dashboard_uses_prompt_builder(self):
        source = (REPO_ROOT / "dashboard.py").read_text(encoding="utf-8")
        self.assertIn("from prompt_builders import build_dashboard_prompt", source)
        self.assertIn("build_dashboard_prompt(", source)

    def test_personal_statement_uses_prompt_builder(self):
        source = (REPO_ROOT / "personal_statement.py").read_text(encoding="utf-8")
        self.assertIn("from prompt_builders import build_personal_statement_prompt", source)
        self.assertIn("build_personal_statement_prompt(", source)

    def test_witness_statement_uses_prompt_builder(self):
        source = (REPO_ROOT / "witness_statement.py").read_text(encoding="utf-8")
        self.assertIn("from prompt_builders import build_witness_statement_prompt", source)
        self.assertIn("build_witness_statement_prompt(", source)


if __name__ == "__main__":
    unittest.main()
