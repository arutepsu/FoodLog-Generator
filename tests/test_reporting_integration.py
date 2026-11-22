from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys

import pytest

from foodlog.reporting import create_report, export_report
from foodlog.skill_engine import evaluate

ROOT=Path(__file__).resolve().parents[1]
CASES=json.loads((ROOT/"tests/acceptance/cases.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("host",[".agents",".claude"])
@pytest.mark.parametrize("case",CASES,ids=[c["id"] for c in CASES])
def test_installed_report_helper_accepts_all_acceptance_results(host,case,tmp_path):
    source=tmp_path/"evaluation.json"
    source.write_text(json.dumps(evaluate(case["payload"])),encoding="utf-8")
    run=subprocess.run([sys.executable,str(ROOT/host/"skills/foodlog/scripts/report.py"),str(source),
                        "--food-name",case["name"]],capture_output=True,text=True,cwd=tmp_path)
    assert run.returncode==0,run.stderr
    output=json.loads(run.stdout)
    assert output["document"]["evaluation"]["display_grade"]==case["expected"]["display_grade"]
    assert output["document"]["evaluation"]["status"]==case["expected"]["status"]
    assert output["files"] is None
    assert "Evaluation Weight Distribution" in output["svg"]


def test_report_helper_export_and_regeneration(tmp_path):
    source=tmp_path/"input.json"
    source.write_text(json.dumps(evaluate(CASES[0]["payload"])),encoding="utf-8")
    helper=ROOT/"skills/foodlog/scripts/report.py"
    command=[sys.executable,str(helper),str(source),"--food-name","Pasta","--report-id","FL-PORTABLE",
             "--export-root",str(tmp_path/"reports")]
    run=subprocess.run(command,capture_output=True,text=True)
    assert run.returncode==0,run.stderr
    output=json.loads(run.stdout)
    saved=Path(output["files"]["evaluation"])
    rerun=subprocess.run([sys.executable,str(helper),str(saved)],capture_output=True,text=True)
    assert rerun.returncode==0,rerun.stderr
    assert json.loads(rerun.stdout)["document"]==output["document"]
    assert json.loads(rerun.stdout)["svg"]==output["svg"]
    repeated=subprocess.run(command,capture_output=True,text=True)
    assert repeated.returncode==2
    assert json.loads(repeated.stderr)["status"]=="error"


def test_report_helper_malformed_input_is_not_a_fake_report(tmp_path):
    source=tmp_path/"input.json"
    source.write_text('{"status":"complete"}',encoding="utf-8")
    run=subprocess.run([sys.executable,str(ROOT/"skills/foodlog/scripts/report.py"),str(source)],
                        capture_output=True,text=True)
    assert run.returncode==2
    assert json.loads(run.stderr)["status"]=="error"
    assert not run.stdout


def test_report_regeneration_does_not_invoke_evaluators(monkeypatch):
    import foodlog.skill_engine as engine
    original=evaluate(CASES[0]["payload"])
    def forbidden(*args,**kwargs):
        raise AssertionError("Reporting must not evaluate again")
    monkeypatch.setattr(engine,"evaluate",forbidden)
    bundle=create_report(original,{"food_name":"Pasta"})
    assert bundle.document.evaluation.display_grade is not None
