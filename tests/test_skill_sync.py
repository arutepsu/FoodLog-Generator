import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/sync.py"
NAMES = {"foodlog","money","taste","effort","nutrition","happiness"}


def run(*args):
    return subprocess.run([sys.executable,str(SCRIPT),*map(str,args)],capture_output=True,text=True)


def test_install_both_hosts_is_portable_and_idempotent(tmp_path):
    result = run("--destination",tmp_path)
    assert result.returncode == 0, result.stderr
    for host in (".agents",".claude"):
        folder = tmp_path/host/"skills"
        assert {p.name for p in folder.iterdir() if p.is_dir()} == NAMES
        for name in NAMES:
            assert (folder/name/"SKILL.md").read_bytes() == (ROOT/"skills"/name/"SKILL.md").read_bytes()
        runtime = folder/"foodlog/scripts/_runtime/foodlog/grading.py"
        assert runtime.read_bytes() == (ROOT/"src/foodlog/grading.py").read_bytes()
        helper = folder/"foodlog/scripts/evaluate.py"
        result = subprocess.run([sys.executable,str(helper),"--schema"],cwd=tmp_path,capture_output=True,text=True)
        assert result.returncode == 0, result.stderr
        assert json.loads(result.stdout)["title"] == "EvaluationInput"
    assert run("--destination",tmp_path,"--check").returncode == 0
    assert run("--destination",tmp_path).returncode == 0


def test_sync_detects_drift_and_does_not_overwrite_local_edits(tmp_path):
    assert run("--destination",tmp_path).returncode == 0
    target = tmp_path/".agents/skills/taste/SKILL.md"
    target.write_text("local user modification",encoding="utf-8")
    assert run("--destination",tmp_path,"--check").returncode != 0
    assert run("--destination",tmp_path).returncode != 0
    assert target.read_text() == "local user modification"


def test_install_refuses_unmanaged_collision(tmp_path):
    target = tmp_path/".claude/skills/money"
    target.mkdir(parents=True)
    (target/"SKILL.md").write_text("Another money skill",encoding="utf-8")
    result = run("--destination",tmp_path)
    assert result.returncode != 0
    assert (target/"SKILL.md").read_text() == "Another money skill"


def test_canonical_skill_structure():
    spec = importlib.util.spec_from_file_location("foodlog_sync", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.validate_structure(ROOT/"skills")

def test_manifest_symlink_cannot_write_outside_destination(tmp_path):
    destination = tmp_path/"project"
    outside = tmp_path/"outside.json"
    outside.write_text("{}",encoding="utf-8")
    folder = destination/".agents/skills"
    folder.mkdir(parents=True)
    marker = folder/".foodlog-manifest.json"
    try:
        marker.symlink_to(outside)
    except OSError:
        pytest.skip("Creating symlinks requires platform permission")
    result = run("--destination",destination)
    assert result.returncode != 0
    assert outside.read_text() == "{}"
    assert not (destination/".claude").exists()

@pytest.mark.parametrize("content", ["[]", "{bad json"])
def test_malformed_manifest_is_reported_without_installing(tmp_path, content):
    folder = tmp_path/".agents/skills"
    folder.mkdir(parents=True)
    (folder/".foodlog-manifest.json").write_text(content,encoding="utf-8")
    result = run("--destination",tmp_path)
    assert result.returncode != 0
    assert "Traceback" not in result.stderr
    assert not (tmp_path/".claude").exists()


def test_second_host_collision_does_not_modify_first_host(tmp_path):
    target = tmp_path/".claude/skills/money"
    target.mkdir(parents=True)
    (target/"SKILL.md").write_text("Another skill",encoding="utf-8")
    assert run("--destination",tmp_path).returncode != 0
    assert not (tmp_path/".agents").exists()


def test_changed_canonical_file_updates_unedited_generated_copy(tmp_path):
    import hashlib
    assert run("--destination",tmp_path).returncode == 0
    target = tmp_path/".agents/skills/taste/SKILL.md"
    old = b"older generated release"
    target.write_bytes(old)
    manifest = tmp_path/".agents/skills/.foodlog-manifest.json"
    data = json.loads(manifest.read_text(encoding="utf-8"))
    data["taste/SKILL.md"] = hashlib.sha256(old).hexdigest()
    manifest.write_text(json.dumps(data),encoding="utf-8")
    assert run("--destination",tmp_path,"--check").returncode != 0
    assert run("--destination",tmp_path).returncode == 0
    assert target.read_bytes() == (ROOT/"skills/taste/SKILL.md").read_bytes()


def test_stale_managed_file_requires_manual_review(tmp_path):
    assert run("--destination",tmp_path).returncode == 0
    marker = tmp_path/".agents/skills/.foodlog-manifest.json"
    data = json.loads(marker.read_text(encoding="utf-8"))
    data["foodlog/removed-resource.txt"] = "old-hash"
    marker.write_text(json.dumps(data),encoding="utf-8")
    result = run("--destination",tmp_path)
    assert result.returncode != 0
    assert "Stale managed file" in result.stderr
