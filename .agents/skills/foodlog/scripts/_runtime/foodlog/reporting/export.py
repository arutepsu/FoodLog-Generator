"""Optional export. Never overwrite an existing report or escape its root."""
import json
from pathlib import Path

from .markdown_renderer import render_markdown


def export_report(bundle, root="reports") -> dict[str,Path]:
    base=Path(root).resolve()
    identifier=bundle.document.metadata.report_id
    # Also validate callers who constructed a bundle manually.
    from .models import ReportMetadata
    ReportMetadata(report_id=identifier)
    if identifier is None:
        raise ValueError("Report identifier is required for export")
    target=base/identifier
    if target.is_symlink() or not target.resolve().is_relative_to(base):
        raise ValueError("Report destination escapes its root")
    if target.exists():
        raise FileExistsError(f"Report already exists; choose a new report ID or export root: {target}")
    base.mkdir(parents=True,exist_ok=True)
    target.mkdir()  # Exclusive creation; never reuse an existing directory.
    charts=target/"charts"
    charts.mkdir()
    paths=dict(evaluation=target/"evaluation.json",markdown=target/"report.md",svg=charts/"evaluation.svg")
    paths["evaluation"].write_text(json.dumps(bundle.document.model_dump(mode="json"),ensure_ascii=True,indent=2)+"\n",encoding="utf-8")
    paths["markdown"].write_text(render_markdown(bundle.document,chart_reference="charts/evaluation.svg"),encoding="utf-8")
    paths["svg"].write_text(bundle.svg,encoding="utf-8")
    return paths
