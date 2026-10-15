"""
Hardened xlsx CLI. Single entry point for all spreadsheet edits.
stdlib argparse + openpyxl only. One JSON object on stdout per call.

Hard guard: write paths NEVER load with data_only=True (that permanently
drops formulas on save). Read-only ops may take a second data_only load
to report cached values alongside formulas.
"""
import argparse
import datetime
import json
import sys
from pathlib import Path

import openpyxl
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import column_index_from_string, get_column_letter, range_boundaries

MAX_READ_CELLS = 500
ERROR_STRINGS = ("#REF!", "#DIV/0!", "#VALUE!", "#N/A", "#NAME?", "#NUM!", "#NULL!")


def _json_default(obj):
    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    raise TypeError(f"not JSON serializable: {obj!r}")


def emit(payload: dict):
    sys.stdout.write(json.dumps(payload, ensure_ascii=False, default=_json_default))
    sys.stdout.write("\n")


def resolve(path_str: str) -> Path:
    return Path(path_str)


def is_vba(path: Path) -> bool:
    return path.suffix.lower() == ".xlsm"


def load_write_wb(path: Path):
    # NEVER data_only=True here. Loading data_only=True and saving destroys formulas.
    return openpyxl.load_workbook(path, data_only=False, keep_vba=is_vba(path))


def load_cached_wb(path: Path):
    # Read-only cached-value view. Never save this workbook.
    return openpyxl.load_workbook(path, data_only=True, keep_vba=is_vba(path))


def save_target(wb, src: Path, out: str | None) -> Path:
    target = Path(out) if out else src
    wb.save(target)
    return target


def sheet_or_default(wb, name: str | None):
    return wb[name] if name else wb.active


def cell_formula(cell):
    v = cell.value
    return v if isinstance(v, str) and v.startswith("=") else None


def auto_type(raw: str):
    low = raw.strip().lower()
    if low in ("true", "false"):
        return low == "true"
    try:
        return int(raw)
    except ValueError:
        pass
    try:
        return float(raw)
    except ValueError:
        pass
    try:
        return datetime.date.fromisoformat(raw)
    except ValueError:
        pass
    try:
        return datetime.datetime.fromisoformat(raw)
    except ValueError:
        pass
    return raw


def col_ref(s: str) -> int:
    return int(s) if s.isdigit() else column_index_from_string(s.upper())


# ---------- ops ----------

def op_read(a):
    p = resolve(a.file)
    wb_f = load_write_wb(p)
    if not a.sheet:
        return {"after": {"sheets": [{"name": n, "dimensions": wb_f[n].dimensions} for n in wb_f.sheetnames]}}

    ws_f = wb_f[a.sheet]
    wb_v = load_cached_wb(p)
    ws_v = wb_v[a.sheet]

    if a.range:
        min_col, min_row, max_col, max_row = range_boundaries(a.range)
    else:
        min_col, min_row, max_col, max_row = range_boundaries(ws_f.dimensions or "A1:A1")

    cells = []
    truncated = False
    for row in range(min_row, max_row + 1):
        for col in range(min_col, max_col + 1):
            if len(cells) >= MAX_READ_CELLS:
                truncated = True
                break
            cf = ws_f.cell(row=row, column=col)
            cv = ws_v.cell(row=row, column=col)
            formula = cell_formula(cf)
            cells.append({
                "cell": cf.coordinate,
                "value": cv.value if formula else cf.value,
                "formula": formula,
                "number_format": cf.number_format,
            })
        if truncated:
            break
    result = {"sheet": a.sheet, "cells": cells}
    if truncated:
        result["truncated"] = True
    return {"after": result}


def op_find(a):
    p = resolve(a.file)
    wb = load_write_wb(p)
    sheets = [a.sheet] if a.sheet else wb.sheetnames
    matches = []
    for sname in sheets:
        ws = wb[sname]
        for row in ws.iter_rows():
            for cell in row:
                if cell.value is None:
                    continue
                if a.text in str(cell.value):
                    matches.append({"sheet": sname, "cell": cell.coordinate, "value": cell.value})
    return {"after": {"matches": matches}}


def op_set_cell(a):
    p = resolve(a.file)
    wb = load_write_wb(p)
    ws = sheet_or_default(wb, a.sheet)
    cell = ws[a.cell]
    before = {"value": cell.value if not cell_formula(cell) else None, "formula": cell_formula(cell)}

    if a.formula is not None:
        if not a.formula.startswith("="):
            raise ValueError("--formula must start with '='")
        new_value = a.formula
    else:
        new_value = auto_type(a.value)
    cell.value = new_value

    target = save_target(wb, p, a.out)
    check_wb = load_write_wb(target)
    check_cell = check_wb[ws.title][a.cell]
    verified = check_cell.value == new_value

    after = {"value": check_cell.value if not cell_formula(check_cell) else None, "formula": cell_formula(check_cell)}
    return {"before": before, "after": after, "verified": verified}


