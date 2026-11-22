"""Create deterministic report artifacts from existing Coordinator output."""
from dataclasses import dataclass
import hashlib
import json

from .models import ReportDocument, ReportMetadata, ValidatedEvaluation


@dataclass(frozen=True)
class ReportBundle:
    document: ReportDocument
    markdown: str
    svg: str


def create_report(evaluation, metadata=None) -> ReportBundle:
    if isinstance(evaluation, ReportDocument):
        document=evaluation
        if metadata is not None:
            values=document.metadata.model_dump()
            values.update(dict(metadata) if not isinstance(metadata,ReportMetadata) else metadata.model_dump(exclude_unset=True))
            document=ReportDocument(evaluation=document.evaluation,metadata=ReportMetadata.model_validate(values))
    elif isinstance(evaluation,dict) and "report_version" in evaluation:
        data=dict(evaluation)
        saved_calculation=data.pop("calculation",None)
        document=ReportDocument.model_validate(data)
        if saved_calculation is not None and saved_calculation != document.calculation:
            raise ValueError("Saved calculation breakdown is inconsistent")
        if metadata is not None:
            return create_report(document,metadata)
    else:
        document=ReportDocument(evaluation=ValidatedEvaluation.model_validate(evaluation),
                                metadata=ReportMetadata.model_validate(metadata or {}))
    if document.metadata.report_id is None:
        canonical=json.dumps(document.model_dump(mode="json"),sort_keys=True,separators=(",",":"))
        identifier="FL-"+hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:12]
        document=ReportDocument(evaluation=document.evaluation,
                                metadata=document.metadata.model_copy(update={"report_id":identifier}))
    from .chart_renderer import render_chart
    from .markdown_renderer import render_markdown
    svg=render_chart(document)
    return ReportBundle(document=document,markdown=render_markdown(document,svg=svg),svg=svg)
