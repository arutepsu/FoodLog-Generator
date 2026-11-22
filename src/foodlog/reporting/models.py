"""Revalidate saved Coordinator output without generating new assessments."""
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import Field, computed_field, field_validator, model_validator

from foodlog.grading import WEIGHTS, classify, display_grade, grade_money, grade_time, nonnegative, number, overall_grade, validated_grade, validated_component_grade
from foodlog.models import Assessment, Contract, EffortAssessment
from foodlog.skill_engine import Conflict, SafetyWarning, Turn

COMPONENT_ORDER = ("money", "taste", "time", "energy", "nutrition", "happiness")
DIMENSION_ORDER = ("money", "taste", "effort", "nutrition", "happiness")


def check_decimal(actual, expected, label):
    if actual is None and expected is None:
        return
    if actual is None or expected is None or number(actual) != expected:
        raise ValueError(f"Inconsistent saved {label}")


def read_assessment(value):
    if isinstance(value, Assessment):
        return value
    data = dict(value)
    saved_display = data.pop("display_grade")
    saved_class = data.pop("classification")
    assessment = Assessment.model_validate(data)
    check_decimal(saved_display, assessment.display_grade, "component display grade")
    if saved_class != assessment.classification:
        raise ValueError("Inconsistent saved component classification")
    return assessment


def read_effort(value):
    if isinstance(value, EffortAssessment):
        return value
    data = dict(value)
    expected = {key: data.pop(key) for key in ("status","grade","display_grade","classification")}
    data["time"] = read_assessment(data["time"])
    data["energy"] = read_assessment(data["energy"])
    result = EffortAssessment.model_validate(data)
    for key in ("grade", "display_grade"):
        check_decimal(expected[key], getattr(result,key), f"Effort {key}")
    if expected["status"] != result.status or expected["classification"] != result.classification:
        raise ValueError("Inconsistent saved Effort result")
    return result


class Measurement(Contract):
    lower: Decimal
    upper: Decimal | None = None
    unit: Literal["EUR per serving", "minutes"]

    @field_validator("lower", "upper", mode="before")
    @classmethod
    def valid_number(cls, value):
        return None if value is None else nonnegative(value)

    @model_validator(mode="after")
    def ordered(self):
        if self.upper is not None and self.upper < self.lower:
            raise ValueError("Measurement bounds are reversed")
        return self


