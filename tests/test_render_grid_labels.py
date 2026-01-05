from scripts.render_grid import build_conflict_label_lines, build_crop_label_lines, fit_text


def test_fit_text_truncates() -> None:
    assert fit_text("Carrots", 4) == "C..."
    assert fit_text("Carrots", 7) == "Carrots"


def test_build_crop_label_lines() -> None:
    lines = build_crop_label_lines("Carrots", "Bolero", width_px=120, font_size=10)
    assert lines[0] == "Carrots"
    assert lines[1] == "Bolero"


def test_build_conflict_label_lines() -> None:
    details = ["Arugula / Wild Arugula", "Lettuce / Allstar", "Spinach / Corvair"]
    lines = build_conflict_label_lines(details, width_px=120, font_size=8, max_lines=3)
    assert lines[0] == "!"
    assert lines[-1].startswith("+")
