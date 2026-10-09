#!/usr/bin/env python3
"""Build combinations.json from the official AADE workbook of allowed E3
classification combinations (one sheet per invoice type).

Usage:
    python3 tools/build_combinations.py [path/to/workbook.xlsx] [version]

Defaults to the workbook kept under sources/ for the current version.

Every cell of the workbook is accounted for: codes become data, and every
non-code text (a rule written in words) is kept VERBATIM next to the data it
qualifies. Anything the builder does not recognise aborts the build instead of
being dropped silently.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

try:
    import openpyxl
except ImportError:  # pragma: no cover
    sys.exit("openpyxl is required: pip install -r tools/requirements.txt")

ROOT = Path(__file__).resolve().parent.parent
VERSION = "2.0.2"
DEFAULT_WORKBOOK = ROOT / "sources" / f"v{VERSION}" / f"syndiasmoi_xaraktirismwn_v{VERSION}.xlsx"

CODE = re.compile(r"^(category\d+(?:_\d+)?|E3_\w+|VAT_\d+|NOT_VAT_\d+)$")
CATEGORY = re.compile(r"^category\d+(?:_\d+)?$")

# Some headers are typed with a LATIN "E" in place of the Greek "Ε".
LATIN_TO_GREEK = str.maketrans({"E": "Ε"})

HEADER_INCOME = "ΧΑΡΑΚΤΗΡΙΣΜΟΙ ΕΣΟΔΩΝ"
HEADER_EXPENSES = "ΧΑΡΑΚΤΗΡΙΣΜΟΙ ΕΞΟΔΩΝ"
STRUCTURAL = {
    "ΕΛΕΓΧΟΙ ΧΑΡΑΚΤΗΡΙΣΜΩΝ Ε3",
    "ΕΠΙΤΡΕΠΤΕΣ ΤΙΜΕΣ ΣΤΗΛΗΣ 9",
    "ΕΠΙΤΡΕΠΤΕΣ ΤΙΜΕΣ Ε3",
}

# Text that qualifies the category it sits under.
SAME_AS_ABOVE = "είναι επιτρεπτοί οι παραπάνω χαρακτηρισμοί ανά τιμή ΣΤ.9"
EMPTY_ALLOWED = "ή κενό"
CORRELATED = "Επιτρέπονται οι συνδυασμοί εκείνων των τιμών που επιτρέπονται για τον τύπο του συσχετιζόμενου παραστατικού"
CORRELATED_LIST = re.compile(r"^Συμπληρώνεται ανά περίπτωση (?:τύπου παραστατικών|συσχετιζόμενων παραστατικών) (.+)$")


def clean(value: object) -> str | None:
    if not isinstance(value, str):
        return None if value is None else str(value)
    text = " ".join(value.split())
    return text or None


def header(text: str) -> str:
    return text.translate(LATIN_TO_GREEK)


def parse_sheet(ws) -> dict:
    rows = [[clean(c) for c in row] for row in ws.iter_rows(values_only=True)]
    title = next((c for r in rows for c in r if c and c.startswith("ΤΥΠΟΣ ΠΑΡΑΣΤΑΤΙΚΟΥ")), None)
    if title is None:
        raise SystemExit(f"[{ws.title}] no title row")

    description = title.split(" - ", 1)[1] if " - " in title else None
    consumed: set[tuple[int, int]] = set()

    # Section starts: every row carrying the income/expenses headers.
    starts = []
    for i, row in enumerate(rows):
        cols = {j: header(c) for j, c in enumerate(row) if c}
        sides = {side: j for j, c in cols.items() for side, h in (("income", HEADER_INCOME), ("expenses", HEADER_EXPENSES)) if c == h}
        if sides:
            starts.append((i, sides))
            for j in sides.values():
                consumed.add((i, j))

    # A section title is the free text line above a later section's headers
    # (1.5 carries two sections); the previous section ends where it starts.
    titles: dict[int, tuple[int, int, str]] = {}
    for n, (start, _) in enumerate(starts[1:], start=1):
        for k in range(start - 1, starts[n - 1][0], -1):
            if any(c and (CODE.match(c) or c.startswith("και μεταφορά") or c == SAME_AS_ABOVE) for c in rows[k]):
                break
            texts = [(j, c) for j, c in enumerate(rows[k]) if c and header(c) not in STRUCTURAL]
            if texts:
                titles[n] = (k, texts[0][0], texts[0][1])
                consumed.add((k, texts[0][0]))
                break

    sections = []
    for n, (start, sides) in enumerate(starts):
        end = len(rows)
        if n + 1 < len(starts):
            end = titles[n + 1][0] if n + 1 in titles else starts[n + 1][0]
        section = {"title": titles[n][2] if n in titles else None}
        for side, col in sides.items():
            section[side] = parse_side(ws.title, rows, start + 1, end, col, consumed)
        sections.append(section)

    # Everything left must be structural or empty — otherwise we lost a rule.
    for i, row in enumerate(rows):
        for j, c in enumerate(row):
            if not c or (i, j) in consumed:
                continue
            if c.startswith("ΤΥΠΟΣ ΠΑΡΑΣΤΑΤΙΚΟΥ") or header(c) in STRUCTURAL:
                continue
            raise SystemExit(f"[{ws.title}] unrecognised cell {i + 1},{j + 1}: {c!r}")

    return {"description": description, "title": title, "sections": sections}


def parse_side(sheet: str, rows, first: int, end: int, col: int, consumed) -> dict:
    """One side (income or expenses): column `col` holds categories, `col+1` E3 types."""
    side: dict = {}
    categories: dict[str, dict] = {}
    current: dict | None = None
    pending_same: list[str] = []

    def flush_same():
        if current is not None and pending_same:
            current["rule"] = "sameTypesAsOtherCategories"
            current["note"] = " ".join(pending_same)
            pending_same.clear()

    for i in range(first, end):
        row = rows[i]
        cat = row[col] if col < len(row) else None
        val = row[col + 1] if col + 1 < len(row) else None
        marker = row[col + 2] if col + 2 < len(row) else None

        if cat is not None:
            consumed.add((i, col))
            if header(cat) in STRUCTURAL:
                continue
            if CATEGORY.match(cat):
                flush_same()
                current = categories.setdefault(cat, {"types": []})
            elif cat == CORRELATED:
                flush_same()
                side["rule"] = "sameAsCorrelatedInvoiceType"
                side["note"] = cat
                current = None
            elif (m := CORRELATED_LIST.match(cat)):
                flush_same()
                side["correlatedInvoiceTypesNote"] = cat
                side["correlatedInvoiceTypes"] = [t for t in re.split(r"[,\s]+", m.group(1)) if t]
                current = None
            else:
                # A note that stands for the whole side (3.1 income).
                flush_same()
                side.setdefault("notes", []).append(cat)
                current = None

        if val is not None:
            consumed.add((i, col + 1))
            if header(val) in STRUCTURAL:
                continue
            if current is None:
                raise SystemExit(f"[{sheet}] value {val!r} at row {i + 1} has no category")
            if CODE.match(val):
                flush_same()
                current["types"].append(val)
            elif val == SAME_AS_ABOVE or (pending_same and val.startswith("και μεταφορά")):
                pending_same.append(val)
            elif val == EMPTY_ALLOWED:
                current["allowsEmptyType"] = True
            else:
                current.setdefault("notes", []).append(val)

        if marker is not None and current is not None and val is not None and CODE.match(val):
            consumed.add((i, col + 2))
            current.setdefault("markers", {})[val] = marker

    flush_same()
    # Multi-line notes ("(Δημόσιο) ...", "μόνο του φόρου ...") read as one.
    for entry in categories.values():
        if "notes" in entry:
            entry["note"] = " ".join(entry.pop("notes"))
    if "notes" in side:
        side["note"] = " ".join(side.pop("notes"))
    if categories:
        side["categories"] = categories
    return side


def main() -> None:
    workbook = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_WORKBOOK
    version = sys.argv[2] if len(sys.argv) > 2 else VERSION
    wb = openpyxl.load_workbook(workbook, data_only=True)

    out = {
        "version": version,
        "source": workbook.name,
        "invoiceTypes": {ws.title.strip(): parse_sheet(ws) for ws in wb.worksheets},
    }
    target = ROOT / "combinations.json"
    target.write_text(json.dumps(out, ensure_ascii=False, indent=4) + "\n", encoding="utf-8")
    print(f"combinations.json: {len(out['invoiceTypes'])} invoice types from {workbook.name}")


if __name__ == "__main__":
    main()
