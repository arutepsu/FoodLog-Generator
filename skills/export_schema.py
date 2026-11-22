"""Generate or check the shared JSON Schema from the canonical Python model."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from foodlog.skill_engine import EvaluationInput


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    target = ROOT / "skills/foodlog/references/evaluation.schema.json"
    expected = json.dumps(EvaluationInput.model_json_schema(), indent=2, ensure_ascii=False) + "\n"
    if args.check:
        if not target.exists() or target.read_text(encoding="utf-8") != expected:
            print("Evaluation schema is missing or out of date",file=sys.stderr)
            return 1
    else:
        target.write_text(expected, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
