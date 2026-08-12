"""Run Stage 4 automated checks without loading a language model."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from validation_common import load_csv_folder, preserved_output_folder, write_reports
from validation_rules import (
    balance_checks,
    label_checks,
    leakage_checks,
    preservation_checks,
    prompt_checks,
    schema_checks,
)

HERE = Path(__file__).resolve().parent.parent


def resolve(value: Path) -> Path:
    return value if value.is_absolute() else HERE / value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("inputs/draft/stage3_assigned_by_topic"),
    )
    parser.add_argument(
        "--original-dir",
        type=Path,
        default=Path("inputs/draft/stage2d_by_topic"),
    )
    parser.add_argument(
        "--split-manifest",
        type=Path,
        default=Path("inputs/validated/stage3_split_assignment_v1.json"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("results/validation/stage4_automated_v1"),
    )
    args = parser.parse_args()

    input_dir = resolve(args.input_dir)
    original_dir = resolve(args.original_dir)
    manifest_path = resolve(args.split_manifest)
    output = preserved_output_folder(resolve(args.output_dir))

    rows, input_files = load_csv_folder(input_dir)
    split_assignment = json.loads(manifest_path.read_text(encoding="utf-8"))
    checks = [
        *schema_checks(rows, input_files),
        *label_checks(rows),
        *balance_checks(rows),
        *leakage_checks(rows, split_assignment),
        *prompt_checks(rows),
        *preservation_checks(rows, original_dir),
    ]
    json_path, markdown_path = write_reports(
        output,
        checks,
        [*input_files, manifest_path],
        {
            "validation_stage": "Stage 4 automated structural validation",
            "validated_at": datetime.now().isoformat(timespec="seconds"),
            "input_directory": str(input_dir),
            "original_directory": str(original_dir),
            "split_manifest": str(manifest_path),
            "row_count": len(rows),
        },
    )
    failed = [item for item in checks if not item.passed]
    print(f"Checks passed: {len(checks) - len(failed)}/{len(checks)}")
    print(f"JSON report: {json_path}")
    print(f"Readable report: {markdown_path}")
    if failed:
        print("Failed checks:")
        for item in failed:
            print(f"  - {item.name}: expected {item.expected!r}; observed {item.observed!r}")
        return 1
    print("Automated validation PASSED. Manual fact verification is still required.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
