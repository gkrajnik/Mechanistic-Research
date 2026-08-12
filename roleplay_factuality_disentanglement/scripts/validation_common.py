"""Shared loading and reporting helpers for Stage 4 dataset validation."""
from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable


REQUIRED_COLUMNS = {
    "example_id",
    "pair_id",
    "topic",
    "split",
    "topic_split",
    "template_partition",
    "frame",
    "factuality",
    "template_family",
    "instruction_template_id",
    "question_variant",
    "context",
    "question",
    "answer_format",
    "forced_answer",
    "factual_answer",
    "source_note",
    "review_status",
}


@dataclass
class CheckResult:
    name: str
    passed: bool
    observed: object
    expected: object
    details: str = ""


def check(name: str, observed: object, expected: object, details: str = "") -> CheckResult:
    return CheckResult(name, observed == expected, observed, expected, details)


def load_csv_folder(folder: Path) -> tuple[list[dict[str, str]], list[Path]]:
    files = sorted(folder.glob("T*.csv"))
    rows: list[dict[str, str]] = []
    for path in files:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames is None:
                raise ValueError(f"{path} has no header row")
            for row_number, row in enumerate(reader, start=2):
                row["_source_file"] = path.name
                row["_source_row"] = str(row_number)
                rows.append(row)
    return rows, files


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def preserved_output_folder(base: Path) -> Path:
    if base.exists() and any(base.iterdir()):
        base = base.parent / f"{base.name}_{datetime.now():%Y%m%d_%H%M%S}"
    base.mkdir(parents=True, exist_ok=True)
    return base


def write_reports(
    output: Path,
    checks: Iterable[CheckResult],
    input_files: Iterable[Path],
    metadata: dict,
) -> tuple[Path, Path]:
    checks = list(checks)
    passed = sum(item.passed for item in checks)
    payload = {
        **metadata,
        "status": "PASS" if passed == len(checks) else "FAIL",
        "checks_passed": passed,
        "checks_total": len(checks),
        "input_files": [
            {"path": str(path), "sha256": sha256(path)} for path in input_files
        ],
        "checks": [asdict(item) for item in checks],
    }
    json_path = output / "validation_report.json"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = [
        "# Stage 4 automated validation report",
        "",
        f"**Status:** {payload['status']}",
        "",
        f"**Checks passed:** {passed}/{len(checks)}",
        "",
        "| Check | Expected | Observed | Result |",
        "|---|---:|---:|---|",
    ]
    for item in checks:
        expected = str(item.expected).replace("|", "\\|")
        observed = str(item.observed).replace("|", "\\|")
        lines.append(
            f"| {item.name} | {expected} | {observed} | "
            f"{'PASS' if item.passed else 'FAIL'} |"
        )
        if item.details:
            lines.extend(["", f"- **{item.name}:** {item.details}"])
    lines.extend([
        "",
        "This report checks structure and experimental bookkeeping only. It does not verify the",
        "real-world facts or establish that the prompts measure consciousness or human-like belief.",
        "",
    ])
    markdown_path = output / "validation_report.md"
    markdown_path.write_text("\n".join(lines), encoding="utf-8")
    return json_path, markdown_path
