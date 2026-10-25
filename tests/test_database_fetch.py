# Tests Supabase NOS and trade-level fetching with a fake client (no live database).
import unittest
from unittest.mock import patch

import database

from helpers import FakeSupabaseClient


class NosLevelSelectionTest(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
