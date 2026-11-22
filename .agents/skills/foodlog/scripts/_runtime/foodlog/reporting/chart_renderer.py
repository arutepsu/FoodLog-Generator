"""Dependency-free, accessible five-segment SVG donut chart."""
from math import cos, sin, radians
import textwrap
from xml.sax.saxutils import escape as _xml_escape

from foodlog.grading import WEIGHTS
from .models import DIMENSION_ORDER

COLORS=dict(money="#4779cb",taste="#d99b3e",effort="#409f88",nutrition="#907acb",happiness="#cf7ba1")
BACKGROUND="#181818"


def xml_text(value):
    # Numeric entities preserve the rendered text without exposing Markdown syntax
    # when the SVG is embedded in a Markdown report.
    return "".join(f"&#{ord(c)};" if c in "[]()|#`*_{}!" else c for c in _xml_escape(str(value)))


def point(radius,angle):
    return f"{450+radius*cos(radians(angle)):.6f} {405+radius*sin(radians(angle)):.6f}"


def render_chart(document) -> str:
    evaluation=document.evaluation
    name=document.metadata.food_name or "Food name not provided"
    complete=evaluation.status=="complete"
    center="Incomplete Evaluation" if evaluation.status=="needs_clarification" else "Evaluation Error"
    if complete:
        center=f"{evaluation.display_grade:.1f} {evaluation.classification.upper()}"
    summary="; ".join(f"{key.title()}: {evaluation.component(key).display_grade if evaluation.component(key).grade is not None else ('evaluation error' if evaluation.component(key).status=='error' else 'not evaluated')}, {WEIGHTS[key]} WP" for key in DIMENSION_ORDER)
    parts=[
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 1060" role="img" aria-labelledby="foodlog-title foodlog-desc">',
        f"<title id=\"foodlog-title\">{xml_text('FoodLog — '+name)}</title>",
        f"<desc id=\"foodlog-desc\">{xml_text('Evaluation Weight Distribution — 40 WP. Fixed weights, not achieved scores. '+center+'. '+summary)}</desc>",
        f'<rect x="1" y="1" width="898" height="1058" rx="24" fill="{BACKGROUND}" stroke="#383838"/>',
        '<g font-family="Arial, Helvetica, sans-serif">',
    ]
    name_lines=textwrap.wrap("FoodLog — "+name,width=52,break_long_words=True)[:2]
    for index,line in enumerate(name_lines):
        parts.append(f'<text x="40" y="{52+index*30}" fill="#ffffff" font-size="26" font-weight="700">{xml_text(line)}</text>')
    parts.append('<text x="40" y="115" fill="#bdbdbd" font-size="16">Coordinator Evaluation Report</text>')
    if evaluation.safety_warnings:
        parts.append('<text x="40" y="150" fill="#ffb4b4" font-size="17" font-weight="700">FOOD SAFETY WARNING — see report; score does not establish safety</text>')
    start=-90
    for key in DIMENSION_ORDER:
        wp=WEIGHTS[key]
        angle=wp*9
        end=start+angle
        path=f"M {point(230,start)} A 230 230 0 0 1 {point(230,end)} L {point(160,end)} A 160 160 0 0 0 {point(160,start)} Z"
        item=evaluation.component(key)
        opacity="1" if item.grade is not None else "0.4"
        parts.append(f'<path data-parameter="{key}" data-weight="{wp}" data-percentage="{wp*100//40}" data-angle="{angle}" d="{path}" fill="{COLORS[key]}" opacity="{opacity}" stroke="{BACKGROUND}" stroke-width="4"><title>{xml_text(key.title()+": "+(str(item.display_grade)+" "+item.classification if item.grade is not None else ("Evaluation error" if item.status=="error" else "Not evaluated")))}</title></path>')
        start=end
    if complete:
        parts.extend([
            '<text x="450" y="360" text-anchor="middle" fill="#bbbbbb" font-size="21">OVERALL GRADE</text>',
            f'<text x="450" y="447" text-anchor="middle" fill="#ffffff" font-size="88" font-weight="700">{evaluation.display_grade:.1f}</text>',
            f'<text x="450" y="490" text-anchor="middle" fill="#ffffff" font-size="28">{xml_text(evaluation.classification.upper())}</text>',
        ])
    else:
        # Exact accessible center wording also appears in a text node.
        parts.append(f'<text x="450" y="400" text-anchor="middle" fill="#ffffff" font-size="24" font-weight="700">{xml_text(center)}</text>')
        parts.append('<text x="450" y="437" text-anchor="middle" fill="#bdbdbd" font-size="16">No overall grade calculated</text>')
    parts.append('<text x="40" y="690" fill="#ffffff" font-size="20" font-weight="700">Evaluation Weight Distribution — 40 WP</text>')
    parts.append('<text x="40" y="720" fill="#bdbdbd" font-size="16">Segment sizes represent fixed weights, not achieved grades.</text>')
    for index,key in enumerate(DIMENSION_ORDER):
        y=766+index*43
        item=evaluation.component(key)
        grade=f"{item.display_grade:.1f} grade" if item.grade is not None else ("Evaluation error" if item.status=="error" else "Not evaluated")
        wp=WEIGHTS[key]
        parts.extend([
            f'<circle cx="48" cy="{y-6}" r="7" fill="{COLORS[key]}"/>',
            f'<text x="66" y="{y}" fill="#ffffff" font-size="18" font-weight="700">{key.title()}</text>',
            f'<text x="858" y="{y}" text-anchor="end" fill="#d1d1d1" font-size="17">{xml_text(grade)} · {wp} WP · {wp*100//40}%</text>',
        ])
    parts.append('<line x1="40" y1="975" x2="860" y2="975" stroke="#383838"/>')
    label=f"Final Result: {evaluation.display_grade:.1f} — {evaluation.classification}" if complete else center+" — full 40 WP grade unavailable"
    parts.append(f'<text x="40" y="1016" fill="#ffffff" font-size="22" font-weight="700">{xml_text(label)}</text>')
    parts.append('</g></svg>')
    return "\n".join(parts)+"\n"
