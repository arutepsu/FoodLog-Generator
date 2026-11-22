"""Replay recorded Codex-host judgments through installed FoodLog helpers.

These are acceptance fixtures, not an automated language-model invocation.
Live cross-host model comparison is tracked separately.
"""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys

import pytest
from foodlog.skill_engine import evaluate

ROOT = Path(__file__).resolve().parents[1]
CASES = json.loads((ROOT/"tests/acceptance/cases.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("host", [".agents", ".claude"])
@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_recorded_host_assessment_replays_in_installed_helper(host, case):
    helper = ROOT/host/"skills/foodlog/scripts/evaluate.py"
    run = subprocess.run([sys.executable,str(helper),"-"],input=json.dumps(case["payload"]),
                         capture_output=True,text=True)
    assert run.returncode == 0, run.stderr
    result = json.loads(run.stdout)
    expected = case["expected"]
    for key in ("status","grade","display_grade","classification"):
        assert result[key] == expected[key]
    assert {a["parameter"]:a["grade"] for a in result["assessments"]} == expected["grades"]
    assert len(result["questions"]) == expected["question_count"]
    assert len(result["conflicts"]) == expected.get("conflict_count",0)
    assert len(result["safety_warnings"]) == expected.get("safety_count",0)
    assert result["safe_to_recommend"] is expected.get("safe_to_recommend")
    assert result["weight_points"] == 40
    assert result["turns"] == case["payload"]["turns"]


def test_money_and_happiness_are_independent_under_price_correction():
    original = next(c for c in CASES if c["id"] == "restaurant")["payload"]
    corrected = deepcopy(original)
    corrected["turns"].append(dict(id="correction",text="Correction: my own meal cost EUR 2 including mandatory charges."))
    money = next(a for a in corrected["assessments"] if a["parameter"] == "money")
    money.update(lower="2",evidence=[dict(source="correction",statement="my own meal cost EUR 2 including mandatory charges")],
                 uncertainties=["User explicitly corrected the earlier price."])
    before,after = evaluate(original),evaluate(corrected)
    assert before["assessments"][0]["grade"] == "5"
    assert after["assessments"][0]["grade"] == "1"
    assert before["assessments"][-1] == after["assessments"][-1]
    assert after["assessments"][-1]["grade"] == "1"


def test_safety_warning_is_independent_of_complete_good_score():
    complete = deepcopy(next(c for c in CASES if c["id"] == "complete-pasta")["payload"])
    complete["turns"].append(dict(id="warning",text="The chicken served alongside it was spoiled."))
    complete["safety_warnings"] = [dict(message="Do not eat the spoiled chicken.",
        evidence=[dict(source="warning",statement="The chicken served alongside it was spoiled.")])]
    result = evaluate(complete)
    assert result["display_grade"] == "1.9"
    assert result["safe_to_recommend"] is False
    assert result["safety_warnings"][0]["message"] == "Do not eat the spoiled chicken."


def test_ambiguous_taste_can_be_resolved_without_assuming_happiness():
    original = deepcopy(next(c for c in CASES if c["id"] == "contradiction")["payload"])
    original["turns"].append(dict(id="clarification",text="Amazing referred to the decoration. I hated the taste. The overall experience was neutral."))
    original["conflicts"] = []
    for a in original["assessments"]:
        if a["parameter"] in ("taste","happiness"):
            key = a["parameter"]
            a.clear()
            a.update(parameter=key,status="evaluated",grade=5 if key=="taste" else 3,
                     evidence=[dict(source="clarification",statement="I hated the taste." if key=="taste" else "The overall experience was neutral.")],
                     reasoning_summary="The user explicitly clarified the ambiguous description.",
                     uncertainties=["Earlier amazing referred to decoration rather than flavor."])
    result = evaluate(original)
    assert result["assessments"][1]["grade"] == "5"
    assert result["assessments"][-1]["grade"] == "3"
    assert not result["conflicts"]
    assert result["grade"] is None
    assert len(result["turns"]) == 2

def test_ramen_followup_completes_without_losing_original_taste():
    payload = json.loads((ROOT/"tests/acceptance/ramen-followup.json").read_text(encoding="utf-8"))
    result = evaluate(payload)
    assert result["status"] == "complete"
    assert result["grade"] == "2.15"
    assert result["display_grade"] == "2.2"
    assert result["classification"] == "Good"
    assert not result["questions"]
    assert len(result["turns"]) == 2
    assert result["assessments"][1]["evidence"][0]["source"] == "meal"
    assert result["assessments"][0]["evidence"][0]["source"] == "followup"


def test_happiness_correction_does_not_change_money():
    payload = deepcopy(next(c for c in CASES if c["id"]=="restaurant")["payload"])
    payload["turns"].append(dict(id="correction",text="Correction: the overall experience was unpleasant."))
    happiness = next(a for a in payload["assessments"] if a["parameter"]=="happiness")
    happiness.update(grade=4,evidence=[dict(source="correction",statement="the overall experience was unpleasant")],
                     uncertainties=["User explicitly corrected the earlier experience description."])
    result = evaluate(payload)
    assert result["assessments"][-1]["grade"] == "4"
    assert result["assessments"][0]["grade"] == "5"
