# /// script
# requires-python = ">=3.12"
# dependencies = ["pydantic>=2.10,<3", "resvg-py>=0.2,<1"]
# ///
"""Render existing Coordinator evaluation JSON; no evaluation agents are called."""
import argparse
import json
from pathlib import Path
import sys

from evaluate import bootstrap


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input",help="Existing evaluation JSON or exported report JSON; '-' reads stdin")
    parser.add_argument("--food-name")
    parser.add_argument("--summary")
    parser.add_argument("--date",dest="evaluation_date")
    parser.add_argument("--type",dest="experience_type")
    parser.add_argument("--report-id")
    parser.add_argument("--export-root",help="Optional reports directory; omitted means no files are saved")
    parser.add_argument("--preview-dir", help="Create a temporary PNG chart for inline chat display; does not export a meal record")
    args=parser.parse_args()
    try:
        bootstrap()
        from foodlog.reporting import create_report,export_report
        raw=sys.stdin.read() if args.input=="-" else Path(args.input).read_text(encoding="utf-8-sig")
        def unique(pairs):
            result={}
            for key,value in pairs:
                if key in result:
                    raise ValueError(f"Duplicate JSON key: {key}")
                result[key]=value
            return result
        payload=json.loads(raw,object_pairs_hook=unique)
        metadata={key:getattr(args,key) for key in ("food_name","summary","evaluation_date","experience_type","report_id") if getattr(args,key) is not None}
        bundle=create_report(payload,metadata or None)
        files=export_report(bundle,args.export_root) if args.export_root else None
        preview = None
        markdown = bundle.markdown
        if args.preview_dir:
            import resvg_py
            import hashlib
            folder = Path(args.preview_dir).resolve()
            folder.mkdir(parents=True, exist_ok=True)
            identifier = hashlib.sha256(bundle.svg.encode("utf-8")).hexdigest()[:16]
            png = folder / ("foodlog-" + identifier + ".png")
            png.write_bytes(resvg_py.svg_to_bytes(svg_string=bundle.svg, width=1200))
            preview = {"png": str(png)}
            markdown = markdown.replace(bundle.svg.strip(), "![Evaluation Weight Distribution](" + png.as_posix() + ")")
        print(json.dumps(dict(document=bundle.document.model_dump(mode="json"),markdown=markdown,preview=preview,
                              svg=bundle.svg,files=None if files is None else {key:str(value) for key,value in files.items()}),
                         ensure_ascii=True,indent=2))
        return 0
    except (ValueError,OSError,RuntimeError,ImportError) as exc:
        print(json.dumps(dict(status="error",error=str(exc)),ensure_ascii=True),file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
