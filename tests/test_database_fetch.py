# Tests Supabase NOS and trade-level fetching with a fake client (no live database).
import unittest
from unittest.mock import patch

import database

from helpers import FakeSupabaseClient


class NosLevelSelectionTest(unittest.TestCase):
    def setUp(self):
        database.fetch_nested_nos.clear()
        database.fetch_trade_levels.clear()

    def test_fetch_trade_levels_returns_selected_trade_levels(self):
        client = FakeSupabaseClient()
        with patch("database.get_admin_supabase", return_value=client):
            levels = database.fetch_trade_levels(1)

        self.assertEqual([lvl["level"] for lvl in levels], [2, 3])
        self.assertEqual(levels[0]["display_name"], "Agriculture Level 2")

    def test_fetch_nested_nos_uses_selected_trade_level(self):
        client = FakeSupabaseClient()
        with patch("database.get_admin_supabase", return_value=client):
            nos_data = database.fetch_nested_nos(trade_id=1, trade_level_id=10)

        self.assertEqual(list(nos_data.keys()), ["AGR/L2/U1: Level 2 Unit"])
        self.assertIn("LO 1: Handle tools safely", nos_data["AGR/L2/U1: Level 2 Unit"])
        self.assertEqual(
            nos_data["AGR/L2/U1: Level 2 Unit"]["LO 1: Handle tools safely"],
            ["1.1: Select the correct tool"],
        )
        self.assertNotIn("AGR/L3/U1: Level 3 Unit", nos_data)

    def test_fetch_nested_nos_sorts_units_and_criteria_ascending(self):
        client = FakeSupabaseClient()
        # Feed unsorted units, LOs, and PCs
        client.units = [
            {"id": 102, "trade_id": 1, "trade_level_id": 10, "code": "HTT/BKC/002/L2", "title": "Teamwork"},
            {"id": 104, "trade_id": 1, "trade_level_id": 10, "code": "HTT/BKC/004/L2", "title": "Recipe Formulation"},
            {"id": 101, "trade_id": 1, "trade_level_id": 10, "code": "HTT/BKC/001/L2", "title": "Communication at Work"},
            {"id": 103, "trade_id": 1, "trade_level_id": 10, "code": "HTT/BKC/003/L2", "title": "Health and Safety"},
        ]
        client.learning_outcomes = [
            {"id": 1002, "unit_id": 101, "lo_num": "2", "description": "Describe medium"},
            {"id": 1001, "unit_id": 101, "lo_num": "1", "description": "Understand communication"},
        ]
        client.performance_criteria = [
            {"id": 10002, "lo_id": 1001, "pc_code": "1.2", "description": "Describe process"},
            {"id": 10001, "lo_id": 1001, "pc_code": "1.1", "description": "Explain communication"},
        ]

        with patch("database.get_admin_supabase", return_value=client):
            nos_data = database.fetch_nested_nos(trade_id=1, trade_level_id=10)

        # Verify units are ordered 001, 002, 003, 004
        expected_unit_order = [
            "HTT/BKC/001/L2: Communication at Work",
            "HTT/BKC/002/L2: Teamwork",
            "HTT/BKC/003/L2: Health and Safety",
            "HTT/BKC/004/L2: Recipe Formulation",
        ]
        self.assertEqual(list(nos_data.keys()), expected_unit_order)

        # Verify LOs in unit 001 are ordered LO 1 then LO 2
        unit_1_los = list(nos_data["HTT/BKC/001/L2: Communication at Work"].keys())
        self.assertEqual(unit_1_los, ["LO 1: Understand communication", "LO 2: Describe medium"])

        # Verify PCs in LO 1 are ordered 1.1 then 1.2
        unit_1_lo_1_pcs = nos_data["HTT/BKC/001/L2: Communication at Work"]["LO 1: Understand communication"]
        self.assertEqual(unit_1_lo_1_pcs, ["1.1: Explain communication", "1.2: Describe process"])

    def test_natural_sort_key_handles_unpadded_and_sub_numbers(self):
        codes = ["Unit 10", "Unit 2", "Unit 1", "Unit 20", "Unit 3"]
        sorted_codes = sorted(codes, key=database._natural_sort_key)
        self.assertEqual(sorted_codes, ["Unit 1", "Unit 2", "Unit 3", "Unit 10", "Unit 20"])

        pc_codes = ["1.10", "1.2", "1.1", "1.20", "1.3"]
        sorted_pcs = sorted(pc_codes, key=database._natural_sort_key)
        self.assertEqual(sorted_pcs, ["1.1", "1.2", "1.3", "1.10", "1.20"])


if __name__ == "__main__":
    unittest.main()
