#!/usr/bin/env python3
"""Black-box verification harness for the Mini-C compiler and U-code interpreter.

The harness deliberately treats the compiler/interpreter as black boxes: it
compiles each fixture in an isolated temporary directory, executes the emitted
U-code, and compares observable output with the test's expected output.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CASES_DIR = Path(__file__).resolve().parent / "cases"


@dataclass
class Result:
    name: str
    status: str
    category: str
    expected: str = ""
    actual: str = ""
    detail: str = ""
    duration_seconds: float = 0.0


def normalize_output(value: str) -> str:
    """Ignore whitespace differences while preserving token/output order."""
    return " ".join(value.split())


def resolve_executable(value: str, root: Path) -> str:
    candidate = Path(value).expanduser()
    if candidate.is_absolute():
        return str(candidate)
    if candidate.parent != Path("."):
        return str((Path.cwd() / candidate).resolve())
    local = root / value
    return str(local.resolve()) if local.exists() else value


def load_cases(filter_text: str | None = None) -> list[dict[str, Any]]:
    cases = []
    for manifest in sorted(CASES_DIR.glob("*.json")):
        data = json.loads(manifest.read_text(encoding="utf-8"))
        source = manifest.with_suffix(".mc")
        if not source.exists():
            raise FileNotFoundError(f"Missing source fixture for {manifest.name}: {source.name}")
        data["manifest"] = manifest
        data["source"] = source
        if filter_text and filter_text.lower() not in data["name"].lower():
            continue
        cases.append(data)
    return cases


def execute_case(case: dict[str, Any], minic: str, ucodei: str, timeout: float) -> Result:
    started = time.monotonic()
    name = case["name"]
    expected = normalize_output(str(case.get("expected_output", "")))
    stdin_data = str(case.get("stdin", ""))
    category = str(case.get("category", "functional"))

    if not Path(minic).exists() or not os.access(minic, os.X_OK):
        return Result(name, "ERROR", "setup", expected, detail=f"Compiler executable not found or not executable: {minic}")
    if not Path(ucodei).exists() or not os.access(ucodei, os.X_OK):
        return Result(name, "ERROR", "setup", expected, detail=f"U-code interpreter not found or not executable: {ucodei}")

    with tempfile.TemporaryDirectory(prefix="minic-verify-") as temporary:
        work = Path(temporary)
        source = work / "case.mc"
        source.write_text(case["source"].read_text(encoding="utf-8"), encoding="utf-8")

        try:
            compiled = subprocess.run(
                [minic, "case.mc"], cwd=work, text=True, capture_output=True,
                timeout=timeout, check=False,
            )
        except subprocess.TimeoutExpired:
            return Result(name, "FAIL", "compiler-timeout", expected, detail=f"Compiler exceeded {timeout:g}s", duration_seconds=time.monotonic()-started)

        uco = work / "case.uco"
        diagnostics = (compiled.stdout + "\n" + compiled.stderr).strip()
        if compiled.returncode != 0 or not uco.exists() or "syntax error" in diagnostics.lower():
            return Result(name, "FAIL", "compile", expected, detail=(diagnostics or f"Compiler exited with {compiled.returncode}"), duration_seconds=time.monotonic()-started)

        try:
            executed = subprocess.run(
                [ucodei, "case.uco"], cwd=work, input=stdin_data, text=True,
                capture_output=True, timeout=timeout, check=False,
            )
        except subprocess.TimeoutExpired:
            return Result(name, "FAIL", "execution-timeout", expected, detail=f"Interpreter exceeded {timeout:g}s", duration_seconds=time.monotonic()-started)

        actual = normalize_output(executed.stdout)
        if executed.returncode != 0:
            return Result(name, "FAIL", "runtime", expected, actual, (executed.stderr or executed.stdout).strip(), time.monotonic()-started)
        if actual != expected:
            detail = f"Output mismatch. Compiler stdout: {compiled.stdout.strip() or '(empty)'}"
            return Result(name, "FAIL", "wrong-output", expected, actual, detail, time.monotonic()-started)
        return Result(name, "PASS", category, expected, actual, duration_seconds=time.monotonic()-started)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run black-box Mini-C compiler verification tests.")
    parser.add_argument("--minic", default=str(ROOT / "minic"), help="Path to the Mini-C compiler (default: ./minic)")
    parser.add_argument("--ucodei", default=str(ROOT / "ucodei"), help="Path to the U-code interpreter (default: ./ucodei)")
    parser.add_argument("--filter", help="Run only test names containing this text")
    parser.add_argument("--timeout", type=float, default=5.0, help="Timeout in seconds per compile or execution (default: 5)")
    parser.add_argument("--list", action="store_true", help="List discovered tests without running them")
    parser.add_argument("--json-report", help="Write machine-readable results to this JSON file")
    args = parser.parse_args()

    minic = resolve_executable(args.minic, ROOT)
    ucodei = resolve_executable(args.ucodei, ROOT)
    try:
        cases = load_cases(args.filter)
    except (OSError, ValueError, KeyError) as error:
        print(f"ERROR: Could not load test cases: {error}", file=sys.stderr)
        return 2

    if args.list:
        for case in cases:
            print(f"{case['name']:<28} {case.get('category', 'functional')}")
        print(f"\n{len(cases)} test(s)")
        return 0
    if not cases:
        print("No test cases matched the requested filter.", file=sys.stderr)
        return 2

    print("Mini-C Compiler Verification Suite")
    print(f"Compiler:     {minic}")
    print(f"Interpreter:  {ucodei}")
    print(f"Test cases:   {len(cases)}\n")

    results = []
    for case in cases:
        result = execute_case(case, minic, ucodei, args.timeout)
        results.append(result)
        marker = "PASS" if result.status == "PASS" else result.status
        print(f"[{marker:<5}] {result.name:<28} {result.detail if result.status != 'PASS' else result.actual}")

    passed = sum(result.status == "PASS" for result in results)
    failed = sum(result.status == "FAIL" for result in results)
    errors = sum(result.status == "ERROR" for result in results)
    print(f"\nSummary: {passed} passed, {failed} failed, {errors} setup error(s), {len(results)} total")

    if args.json_report:
        report_path = Path(args.json_report).expanduser().resolve()
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps({"summary": {"passed": passed, "failed": failed, "errors": errors, "total": len(results)}, "results": [asdict(r) for r in results]}, indent=2), encoding="utf-8")
        print(f"JSON report: {report_path}")

    return 0 if failed == 0 and errors == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
