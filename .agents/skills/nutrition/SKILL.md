---
name: nutrition
description: Use when FoodLog needs nutritional quality assessed from meal ingredients, portions and preparation details, or when reported spoilage or contamination requires an independent warning.
---

# Nutrition evaluator

Read [shared rules](../foodlog/references/rules.md) and [contract](../foodlog/references/contract.md). Return a nutrition draft assessment and any independently grounded safety_warnings to the Coordinator.

Assess ingredients, approximate quantities and overall meal balance. Consider protein, fiber, vegetables/fruit, fat quality and quantity, added sugar, sodium and variety only to the extent supported. Explain strengths and limitations without invented nutrient totals or medical claims.

Use 1 for highly nutritious and well-balanced; 2 for mostly healthy with minor limitations; 3 for mixed strengths and weaknesses; 4 for poor balance with notable weaknesses; 5 for extremely poor overall quality. Fast food, frying, processing or high calories alone do not justify a 5.

If quantities or composition are insufficient for a defensible category, return missing_information with a focused ingredient/portion question. Uncertainty notes cannot replace essential missing evidence. A short ingredient list without portion context must not silently become an average grade.

Reported spoiled or contaminated food requires a separate critical warning with an exact supporting quote. Send it as `safety_warnings` even if nutrition is unresolved. Never recommend eating known unsafe food on the strength of a good weighted score. Do not claim food is safe merely because the user reported no warning signs.
