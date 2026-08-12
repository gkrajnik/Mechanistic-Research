"""Independent structural, balance, and leakage checks for the role-play dataset."""
from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path

from validation_common import REQUIRED_COLUMNS, CheckResult, check, load_csv_folder


def _count(rows: list[dict[str, str]], **conditions: str) -> int:
    return sum(
        all(row.get(column) == value for column, value in conditions.items())
        for row in rows
    )


def schema_checks(rows: list[dict[str, str]], files: list[Path]) -> list[CheckResult]:
    results = [
        check("topic file count", len(files), 10),
        check("total row count", len(rows), 480),
    ]
    missing = sorted({column for row in rows for column in REQUIRED_COLUMNS if column not in row})
    blank_required = sum(
        not str(row.get(column, "")).strip()
        for row in rows
        for column in REQUIRED_COLUMNS
    )
    results.extend([
        check("missing required columns", len(missing), 0, ", ".join(missing)),
        check("blank required values", blank_required, 0),
        check("unique example IDs", len({row["example_id"] for row in rows}), 480),
        check(
            "duplicate complete rows",
            len(rows) - len({
                tuple(sorted((key, value) for key, value in row.items() if not key.startswith("_")))
                for row in rows
            }),
            0,
        ),
        check("rows per topic file", sorted(Counter(row["_source_file"] for row in rows).values()), [48] * 10),
    ])
    return results


def label_checks(rows: list[dict[str, str]]) -> list[CheckResult]:
    allowed = {
        "topic_split": {"train", "validation", "test"},
        "template_partition": {"development", "heldout_wording"},
        "frame": {"normal", "roleplay"},
        "factuality": {"factual", "nonfactual"},
        "question_variant": {"true_form", "false_form"},
        "forced_answer": {"Yes", "No"},
        "factual_answer": {"Yes", "No"},
        "review_status": {"draft"},
    }
    results: list[CheckResult] = []
    for column, values in allowed.items():
        invalid = sorted({row[column] for row in rows if row[column] not in values})
        results.append(check(f"allowed values: {column}", len(invalid), 0, ", ".join(invalid)))

    factuality_errors = sum(
        row["factuality"]
        != ("factual" if row["forced_answer"] == row["factual_answer"] else "nonfactual")
        for row in rows
    )
    question_answer_errors = sum(
        row["factual_answer"]
        != ("Yes" if row["question_variant"] == "true_form" else "No")
        for row in rows
    )
    template_errors = 0
    for row in rows:
        suffix = row["template_family"][1:]
        expected_id = ("N" if row["frame"] == "normal" else "R") + suffix
        template_errors += row["instruction_template_id"] != expected_id
    results.extend([
        check("factuality labels agree with forced answers", factuality_errors, 0),
        check("question forms agree with factual answers", question_answer_errors, 0),
        check("template IDs agree with frame and family", template_errors, 0),
        check(
            "fixed answer-format instruction",
            sum(row["answer_format"] != "Answer only Yes or No." for row in rows),
            0,
        ),
    ])
    return results


def balance_checks(rows: list[dict[str, str]]) -> list[CheckResult]:
    expected_counts = [
        ("normal frame", _count(rows, frame="normal"), 240),
        ("role-play frame", _count(rows, frame="roleplay"), 240),
        ("factual", _count(rows, factuality="factual"), 240),
        ("nonfactual", _count(rows, factuality="nonfactual"), 240),
        ("forced Yes", _count(rows, forced_answer="Yes"), 240),
        ("forced No", _count(rows, forced_answer="No"), 240),
        ("factual-answer Yes", _count(rows, factual_answer="Yes"), 240),
        ("factual-answer No", _count(rows, factual_answer="No"), 240),
        ("train rows", _count(rows, topic_split="train"), 288),
        ("validation rows", _count(rows, topic_split="validation"), 96),
        ("test rows", _count(rows, topic_split="test"), 96),
        ("development wording", _count(rows, template_partition="development"), 400),
        ("held-out wording", _count(rows, template_partition="heldout_wording"), 80),
        ("probe-fitting subset", _count(rows, topic_split="train", template_partition="development"), 240),
        ("selection subset", _count(rows, topic_split="validation", template_partition="development"), 80),
        ("primary topic test", _count(rows, topic_split="test", template_partition="development"), 80),
        ("held-out wording test", _count(rows, topic_split="train", template_partition="heldout_wording"), 48),
        ("joint generalization test", _count(rows, topic_split="test", template_partition="heldout_wording"), 16),
    ]
    results = [check(name, observed, expected) for name, observed, expected in expected_counts]

    groups: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[(row["pair_id"], row["question_variant"], row["template_family"])].append(row)
    invalid_groups = 0
    expected_cells = {
        ("normal", "Yes"), ("normal", "No"),
        ("roleplay", "Yes"), ("roleplay", "No"),
    }
    for group in groups.values():
        cells = {(row["frame"], row["forced_answer"]) for row in group}
        invalid_groups += len(group) != 4 or cells != expected_cells
    results.append(check("complete 2x2 groups", invalid_groups, 0))
    return results


