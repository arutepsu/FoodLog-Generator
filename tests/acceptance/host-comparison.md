# Identical prompts for live host comparison

Open a fresh session in this repository in each host. Invoke $foodlog in Codex,
or /foodlog in Claude Code, followed by the identical description below.
Record host version/model, skill revision, source quotes, all six component grades,
questions, warnings, raw overall grade and displayed classification.

The fixtures in cases.json record the current Codex session's interpretations.
Replaying them through .claude/skills validates that helper installation only;
it does not count as a Claude language-model evaluation.

## Complete meal

I cooked pasta with salmon at home. Per serving I used 150 g cooked refined-wheat pasta, 150 g salmon, 200 g broccoli and 5 g olive oil, with a small pinch of salt and no added sugar. The consumed ingredients cost exactly EUR 5 per serving. Total food-related time including shopping, preparation, cooking and cleanup was 30 minutes, without overlapping tasks counted twice. Preparation was easy. I absolutely loved the taste. The overall dinner experience was pleasant.

## Restaurant visit

I ate dinner at a restaurant. My own share was EUR 48 including all mandatory charges, with no optional tip included. Total return travel and waiting took 45 minutes; eating time is excluded. Obtaining the meal was easy. I liked the taste. My plate had 150 g grilled salmon, 150 g cooked refined-wheat pasta and 200 g broccoli, with about 5 g olive oil, a small pinch of salt and no added sugar. The service was excellent and the overall experience was exceptional.

## Ambiguous experience

It was amazing, but I hated the taste.

## Comparison criteria

- Money and Time thresholds, 40 WP, arithmetic and half-up rounding must agree
  when the input facts/component grades agree.
- Different qualitative grades require comparison of the supporting quotes and
  rubric interpretation; do not force a match by copying another host's judgment.
- Neither host should invent missing information or claim a full grade with an
  unresolved component.
- Ambiguous amazing may refer to atmosphere rather than flavor: ask before
  treating it as contradictory taste evidence.
- Safety warnings must remain independent of the weighted score.

Live Claude comparison: pending. The executable was not found on PATH during
the 2026-11-22 acceptance run; no Claude-model result has been fabricated.
