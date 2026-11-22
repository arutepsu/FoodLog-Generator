from copy import deepcopy
from decimal import Decimal
import json
from pathlib import Path
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

import pytest

from foodlog.skill_engine import evaluate
from foodlog.reporting import create_report, export_report

ROOT = Path(__file__).resolve().parents[1]
CASES = json.loads((ROOT/"tests/acceptance/cases.json").read_text(encoding="utf-8"))


def evaluation(case="complete-pasta"):
    return evaluate(next(c for c in CASES if c["id"] == case)["payload"])


def report(case="complete-pasta", **metadata):
    return create_report(evaluation(case), {"food_name":"Homemade Pasta", **metadata})


def texts(svg):
    return " ".join(ET.fromstring(svg).itertext())


def test_complete_report_agrees_with_validated_result():
    bundle = report(evaluation_date="2026-11-22",experience_type="Home-cooked",report_id="FL-TEST")
    assert bundle.document.evaluation.grade == Decimal("1.85")
    assert "**Overall Grade: 1.9 — GOOD**" in bundle.markdown
    assert "1.9" in texts(bundle.svg)
    assert "GOOD" in texts(bundle.svg)
    assert "22 November 2026" in bundle.markdown
    assert r"FL\-TEST" in bundle.markdown
    assert r"Home\-cooked" in bundle.markdown


def test_actual_five_annular_segments_have_fixed_geometry_and_legend():
    bundle = report()
    root = ET.fromstring(bundle.svg)
    paths = [p for p in root.iter() if p.tag.endswith("path") and "data-parameter" in p.attrib]
    assert len(paths) == 5
    expected = [("money","12","30","108"),("taste","8","20","72"),
                ("effort","6","15","54"),("nutrition","8","20","72"),("happiness","6","15","54")]
    for path, values in zip(paths,expected):
        assert tuple(path.attrib[k] for k in ("data-parameter","data-weight","data-percentage","data-angle")) == values
        assert path.attrib["d"].count(" A ") == 2
        assert path.attrib["d"].endswith(" Z")
    assert sum(Decimal(p.attrib["data-angle"]) for p in paths) == 360
    content = texts(bundle.svg)
    assert "Evaluation Weight Distribution" in content
    for label in ("Money","Taste","Effort","Nutrition","Happiness","30%","20%","15%"):
        assert label in content


def test_svg_is_responsive_and_accessible():
    root = ET.fromstring(report().svg)
    assert root.attrib["viewBox"] == "0 0 900 1060"
    assert root.attrib["role"] == "img"
    assert root.find("{http://www.w3.org/2000/svg}title") is not None
    assert root.find("{http://www.w3.org/2000/svg}desc") is not None


def test_effort_and_exact_weighted_breakdown_are_visible():
    bundle = report()
    assert "Time" in bundle.markdown and "Energy" in bundle.markdown
    assert "2.3" in bundle.markdown
    calculation = bundle.document.calculation
    assert calculation["weighted_total"] == "74"
    assert calculation["divisor"] == 40
    assert calculation["overall_raw"] == "1.85"
    assert calculation["components"][2]["weight_points"] == 4
    assert calculation["components"][2]["weighted_points"] == "12"
    assert calculation["components"][3]["weight_points"] == 2
    assert calculation["components"][3]["weighted_points"] == "2"
    assert "74 / 40 = 1.85" in bundle.markdown


@pytest.mark.parametrize("case",["missing-ramen","contradiction"])
def test_incomplete_report_preserves_available_grades_without_overall(case):
    bundle = report(case)
    assert "Incomplete Evaluation" in bundle.markdown
    assert "Incomplete Evaluation" in texts(bundle.svg)
    assert bundle.document.evaluation.grade is None
    assert bundle.document.calculation["weighted_total"] is None
    assert "Not evaluated" in bundle.markdown
    assert "**Overall Grade:" not in bundle.markdown
    if case == "missing-ramen":
        assert "| Taste | 8 WP | 2.0 | Good |" in bundle.markdown
        assert "five" not in texts(bundle.svg).lower()


