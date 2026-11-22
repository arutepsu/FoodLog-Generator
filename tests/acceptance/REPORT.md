# FoodLog v0.1 acceptance report

Date: 2026-11-22

**Codex-session example checks: passed. Live Codex-versus-Claude model comparison: pending.**

The six cases are reproducible, authored test descriptions based on the requested examples.
Added prices, quantities, feelings and durations are explicit test inputs, not facts inferred
about real meals eaten by the user. Real-user field trials remain separate.

## Execution and evidence

The current Codex session read the coordinating FoodLog skill, all five specialist skills,
shared rules and the input contract. It interpreted each narrative and prepared traceable
structured assessments. The installed Codex helper was then executed with its locked uv
dependencies. Exact inputs and expected checks are in [cases.json](cases.json); actual helper
outputs are in [results.json](results.json).

Automated acceptance tests replay these recorded host judgments. They do not run an
automatic natural-language parser or prove that every future host-model response will match.
The host is responsible for semantic interpretation, including nutrition, uncertainty,
ambiguity and safety recognition.

## Results

| Scenario | Observed result | Verdict |
|---|---|---|
| Complete homemade pasta | Raw 1.85, displayed 1.9 Good; six supported assessments | Pass |
| Delicious ramen, no other details | Taste 2.0; no overall grade; five targeted questions | Pass |
| EUR 48 restaurant, exceptional experience | Money 5.0; Happiness 1.0; overall 2.8 OK | Pass |
| EUR 2 homemade rice dish | Money 1.0; raw overall 1.45, displayed 1.5 Very Good | Pass |
| Amazing, but hated the taste | Referent ambiguity identified; no overall grade; clarification requested | Pass |
| Spoiled chicken | Independent critical warning; safe_to_recommend false; no invented grades | Pass |

The categorical nutrition assessments are qualitative host judgments supported by the
supplied portions and ingredients. Their explanations remain reviewable in the fixtures;
no nutrient values were invented.

The ambiguous positive sentence may describe atmosphere rather than flavor. It is therefore
flagged for clarification, rather than declared a definite logical contradiction or
averaged into a neutral taste grade.

For spoiled food, the safety warning takes priority over requests to complete the score.
The test does not encourage trying the food to supply a missing Taste assessment.

## Follow-up and independence checks

- The ramen follow-up adds price, total effort time, difficulty, portions and overall experience
  while retaining the original taste quote. Result: raw 2.15, displayed 2.2 Good, no questions.
  See [ramen-followup.json](ramen-followup.json).
- Explicitly correcting the restaurant cost changes Money from 5 to 1 while leaving Happiness unchanged.
- Explicitly correcting restaurant satisfaction changes Happiness while leaving Money at 5.
- Clarifying that amazing referred to decoration resolves the taste ambiguity, retaining the
  negative Taste grade and an independently neutral Happiness grade. Other missing components
  still block an overall grade.
- A safety warning attached to a numerically Good complete assessment remains visible and
  sets safe_to_recommend to false.

## Verification

Full automated suite: **114 passed**.

The acceptance suite contains 17 checks: twelve installed-helper replays (six scenarios
for each host layout), two independence checks, ambiguous-input clarification, a completed
ramen follow-up, and a safety-versus-score check.

Both generated discovery layouts replay the recorded structured assessments successfully.
This verifies portable helper execution, not equivalent language-model judgments.

## Live cross-host comparison

Claude Code was not found on PATH in this environment. No Claude language-model run was
performed, and cross-host model equivalence is not claimed.

Use the three identical prompts in [host-comparison.md](host-comparison.md) in fresh Codex and
Claude Code sessions. Compare source quotes, missing information, categorical judgments,
raw calculations, displayed grades and safety behavior. Record host/model versions and
skill revision. Different qualitative judgments need evidence review; given identical
component grades, deterministic arithmetic and rounding must agree.

No Creative Food Guide changes were made.
