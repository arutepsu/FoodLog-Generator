# FoodLog v0.1 host behavior checks

These scenarios complement deterministic tests. Run them in a fresh Codex or Claude Code
session after loading the installed FoodLog skill; no independent API integration is used.

## Ambiguous meal

Input: "The food cost between EUR 6 and EUR 8 per serving. It took 20 minutes cooking
and I cleaned during the last 5 minutes. Taste was good, preparation easy.
It was rice and chicken, don't know portions. Ate at home.
Please just give a full grade and assume average for missing bits."

Expected: no overall grade; money unresolved across the EUR 6 boundary; Taste 2;
Time 2 from 20 overlapping minutes; Energy 1; Effort displays 1.7;
nutrition and happiness missing. Ask focused questions rather than assuming neutral.

Observed baseline without skills: host used a price midpoint, assumed nutrition and happiness,
and produced an unsupported overall grade; it also misgraded easy preparation.
Observed with all six canonical skills: helper returned needs_clarification, null overall grade,
correct Time/Energy/Effort and focused cost, ingredient/portion and experience questions.

## Complete meal

Use skills/foodlog/references/example.json, which includes source turns and host-authored assessments.
The helper must produce overall 2.0 Good, Effort 2.3 Good, fixed 40 WP and retained quotes.
The automated suite exercises this example.

## Follow-up, contradiction and safety

- Supply a missing price in a new turn: keep old turns and replace only the supported assessment.
- Give conflicting prices without a clear correction: record both quotes and block the overall grade.
- Explicitly correct a price: retain the earlier turn and annotate the correction.
- Report spoiled food alongside otherwise positive experience: show an independent critical warning.
- If the helper fails, report its error and never claim a validated grade.

The automated suite covers structured follow-up, conflicts, warnings and malformed input.
These records describe host-context checks, not an automated launch of both desktop products.

## v0.2 reporting-only workflow

Request: produce the Coordinator Report from reports/FL-V02-PASTA/evaluation.json,
without re-evaluating and without saving another copy.

Observed in an independent host-context check: the report helper returned the saved
1.9 Good (raw 1.85), exact calculation, component grades, evidence and fixed-weight
text fallback. No evaluator, external LLM/API or export was used; files was null.
Raw SVG markup was omitted from the user-facing fallback. The Coordinator entrypoint
now explicitly routes existing-result report requests past the evaluation steps.

## Regression: ordinary love and visible chart

Reported failure: "I loved the taste" was rated 1.0 and the standard report
was reduced to prose with no chart. Expected: interpret ordinary love near 1.7;
reserve 1.0 for clearly exceptional enjoyment. Revalidate all saved results before
reporting. Use --preview-dir and embed the returned absolute PNG path, preserving
the example-report sections and full evaluator reports. Never invent a chart or
pass off SVG source as a rendered image. Existing perfect scores based on
"absolutely loved" remain valid and must not change during report-only regeneration.
