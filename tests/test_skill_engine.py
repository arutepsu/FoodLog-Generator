from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import pytest
from pydantic import ValidationError
from foodlog.skill_engine import EvaluationInput, evaluate

ROOT = Path(__file__).resolve().parents[1]


def sample():
    texts = {
        "money": "The meal cost 5 euros per serving.",
        "taste": "I absolutely loved the taste.",
        "time": "Total food related time including cleanup was 30 minutes.",
        "energy": "Preparing it was easy.",
        "nutrition": "150 g salmon, 150 g cooked wholegrain pasta, 200 g broccoli, 5 g olive oil.",
        "happiness": "It was an ordinary neutral experience.",
    }
    grades = dict(taste=1, energy=1, nutrition=2, happiness=3)
    assessments = []
    for key,text in texts.items():
        item = dict(parameter=key,status="evaluated",evidence=[dict(source=key,statement=text)],
                    reasoning_summary="Assessment based on the quoted user report.")
        if key in ("money","time"):
            item["lower"] = "5" if key == "money" else "30"
        else:
            item["grade"] = grades[key]
        assessments.append(item)
    return dict(turns=[dict(id=k,text=v) for k,v in texts.items()],assessments=assessments)


def test_complete_evaluation_preserves_weights_and_evidence():
    result = evaluate(sample())
    assert result["grade"] == "2"
    assert result["display_grade"] == "2.0"
    assert result["classification"] == "Good"
    assert result["status"] == "complete"
    assert result["effort"]["display_grade"] == "2.3"
    assert result["assessments"][0]["weight_points"] == 12
    assert result["safe_to_recommend"] is None


def test_missing_data_blocks_authoritative_grade_and_asks_question():
    data = sample()
    data["assessments"][0] = dict(parameter="money",status="missing_information",
                                  missing_information=["What was the cost per serving?"])
    result = evaluate(data)
    assert result["grade"] is None
    assert result["status"] == "needs_clarification"
    assert result["questions"] == ["What was the cost per serving?"]


def test_range_crossing_boundary_stays_unresolved():
    data = sample()
    data["assessments"][0].update(lower="6",upper="8")
    result = evaluate(data)
    assert result["grade"] is None
    assert result["assessments"][0]["status"] == "unresolved"
    assert result["questions"]


def test_range_in_one_category_is_graded_with_uncertainty():
    data = sample()
    data["assessments"][0].update(lower="8",upper="10")
    result = evaluate(data)
    assert result["assessments"][0]["grade"] == "3"
    assert result["assessments"][0]["uncertainties"]


@pytest.mark.parametrize("mutation", ["fake_quote","fake_source","duplicate","absent","fractional_qualitative",
                                      "invented_numeric_grade","negative","reversed","boolean","extra"])
def test_invalid_host_output_is_rejected(mutation):
    data = sample()
    if mutation == "fake_quote": data["assessments"][0]["evidence"][0]["statement"] = "Made up evidence"
    if mutation == "fake_source": data["assessments"][0]["evidence"][0]["source"] = "unknown"
    if mutation == "duplicate": data["assessments"][1] = deepcopy(data["assessments"][0])
    if mutation == "absent": data["assessments"].pop()
    if mutation == "fractional_qualitative": data["assessments"][1]["grade"] = "1.5"
    if mutation == "invented_numeric_grade": data["assessments"][0]["grade"] = 1
    if mutation == "negative": data["assessments"][0]["lower"] = "-1"
    if mutation == "reversed": data["assessments"][0].update(lower="8",upper="6")
    if mutation == "boolean": data["assessments"][0]["lower"] = True
    if mutation == "extra": data["untrusted"] = "extra field"
    with pytest.raises((ValidationError,ValueError)):
        evaluate(data)


def test_contradictions_block_results_until_explicitly_resolved():
    data = sample()
    data["turns"].append(dict(id="followup",text="Actually I am unsure whether it cost 5 or 15 euros."))
    data["conflicts"] = [dict(parameter="money",question="Was the per-serving price 5 or 15 euros?",
                             evidence=[data["assessments"][0]["evidence"][0],
                                       dict(source="followup",statement="5 or 15 euros")])]
    result = evaluate(data)
    assert result["grade"] is None
    assert result["assessments"][0]["status"] == "unresolved"
    assert result["conflicts"]


