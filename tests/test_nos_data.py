# Data-integrity checks for every NOS JSON file in data/, guarding against duplicate PCs and malformed records.
import json
import pathlib
import unittest

from workbook_utils import normalize_nos


DATA_ROOT = pathlib.Path(__file__).resolve().parents[1] / "data"


def _to_nested_nos(nos):
    nested = {}
    for unit in nos.get("units", []):
        unit_code = str(unit.get("code", "")).strip()
        unit_title = str(unit.get("title", "")).strip()
        los = {}
        for lo in unit.get("learning_outcomes", []):
            lo_num = str(lo.get("lo_num", "")).strip()
            lo_description = str(lo.get("description", "")).strip()
            pcs = []
            for pc in lo.get("performance_criteria", []):
                pc_code = str(pc.get("pc_code", "")).strip()
                pc_description = str(pc.get("description", "")).strip()
                pcs.append(f"{pc_code}: {pc_description}")
            los[f"LO {lo_num}: {lo_description}"] = pcs
        nested[f"{unit_code}: {unit_title}"] = los
    return nested


class NosDataTest(unittest.TestCase):
    def test_every_nos_file_normalizes_without_duplicate_pc_identities(self):
        files = sorted(DATA_ROOT.rglob("*.json"))
        self.assertTrue(files, "No NOS JSON files found under data/")

        for data_file in files:
            with self.subTest(file=data_file.name):
                nos = json.loads(data_file.read_text(encoding="utf-8"))
                units = nos.get("units", [])
                self.assertIsInstance(units, list, data_file)

                total_pcs = sum(
                    len(lo.get("performance_criteria", []))
                    for unit in units
                    for lo in unit.get("learning_outcomes", [])
                )
                records = normalize_nos(_to_nested_nos(nos))

                self.assertEqual(
                    len(records),
                    total_pcs,
                    f"Malformed or empty PC code in {data_file}",
                )
                identities = [(r["unit_code"], r["lo_num"], r["pc_code"]) for r in records]
                self.assertEqual(len(identities), len(set(identities)), data_file)
                for record in records:
                    self.assertTrue(record["unit_code"], data_file)
                    self.assertTrue(record["lo_num"], data_file)
                    self.assertTrue(record["pc_code"], data_file)
                    self.assertTrue(record["pc_description"], data_file)


if __name__ == "__main__":
    unittest.main()
