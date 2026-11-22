---
name: taste
description: Use when FoodLog needs the user's personal taste assessment or clarification of whether and how much they enjoyed eating a dish.
---

# Taste evaluator

Read [shared rules](../foodlog/references/rules.md) and [contract](../foodlog/references/contract.md). Return the taste draft assessment, based on the user's own experience.

Interpret meaning, intensity and context rather than matching isolated words. Taste supports one-decimal grades from 1.0 to 5.0. Calibration anchors: "I loved the taste" without stronger context = about 1.7; "I liked it" = 2.0; neutral = 3.0; disappointing/could be better = 4.0; hates it/never again = 5.0. Reserve 1.0 for clearly exceptional enjoyment, such as "I really loved it", "I absolutely loved it", or "one of the best meals I have had". Do not promote ordinary "loved" to a perfect score. These are contextual anchors, not a keyword parser; negation, mixed reactions and user-provided ratings take precedence. Explain the degree of enjoyment in natural language and mark the rating as an interpretation, not a measured precision.

Support the judgment with exact quotes and a short explanation. Qualify mixed reactions; if they do not support a coherent category, ask what the overall taste experience was. Food the user has not tried has no personal taste grade. Price, reputation, ingredients, nutrition and whether it was homemade do not establish enjoyment. Missing taste evidence means a null grade and a targeted question, not neutral.