def test_followup_keeps_original_sources():
    data = sample()
    initial = deepcopy(data)
    initial["assessments"][0] = dict(parameter="money",status="missing_information",
                                     missing_information=["Price per serving?"])
    assert evaluate(initial)["grade"] is None
    data["turns"].append(dict(id="followup",text="Confirmed: 5 euros per serving."))
    data["assessments"][0]["evidence"] = [dict(source="followup",statement="5 euros per serving")]
    result = evaluate(data)
    assert result["status"] == "complete"
    assert len(result["turns"]) == 7


def test_safety_warning_survives_good_grades():
    data = sample()
    data["turns"].append(dict(id="safety",text="The salmon was spoiled."))
    data["safety_warnings"] = [dict(message="Do not eat the spoiled food.",
                                  evidence=[dict(source="safety",statement="salmon was spoiled")])]
    result = evaluate(data)
    assert result["safe_to_recommend"] is False
    assert result["safety_warnings"][0]["message"] == "Do not eat the spoiled food."


def test_schema_accepts_the_example():
    assert EvaluationInput.model_json_schema()["additionalProperties"] is False
    assert EvaluationInput.model_validate(sample())


def test_json_helper_reports_invalid_json_without_fake_success(tmp_path):
    file = tmp_path/"bad.json"
    file.write_text("{invalid",encoding="utf-8")
    result = subprocess.run([sys.executable,str(ROOT/"skills/foodlog/scripts/evaluate.py"),str(file)],
                            capture_output=True,text=True)
    assert result.returncode == 2
    assert json.loads(result.stderr)["status"] == "error"
    assert not result.stdout

def test_turn_text_is_preserved_verbatim():
    data = sample()
    data["turns"][0]["text"] = "  The meal cost 5 euros per serving.\n"
    result = evaluate(data)
    assert result["turns"][0]["text"] == "  The meal cost 5 euros per serving.\n"


@pytest.mark.parametrize("arguments,expected", [
    (["--cost-per-serving","12","4"], {"cost_per_serving_eur":"3"}),
    (["--ingredient-cost","3","200","1000"], {"consumed_cost_eur":"0.6"}),
])
def test_helper_exposes_deterministic_cost_allocation(arguments, expected):
    result = subprocess.run([sys.executable,str(ROOT/"skills/foodlog/scripts/evaluate.py"),*arguments],
                            capture_output=True,text=True)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == expected


def test_exported_schema_matches_current_contract():
    file = ROOT/"skills/foodlog/references/evaluation.schema.json"
    assert json.loads(file.read_text(encoding="utf-8")) == EvaluationInput.model_json_schema()


def test_complete_bundled_example_through_helper():
    result = subprocess.run([sys.executable,str(ROOT/"skills/foodlog/scripts/evaluate.py"),
                             str(ROOT/"skills/foodlog/references/example.json")], capture_output=True,text=True)
    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout)
    assert output["display_grade"] == "2.0"
    assert output["classification"] == "Good"


def test_helper_rejects_duplicate_json_fields(tmp_path):
    file = tmp_path/"duplicate.json"
    file.write_text('{"turns":[],"turns":[]}',encoding="utf-8")
    result = subprocess.run([sys.executable,str(ROOT/"skills/foodlog/scripts/evaluate.py"),str(file)],
                            capture_output=True,text=True)
    assert result.returncode == 2
    assert "Duplicate JSON key" in json.loads(result.stderr)["error"]

@pytest.mark.parametrize("via_stdin", [False, True])
def test_helper_unicode_transport_is_portable_on_windows(tmp_path, via_stdin):
    import os
    data = sample()
    text = "My dinner was lovely \U0001f35d."
    data["turns"].append(dict(id="emoji",text=text))
    file = tmp_path/"unicode.json"
    file.write_text(json.dumps(data,ensure_ascii=False),encoding="utf-8")
    env = dict(os.environ,PYTHONIOENCODING="cp1252")
    args = [sys.executable,str(ROOT/"skills/foodlog/scripts/evaluate.py"),"-" if via_stdin else str(file)]
    result = subprocess.run(args,input=json.dumps(data) if via_stdin else None,
                            capture_output=True,text=True,env=env)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["turns"][-1]["text"] == text
