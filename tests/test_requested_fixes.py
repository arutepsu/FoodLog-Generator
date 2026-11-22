import json
from pathlib import Path
import subprocess
import sys

import pytest

from foodlog.skill_engine import evaluate
from foodlog.reporting import create_report

ROOT = Path(__file__).resolve().parents[1]


def meal(taste="1.7"):
    payload = json.loads((ROOT / "skills/foodlog/references/example.json").read_text())
    item = next(a for a in payload["assessments"] if a["parameter"] == "taste")
    item["grade"] = taste
    return payload


def test_decimal_taste_survives_evaluation_report_and_revalidation():
    result = evaluate(meal())
    assert result["grade"] == "2.14"
    assert result["display_grade"] == "2.1"
    bundle = create_report(result)
    assert "| Taste | 8 WP | 1.7 | Very Good |" in bundle.markdown
    assert "1.7" in bundle.svg
    assert create_report(bundle.document.model_dump(mode="json")).svg == bundle.svg


@pytest.mark.parametrize("grade", ["0.9", "5.1", "1.75"])
def test_taste_requires_one_decimal_within_scale(grade):
    with pytest.raises(ValueError):
        evaluate(meal(grade))


def test_report_helper_creates_inline_png_without_permanent_export(tmp_path):
    source = tmp_path / "evaluation.json"
    source.write_text(json.dumps(evaluate(meal())), encoding="utf-8")
    preview = tmp_path / "preview"
    run = subprocess.run([sys.executable, str(ROOT / "skills/foodlog/scripts/report.py"),
                          str(source), "--preview-dir", str(preview)], capture_output=True, text=True)
    assert run.returncode == 0, run.stderr
    data = json.loads(run.stdout)
    png = Path(data["preview"]["png"])
    assert png.is_absolute() and png.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    assert str(png).replace("\\", "/") in data["markdown"]
    assert "<svg" not in data["markdown"]
    assert data["files"] is None
    assert not (tmp_path / "reports").exists()
