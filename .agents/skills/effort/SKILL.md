---
name: effort
description: Use when FoodLog needs food-related time and physical or mental difficulty assessed, including overlapping tasks, passive cooking, travel, waiting, and cleanup.
---

# Effort evaluator

Read [shared rules](../foodlog/references/rules.md) and [contract](../foodlog/references/contract.md). Return two separate draft assessments: time (4 WP) and energy (2 WP). The Python helper computes their combined 6 WP grade.

For Time, establish total relevant elapsed food-related time: necessary shopping, travel both ways, ordering, waiting, preparation, cooking and cleanup. Exclude ordinary eating/enjoyment time. Count overlapping activities once. For "20 minutes cooking, cleaning during the last 5 minutes", these tasks total 20 minutes, not 25. If timing or the scope of "30 minutes" is unclear, ask whether it covers the relevant tasks. Do not invent missing cleanup, travel or shopping durations. Use Python for adding durations or merging explicit intervals.

Set time `lower` to supported minutes; `upper` is optional for a range. Omit its grade. "Quick" alone does not establish a numeric threshold; ask for time.

Energy reflects perceived difficulty: easy = 1; some effort but still simple = 2; moderate = 3; complicated = 4; significantly difficult/exhausting = 5. Quote the user's evidence. Do not infer difficulty from duration: passive slow cooking may be easy. Missing energy evidence means missing_information, not an assumed grade.

Report uncertainty separately for each component. The Coordinator must retain both unrounded components for the overall calculation.
