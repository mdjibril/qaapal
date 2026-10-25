import unittest
import sys
import types


def _install_docx_stubs():
    if "docx" in sys.modules:
        return

    docx = types.ModuleType("docx")
    docx.Document = object
    sys.modules["docx"] = docx

    shared = types.ModuleType("docx.shared")
    shared.Pt = lambda value: value
    shared.Inches = lambda value: value
    sys.modules["docx.shared"] = shared

    enum_text = types.ModuleType("docx.enum.text")
    enum_text.WD_ALIGN_PARAGRAPH = types.SimpleNamespace(CENTER=1)
    sys.modules["docx.enum.text"] = enum_text

    enum_table = types.ModuleType("docx.enum.table")
    enum_table.WD_ALIGN_VERTICAL = types.SimpleNamespace(CENTER=1, TOP=2)
    sys.modules["docx.enum.table"] = enum_table

    oxml = types.ModuleType("docx.oxml")
    oxml.OxmlElement = lambda *_args, **_kwargs: types.SimpleNamespace(
        append=lambda *_a, **_k: None,
        set=lambda *_a, **_k: None,
        find=lambda *_a, **_k: None,
        get_or_add_tcPr=lambda: types.SimpleNamespace(
            find=lambda *_a, **_k: None,
            append=lambda *_a, **_k: None,
        ),
        _tc=types.SimpleNamespace(
            get_or_add_tcPr=lambda: types.SimpleNamespace(
                find=lambda *_a, **_k: None,
                append=lambda *_a, **_k: None,
            )
        ),
        _r=types.SimpleNamespace(append=lambda *_a, **_k: None),
    )
    sys.modules["docx.oxml"] = oxml

    oxml_ns = types.ModuleType("docx.oxml.ns")
    oxml_ns.qn = lambda value: value
    sys.modules["docx.oxml.ns"] = oxml_ns


_install_docx_stubs()

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
