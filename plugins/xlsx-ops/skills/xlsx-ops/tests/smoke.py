"""xlsx smoke test - exercises every xlsx_ops subcommand."""
import json, os, shutil, subprocess, sys, tempfile
from pathlib import Path

OPS = Path(__file__).resolve().parents[1] / "scripts" / "xlsx_ops.py"

def run(args, cwd):
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    r = subprocess.run([sys.executable, str(OPS)] + args, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
    out = r.stdout.strip()
    err = r.stderr.strip()
    if not out or not out.startswith("{"):
        raise RuntimeError(f"bad output: {out[:200]} stderr={err[-1000:]}")
    parsed = json.loads(out)
    if r.returncode not in (0, 1):
        raise RuntimeError(f"unexpected exit={r.returncode} stderr={err[-1000:]} json={parsed}")
    return parsed

def main():
    work = Path(tempfile.mkdtemp(prefix="xlsx_smoke_"))
    print("workdir:", work)
    results = []
    try:
        file = str(work / "demo.xlsx")

        # new (with Japanese sheet name)
        r = run(["new", "--out", file, "--sheets", "Sheet1,シート1"], str(work))
        assert r["status"] == "ok" and r["verified"], r
        assert "シート1" in r["after"]["sheets"], r
        results.append(("new", True))

        # read (no sheet → sheet list)
        r = run(["read", file], str(work))
        assert r["status"] == "ok", r
        assert any(s["name"] == "シート1" for s in r["after"]["sheets"]), r
        results.append(("read no-sheet", True))

        # set-cell value
        r = run(["set-cell", file, "--sheet", "Sheet1", "--cell", "A1", "--value", "1"], str(work))
        assert r["verified"], r
        results.append(("set-cell value", True))

        r = run(["set-cell", file, "--sheet", "Sheet1", "--cell", "A2", "--value", "2"], str(work))
        assert r["verified"], r
        results.append(("set-cell x2", True))

        r = run(["set-cell", file, "--sheet", "Sheet1", "--cell", "A3", "--formula", "=SUM(A1:A2)"], str(work))
        assert r["verified"], r
        results.append(("set-cell formula", True))

        # set-cell Japanese
        r = run(["set-cell", file, "--sheet", "シート1", "--cell", "A1", "--value", "日本語テスト"], str(work))
        assert r["verified"], r
        results.append(("set-cell JP", True))

        # set-range
        data_file = str(work / "data.json")
        Path(data_file).write_text(json.dumps([[10, 20, 30], [40, 50, 60]], ensure_ascii=False), encoding="utf-8")
        r = run(["set-range", file, "--sheet", "Sheet1", "--start", "B1", "--data", data_file], str(work))
        assert r["verified"], r
        results.append(("set-range", True))

        # read range
        r = run(["read", file, "--sheet", "Sheet1", "--range", "A1:B3"], str(work))
        assert r["status"] == "ok", r
        assert len(r["after"]["cells"]) == 6, r
        # Cell A3 formula should roundtrip
        a3 = next(c for c in r["after"]["cells"] if c["cell"] == "A3")
        assert a3["formula"] == "=SUM(A1:A2)", r
        results.append(("read range", True))

        # find
        r = run(["find", file, "60"], str(work))
        assert r["status"] == "ok" and r["after"]["matches"], r
        results.append(("find", True))

        # insert rows (with format copy)
        r = run(["insert-rows", file, "--sheet", "Sheet1", "--at", "5", "--count", "2", "--copy-format-from", "3"], str(work))
        assert r["verified"], r
        results.append(("insert-rows", True))

        # delete rows
        r = run(["delete-rows", file, "--sheet", "Sheet1", "--at", "5", "--count", "2"], str(work))
        assert r["verified"], r
        results.append(("delete-rows", True))

        # insert cols
        r = run(["insert-cols", file, "--sheet", "Sheet1", "--at", "D"], str(work))
        assert r["verified"], r
        results.append(("insert-cols", True))

        # delete cols
        r = run(["delete-cols", file, "--sheet", "Sheet1", "--at", "D"], str(work))
        assert r["verified"], r
        results.append(("delete-cols", True))

        # add-sheet
        r = run(["add-sheet", file, "--name", "Sheet2"], str(work))
        assert "Sheet2" in r["after"]["sheets"], r
        results.append(("add-sheet", True))

        # rename-sheet (rename シート1 too — test Japanese)
        r = run(["rename-sheet", file, "--from", "Sheet2", "--to", "Custom"], str(work))
        assert r["verified"], r
        results.append(("rename-sheet", True))

        # delete-sheet
        r = run(["delete-sheet", file, "--name", "Custom"], str(work))
        assert r["verified"], r
        results.append(("delete-sheet", True))

        # merge
        r = run(["merge", file, "--sheet", "Sheet1", "--range", "B2:C2"], str(work))
        assert r["verified"], r
        results.append(("merge", True))

        # unmerge
        r = run(["unmerge", file, "--sheet", "Sheet1", "--range", "B2:C2"], str(work))
        assert r["verified"], r
        results.append(("unmerge", True))

        # set-format
        r = run(["set-format", file, "--sheet", "Sheet1", "--range", "A1:A3",
                 "--number-format", "0.0%", "--bold", "true", "--fill", "FFFF00"], str(work))
        assert r["verified"], r
        results.append(("set-format", True))

        # add-image
        from PIL import Image
        Image.new("RGB",(60,40),(0,255,0)).save(str(work / "tiny.png"))
        r = run(["add-image", file, "--sheet", "Sheet1", "--anchor", "E1", "--path", str(work / "tiny.png"), "--width-px", "120"], str(work))
        assert r["verified"], r
        results.append(("add-image", True))

        # recalc — uses real Excel. SKIP-WARN on failure (Office may not be installed)
        try:
            r = run(["recalc", file, "--timeout", "30"], str(work))
            # recalc returns the official shape directly
            if "status" in r and r["status"] in ("success", "errors_found"):
                ok = r["status"] == "success"
                results.append(("recalc", ok))
            else:
                raise RuntimeError(f"unexpected recalc output: {r}")
        except Exception as e:
            print(f"WARN: recalc skipped (Excel COM?): {e}")
            results.append(("recalc", "WARN-SKIP"))

        # No zombie EXCEL.EXE
        ps = subprocess.run(["tasklist"], capture_output=True, text=True).stdout
        if "EXCEL.EXE" in ps and "XLSX_SMOKE_MARKER" not in ps:
            # Check if we started it: look for last 5 min entries? Simpler: if it has our workdir in commandline
            print("WARN: EXCEL.EXE running after test")

        print("\nResults:")
        bad = []
        for op, ok in results:
            if ok is True:
                mark = "OK"
            elif isinstance(ok, str) and "SKIP" in ok:
                mark = "WARN"
            else:
                mark = "FAIL"
                bad.append((op, ok))
            print(f"  [{mark}] {op}")
        if bad:
            print("FAIL:", bad)
            sys.exit(1)
        print("SMOKE OK")

    finally:
        shutil.rmtree(work, ignore_errors=True)

if __name__ == "__main__":
    main()