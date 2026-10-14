# PDF stamp annotations

Some Japanese PDF editors store 電子印鑑 (approval stamps) as page annotations with a vendor
subtype, for example `/ASNT:DSTMP5`. They're neither images nor signatures: no `/Subtype /Image`,
no `/ByteRange`. Match the vendor prefix. A `\w+` regex stops at the colon, and an exact
`== "/ASNT"` check misses the suffix.

```python
from pypdf import PdfReader

def stamp_count(path, prefix="/ASNT"):
    r = PdfReader(path)
    return sum(1 for pg in r.pages for a in (pg.get("/Annots") or [])
               if str(a.get_object().get("/Subtype", "")).startswith(prefix))
```

Run it on a known-stamped original first to learn the prefix your tool writes. `/Link` annotations
on the same page are not stamps.

## Rules

- Regenerating a stamped PDF from its source drops every stamp. Produce the corrected export
  locally and have the stamp owner stamp it; never publish it unstamped.
- Before publishing a re-stamped file, compare it with the original: same page count, same page
  size, and `stamp_count(new) >= 1`.
- Count pages and read media boxes with pypdf, not regex. Microsoft Print to PDF output keeps page
  objects inside compressed object streams, so `/Type /Page` regexes find nothing.
