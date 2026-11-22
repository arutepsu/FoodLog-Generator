# Shared FoodLog v0.1 rules

Source of truth for executable rules: the preserved Python package, src/foodlog/grading.py.
The generated host runtime is synchronized from that package, not independently maintained.
All grades run from 1 (best) to 5 (worst); OK is neutral.

| Component | WP |
|---|---:|
| Money | 12 |
| Taste | 8 |
| Time | 4 |
| Energy | 2 |
| Nutrition | 8 |
| Happiness | 6 |

Effort has 6 WP: (4 × Time + 2 × Energy) / 6.
Overall = (12 × Money + 8 × Taste + 4 × Time + 2 × Energy + 8 × Nutrition + 6 × Happiness) / 40.
Use all six original component grades, never a rounded Effort grade.
Do not normalize over available weights or replace missing components with 3.

Money in EUR per serving: [0,3] => 1; (3,6] => 2; (6,12] => 3; (12,20] => 4; above 20 => 5.
Time in minutes: [0,15) => 1; [15,30) => 2; [30,120) => 3; [120,240] => 4; above 240 => 5.
Negative/nonfinite values and boolean pseudo-numbers are invalid. Zero price and time are valid.
A numeric range must have both endpoints in the same category to receive a grade.

Taste: adores 1; likes 2; neutral 3; disappointing 4; never again 5.
Energy: easy 1; some effort but simple 2; moderate 3; complicated 4; significantly difficult 5.
Nutrition: highly balanced 1; mostly healthy 2; mixed 3; poor balance 4; extremely poor 5.
Happiness: exceptional 1; pleasant 2; neutral 3; unpleasant 4; extremely negative 5.

Preserve raw Decimal precision. Display ROUND_HALF_UP to one decimal, then classify:
1.0–1.7 Very Good; 1.8–2.5 Good; 2.6–3.3 OK; 3.4–4.0 Bad; 4.1–5.0 Terrible.
Qualitative grades use only 1,2,3,4,5. Weighted results can be intermediate.

Evidence must be exact quotations traceable to user turns. Do not invent prices, durations,
ingredients, portions, preferences, experiences, nutrient totals or exchange rates.
Explicit estimates need uncertainty notes. Contradictions require clarification, not averaging.
Warnings about spoiled/contaminated food are independent of the weighted result.
