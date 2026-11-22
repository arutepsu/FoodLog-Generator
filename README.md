# FoodLog Generator

FoodLog Generator is a portable collection of Agent Skills for OpenAI Codex and Claude Code, designed to turn everyday meal descriptions into clear, explainable food evaluations. It considers the whole experience of obtaining, preparing, and eating food through five dimensions: **Money, Taste, Effort, Nutrition, and Happiness**.

The product is designed for home-cooked meals, restaurants, cafeterias, street food, takeaway, delivery, and snacks. Its purpose is to help you understand what made a meal worthwhile and where its tradeoffs were.

## How it works

Describe your meal in your own words: what you ate, what it cost, how much work it required, and how you felt about it.

> "I cooked pasta with salmon. It cost around €5 per serving, took 30 minutes including cleanup, and was easy to prepare. I loved the taste and enjoyed a relaxed dinner at home."

Five specialized evaluators each examine a different part of the description. A Coordinator brings their findings together, checks for missing or contradictory details, and asks focused follow-up questions when needed. Additional answers build on the information already supplied.

Once every required assessment is supported, the Coordinator calculates an overall grade using fixed weights. The result explains the individual grades, the evidence behind them, strengths, weaknesses, and any uncertainty. Missing information stays unresolved rather than becoming an assumed neutral score.

## What the five dimensions mean

| Dimension | What it evaluates | Weight |
|---|---|---:|
| **Money** | Actual cost per person or serving | 12 WP · 30% |
| **Taste** | How much you personally enjoyed the food | 8 WP · 20% |
| **Effort** | Time and physical or mental difficulty involved | 6 WP · 15% |
| **Nutrition** | Nutritional quality and balance supported by ingredients and quantities | 8 WP · 20% |
| **Happiness** | Atmosphere, comfort, service, and personal satisfaction | 6 WP · 15% |

The total is **40 Weight Points (WP)**. Each dimension is evaluated independently: price does not determine taste, and an expensive setting does not automatically mean a better experience.

### Money

Money measures the actual cost of the evaluated meal per serving in euros. For cooking at home, only the ingredients used count toward the meal; buying a full package does not mean its whole price belongs to one dish. Shared bills use the appropriate personal share, including applicable mandatory fees. Optional tips are recorded separately unless you intend to evaluate your total personal spending.

| Cost per serving | Grade |
|---|---:|
| €0–€3 | 1.0 |
| Above €3 up to €6 | 2.0 |
| Above €6 up to €12 | 3.0 |
| Above €12 up to €20 | 4.0 |
| Above €20 | 5.0 |

Estimates are marked as uncertain. A price range spanning different grades needs clarification. Other currencies require an explicit conversion mechanism or verified exchange rate.

### Taste

Taste reflects your own experience, from adoring a dish (**1.0**) to never wanting to eat it again (**5.0**). Liking it corresponds to **2.0**, feeling neutral to **3.0**, and finding it disappointing to **4.0**. Your description is interpreted in context rather than through rigid keyword matching.

### Effort

Effort combines **Time (4 WP)** and **Energy (2 WP)**. Time includes relevant shopping, travel, waiting, preparation, cooking, and cleanup. Ordinary time spent eating and enjoying the meal is excluded, and overlapping activities are not counted twice.

| Required time | Grade |
|---|---:|
| Under 15 minutes | 1.0 |
| 15 to under 30 minutes | 2.0 |
| 30 to under 120 minutes | 3.0 |
| 120 to 240 minutes inclusive | 4.0 |
| Over 240 minutes | 5.0 |

Energy reflects perceived physical and mental difficulty: easy (**1.0**), some effort but still simple (**2.0**), moderate (**3.0**), complicated (**4.0**), or significantly difficult (**5.0**). Long cooking time alone does not imply high energy expenditure.

The combined Effort grade is `(4 × Time + 2 × Energy) / 6`.

### Nutrition

Nutrition considers available evidence about ingredients, portions, protein, fiber, fats, added sugar, sodium, and overall variety. Grades range from highly nutritious and well-balanced (**1.0**) to extremely poor nutritional quality (**5.0**), with a mixed nutritional profile represented by **3.0**.

The assessment must explain its evidence and limitations without inventing nutrient quantities or making unsupported medical claims. A meal is not automatically rated poorly because it is fast food, fried, or high in calories. Food-safety concerns are treated as independent critical warnings, regardless of the weighted grade.

### Happiness

Happiness captures the personal experience around the meal: atmosphere, environment, comfort, service, company, and emotional satisfaction. It ranges from exceptional (**1.0**) through pleasant (**2.0**), neutral (**3.0**), and unpleasant (**4.0**) to extremely negative (**5.0**).

Home dining, eating alone, and cafeteria meals carry no automatic positive or negative assumptions. The assessment follows your experience.

## Understanding the overall grade

Grades follow a German-style scale: **1.0 is best and 5.0 is worst**.

| Displayed grade | Classification |
|---|---|
| 1.0–1.7 | Very Good |
| 1.8–2.5 | Good |
| 2.6–3.3 | OK |
| 3.4–4.0 | Bad |
| 4.1–5.0 | Terrible |

**OK is a neutral result.** Qualitative assessments use representative grades of 1.0, 2.0, 3.0, 4.0, or 5.0; the weighted result can fall between them.

```text
Overall grade =
(12 × Money + 8 × Taste + 4 × Time + 2 × Energy
 + 8 × Nutrition + 6 × Happiness) / 40
```

