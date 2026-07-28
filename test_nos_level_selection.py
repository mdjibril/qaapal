import unittest
from unittest.mock import patch

import database


class FakeResponse:
    def __init__(self, data):
        self.data = data


class FakeQuery:
    def __init__(self, client, table_name):
        self.client = client
        self.table_name = table_name
        self.filters = []
        self.order_key = None

    def select(self, *_args, **_kwargs):
        return self

    def eq(self, column, value):
        self.filters.append(("eq", column, value))
        return self

    def in_(self, column, values):
        self.filters.append(("in", column, list(values)))
        return self

    def order(self, column):
        self.order_key = column
        return self

    def limit(self, *_args, **_kwargs):
        return self

    def execute(self):
        data = self.client.rows_for(self.table_name, self.filters)
        if self.order_key:
            data = sorted(data, key=lambda row: row.get(self.order_key))
        return FakeResponse(data)


class FakeSupabaseClient:
    def __init__(self):
        self.trades = [
            {"id": 1, "name": "AGRICULTURE"},
        ]
        self.trade_levels = [
            {"id": 10, "trade_id": 1, "level": 2, "display_name": "Agriculture Level 2"},
            {"id": 11, "trade_id": 1, "level": 3, "display_name": "Agriculture Level 3"},
        ]
        self.units = [
            {"id": 100, "trade_id": 1, "trade_level_id": 10, "code": "AGR/L2/U1", "title": "Level 2 Unit"},
            {"id": 200, "trade_id": 1, "trade_level_id": 11, "code": "AGR/L3/U1", "title": "Level 3 Unit"},
        ]
        self.learning_outcomes = [
            {"id": 1000, "unit_id": 100, "lo_num": "1", "description": "Handle tools safely"},
            {"id": 2000, "unit_id": 200, "lo_num": "1", "description": "Plan workflow"},
        ]
        self.performance_criteria = [
            {"id": 10000, "lo_id": 1000, "pc_code": "1.1", "description": "Select the correct tool"},
            {"id": 20000, "lo_id": 2000, "pc_code": "1.1", "description": "Sequence the task"},
        ]

    def table(self, table_name):
        return FakeQuery(self, table_name)

    def rows_for(self, table_name, filters):
        if table_name == "trades":
            return self._filter_rows(self.trades, filters)
        if table_name == "trade_levels":
            return self._filter_rows(self.trade_levels, filters)
        if table_name == "units":
            rows = self._filter_rows(self.units, filters)
            return [self._attach_children(row) for row in rows]
        if table_name == "learning_outcomes":
            return self._filter_rows(self.learning_outcomes, filters)
        if table_name == "performance_criteria":
            return self._filter_rows(self.performance_criteria, filters)
        return []

    def _filter_rows(self, rows, filters):
        result = list(rows)
        for op, column, value in filters:
            if op == "eq":
                result = [row for row in result if row.get(column) == value]
            elif op == "in":
                result = [row for row in result if row.get(column) in value]
        return result

    def _attach_children(self, unit_row):
        row = dict(unit_row)
        los = [dict(lo) for lo in self.learning_outcomes if lo["unit_id"] == unit_row["id"]]
        for lo in los:
            lo["performance_criteria"] = [
                dict(pc) for pc in self.performance_criteria if pc["lo_id"] == lo["id"]
            ]
        row["learning_outcomes"] = los
        return row


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
