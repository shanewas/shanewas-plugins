---
name: xlsx-ops
description: Use when editing an existing .xlsx or .xlsm file, or creating one, and the change has to keep formulas, styles, and Japanese text intact. Every edit runs through one CLI that prints a JSON result and re-reads the saved file to verify it. Formula recalculation runs in real Microsoft Excel over COM, so it needs Windows with Excel installed.
---

# xlsx-ops

Edit workbooks through `scripts/xlsx_ops.py`, not through ad-hoc openpyxl code. Each call loads
the workbook with formulas kept, makes one change, saves, reloads the saved file, and prints one
JSON object with `before`, `after`, and `verified`.

`$SKILL` below is the directory that holds this file.

Requirements: Python 3.10+, `openpyxl`, `Pillow` (for `add-image`), and `pywin32` plus Microsoft
Excel on Windows (for `recalc`). Install with `pip install openpyxl pillow pywin32`.

## Commands

| Task | Command |
|---|---|
| List sheets | `python $SKILL/scripts/xlsx_ops.py read FILE` |
| Read cells | `python $SKILL/scripts/xlsx_ops.py read FILE --sheet S [--range A1:C10]` |
| Find text | `python $SKILL/scripts/xlsx_ops.py find FILE "text" [--sheet S]` |
| Set a value | `python $SKILL/scripts/xlsx_ops.py set-cell FILE --sheet S --cell B5 --value 42` |
| Set a formula | `python $SKILL/scripts/xlsx_ops.py set-cell FILE --sheet S --cell B5 --formula "=SUM(B2:B4)"` |
| Write a block | `python $SKILL/scripts/xlsx_ops.py set-range FILE --sheet S --start A2 --data rows.json` |
| Insert / delete rows | `insert-rows FILE --sheet S --at 5 --count 3 [--copy-format-from 4]` / `delete-rows ...` |
| Insert / delete columns | `insert-cols FILE --sheet S --at C --count 1 [--copy-format-from B]` / `delete-cols ...` |
| Sheets | `add-sheet FILE --name N [--index 1]`, `rename-sheet FILE --from A --to B`, `delete-sheet FILE --name N` |
| Merge / unmerge | `merge FILE --sheet S --range A1:C1` / `unmerge ...` |
| Format | `set-format FILE --sheet S --range A1:C5 [--number-format "0.0%"] [--bold true] [--font-color FF0000] [--fill FFFF00] [--font Arial] [--size 12]` |
| Image | `add-image FILE --sheet S --anchor B2 --path img.png [--width-px 200]` |
| Recalculate | `python $SKILL/scripts/xlsx_ops.py recalc FILE [--timeout 60]` |
| New workbook | `python $SKILL/scripts/xlsx_ops.py new --out FILE [--sheets "A,B"]` |

Every write command takes `--out OTHER.xlsx` to leave the source untouched. Without it the file is
overwritten in place. `set-range --data` is a JSON file holding a list of rows.

## Workflow

1. Run `read` or `find` to see what the file holds and where.
2. Run one edit command and check that `"verified": true`.
3. If the edit wrote a formula, run `recalc`. `"status": "success"` means Excel recalculated with no
   error cells. `"status": "errors_found"` lists each error value with up to 20 cell locations; stop
   and report them instead of retrying.

On failure the CLI prints `{"status": "error", "detail": ...}` and exits 1.

## Rules

- Write calculations as formulas so the sheet stays live. A number computed in Python goes stale
  the moment an input changes.
- Keep the file's existing fonts, colors, and number formats. Format only what was asked for.
- `read` returns at most 500 cells per call. Narrow `--range` when the result says `truncated`.
- `delete-sheet` refuses to remove the last sheet.
- `.xlsm` files keep their VBA project.

## Gotchas

- openpyxl drops every formula when a workbook opened with `data_only=True` is saved. The CLI only
  uses that mode for read-only lookups of cached values and never saves from it.
- openpyxl does not calculate. Until `recalc` runs, a new formula cell has no cached value, so other
  tools reading the file see it as empty.
- On Windows, non-ASCII arguments such as `find "日本語"` can reach the CLI as mojibake when the
  calling shell runs a legacy code page. Text inside the workbook is unaffected. If `find` returns
  no matches for Japanese text that is visibly there, suspect the argument first.
- `recalc` starts its own hidden Excel instance and quits it afterwards. A crash mid-run can leave
  `EXCEL.EXE` behind; check Task Manager before rerunning.

## Self-check

`python $SKILL/tests/smoke.py` runs every command against a temporary workbook, Japanese sheet
names included. `recalc` is reported as WARN when Excel is not available.