For example, Money **2.0**, Taste **1.0**, Time **3.0**, Energy **1.0**, Nutrition **2.0**, and Happiness **3.0** produce **2.0 — Good**.

Calculations retain the unrounded grade. The displayed result is rounded to one decimal using decimal half-up rounding, then classified using the table above. A complete overall grade requires all assessments; missing dimensions are never silently replaced with 3.0.

## AI interpretation, consistent calculations

AI interprets natural language, subjective experiences, and qualitative evidence. Fixed rules handle prices, time thresholds, weighting, validation, and rounding. This separation keeps arithmetic consistent while allowing people to describe meals naturally.

Every assessment is designed to include its status, grade, classification, weight, supporting evidence, explanation, strengths, weaknesses, missing information, and uncertainties.

## Install and use FoodLog

FoodLog runs inside **OpenAI Codex or Claude Code**, using the host's own model to interpret your meal description. The existing Python package supplies the deterministic grading engine.

Install [uv](https://docs.astral.sh/uv/) and Python 3.12 or newer. From this repository, run these commands on Windows, macOS, or Linux:

```text
uv sync --locked
uv run python skills/sync.py
```

The synchronization command creates the six discoverable skills in both `.agents/skills/` and `.claude/skills/`. Start a new host session in this project, or reload skills if your host supports it.

- **Codex:** invoke `$foodlog`, followed by your meal description.
- **Claude Code:** invoke `/foodlog`, followed by your meal description.
- You can also ask the host to evaluate a meal with FoodLog in ordinary language.

For example:

```text
$foodlog I cooked chicken and rice for 5 euros.
It took 30 minutes, and I loved the taste.
```

FoodLog asks whether the price was per serving, what the total relevant time covered, how difficult preparation felt, what ingredients and approximate portions were involved, and how the overall experience felt wherever those details remain unclear. Reply in the same conversation; earlier answers remain part of the evaluation.

To install project-local skills into another workspace, run this from the package repository:

```text
uv run python skills/sync.py --destination "/path/to/another/project"
```

Use a Windows path such as `C:\My Project` on Windows. Install all six skills together: specialist skills share references with the coordinating skill. Each generated installation includes the Python runtime and the helper's dependency lock, so it can run without the original repository. The first helper invocation may need network access to download its locked Python dependencies. No separate LLM API key is required.

## Package structure

```text
skills/
  foodlog/
    SKILL.md
    references/        Shared rules, contract, schema and example
    scripts/           Deterministic JSON helper and its uv lock
  money/SKILL.md
  taste/SKILL.md
  effort/SKILL.md
  nutrition/SKILL.md
  happiness/SKILL.md
  sync.py              Cross-platform discovery synchronization
  export_schema.py     Schema generation from the Python model
src/foodlog/           Preserved Python package and shared grading engine
tests/                Automated scoring, contract and installation tests
.agents/skills/        Generated Codex discovery copies
.claude/skills/        Generated Claude Code discovery copies
```

Edit canonical skill instructions under `skills/` and grading logic under `src/foodlog/`. Run synchronization after changes; generated host copies are not independently maintained. The installer refuses to overwrite local edits or colliding skills and does not remove unrelated files.

## How the skills execute

The coordinating skill applies the five specialist roles within the host session. Subagents are optional, not required. It records the user's messages, collects traceable evidence and builds a structured assessment. Its Python helper checks the structure and exact evidence references, derives numeric grades, and computes the weighted result.

The host model remains responsible for deciding whether evidence supports an interpretation and for identifying semantic contradictions. Structural validation cannot prove those judgments. Contradictions recorded in the input block a final grade until clarified. Food-safety warnings remain visible independently of the arithmetic.

The helper accepts JSON and returns JSON; it is a tool for the host, not a separate conversational application. Decimal values are serialized as strings to retain precision. Its JSON output is encoding-independent, including for Unicode meal descriptions.

You can run the complete example directly:

```text
uv run --locked skills/foodlog/scripts/evaluate.py skills/foodlog/references/example.json
```

It returns **2.0 — Good** from six supported component assessments. To inspect the input contract:

```text
uv run --locked skills/foodlog/scripts/evaluate.py --schema
```

## Verification and maintenance

```text
uv run python -m pytest
uv run python skills/export_schema.py --check
uv run python skills/sync.py --check
```

Dependencies for the preserved Python package are pinned in `uv.lock`. The helper has a separate inline-script lock at `skills/foodlog/scripts/evaluate.py.lock`. The existing package configuration and grading tests are preserved.

After changing an input model, regenerate the schema and synchronize:

```text
uv run python skills/export_schema.py
uv run python skills/sync.py
```

If uv cannot use its default cache directory, add `--cache-dir .uv-cache` immediately after `uv`.

Scoring, schema validation, failure handling, evidence references, follow-up inputs, installation drift and both discovery folder layouts are covered by offline tests. A host-model behavioral check also exercises an ambiguous meal description and verifies clarification rather than an invented overall grade. The repository does not automate launching or testing an installed Claude Code session.

Host conventions: [Codex skills](https://developers.openai.com/codex/skills/) and [Claude Code skills](https://code.claude.com/docs/en/skills).

Acceptance examples and execution limits are recorded in [the v0.1 acceptance report](tests/acceptance/REPORT.md). The six scenario inputs and recorded outputs are included for reproducible checks. Live Claude model comparison remains pending.
