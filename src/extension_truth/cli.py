from __future__ import annotations

import argparse
import csv
import io
import json
import sys
from pathlib import Path

from .checker import Finding, inspect_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="extension-truth", description="Compare filename extensions with actual file signatures without renaming anything.")
    parser.add_argument("target", type=Path)
    parser.add_argument("--recursive", action="store_true")
    parser.add_argument("--format", choices=("text", "json", "csv"), default="text")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--fail-on-mismatch", action="store_true")
    args = parser.parse_args(argv)
    try:
        findings = inspect_path(args.target, args.recursive)
    except (OSError, ValueError) as exc:
        print(f"extension-truth: {exc}", file=sys.stderr)
        return 2
    report = render(findings, args.format)
    if args.output:
        args.output.write_text(report, encoding="utf-8")
        print(f"Wrote {args.format} report to {args.output}")
    else:
        print(report, end="")
    return 1 if args.fail_on_mismatch and any(item.status == "mismatch" for item in findings) else 0


def render(findings: tuple[Finding, ...], format_name: str) -> str:
    if format_name == "json":
        return json.dumps({"files": [item.to_dict() for item in findings]}, indent=2) + "\n"
    if format_name == "csv":
        output = io.StringIO(newline="")
        writer = csv.writer(output)
        writer.writerow(("path", "status", "detected_type", "current_extension", "expected_extensions", "proposed_name", "collision"))
        for item in findings:
            writer.writerow((item.path, item.status, item.detected_type or "", item.current_extension, " ".join(item.expected_extensions), item.proposed_name or "", str(item.collision).lower()))
        return output.getvalue()
    lines = []
    for item in findings:
        detail = item.detected_type or "signature not recognized"
        if item.proposed_name:
            detail += f"; proposed {item.proposed_name}" + (" (collision)" if item.collision else "")
        lines.append(f"{item.status.upper():8} {item.path} — {detail}")
    return "\n".join(lines) + ("\n" if lines else "")


if __name__ == "__main__":
    raise SystemExit(main())