class ValidatedEvaluation(Contract):
    version: str
    status: Literal["complete", "needs_clarification", "error"]
    grade: Decimal | None
    display_grade: Decimal | None
    classification: Literal["Very Good","Good","OK","Bad","Terrible"] | None
    weight_points: int = Field(strict=True)
    turns: tuple[Turn, ...] = Field(min_length=1)
    assessments: tuple[Assessment, ...] = Field(min_length=6,max_length=6)
    effort: EffortAssessment
    questions: tuple[str, ...]
    conflicts: tuple[Conflict, ...]
    safety_warnings: tuple[SafetyWarning, ...]
    safe_to_recommend: Literal[False] | None
    measurements: dict[Literal["money","time"], Measurement] = Field(default_factory=dict)

    @field_validator("assessments",mode="before")
    @classmethod
    def parse_assessments(cls, values):
        try:
            return tuple(read_assessment(value) for value in values)
        except (KeyError, TypeError) as exc:
            raise ValueError("Malformed saved component assessment") from exc

    @field_validator("effort",mode="before")
    @classmethod
    def parse_effort(cls, value):
        try:
            return read_effort(value)
        except (KeyError, TypeError) as exc:
            raise ValueError("Malformed saved Effort assessment") from exc

    @field_validator("grade","display_grade",mode="before")
    @classmethod
    def valid_grade(cls,value):
        return None if value is None else validated_grade(value)

    @model_validator(mode="after")
    def consistent(self):
        items = {a.parameter:a for a in self.assessments}
        if set(items) != set(COMPONENT_ORDER):
            raise ValueError("Exactly six distinct component assessments required")
        for assessment in self.assessments:
            if assessment.grade is not None:
                validated_component_grade(assessment.parameter, assessment.grade)
        if self.weight_points != 40:
            raise ValueError("The approved total is 40 WP")
        for key in ("time","energy"):
            if getattr(self.effort,key).model_dump() != items[key].model_dump():
                raise ValueError("Effort components disagree with the top-level assessments")
        sources = {turn.id:turn.text for turn in self.turns}
        if len(sources) != len(self.turns):
            raise ValueError("Duplicate source turn IDs")
        for item in (*self.assessments,*self.conflicts,*self.safety_warnings):
            for evidence in item.evidence:
                if evidence.source not in sources or evidence.statement not in sources[evidence.source]:
                    raise ValueError("Saved evidence is not traceable to the source turns")
        for conflict in self.conflicts:
            if items[conflict.parameter].status == "evaluated":
                raise ValueError("Unresolved conflict cannot have an evaluated component")
        expected = overall_grade(**{key:items[key].grade for key in COMPONENT_ORDER})
        check_decimal(self.grade, expected, "overall raw grade")
        check_decimal(self.display_grade, None if expected is None else display_grade(expected), "overall displayed grade")
        if self.classification != (None if expected is None else classify(expected)):
            raise ValueError("Saved overall classification disagrees with the grading engine")
        expected_status = "error" if any(a.status=="error" for a in self.assessments) else ("complete" if expected is not None else "needs_clarification")
        if self.status != expected_status:
            raise ValueError("Saved completeness status is inconsistent")
        if self.safe_to_recommend is not (False if self.safety_warnings else None):
            raise ValueError("Saved safety status is inconsistent")
        for key,measurement in self.measurements.items():
            if measurement.unit != ("EUR per serving" if key=="money" else "minutes"):
                raise ValueError("Measurement unit does not match its component")
            grader = grade_money if key=="money" else grade_time
            if items[key].grade is not None:
                if grader(measurement.lower) != items[key].grade or grader(measurement.upper if measurement.upper is not None else measurement.lower) != items[key].grade:
                    raise ValueError("Recorded measurement disagrees with its grade")
        return self

    def component(self, name):
        return self.effort if name=="effort" else next(a for a in self.assessments if a.parameter==name)


class ReportMetadata(Contract):
    food_name: str | None = Field(default=None,min_length=1,max_length=240)
    summary: str | None = Field(default=None,min_length=1,max_length=4000)
    evaluation_date: date | None = None
    experience_type: str | None = Field(default=None,min_length=1,max_length=120)
    report_id: str | None = Field(default=None,pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]{0,79}$")

    @field_validator("evaluation_date",mode="before")
    @classmethod
    def explicit_date(cls,value):
        if value is None:
            return None
        if isinstance(value,datetime) or not isinstance(value,(str,date)):
            raise ValueError("Supply an explicit ISO date, not an inferred timestamp")
        return value


class ReportDocument(Contract):
    report_version: Literal["0.2"] = "0.2"
    metadata: ReportMetadata = Field(default_factory=ReportMetadata)
    evaluation: ValidatedEvaluation

    @computed_field
    @property
    def calculation(self) -> dict:
        rows=[]
        for key in COMPONENT_ORDER:
            item=self.evaluation.component(key)
            weighted=None if item.grade is None else item.grade*WEIGHTS[key]
            rows.append(dict(parameter=key,grade=None if item.grade is None else str(item.grade),
                             weight_points=WEIGHTS[key],weighted_points=None if weighted is None else str(weighted),
                             overall_contribution=None if weighted is None else str(weighted/Decimal(40))))
        total=None if self.evaluation.grade is None else sum((Decimal(r["weighted_points"]) for r in rows),Decimal(0))
        return dict(formula="(12*Money + 8*Taste + 4*Time + 2*Energy + 8*Nutrition + 6*Happiness) / 40",
                    components=rows,weighted_total=None if total is None else str(total),divisor=40,
                    overall_raw=None if self.evaluation.grade is None else str(self.evaluation.grade))
