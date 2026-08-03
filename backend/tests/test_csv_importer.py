"""
Tests for the CSV importer service.

Covers: CSV parsing (utf-8/gbk), column-name normalization (Chinese→English),
Excel (.xlsx) parsing, and error handling for malformed input.
"""

import io
import pytest
from app.services.csv_importer import (
    parse_csv_content,
    _normalize_column_name,
    ImportError_,
)


# ─── CSV parsing ─────────────────────────────────────────────────────

class TestParseCSV:
    def test_basic_utf8_csv(self):
        content = "name,age_group,class_name\n小明,middle,中一班\n小红,small,小一班".encode("utf-8")
        rows = parse_csv_content(content, "kids.csv")
        assert len(rows) == 2
        assert rows[0]["name"] == "小明"
        assert rows[0]["age_group"] == "middle"
        assert rows[1]["class_name"] == "小一班"

    def test_utf8_with_bom(self):
        content = "name,age_group\n小明,middle".encode("utf-8-sig")
        rows = parse_csv_content(content, "kids.csv")
        assert len(rows) == 1
        assert rows[0]["name"] == "小明"

    def test_gbk_encoded_csv(self):
        content = "name,age_group\n小明,middle".encode("gbk")
        rows = parse_csv_content(content, "kids.csv")
        assert len(rows) == 1
        assert rows[0]["name"] == "小明"

    def test_row_has_row_index(self):
        content = "name,age_group\n小明,middle\n小红,small".encode("utf-8")
        rows = parse_csv_content(content, "kids.csv")
        # _row is 1-indexed + header row → data rows start at 2
        assert rows[0]["_row"] == "2"
        assert rows[1]["_row"] == "3"

    def test_strips_whitespace_in_values(self):
        content = "name,age_group\n  小明  ,  middle  ".encode("utf-8")
        rows = parse_csv_content(content, "kids.csv")
        assert rows[0]["name"] == "小明"
        assert rows[0]["age_group"] == "middle"

    def test_empty_values_become_empty_string(self):
        content = "name,age_group,class_name\n小明,middle,".encode("utf-8")
        rows = parse_csv_content(content, "kids.csv")
        assert rows[0]["class_name"] == ""


# ─── Column name normalization ───────────────────────────────────────

class TestColumnNormalization:
    @pytest.mark.parametrize("input_key,expected", [
        ("姓名", "name"),
        ("名字", "name"),
        ("幼儿姓名", "name"),
        ("年龄段", "age_group"),
        ("年龄", "age_group"),
        ("班级", "class_name"),
        ("出生日期", "birth_date"),
        ("生日", "birth_date"),
        ("备注", "notes"),
        ("说明", "notes"),
    ])
    def test_chinese_column_names_mapped(self, input_key, expected):
        assert _normalize_column_name(input_key) == expected

    def test_english_column_names_pass_through(self):
        assert _normalize_column_name("name") == "name"
        assert _normalize_column_name("age_group") == "age_group"

    def test_unknown_column_name_passes_through(self):
        assert _normalize_column_name("自定义列") == "自定义列"

    def test_chinese_columns_in_csv(self):
        content = "姓名,年龄段,班级\n小明,middle,中一班".encode("utf-8")
        rows = parse_csv_content(content, "kids.csv")
        assert rows[0]["name"] == "小明"
        assert rows[0]["age_group"] == "middle"
        assert rows[0]["class_name"] == "中一班"


# ─── Excel parsing ───────────────────────────────────────────────────

class TestExcelParsing:
    def test_xlsx_parsed_correctly(self):
        openpyxl = pytest.importorskip("openpyxl")
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(["name", "age_group", "class_name"])
        ws.append(["小明", "middle", "中一班"])
        ws.append(["小红", "small", "小一班"])
        buf = io.BytesIO()
        wb.save(buf)
        rows = parse_csv_content(buf.getvalue(), "kids.xlsx")
        assert len(rows) == 2
        assert rows[0]["name"] == "小明"
        assert rows[1]["class_name"] == "小一班"

    def test_xlsx_with_chinese_headers(self):
        openpyxl = pytest.importorskip("openpyxl")
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(["姓名", "年龄段"])
        ws.append(["小明", "middle"])
        buf = io.BytesIO()
        wb.save(buf)
        rows = parse_csv_content(buf.getvalue(), "kids.xlsx")
        assert rows[0]["name"] == "小明"
        assert rows[0]["age_group"] == "middle"

    def test_xlsx_dispatches_on_extension(self):
        # .xls extension also routes to Excel parser
        openpyxl = pytest.importorskip("openpyxl")
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(["name"])
        ws.append(["小明"])
        buf = io.BytesIO()
        wb.save(buf)
        rows = parse_csv_content(buf.getvalue(), "kids.xls")
        assert len(rows) == 1


# ─── Error handling ──────────────────────────────────────────────────

class TestErrorHandling:
    def test_empty_content_raises(self):
        with pytest.raises(ImportError_):
            parse_csv_content(b"", "empty.csv")

    def test_unsupported_encoding_raises(self):
        # Bytes that can't decode as utf-8/gbk
        with pytest.raises(ImportError_):
            parse_csv_content(b"\xff\xfe\x00\x01\x02", "bad.csv")

    def test_empty_excel_raises(self):
        openpyxl = pytest.importorskip("openpyxl")
        wb = openpyxl.Workbook()
        ws = wb.active
        # no rows at all
        buf = io.BytesIO()
        wb.save(buf)
        with pytest.raises(ImportError_):
            parse_csv_content(buf.getvalue(), "empty.xlsx")
