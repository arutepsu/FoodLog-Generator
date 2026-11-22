# Coordinator Evaluation Report — v0.2

After a Coordinator evaluation is validated, use the report helper to generate the
analytical report from that result. Do not call specialist skills again, ask a model
to reconstruct calculations, or change a grade while writing the report.

## In-conversation report

Pass the existing normalized evaluation JSON (the output of evaluate.py), not the
original draft. The helper also accepts an exported v0.2 evaluation.json for regeneration.

```text
uv run --locked "<foodlog-skill-dir>/scripts/report.py" "<evaluation.json>" --food-name "Homemade Pasta"
```

The tool returns document (structured JSON), markdown and svg. In Codex, always add
--preview-dir "<authorized temporary visualization directory>". This creates a PNG
chart for display without exporting a permanent meal record. The JSON then includes
preview.png as an absolute path and Markdown with the PNG image embedded. Present
that Markdown directly, including the image in the Circle Chart section, so the
result follows the example report. Never shorten it to a prose-only summary or
silently omit the chart. Use an absolute path in the image tag, for example:
![Evaluation Weight Distribution](/absolute/path/foodlog-identifier.png)

Keep the generated section order, all five evaluator reports, Effort subgrades,
calculation, evidence, strengths, weaknesses and uncertainty. Do not replace these
with one paragraph per parameter. A chart is part of the standard report.
If PNG generation fails, report the specific failure and retain the full text table
as a fallback; do not claim that a chart was displayed. Never paste raw SVG source
as though it were a rendered chart. Without --preview-dir, the helper remains
file-free for integrations that render its SVG themselves.

Use the report's section order: header and food summary; overall grade; weight chart;
parameter summary including Effort subgrades; weighted calculation; five evaluator
reports; strengths/weaknesses/missing information; final analytical conclusion.
Prominent food-safety warnings precede the overall grade and also appear in Nutrition.

Supply only supported metadata. The food name and summary may concisely describe
known facts; do not invent a meal date, location or experience type. Optional flags:
--summary, --date (ISO YYYY-MM-DD), --type, --report-id. Without a supplied ID the helper
creates a deterministic FL- hash identifier; it does not infer a date.

## Optional export

Save files when requested by the user. For an ordinary evaluation, offer export
without silently creating a permanent meal record.

```text
uv run --locked "<foodlog-skill-dir>/scripts/report.py" "<evaluation.json>" --food-name "Homemade Pasta" --export-root "reports"
```

Output layout: reports/<foodlog-id>/evaluation.json, report.md and charts/evaluation.svg.
Existing report folders are never overwritten. Choose a new ID or export root to
save another copy. The JSON includes metadata, the original validated evaluation
and the exact weighted calculation. Render again from that JSON without re-evaluating.

Link exported files in the host's supported format. When showing the SVG in a chat,
resolve the file path from the returned files mapping; the Markdown saved on disk
uses a relative charts/evaluation.svg reference for portability.

## Invariants

- Chart segments always show Money 30%, Taste 20%, Effort 15%, Nutrition 20%,
  Happiness 15%. They represent weights, not scores.
- The center grade/classification is copied from the validated result.
- An incomplete result has no overall grade and shows Incomplete Evaluation.
- A failed assessment shows Evaluation Error / Technical failure, not a request for
  the user to repair a tool problem.
- Effort keeps Time 4 WP and Energy 2 WP. The overall formula uses those original
  components, never rounded combined Effort.
- A safety warning remains independent of a good numerical score.
- Evidence is quoted from its identified user turn; no creative narrative or new facts.
- Older evaluation JSON without structured price/time values remains supported.
  Report only the saved numeric measurements or quoted evidence, not inferred amounts.
- Malformed or inconsistent saved results fail validation rather than being
  silently corrected. Report the failure and request the original validated JSON.
