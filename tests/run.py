#!/usr/bin/env python3
"""Zero-dependency test runner for shanewas-plugins (stdlib only).

Discovers tests/test_*.py next to this file, runs every test_* function,
and reports results. Works on Python 3.9+ with no third-party packages.

Usage:
    python3 tests/run.py        # from the repo root (or any cwd)
"""

import importlib.util
import sys
import traceback
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTS_DIR))


def discover():
    cases = []
    for path in sorted(TESTS_DIR.glob("test_*.py")):
        spec = importlib.util.spec_from_file_location(path.stem, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        for attr in sorted(dir(module)):
            if attr.startswith("test_") and callable(getattr(module, attr)):
                cases.append(("%s.%s" % (path.stem, attr),
                              getattr(module, attr)))
    return cases


def main():
    cases = discover()
    if not cases:
        print("ERROR: no tests discovered under %s" % TESTS_DIR)
        return 1
    failures = 0
    for name, fn in cases:
        try:
            fn()
        except AssertionError as exc:
            failures += 1
            print("FAIL %s: %s" % (name, exc))
        except Exception:  # noqa: BLE001 - runner must report, not crash
            failures += 1
            print("FAIL %s: unexpected error" % name)
            traceback.print_exc()
        else:
            print("ok %s" % name)
    passed = len(cases) - failures
    print("%d passed, %d failed (%d total)" % (passed, failures, len(cases)))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
