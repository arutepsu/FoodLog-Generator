"""Analytical Markdown from validated facts, with a complete text fallback."""
from html import escape
import re

from foodlog.grading import WEIGHTS
from .models import COMPONENT_ORDER, DIMENSION_ORDER


def md(value):
    text=escape(str(value),quote=False).replace("\r"," ").replace("\n"," ")
    return re.sub(r"([\\\\`*_{}\[\]()#+.!|>-])",r"\\\1",text)


def lists(values, empty="None reported."):
    return "\n".join("- "+md(value) for value in dict.fromkeys(values)) if values else empty


def grade(item):
    return f"{item.display_grade:.1f}" if item.grade is not None else ("Evaluation error" if item.status=="error" else "Not evaluated")


def facts_section(item, label=None):
    label=label or item.parameter.title()
    heading=f"### {label} — {grade(item)}"
    if item.classification:
        heading+=" ("+item.classification+")"
    pieces=[heading,"",f"Status: {md(item.status)}","", "**Evidence**",""]
    pieces.extend([f'> “{md(e.statement)}” — source: {md(e.source)}' for e in item.evidence] or ["No supporting evidence recorded."])
    pieces += ["","**Reasoning**","",md(item.reasoning_summary) if item.reasoning_summary else "Not available.",
               "","**Strengths**","",lists(item.strengths),"","**Weaknesses**","",lists(item.weaknesses),
               "","**Missing information and uncertainty**","",lists((*item.missing_information,*item.uncertainties))]
    return "\n".join(pieces)


