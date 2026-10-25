# Tests report parsing and unit-code helpers in file_utils.
import unittest

from file_utils import get_unit_number, parse_report_chunks


class FileUtilsParsingTest(unittest.TestCase):
    def test_get_unit_number_supports_fish_farming_codes(self):
        self.assertEqual(get_unit_number("AqCS/FFA/007/L3"), "7")
        self.assertEqual(get_unit_number("AqCS/FFA/010/L2"), "10")

    def test_parse_report_chunks_supports_mixed_case_unit_codes(self):
        text = (
            "The candidate prepared the pond and measured water quality. "
            "(AqCS/FFA/007/L3 - LO 1:PC 1.1: Prepare pond conditions)"
            "\n"
            "The candidate stocked the fingerlings and recorded the feed plan. "
            "(AqCS/FFA/007/L3 - LO 1:PC 1.2: Stock fingerlings safely)"
        )

        chunks = parse_report_chunks(text)

        self.assertEqual(len(chunks), 2)
        self.assertEqual(chunks[0]["unit"], "7")
        self.assertEqual(chunks[0]["mapping"], "LO 1:PC 1.1: Prepare pond conditions")
        self.assertEqual(chunks[1]["unit"], "7")
        self.assertEqual(chunks[1]["mapping"], "LO 1:PC 1.2: Stock fingerlings safely")


if __name__ == "__main__":
    unittest.main()
