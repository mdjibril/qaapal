import pathlib
import unittest


class StatementPromptRulesTest(unittest.TestCase):
    def _read_source(self, filename):
        return pathlib.Path(__file__).with_name(filename).read_text(encoding="utf-8")

    def test_personal_statement_prompt_matches_dashboard_ordering_rules(self):
        source = self._read_source("personal_statement.py")

        required_phrases = [
            "8. **Volume**: Generate a dynamic number of dense, technical paragraphs based on the total PCs selected.",
            "11. **Exhaustive Usage**: You MUST use every PC provided in the list exactly once. Weave at least 2 PCs logically into every paragraph.",
            "12. **No Sequential Listing**",
            "13. **Mixed Unit/LO Weaving**",
        ]

        for phrase in required_phrases:
            self.assertIn(phrase, source)

        self.assertNotIn("Generate exactly 7 to 8 dense, technical paragraphs.", source)
        self.assertNotIn("Weave 2-3 PCs logically into every paragraph.", source)

    def test_witness_statement_prompt_matches_dashboard_ordering_rules(self):
        source = self._read_source("witness_statement.py")

        required_phrases = [
            "10. **Volume**: Generate a dynamic number of dense, technical paragraphs based on the total PCs selected.",
            "13. **Exhaustive Usage**: You MUST use every PC provided in the list exactly once. Weave at least 2 PCs logically into every paragraph.",
            "14. **No Sequential Listing**",
            "15. **Mixed Unit/LO Weaving**",
        ]

        for phrase in required_phrases:
            self.assertIn(phrase, source)

        self.assertNotIn("Generate exactly 7 to 8 dense, technical paragraphs.", source)
        self.assertNotIn("Weave 2-3 PCs logically into every paragraph.", source)


if __name__ == "__main__":
    unittest.main()
