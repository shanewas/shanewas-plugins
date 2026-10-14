# Japanese review checklists in Excel

## Reading cell text

- `xl/sharedStrings.xml` entries can carry `<rPh>` furigana runs. Take text only from `<si>/<t>` and
  `<si>/<r>/<t>`, never every `<t>` under `<si>`. Excel keeps or drops furigana per save, so a naive
  reader reports "item text changed" between two files whose visible text is identical.
- Skip `~$*.xlsx` names. They're Excel lock files, and opening one raises `PermissionError` or
  `BadZipFile`.

## Filled or blank

File size says nothing: a filled copy can be within a few hundred bytes of its template. Count
judgement marks (cells whose whole value is one of ○ 〇 ◯ × ✕ ● － - ー △) and compare with the
template's own count. More marks than the template means someone filled it in.

## Look-alike marks break the score

Score cells typically use `COUNTIF(range,"○")` with ○ = U+25CB. Marks typed as 〇 (U+3007, kanji
zero) or ◯ (U+25EF) look identical on screen but aren't counted, so the score shows `0` or `#DIV/0!`.

- Flag a sheet only when a worksheet XML has a formula matching `<f>[^<]*"○"` *and* the sheet holds
  more 〇/◯ cells than its template. Checklists without a score formula may use 〇 on purpose.
- Fix with Excel COM on a local copy, whole-cell only, so longer text containing 〇 is untouched:

  ```powershell
  foreach ($ws in $wb.Worksheets) {
      foreach ($b in @([string][char]0x3007, [string][char]0x25EF)) {
          # LookAt 1 = xlWhole
          [void]$ws.UsedRange.Replace($b, [string][char]0x25CB, 1, 1, $false, $true)
      }
  }
  $xl.CalculateFull(); $wb.Save()
  ```

- Verify with a cell-level diff of original and fixed copy. Allowed changes: 〇/◯ → ○, and the
  results of formula cells. Anything else means stop.

## Re-exporting a PDF that must match the original

- `Workbook.ExportAsFixedFormat` prints every visible sheet (cover and instruction sheets included)
  at whatever paper size the active printer reports, which can come out non-A4. Originals are often
  one sheet only, on A4.
- `PrintOut` on that one sheet with an explicit printer and file name is silent:

  ```powershell
  $port = (Get-ItemProperty 'HKCU:\Software\Microsoft\Windows NT\CurrentVersion\Devices').'Microsoft Print to PDF'.Split(',')[1]
  $ws.PrintOut([Type]::Missing, [Type]::Missing, 1, $false, "Microsoft Print to PDF on $port", $true, [Type]::Missing, $pdfPath)
  ```

- Another driver has other margins, so row breaks move and the page count grows. Pin it to the
  original's count before printing, and don't save the workbook afterwards:
  `$ps.Zoom = $false; $ps.FitToPagesWide = 1; $ps.FitToPagesTall = <original pages>`.
- Setting `Application.ActivePrinter` fails under automation ("Unable to set the ActivePrinter
  property"), even to its current value. Pass the printer to `PrintOut` instead.
- Check the result with pypdf: page count, and every `mediabox` 595×842 for A4, against the original.
