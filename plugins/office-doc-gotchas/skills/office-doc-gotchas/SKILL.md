---
name: office-doc-gotchas
description: Use when fixing or auditing filled Japanese review checklists in Excel (○/×/－ judgement column with a COUNTIF score showing 0 or #DIV/0!), when re-exporting a worksheet to a PDF that must match an existing one in page size and page count, or when replacing a PDF that carries stamp annotations (電子印鑑, 承認印).
---

# office-doc-gotchas

Field-tested traps in Excel and PDF work that ordinary spreadsheet and PDF guides don't cover. Load
the reference that matches the task:

| Task | Reference |
|---|---|
| Read, judge, or fix a filled checklist; score cells wrong; re-export a sheet to PDF | `references/excel-checklists.md` |
| Replace, regenerate, or check a PDF that has stamp annotations | `references/pdf-stamps.md` |

## Rules that apply to both

- Work on a local copy. Write back only after moving the original into a dated backup and comparing
  sha256 of the source and destination.
- Prove a fix with a cell-level or page-level diff against the original, not with a visual check.
- Never regenerate a stamped PDF and publish it unstamped. The stamp owner re-stamps the new export.