def test_error_is_technical_failure_not_missing_user_information():
    payload = deepcopy(next(c for c in CASES if c["id"]=="complete-pasta")["payload"])
    payload["assessments"][1] = dict(parameter="taste",status="error",
                                    reasoning_summary="Assessment tool failed.")
    bundle = create_report(evaluate(payload))
    assert "Evaluation Error" in bundle.markdown
    assert "Evaluation Error" in texts(bundle.svg)
    assert "Assessment tool failed" in bundle.markdown
    assert "Technical failure" in bundle.markdown
    assert bundle.document.evaluation.grade is None


def test_independent_safety_warning_is_prominent_even_with_good_grade():
    data = evaluation()
    data["turns"].append(dict(id="safety",text="The chicken served alongside was spoiled."))
    data["safety_warnings"] = [dict(message="Do not eat the spoiled chicken.",
        evidence=[dict(source="safety",statement="The chicken served alongside was spoiled.")])]
    data["safe_to_recommend"] = False
    bundle = create_report(data)
    assert bundle.markdown.index("FOOD SAFETY WARNING") < bundle.markdown.index("Overall Grade")
    assert "Do not eat the spoiled chicken" in bundle.markdown
    assert "FOOD SAFETY WARNING" in texts(bundle.svg)
    assert "1.9" in texts(bundle.svg)


@pytest.mark.parametrize("mutation",["overall","display","classification","component_display","effort",
                                     "evidence","weight","status","safe","duplicate"])
def test_report_rejects_tampered_saved_results(mutation):
    data = evaluation()
    if mutation=="overall": data["grade"]="1"
    if mutation=="display": data["display_grade"]="2.0"
    if mutation=="classification": data["classification"]="Very Good"
    if mutation=="component_display": data["assessments"][0]["display_grade"]="5.0"
    if mutation=="effort": data["effort"]["grade"]="1"
    if mutation=="evidence": data["assessments"][0]["evidence"][0]["statement"]="Invented quote"
    if mutation=="weight": data["weight_points"]=50
    if mutation=="status": data["status"]="needs_clarification"
    if mutation=="safe": data["safe_to_recommend"]=True
    if mutation=="duplicate": data["assessments"][1]=data["assessments"][0]
    with pytest.raises(ValueError):
        create_report(data)


def test_user_text_is_escaped_in_markdown_and_svg():
    hostile = '<script>alert("x")</script> [link](javascript:evil) | # Title'
    data = evaluation()
    data["turns"][0]["text"] += " "+hostile
    data["assessments"][0]["evidence"].append(dict(source="meal",statement=hostile))
    # The complete-pasta fixture's single turn ID is meal.
    bundle = create_report(data,{"food_name":hostile,"summary":hostile})
    assert "<script>" not in bundle.svg
    assert "<script>" not in bundle.markdown
    assert "[link](javascript:evil)" not in bundle.markdown
    assert "\\|" in bundle.markdown
    assert hostile in texts(bundle.svg)
    assert all(not e.tag.endswith("script") for e in ET.fromstring(bundle.svg).iter())


def test_unknown_metadata_is_not_invented():
    bundle = create_report(evaluation())
    assert bundle.document.metadata.evaluation_date is None
    assert bundle.document.metadata.experience_type is None
    assert "Date:" not in bundle.markdown
    assert "Location:" not in bundle.markdown
    assert "Food name not provided" in bundle.markdown


