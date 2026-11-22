# /// script
# requires-python = ">=3.12"
# dependencies = ["pydantic>=2.10,<3"]
# ///
"""JSON-in/JSON-out tool for the host agent; not an interactive chat application."""
import argparse
import json
from pathlib import Path
import sys


def bootstrap():
    here = Path(__file__).resolve()
    bundled = here.parent / "_runtime"
    if (bundled / "foodlog").is_dir():
        sys.path.insert(0, str(bundled))
        return
    for parent in here.parents:
        if (parent / "src/foodlog/skill_engine.py").is_file():
            sys.path.insert(0, str(parent / "src"))
            return
    raise RuntimeError("FoodLog runtime missing; synchronize the skills from the package repository")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", nargs="?", help="Host-authored evaluation JSON file; '-' reads stdin")
    parser.add_argument("--schema", action="store_true", help="Print the validated input JSON Schema")
    parser.add_argument("--cost-per-serving", nargs=2, metavar=("TOTAL_EUR", "SERVINGS"))
    parser.add_argument("--ingredient-cost", nargs=3, metavar=("PRICE_EUR", "USED", "PURCHASED"))
    args = parser.parse_args()
    try:
        bootstrap()
        from foodlog.skill_engine import EvaluationInput, evaluate
        if sum((bool(args.input), args.schema, bool(args.cost_per_serving), bool(args.ingredient_cost))) != 1:
            raise ValueError("Supply exactly one input file, --schema, --cost-per-serving or --ingredient-cost")
        from foodlog.grading import cost_per_serving, ingredient_cost
        if args.cost_per_serving:
            print(json.dumps({"cost_per_serving_eur": str(cost_per_serving(*args.cost_per_serving))}))
            return 0
        if args.ingredient_cost:
            print(json.dumps({"consumed_cost_eur": str(ingredient_cost(*args.ingredient_cost))}))
            return 0
        if args.schema:
            print(json.dumps(EvaluationInput.model_json_schema(), indent=2))
            return 0
        if not args.input:
            parser.error("input JSON path or --schema required")
        raw = sys.stdin.read() if args.input == "-" else Path(args.input).read_text(encoding="utf-8-sig")
        def unique_keys(pairs):
            result = {}
            for key, value in pairs:
                if key in result:
                    raise ValueError(f"Duplicate JSON key: {key}")
                result[key] = value
            return result
        payload = json.loads(raw, object_pairs_hook=unique_keys)
        print(json.dumps(evaluate(payload), ensure_ascii=True, indent=2))
        return 0
    except (ValueError, OSError, RuntimeError, ImportError) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
