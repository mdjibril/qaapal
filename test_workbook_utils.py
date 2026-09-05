import json
import unittest

from workbook_utils import normalize_nos, split_workbook_records, validate_workbook_items


class WorkbookUtilsTest(unittest.TestCase):
    def setUp(self):
        self.nos = {
            "ICT/301: Install Network Equipment": {
                "LO 1: Install devices": [
                    "1.1: Switch installed safely",
                    "1.2: Connectivity tested",
                ]
            }
        }
        self.records = normalize_nos(self.nos)

    def test_normalizes_each_pc(self):
        self.assertEqual([record["pc_code"] for record in self.records], ["1.1", "1.2"])
        self.assertEqual(self.records[0]["unit_code"], "ICT/301")
        self.assertEqual(self.records[0]["lo_num"], "1")

    def test_splits_large_workbook_into_bounded_batches(self):
        batches = split_workbook_records(self.records, batch_size=1)
        self.assertEqual(len(batches), 2)
        self.assertEqual(sum(len(batch) for batch in batches), len(self.records))

    def test_rejects_missing_pc(self):
        response = {"items": [self._item("1.1")]}
        with self.assertRaisesRegex(ValueError, "Missing PC"):
            validate_workbook_items(json.dumps(response), self.records)

    def test_rejects_duplicate_pc(self):
        response = {"items": [self._item("1.1"), self._item("1.1")]}
        with self.assertRaisesRegex(ValueError, "Duplicate PC"):
            validate_workbook_items(json.dumps(response), self.records)

    def test_allows_same_pc_code_in_different_units(self):
        records = normalize_nos(
            {
                "ICT/301: Install Network Equipment": {"LO 1: Install devices": ["1.1: Install a switch"]},
                "ICT/302: Test Network Services": {"LO 1: Test connections": ["1.1: Test connectivity"]},
            }
        )
        response = {
            "items": [
                {**self._item("1.1"), "unit_code": "ICT/301", "lo_num": "1"},
                {**self._item("1.1"), "unit_code": "ICT/302", "lo_num": "1"},
            ]
        }
        items = validate_workbook_items(json.dumps(response), records)
        self.assertEqual([item["unit_code"] for item in items], ["ICT/301", "ICT/302"])

    def _item(self, pc_code):
        return {
            "pc_code": pc_code,
            "question_type": "Direct",
            "question": f"How do you complete {pc_code}?",
            "weight": 5,
            "ideal_answer": ["Complete the required action."],
            "marking_scheme": ["Correct action: 5 marks"],
        }


if __name__ == "__main__":
    unittest.main()
