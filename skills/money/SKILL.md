---
name: money
description: Use when FoodLog needs a meal price assessment, consumed ingredient cost allocation, a shared bill interpretation, or clarification of an uncertain per-serving cost.
---

# Money evaluator

Read [shared rules](../foodlog/references/rules.md) and [contract](../foodlog/references/contract.md). Return only the money draft assessment for the FoodLog coordinator. Assess price independently of taste, nutrition, luxury or enjoyment.

Establish actual EUR cost per serving. Distinguish purchased ingredients from consumed quantities; sum all consumed ingredient costs and divide by the supported serving count. For a shared bill, use the user's own share or an explicitly appropriate equal split. Include mandatory direct fees. Keep optional tips separate unless the user intends total personal spending. Use actual discounted prices. Free food is zero.

For portable cost arithmetic, run the FoodLog helper relative to the loaded sibling skill:

```text
uv run --locked "<foodlog-skill-dir>/scripts/evaluate.py" --cost-per-serving 12 4
uv run --locked "<foodlog-skill-dir>/scripts/evaluate.py" --ingredient-cost 3 200 1000
```

These return EUR 3 per serving and EUR 0.60 consumed cost respectively. Quantities in the second command must use the same unit. Add all consumed costs with Decimal arithmetic in Python before allocating servings.

The helper uses the existing runtime helpers `cost_per_serving` and `ingredient_cost` through Python, or calculate Decimal expressions in Python using quoted inputs. The coordinator's final helper grades the established amount, not a guessed grade. Do not round a per-serving amount before threshold comparison.

Set `lower` to the supported exact/estimated price per serving and `upper` to the range maximum if supplied. Omit `grade`. Record estimates in uncertainties. A range spanning categories remains unresolved; do not choose its midpoint. Without a supported price or allocation, return missing_information and a precise question. A non-EUR price requires an explicit user-supplied EUR equivalent or verified conversion with provenance; do not invent a rate.

Quote the underlying user statements and explain any deterministic allocation in reasoning. A receipt total that includes unused groceries is not automatically the meal cost.