def leakage_checks(
    rows: list[dict[str, str]], split_assignment: dict
) -> list[CheckResult]:
    pair_splits: dict[str, set[str]] = defaultdict(set)
    errors = Counter()
    for row in rows:
        pair_splits[row["pair_id"]].add(row["topic_split"])
        errors["split_copy"] += row["split"] != row["topic_split"]
        errors["topic_manifest"] += (
            row["topic_split"] != split_assignment["topic_assignments"].get(row["pair_id"])
        )
        errors["template_manifest"] += (
            row["template_partition"]
            != split_assignment["template_partitions"].get(row["template_family"])
        )
        errors["f06_development"] += (
            row["template_family"] == "F06"
            and row["template_partition"] == "development"
        )
        errors["development_heldout"] += (
            row["template_family"] != "F06"
            and row["template_partition"] == "heldout_wording"
        )
    crossing = sum(len(splits) > 1 for splits in pair_splits.values())
    return [
        check("pair IDs crossing topic splits", crossing, 0),
        check("split compatibility column", errors["split_copy"], 0),
        check("topic assignments match frozen manifest", errors["topic_manifest"], 0),
        check("template assignments match frozen manifest", errors["template_manifest"], 0),
        check("F06 rows leaking into development", errors["f06_development"], 0),
        check("F01-F05 rows leaking into held-out wording", errors["development_heldout"], 0),
    ]


def prompt_checks(rows: list[dict[str, str]]) -> list[CheckResult]:
    errors = Counter()
    f06_scenarios: dict[tuple[str, str], dict[str, str]] = defaultdict(dict)
    for row in rows:
        errors["placeholder"] += "{" in row["context"] or "}" in row["context"]
        errors["question_in_context"] += row["question"].lower() in row["context"].lower()
        if row["template_family"] == "F06":
            scenario = row["context"].split(".", 1)[0].strip().lower()
            f06_scenarios[(row["pair_id"], row["question_variant"])][row["frame"]] = scenario
    scenario_errors = sum(
        frames.get("normal") != frames.get("roleplay") for frames in f06_scenarios.values()
    )
    return [
        check("unresolved context placeholders", errors["placeholder"], 0),
        check("questions copied into framing context", errors["question_in_context"], 0),
        check("matched F06 neutral scenarios", scenario_errors, 0),
    ]


def preservation_checks(
    assigned_rows: list[dict[str, str]], original_folder: Path
) -> list[CheckResult]:
    original_rows, original_files = load_csv_folder(original_folder)
    added_columns = {"topic_split", "template_partition"}

    def canonical(row: dict[str, str], assigned: bool) -> tuple:
        cleaned = {
            key: value
            for key, value in row.items()
            if not key.startswith("_") and key not in added_columns
        }
        if assigned:
            cleaned["split"] = "unassigned"
        return tuple(sorted(cleaned.items()))

    original_set = {canonical(row, False) for row in original_rows}
    assigned_set = {canonical(row, True) for row in assigned_rows}
    preservation_mismatches = len(original_set.symmetric_difference(assigned_set))
    return [
        check("original Stage 2D file count", len(original_files), 10),
        check("assigned rows preserve Stage 2D content", preservation_mismatches, 0),
    ]