def render_markdown(document,svg=None,chart_reference=None) -> str:
    if chart_reference not in (None,"charts/evaluation.svg"):
        raise ValueError("Only the bundled chart reference is supported")
    evaluation=document.evaluation
    meta=document.metadata
    name=meta.food_name or "Food name not provided"
    lines=["# FoodLog — "+md(name),""]
    if meta.evaluation_date:
        # Explicit English month names, independent of OS locale.
        months=("January","February","March","April","May","June","July","August","September","October","November","December")
        d=meta.evaluation_date
        lines += [f"Date: {d.day} {months[d.month-1]} {d.year}",""]
    if meta.experience_type:
        lines += ["Type: "+md(meta.experience_type),""]
    lines += ["Report ID: "+md(meta.report_id),"","**Food summary**",""]
    lines += [md(meta.summary) if meta.summary else "> "+md(evaluation.turns[0].text),""]
    for warning in evaluation.safety_warnings:
        lines += ["**FOOD SAFETY WARNING:** "+md(warning.message),""]
        lines += ["> "+md(e.statement)+" — source: "+md(e.source) for e in warning.evidence]
        lines += [""]
    lines += ["## Overall Grade",""]
    if evaluation.status=="complete":
        lines += [f"**Overall Grade: {evaluation.display_grade:.1f} — {evaluation.classification.upper()}**",
                  "",f"Raw unrounded grade: {evaluation.grade}.",""]
    elif evaluation.status=="error":
        lines += ["**Evaluation Error — no overall grade or classification.**",
                  "","Technical failure: one or more assessments failed; this is not missing user information.",""]
    else:
        lines += ["**Incomplete Evaluation — no overall grade or classification.**",
                  "","A full 40 WP grade has not been calculated.",""]
    lines += ["## Circle Chart","","**Evaluation Weight Distribution — 40 WP**","",
              "Segment sizes show the fixed weights, not achieved grades.",""]
    if chart_reference:
        lines += ["![Evaluation Weight Distribution — 40 WP]("+chart_reference+")",""]
    elif svg:
        lines += [svg.strip(),""]
    lines += ["Text fallback: Money 30%; Taste 20%; Effort 15%; Nutrition 20%; Happiness 15%.","",
              "## Parameter Grade Summary","","| Parameter | Weight | Grade | Classification |",
              "|---|---:|---:|---|"]
    for key in DIMENSION_ORDER:
        item=evaluation.component(key)
        lines.append(f"| {key.title()} | {WEIGHTS[key]} WP | {grade(item)} | {item.classification or '—'} |")
    overall=f"{evaluation.display_grade:.1f}" if evaluation.grade is not None else "Not calculated"
    lines += [f"| **Overall** | **40 WP** | **{overall}** | **{evaluation.classification or '—'}** |","",
              "### Effort subgrades","",
              f"Time: {grade(evaluation.component('time'))} (4 WP).",
              f"Energy: {grade(evaluation.component('energy'))} (2 WP).",
              f"Combined Effort: {grade(evaluation.effort)} (6 WP).",
              "","Effort = (4 × Time + 2 × Energy) / 6. The overall calculation uses the original component grades.","",
              "## Weighted Calculation Breakdown","",
              "(12 × Money + 8 × Taste + 4 × Time + 2 × Energy + 8 × Nutrition + 6 × Happiness) / 40","",
              "| Component | Grade (raw) | Weight | Grade × WP | Contribution to overall (÷40) |",
              "|---|---:|---:|---:|---:|"]
    for row in document.calculation["components"]:
        lines.append(f"| {row['parameter'].title()} | {row['grade'] or ('Evaluation error' if evaluation.component(row['parameter']).status=='error' else 'Not evaluated')} | {row['weight_points']} | {row['weighted_points'] or '—'} | {row['overall_contribution'] or '—'} |")
    calc=document.calculation
    if calc["weighted_total"] is not None:
        lines += ["",f"Exact total: {calc['weighted_total']} / 40 = {calc['overall_raw']}.",
                  "",f"Displayed with ROUND_HALF_UP: {evaluation.display_grade:.1f} — {evaluation.classification}.",""]
    else:
        lines += ["","No complete weighted total is shown while required assessments are unavailable.",""]
    lines += ["Contributions above are exact Decimal values; displayed Effort is not used as a rounded intermediate.","",
              "## Individual Evaluator Reports",""]
    for key in DIMENSION_ORDER:
        if key=="effort":
            lines += [f"### Effort — {grade(evaluation.effort)}"+(f" ({evaluation.effort.classification})" if evaluation.effort.classification else ""),"",
                      "Combined from separate Time (4 WP) and Energy (2 WP) assessments.","",
                      facts_section(evaluation.component("time"),"Time"),"",facts_section(evaluation.component("energy"),"Energy"),""]
            if "time" in evaluation.measurements:
                value=evaluation.measurements["time"]
                amount=str(value.lower)+(f" to {value.upper}" if value.upper is not None else "")
                lines += [f"Reported total food-related time: {amount} minutes.",""]
        else:
            item=evaluation.component(key)
            lines += [facts_section(item),""]
            if key=="money":
                if "money" in evaluation.measurements:
                    value=evaluation.measurements["money"]
                    amount=str(value.lower)+(f" to {value.upper}" if value.upper is not None else "")
                    lines += [f"Reported cost: EUR {amount} per serving.",""]
                else:
                    lines += ["Structured price not recorded; see the quoted price evidence and allocation reasoning above.",""]
            if key=="nutrition" and evaluation.safety_warnings:
                lines += ["**Independent food-safety warnings:**","",lists([w.message for w in evaluation.safety_warnings]),""]
    for conflict in evaluation.conflicts:
        lines += ["**Unresolved "+conflict.parameter.title()+" ambiguity:** "+md(conflict.question),""]
        lines += ["> "+md(e.statement)+" — source: "+md(e.source) for e in conflict.evidence]
        lines += [""]
    strengths=[f"{a.parameter.title()}: {s}" for a in evaluation.assessments for s in a.strengths]
    weaknesses=[f"{a.parameter.title()}: {s}" for a in evaluation.assessments for s in a.weaknesses]
    gaps=[f"{a.parameter.title()}: {s}" for a in evaluation.assessments for s in (*a.missing_information,*a.uncertainties)]
    failures=[f"{a.parameter.title()}: {a.reasoning_summary}" for a in evaluation.assessments if a.status=="error"]
    lines += ["## Strengths and Weaknesses Summary","","### Strengths","",lists(strengths),"",
              "### Weaknesses","",lists(weaknesses),"","### Missing information and uncertainty","",lists(gaps),""]
    if failures:
        lines += ["### Technical failures","",lists(failures),""]
    lines += ["## Final Analytical Conclusion",""]
    if evaluation.grade is not None:
        items=[(key,evaluation.component(key)) for key in DIMENSION_ORDER]
        best=min(item.grade for _,item in items)
        worst=max(item.grade for _,item in items)
        strongest=", ".join(f"{key.title()} ({item.display_grade:.1f})" for key,item in items if item.grade==best)
        weakest=", ".join(f"{key.title()} ({item.display_grade:.1f})" for key,item in items if item.grade==worst)
        lines += [f"Overall, this meal received {evaluation.display_grade:.1f} — {evaluation.classification}.",
                  f"Strongest dimensions by grade: {strongest}. Weakest dimensions by grade: {weakest}.",
                  "The final result reflects the fixed weighting shown above; each dimension retains its independent assessment."]
    elif evaluation.status=="error":
        lines += ["The evaluation has a technical failure. Available assessments remain visible, but no final grade is available."]
    else:
        lines += ["The evaluation remains incomplete. Available grades are preserved; clarification is required before a final grade can be reported."]
    if evaluation.safety_warnings:
        lines += ["Food-safety warnings take priority over a favorable numerical result. Do not eat food reported as spoiled or contaminated."]
    return "\n".join(lines)+"\n"
