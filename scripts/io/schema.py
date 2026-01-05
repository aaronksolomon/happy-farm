"""Schema helpers for CSV and JSONL inputs."""

from __future__ import annotations

import json
from pathlib import Path


def _read_lines(path: str | Path) -> list[str]:
    return Path(path).read_text(encoding="utf-8").splitlines()


def read_schema_version_from_csv(path: str | Path) -> int:
    """Return schema_version from a CSV header comment like '# schema_version: 1'."""
    for line in _read_lines(path):
        stripped = line.strip()
        if not stripped:
            continue
        if not stripped.startswith("#"):
            raise ValueError(f"Missing schema_version header comment in {path}")
        key, sep, value = stripped.lstrip("#").strip().partition(":")
        if key.strip() != "schema_version" or not sep:
            continue
        return int(value.strip())
    raise ValueError(f"Missing schema_version header comment in {path}")


def read_schema_version_from_jsonl(path: str | Path) -> int:
    """Return the first schema_version found in a JSONL config."""
    for line in _read_lines(path):
        stripped = line.strip()
        if not stripped:
            continue
        obj = json.loads(stripped)
        if "schema_version" in obj:
            return int(obj["schema_version"])
    raise ValueError(f"Missing schema_version in {path}")


def ensure_csv_schema(path: str | Path, expected_version: int) -> int:
    """Validate the CSV schema_version header comment and return it."""
    actual = read_schema_version_from_csv(path)
    _validate_schema_version(path, actual, expected_version)
    return actual


def ensure_jsonl_schema(path: str | Path, expected_version: int) -> int:
    """Validate the JSONL schema_version and return it."""
    actual = read_schema_version_from_jsonl(path)
    _validate_schema_version(path, actual, expected_version)
    return actual


def _validate_schema_version(path: str | Path, actual: int, expected: int) -> None:
    if actual != expected:
        raise ValueError(
            f"Schema version mismatch in {path}: expected {expected}, got {actual}"
        )


def validate_required_columns(
    df,
    required: list[str],
    context: str,
) -> None:
    missing_cols = [col for col in required if col not in df.columns]
    if missing_cols:
        missing_str = ", ".join(missing_cols)
        raise ValueError(f"{context} is missing required columns: {missing_str}")

    missing_values = [
        col for col in required if df[col].isna().any() or (df[col] == "").any()
    ]
    if missing_values:
        missing_str = ", ".join(missing_values)
        raise ValueError(f"{context} has empty required values: {missing_str}")
