import sys

from scripts.build_assignments import main as build_main
from scripts.calculate_succession_planting import main as calc_main
from scripts.load_data import main as load_main
from scripts.render_grid import main as render_main


def test_load_data_main_handles_error(monkeypatch, capsys) -> None:
    monkeypatch.setattr(sys, "argv", ["load_data.py", "--schedule", "/nope.csv"])
    assert load_main() == 1
    assert "Error:" in capsys.readouterr().out


def test_build_assignments_main_handles_error(monkeypatch, capsys) -> None:
    monkeypatch.setattr(sys, "argv", ["build_assignments.py", "--assignments", "/nope.csv"])
    assert build_main() == 1
    assert "Error:" in capsys.readouterr().out


def test_calculate_succession_main_handles_error(monkeypatch, capsys) -> None:
    monkeypatch.setattr(sys, "argv", ["calculate_succession_planting.py", "--plant-data", "/nope.csv"])
    assert calc_main() == 1
    assert "Error:" in capsys.readouterr().out


def test_render_grid_main_handles_error(monkeypatch, capsys) -> None:
    monkeypatch.setattr(sys, "argv", ["render_grid.py", "--assignments", "/nope.csv"])
    assert render_main() == 1
    assert "Error:" in capsys.readouterr().out