def op_set_range(a):
    p = resolve(a.file)
    wb = load_write_wb(p)
    ws = sheet_or_default(wb, a.sheet)
    data = json.loads(Path(a.data).read_text(encoding="utf-8"))

    min_col, min_row, _, _ = range_boundaries(f"{a.start}:{a.start}")
    written = []
    for r, row_vals in enumerate(data):
        for c, val in enumerate(row_vals):
            cell = ws.cell(row=min_row + r, column=min_col + c)
            cell.value = val
            written.append(cell.coordinate)

    target = save_target(wb, p, a.out)
    check_wb = load_write_wb(target)
    check_ws = check_wb[ws.title]
    verified = all(
        check_ws[coord].value == data[i // len(data[0])][i % len(data[0])]
        for i, coord in enumerate(written)
    ) if data and data[0] else True

    return {"after": {"cells_written": len(written), "start": a.start}, "verified": verified}


def op_insert_rows(a):
    p = resolve(a.file)
    wb = load_write_wb(p)
    ws = sheet_or_default(wb, a.sheet)
    before_max_row = ws.max_row
    ws.insert_rows(a.at, amount=a.count)
    if a.copy_format_from:
        max_col = ws.max_column
        for new_row in range(a.at, a.at + a.count):
            for col in range(1, max_col + 1):
                src_cell = ws.cell(row=a.copy_format_from, column=col)
                ws.cell(row=new_row, column=col)._style = src_cell._style
    # materialise at least one cell on the last inserted row so max_row reflects it
    ws.cell(row=a.at + a.count - 1, column=1).value = ""
    target = save_target(wb, p, a.out)
    check_ws = load_write_wb(target)[ws.title]
    verified = check_ws.max_row >= a.at + a.count - 1
    return {"before": {"max_row": before_max_row}, "after": {"max_row": check_ws.max_row}, "verified": verified}


def op_delete_rows(a):
    p = resolve(a.file)
    wb = load_write_wb(p)
    ws = sheet_or_default(wb, a.sheet)
    before_max_row = ws.max_row
    ws.delete_rows(a.at, amount=a.count)
    target = save_target(wb, p, a.out)
    check_ws = load_write_wb(target)[ws.title]
    verified = check_ws.max_row <= before_max_row
    return {"before": {"max_row": before_max_row}, "after": {"max_row": check_ws.max_row}, "verified": verified}


def op_insert_cols(a):
    p = resolve(a.file)
    wb = load_write_wb(p)
    ws = sheet_or_default(wb, a.sheet)
    at = col_ref(a.at)
    before_max_col = ws.max_column
    ws.insert_cols(at, amount=a.count)
    if a.copy_format_from:
        src_col = col_ref(a.copy_format_from)
        max_row = ws.max_row
        for new_col in range(at, at + a.count):
            for row in range(1, max_row + 1):
                src_cell = ws.cell(row=row, column=src_col)
                ws.cell(row=row, column=new_col)._style = src_cell._style
    target = save_target(wb, p, a.out)
    check_ws = load_write_wb(target)[ws.title]
    verified = check_ws.max_column >= before_max_col + a.count
    return {"before": {"max_column": before_max_col}, "after": {"max_column": check_ws.max_column}, "verified": verified}


def op_delete_cols(a):
    p = resolve(a.file)
    wb = load_write_wb(p)
    ws = sheet_or_default(wb, a.sheet)
    at = col_ref(a.at)
    before_max_col = ws.max_column
    ws.delete_cols(at, amount=a.count)
    target = save_target(wb, p, a.out)
    check_ws = load_write_wb(target)[ws.title]
    verified = check_ws.max_column <= before_max_col
    return {"before": {"max_column": before_max_col}, "after": {"max_column": check_ws.max_column}, "verified": verified}


def op_add_sheet(a):
    p = resolve(a.file)
    wb = load_write_wb(p)
    wb.create_sheet(title=a.name, index=a.index)
    target = save_target(wb, p, a.out)
    names = load_write_wb(target).sheetnames
    return {"after": {"sheets": names}, "verified": a.name in names}


def op_rename_sheet(a):
    p = resolve(a.file)
    wb = load_write_wb(p)
    wb[a.from_].title = a.to
    target = save_target(wb, p, a.out)
    names = load_write_wb(target).sheetnames
    return {"before": {"name": a.from_}, "after": {"name": a.to}, "verified": a.to in names and a.from_ not in names}


def op_delete_sheet(a):
    p = resolve(a.file)
    wb = load_write_wb(p)
    if len(wb.sheetnames) == 1:
        raise ValueError("refusing to delete the last sheet in the workbook")
    del wb[a.name]
    target = save_target(wb, p, a.out)
    names = load_write_wb(target).sheetnames
    return {"after": {"sheets": names}, "verified": a.name not in names}


def op_merge(a):
    p = resolve(a.file)
    wb = load_write_wb(p)
    ws = sheet_or_default(wb, a.sheet)
    ws.merge_cells(a.range)
    target = save_target(wb, p, a.out)
    check_ws = load_write_wb(target)[ws.title]
    verified = any(str(r) == a.range for r in check_ws.merged_cells.ranges)
    return {"after": {"merged": a.range}, "verified": verified}


def op_unmerge(a):
    p = resolve(a.file)
    wb = load_write_wb(p)
    ws = sheet_or_default(wb, a.sheet)
    ws.unmerge_cells(a.range)
    target = save_target(wb, p, a.out)
    check_ws = load_write_wb(target)[ws.title]
    verified = not any(str(r) == a.range for r in check_ws.merged_cells.ranges)
    return {"after": {"unmerged": a.range}, "verified": verified}


def op_set_format(a):
    p = resolve(a.file)
    wb = load_write_wb(p)
    ws = sheet_or_default(wb, a.sheet)
    min_col, min_row, max_col, max_row = range_boundaries(a.range)

    touched = 0
    for row in range(min_row, max_row + 1):
        for col in range(min_col, max_col + 1):
            cell = ws.cell(row=row, column=col)
            f = cell.font
            existing_color = None
            try:
                if f.color is not None and f.color.type == "rgb" and f.color.rgb:
                    rgb_val = f.color.rgb
                    if isinstance(rgb_val, str):
                        existing_color = rgb_val
                    elif hasattr(rgb_val, "value") and isinstance(rgb_val.value, str):
                        existing_color = rgb_val.value
            except Exception:
                existing_color = None
            cell.font = Font(
                name=a.font or f.name,
                size=a.size or f.size,
                bold=f.bold if a.bold is None else a.bold,
                color=a.font_color or existing_color,
            )
            if a.fill:
                cell.fill = PatternFill(fill_type="solid", start_color=a.fill, end_color=a.fill)
            if a.number_format:
                cell.number_format = a.number_format
            touched += 1

    target = save_target(wb, p, a.out)
    check_cell = load_write_wb(target)[ws.title].cell(row=min_row, column=min_col)
    verified = True
    if a.number_format:
        verified = verified and check_cell.number_format == a.number_format
    if a.bold is not None:
        verified = verified and bool(check_cell.font.bold) == a.bold
    return {"after": {"range": a.range, "cells_formatted": touched}, "verified": verified}


def op_add_image(a):
    from openpyxl.drawing.image import Image as XLImage
    from PIL import Image as PILImage

    p = resolve(a.file)
    wb = load_write_wb(p)
    ws = sheet_or_default(wb, a.sheet)

    img_path = resolve(a.path)
    if a.width_px:
        with PILImage.open(img_path) as im:
            ratio = a.width_px / im.width
            height_px = round(im.height * ratio)
        img = XLImage(str(img_path))
        img.width = a.width_px
        img.height = height_px
    else:
        img = XLImage(str(img_path))

    ws.add_image(img, a.anchor)
    target = save_target(wb, p, a.out)
    check_ws = load_write_wb(target)[ws.title]
    verified = len(check_ws._images) >= 1
    return {"after": {"anchor": a.anchor, "path": str(img_path)}, "verified": verified}


def op_recalc(a):
    import excel_com
    return excel_com.recalc(a.file, a.timeout)


def op_new(a):
    out = resolve(a.out)
    wb = openpyxl.Workbook()
    if a.sheets:
        names = [s.strip() for s in a.sheets.split(",") if s.strip()]
        wb.active.title = names[0]
        for n in names[1:]:
            wb.create_sheet(title=n)
    wb.save(out)
    names_after = load_write_wb(out).sheetnames
    return {"after": {"path": str(out), "sheets": names_after}, "verified": out.exists()}


# ---------- CLI wiring ----------

def build_parser():
    p = argparse.ArgumentParser(prog="xlsx_ops")
    sub = p.add_subparsers(dest="op", required=True)

    r = sub.add_parser("read")
    r.add_argument("file")
    r.add_argument("--sheet")
    r.add_argument("--range")

    f = sub.add_parser("find")
    f.add_argument("file")
    f.add_argument("text")
    f.add_argument("--sheet")

    sc = sub.add_parser("set-cell")
    sc.add_argument("file")
    sc.add_argument("--sheet", required=True)
    sc.add_argument("--cell", required=True)
    g = sc.add_mutually_exclusive_group(required=True)
    g.add_argument("--value")
    g.add_argument("--formula")
    sc.add_argument("--out")

    sr = sub.add_parser("set-range")
    sr.add_argument("file")
    sr.add_argument("--sheet", required=True)
    sr.add_argument("--start", required=True)
    sr.add_argument("--data", required=True)
    sr.add_argument("--out")

    ir = sub.add_parser("insert-rows")
    ir.add_argument("file")
    ir.add_argument("--sheet", required=True)
    ir.add_argument("--at", type=int, required=True)
    ir.add_argument("--count", type=int, default=1)
    ir.add_argument("--copy-format-from", type=int)
    ir.add_argument("--out")

    dr = sub.add_parser("delete-rows")
    dr.add_argument("file")
    dr.add_argument("--sheet", required=True)
    dr.add_argument("--at", type=int, required=True)
    dr.add_argument("--count", type=int, default=1)
    dr.add_argument("--out")

    ic = sub.add_parser("insert-cols")
    ic.add_argument("file")
    ic.add_argument("--sheet", required=True)
    ic.add_argument("--at", required=True)
    ic.add_argument("--count", type=int, default=1)
    ic.add_argument("--copy-format-from")
    ic.add_argument("--out")

    dc = sub.add_parser("delete-cols")
    dc.add_argument("file")
    dc.add_argument("--sheet", required=True)
    dc.add_argument("--at", required=True)
    dc.add_argument("--count", type=int, default=1)
    dc.add_argument("--out")

    as_ = sub.add_parser("add-sheet")
    as_.add_argument("file")
    as_.add_argument("--name", required=True)
    as_.add_argument("--index", type=int)
    as_.add_argument("--out")

    rs = sub.add_parser("rename-sheet")
    rs.add_argument("file")
    rs.add_argument("--from", dest="from_", required=True)
    rs.add_argument("--to", required=True)
    rs.add_argument("--out")

    ds = sub.add_parser("delete-sheet")
    ds.add_argument("file")
    ds.add_argument("--name", required=True)
    ds.add_argument("--out")

    mg = sub.add_parser("merge")
    mg.add_argument("file")
    mg.add_argument("--sheet", required=True)
    mg.add_argument("--range", required=True)
    mg.add_argument("--out")

    um = sub.add_parser("unmerge")
    um.add_argument("file")
    um.add_argument("--sheet", required=True)
    um.add_argument("--range", required=True)
    um.add_argument("--out")

    sf = sub.add_parser("set-format")
    sf.add_argument("file")
    sf.add_argument("--sheet", required=True)
    sf.add_argument("--range", required=True)
    sf.add_argument("--number-format")
    sf.add_argument("--bold", type=lambda s: s.lower() == "true")
    sf.add_argument("--font-color")
    sf.add_argument("--fill")
    sf.add_argument("--font")
    sf.add_argument("--size", type=float)
    sf.add_argument("--out")

    ai = sub.add_parser("add-image")
    ai.add_argument("file")
    ai.add_argument("--sheet", required=True)
    ai.add_argument("--anchor", required=True)
    ai.add_argument("--path", required=True)
    ai.add_argument("--width-px", type=int)
    ai.add_argument("--out")

    rc = sub.add_parser("recalc")
    rc.add_argument("file")
    rc.add_argument("--timeout", type=int, default=60)

    nw = sub.add_parser("new")
    nw.add_argument("--out", required=True)
    nw.add_argument("--sheets")

    return p


OPS = {
    "read": op_read,
    "find": op_find,
    "set-cell": op_set_cell,
    "set-range": op_set_range,
    "insert-rows": op_insert_rows,
    "delete-rows": op_delete_rows,
    "insert-cols": op_insert_cols,
    "delete-cols": op_delete_cols,
    "add-sheet": op_add_sheet,
    "rename-sheet": op_rename_sheet,
    "delete-sheet": op_delete_sheet,
    "merge": op_merge,
    "unmerge": op_unmerge,
    "set-format": op_set_format,
    "add-image": op_add_image,
    "recalc": op_recalc,
    "new": op_new,
}


def main():
    sys.path.insert(0, str(Path(__file__).parent))
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    args = build_parser().parse_args()
    try:
        result = OPS[args.op](args)
        if args.op == "recalc":
            emit(result)
        else:
            emit({"status": "ok", "op": args.op, **result})
    except Exception as e:
        emit({"status": "error", "op": args.op, "detail": str(e)})
        sys.exit(1)


if __name__ == "__main__":
    main()
