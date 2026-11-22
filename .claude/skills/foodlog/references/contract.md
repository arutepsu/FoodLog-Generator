# Host-to-Python evaluation contract

Use evaluation.schema.json for exact fields and example.json for a complete working payload.
The schema is generated from foodlog.skill_engine.EvaluationInput; do not edit it independently.

Top-level fields:
- turns: one or more {id, text} objects. Preserve user messages verbatim and keep IDs stable.
- assessments: exactly six draft objects, one each for money, taste, time, energy, nutrition, happiness.
- conflicts: optional unresolved {parameter, question, evidence} objects, each with at least two quotes.
- safety_warnings: optional {message, evidence} objects.

Every draft has parameter, status, optional grade, lower, upper, currency, evidence,
reasoning_summary, strengths, weaknesses, missing_information, uncertainties.
The lists default to empty. Status is evaluated, missing_information, unresolved, or error.

Evidence is {source: "<turn ID>", statement: "<exact substring of that turn>"}.
Use a meaningful quote with enough context; a token shared with the turn is not substantive evidence.
Python verifies source IDs and exact substrings. The host must verify that the quote actually
supports the claim, numeric amount and interpretation. Syntax checks cannot establish semantic truth.

Evaluated drafts require evidence and reasoning_summary, and cannot have missing_information.
For Money and Time, omit grade; supply lower as a decimal string in EUR/serving or minutes.
For an exact number, omit upper. For a range, supply both; the helper grades both endpoints.
For qualitative components, supply grade as 1,2,3,4,5 and omit lower/upper.
Weights, classifications and displayed grades are output-only and must not be supplied.
Only EUR is accepted; convert with verified provenance before sending a Money value.

Unresolved/missing/error drafts have grade, lower and upper null or absent. Include an actionable
missing_information question or an explanation in reasoning_summary/uncertainties.
Error represents a failed assessment, never a fallback success.

The helper returns all six normalized assessments, the derived Effort result, full source turns,
questions, conflicts and independent safety warnings. grade/display_grade/classification are null
until all components are evaluated. safe_to_recommend is false with warnings and otherwise null
(no safety determination). A complete numerical assessment is not permission to eat unsafe food.

On follow-up, retain prior turns, append the new turn and update only supported assessments.
When a user explicitly corrects a value, remove its resolved conflict, use the correction's quote,
and preserve the correction history in uncertainties. Do not silently discard contradictions.

Tool errors return exit code 2 and an error JSON object on stderr. There is no model/API fallback.
Do not save meal data outside the user's authorized workspace. Temporary JSON files can be kept
for clarification during the conversation; there is no database or automatic journal persistence.
