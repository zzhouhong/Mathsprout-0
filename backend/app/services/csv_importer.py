"""
CSV / Excel importer for batch child registration.

Expected columns (header row required):
  name*       — 幼儿姓名 (required)
  age_group*  — 年龄段: small | middle | large (required)
  class_name  — 班级名称 (optional)
  birth_date  — 出生日期 YYYY-MM-DD (optional)
  notes       — 备注 (optional)

The importer validates each row, collects errors, and batch-inserts valid
children using db.add_all() for efficiency.
"""

import csv
import io
import secrets
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Child

# Valid age_group values
VALID_AGE_GROUPS = {"small", "middle", "large"}

# Required and optional columns
REQUIRED_COLUMNS = {"name", "age_group"}
OPTIONAL_COLUMNS = {"class_name", "birth_date", "notes"}
ALL_COLUMNS = REQUIRED_COLUMNS | OPTIONAL_COLUMNS


class ImportError_(Exception):
    """Raised when the CSV file itself is invalid (not row-level errors)."""
    pass


def parse_csv_content(content: bytes, filename: str) -> List[Dict[str, str]]:
    """
    Parse CSV or Excel content into a list of row dicts.

    Returns list of dicts with normalized column names (lowercase, stripped).
    Raises ImportError_ on format issues.
    """
    if filename.lower().endswith((".xlsx", ".xls")):
        return _parse_excel(content)

    # Detect encoding and parse CSV
    text = None
    for encoding in ("utf-8-sig", "utf-8", "gbk", "gb2312"):
        try:
            text = content.decode(encoding)
            break
        except (UnicodeDecodeError, LookupError):
            continue

    if text is None:
        raise ImportError_("无法识别文件编码，请使用 UTF-8 或 GBK 编码的 CSV 文件")

    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise ImportError_("CSV 文件为空或无表头行。第一行应为：name, age_group, class_name, birth_date, notes")

    rows = []
    for i, row in enumerate(reader):
        # Normalize keys: strip whitespace, lowercase
        normalized = {}
        for k, v in row.items():
            if k is None:
                continue
            key = k.strip().lower().replace(" ", "_").replace("（", "").replace("）", "")
            # Handle common Chinese column names
            key = _normalize_column_name(key)
            normalized[key] = (v or "").strip()
        normalized["_row"] = str(i + 2)  # 1-indexed + header row
        rows.append(normalized)

    return rows


def _normalize_column_name(key: str) -> str:
    """Map common Chinese/alternative column names to standard keys."""
    mapping = {
        "姓名": "name",
        "名字": "name",
        "幼儿姓名": "name",
        "年龄段": "age_group",
        "年龄": "age_group",
        "班级": "class_name",
        "班": "class_name",
        "出生日期": "birth_date",
        "生日": "birth_date",
        "备注": "notes",
        "说明": "notes",
    }
    return mapping.get(key, key)


def _parse_excel(content: bytes) -> List[Dict[str, str]]:
    """Parse Excel file using openpyxl."""
    try:
        import openpyxl
    except ImportError:
        raise ImportError_(
            "不支持 Excel 文件。请安装 openpyxl（pip install openpyxl）或将文件保存为 CSV 格式。"
        )

    wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True)
    ws = wb.active

    rows_iter = ws.iter_rows(values_only=True)
    try:
        headers = [str(h or "").strip().lower() for h in next(rows_iter)]
    except StopIteration:
        raise ImportError_("Excel 文件为空")

    headers = [_normalize_column_name(h) for h in headers]

    rows = []
    for i, row in enumerate(rows_iter):
        normalized = {}
        for j, h in enumerate(headers):
            if j < len(row) and row[j] is not None:
                normalized[h] = str(row[j]).strip()
            else:
                normalized[h] = ""
        normalized["_row"] = str(i + 2)
        rows.append(normalized)

    wb.close()
    return rows


async def import_children_from_csv(
    db: AsyncSession,
    content: bytes,
    filename: str,
) -> Dict[str, Any]:
    """
    Parse CSV/Excel and batch-import children to the database.

    Returns: {
        "total": int,       total rows in file
        "imported": int,    successfully created
        "skipped": int,     rows with validation errors
        "errors": [{"row": str, "reason": str}],
        "imported_ids": [int],
    }
    """
    # Parse
    try:
        rows = parse_csv_content(content, filename)
    except ImportError_ as e:
        return {
            "total": 0,
            "imported": 0,
            "skipped": 0,
            "errors": [{"row": "N/A", "reason": str(e)}],
            "imported_ids": [],
        }

    if not rows:
        return {
            "total": 0, "imported": 0, "skipped": 0,
            "errors": [{"row": "N/A", "reason": "文件中没有数据行"}],
            "imported_ids": [],
        }

    # Validate each row
    valid_children: List[Child] = []
    errors: List[Dict[str, str]] = []

    for row in rows:
        row_num = row.get("_row", "?")
        reasons = []

        # Required: name
        name = row.get("name", "")
        if not name:
            reasons.append("缺少姓名")

        # Required: age_group
        age_group = row.get("age_group", "").lower()
        if not age_group:
            reasons.append("缺少年龄段")
        elif age_group not in VALID_AGE_GROUPS:
            reasons.append(f"无效年龄段 '{age_group}'，应为 small/middle/large")

        if reasons:
            errors.append({"row": row_num, "reason": "; ".join(reasons)})
            continue

        # Build child
        access_code = secrets.token_hex(4).upper()
        birth_date = row.get("birth_date") or None
        notes = row.get("notes") or None
        class_name = row.get("class_name") or None

        child = Child(
            name=name,
            age_group=age_group,
            class_name=class_name,
            birth_date=birth_date if birth_date else None,
            parent_access_code=access_code,
            notes=notes,
        )
        valid_children.append(child)

    # Batch insert
    if valid_children:
        db.add_all(valid_children)
        await db.flush()
        # Refresh to get IDs
        for c in valid_children:
            await db.refresh(c)
        await db.commit()

    return {
        "total": len(rows),
        "imported": len(valid_children),
        "skipped": len(errors),
        "errors": errors[:50],  # Cap error list at 50
        "imported_ids": [c.id for c in valid_children],
    }
