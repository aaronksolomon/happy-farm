from pathlib import Path

import pandas as pd
import pytest

from scripts.io.schema import (
    ensure_csv_schema,
    ensure_jsonl_schema,
    read_schema_version_from_csv,
    read_schema_version_from_jsonl,
    validate_required_columns,
)


def test_read_schema_version_from_csv(tmp_path: Path) -> None:
    path = tmp_path / "data.csv"
    path.write_text("# schema_version: 2\ncol_a,col_b\n1,2\n", encoding="utf-8")
    assert read_schema_version_from_csv(path) == 2


def test_read_schema_version_from_csv_missing(tmp_path: Path) -> None:
    path = tmp_path / "data.csv"
    path.write_text("col_a,col_b\n1,2\n", encoding="utf-8")
    with pytest.raises(ValueError, match="schema_version"):
        read_schema_version_from_csv(path)


def test_read_schema_version_from_jsonl(tmp_path: Path) -> None:
    path = tmp_path / "config.jsonl"
    path.write_text('{"schema_version": 3}\n{"other": true}\n', encoding="utf-8")
    assert read_schema_version_from_jsonl(path) == 3


def test_schema_version_validation(tmp_path: Path) -> None:
    csv_path = tmp_path / "data.csv"
    csv_path.write_text("# schema_version: 1\ncol_a\n1\n", encoding="utf-8")
    assert ensure_csv_schema(csv_path, 1) == 1

    jsonl_path = tmp_path / "config.jsonl"
    jsonl_path.write_text('{"schema_version": 1}\n', encoding="utf-8")
    assert ensure_jsonl_schema(jsonl_path, 1) == 1


def test_validate_required_columns(tmp_path: Path) -> None:
    df = pd.DataFrame({"a": [1, ""], "b": [2, 3]})
    with pytest.raises(ValueError, match="empty required values"):
        validate_required_columns(df, ["a", "b"], "test")