def test_export_regeneration_is_deterministic_and_json_retains_raw_grade(tmp_path):
    bundle = report(report_id="FL-EXAMPLE")
    paths = export_report(bundle,tmp_path/"reports")
    assert paths["evaluation"].relative_to(tmp_path).as_posix() == "reports/FL-EXAMPLE/evaluation.json"
    stored = json.loads(paths["evaluation"].read_text(encoding="utf-8"))
    assert stored["evaluation"]["grade"] == "1.85"
    assert stored["report_version"] == "0.2"
    regenerated = create_report(stored)
    assert regenerated.svg == bundle.svg
    assert regenerated.markdown == bundle.markdown
    assert regenerated.document.calculation == bundle.document.calculation
    assert "charts/evaluation.svg" in paths["markdown"].read_text(encoding="utf-8")
    assert paths["svg"].read_text(encoding="utf-8") == bundle.svg
    with pytest.raises(FileExistsError):
        export_report(bundle,tmp_path/"reports")


@pytest.mark.parametrize("identifier",["../outside","a/b","..",""])
def test_export_id_cannot_escape_report_directory(identifier):
    with pytest.raises(ValueError):
        report(report_id=identifier)


def test_exported_calculations_cannot_be_tampered_with():
    data = report().document.model_dump(mode="json")
    data["calculation"]["weighted_total"]="40"
    with pytest.raises(ValueError):
        create_report(data)


def test_legacy_evaluation_without_numeric_measurements_still_reports():
    data = evaluation()
    data.pop("measurements",None)
    bundle = create_report(data)
    assert "Structured price not recorded" in bundle.markdown
    assert "EUR 5 per serving" in bundle.markdown


def test_new_evaluation_retains_supported_numeric_measurements():
    data = evaluation()
    assert data["measurements"]["money"]["lower"] == "5"
    assert data["measurements"]["time"]["lower"] == "30"
    bundle = create_report(data)
    assert "EUR 5 per serving" in bundle.markdown
    assert "30 minutes" in bundle.markdown


def test_report_helper_works_without_export_and_without_model_calls(tmp_path):
    data = tmp_path/"evaluation.json"
    data.write_text(json.dumps(evaluation()),encoding="utf-8")
    helper = ROOT/"skills/foodlog/scripts/report.py"
    run = subprocess.run([sys.executable,str(helper),str(data),"--food-name","Pasta"],
                         capture_output=True,text=True,cwd=tmp_path)
    assert run.returncode == 0,run.stderr
    result = json.loads(run.stdout)
    assert result["document"]["evaluation"]["display_grade"] == "1.9"
    assert result["files"] is None
    assert not (tmp_path/"reports").exists()

@pytest.mark.parametrize("parameter,raw,shown,label",[
    ("money","1.7","1.7","Very Good"),
    ("time","1.7","1.7","Very Good"),("energy","1.875","1.9","Good"),
    ("nutrition","1.75","1.8","Good"),("happiness","1.775","1.8","Good"),
])
def test_saved_component_domain_matches_approved_categorical_grades(parameter,raw,shown,label):
    data=evaluation()
    data.pop("measurements",None)
    item=next(a for a in data["assessments"] if a["parameter"]==parameter)
    item.update(grade="1.5",display_grade="1.5",classification="Very Good")
    data.update(grade=raw,display_grade=shown,classification=label)
    if parameter in ("time","energy"):
        data["effort"][parameter]=deepcopy(item)
        data["effort"].update(grade="1.333333333333333333333333333" if parameter=="time" else "2.5",
                              display_grade="1.3" if parameter=="time" else "2.5",
                              classification="Very Good" if parameter=="time" else "Good")
    with pytest.raises(ValueError,match="representative"):
        create_report(data)


def test_error_is_distinct_in_breakdown_and_accessible_chart_description():
    payload=deepcopy(next(c for c in CASES if c["id"]=="complete-pasta")["payload"])
    payload["assessments"][1]=dict(parameter="taste",status="error",reasoning_summary="Tool unavailable.")
    bundle=create_report(evaluate(payload))
    assert "| Taste | Evaluation error |" in bundle.markdown
    desc=ET.fromstring(bundle.svg).find("{http://www.w3.org/2000/svg}desc").text
    assert "Taste: evaluation error" in desc
