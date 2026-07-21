import pathlib
import unittest

import datetime

from prompt_builders import build_personal_statement_prompt, build_witness_statement_prompt


class StatementPromptRulesTest(unittest.TestCase):
    def test_personal_statement_prompt_matches_dashboard_ordering_rules(self):
        source = pathlib.Path(__file__).with_name("personal_statement.py").read_text(encoding="utf-8")
        self.assertIn("from prompt_builders import build_personal_statement_prompt", source)
        self.assertIn("build_personal_statement_prompt(", source)

        prompt_bundle = build_personal_statement_prompt(
            student_name="Ada Lovelace",
            statement_date=datetime.date(2026, 7, 21),
            reflection="I replaced the gasket and checked the hydraulic line.",
            trade_context="AGR/AEM/L2",
            selected_pcs=[
                "AGR/AEM/L2/004 - 1 - 1.1: Work In line with organizational standard and structure.",
                "AGR/AEM/L2/005 - 2 - 2.2: Select appropriate maintenance strategy.",
                "AGR/AEM/L2/006 - 3 - 2.5: Store the equipment in safe place after use.",
            ],
        )

        system_prompt = prompt_bundle["system_prompt"]
        user_prompt = prompt_bundle["user_prompt"]

        required_phrases = [
            "8. **Volume**: Generate a dynamic number of dense, technical paragraphs based on the total PCs selected.",
            "11. **Exhaustive Usage**: You MUST use every PC provided in the list exactly once. Weave at least 2 PCs logically into every paragraph.",
            "12. **No Sequential Listing**",
            "13. **Mixed Unit/LO Weaving**",
        ]

        for phrase in required_phrases:
            self.assertIn(phrase, system_prompt)

        self.assertNotIn("Generate exactly 7 to 8 dense, technical paragraphs.", system_prompt)
        self.assertNotIn("Weave 2-3 PCs logically into every paragraph.", system_prompt)
        self.assertIn("Performance Criteria to cover:", user_prompt)

    def test_witness_statement_prompt_matches_dashboard_ordering_rules(self):
        source = pathlib.Path(__file__).with_name("witness_statement.py").read_text(encoding="utf-8")
        self.assertIn("from prompt_builders import build_witness_statement_prompt", source)
        self.assertIn("build_witness_statement_prompt(", source)

        prompt_bundle = build_witness_statement_prompt(
            witness_name="Engr. Sarah Ahmed",
            witness_role="Senior Workshop Supervisor",
            candidate_name="John Doe",
            observation_date=datetime.date(2026, 7, 21),
            witness_notes="John removed the cover and tested the pulley alignment.",
            trade_context="AGR/AEM/L2",
            selected_pcs=[
                "AGR/AEM/L2/004 - 1 - 1.1: Work In line with organizational standard and structure.",
                "AGR/AEM/L2/005 - 2 - 2.2: Select appropriate maintenance strategy.",
                "AGR/AEM/L2/006 - 3 - 2.5: Store the equipment in safe place after use.",
            ],
        )

        system_prompt = prompt_bundle["system_prompt"]
        user_prompt = prompt_bundle["user_prompt"]

        required_phrases = [
            "10. **Volume**: Generate a dynamic number of dense, technical paragraphs based on the total PCs selected.",
            "13. **Exhaustive Usage**: You MUST use every PC provided in the list exactly once. Weave at least 2 PCs logically into every paragraph.",
            "14. **No Sequential Listing**",
            "15. **Mixed Unit/LO Weaving**",
        ]

        for phrase in required_phrases:
            self.assertIn(phrase, system_prompt)

        self.assertNotIn("Generate exactly 7 to 8 dense, technical paragraphs.", system_prompt)
        self.assertNotIn("Weave 2-3 PCs logically into every paragraph.", system_prompt)
        self.assertIn("Performance Criteria to cover:", user_prompt)


if __name__ == "__main__":
    unittest.main()
