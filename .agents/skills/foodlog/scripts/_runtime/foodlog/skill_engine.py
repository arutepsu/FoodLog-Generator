"""Contracts and deterministic execution for host-authored skill assessments."""
from decimal import Decimal
from typing import Literal

from pydantic import ConfigDict, Field, field_validator, model_validator

from foodlog.grading import WEIGHTS, classify, display_grade, grade_money, grade_time, nonnegative, overall_grade
from foodlog.models import Assessment, Contract, EffortAssessment, Evidence

Component = Literal["money", "taste", "time", "energy", "nutrition", "happiness"]
Status = Literal["evaluated", "missing_information", "unresolved", "error"]
COMPONENTS = {"money", "taste", "time", "energy", "nutrition", "happiness"}


class Turn(Contract):
    model_config = ConfigDict(str_strip_whitespace=False)
    id: str = Field(min_length=1)
    text: str = Field(min_length=1)


class DraftAssessment(Contract):
    parameter: Component
    status: Status
    grade: Decimal | None = None
    lower: Decimal | None = None
    upper: Decimal | None = None
    currency: Literal["EUR"] = "EUR"
    evidence: tuple[Evidence, ...] = ()
    reasoning_summary: str = ""
    strengths: tuple[str, ...] = ()
    weaknesses: tuple[str, ...] = ()
    missing_information: tuple[str, ...] = ()
    uncertainties: tuple[str, ...] = ()

    @field_validator("grade", "lower", "upper", mode="before")
    @classmethod
    def numeric(cls, value):
        return None if value is None else nonnegative(value)

    @model_validator(mode="after")
    def consistent(self):
        numeric = self.parameter in ("money", "time")
        if numeric and self.grade is not None:
            raise ValueError("Money and Time grades are computed from lower/upper, never supplied")
        if not numeric and (self.lower is not None or self.upper is not None):
            raise ValueError("Only Money and Time accept numeric bounds")
        if self.upper is not None and (self.lower is None or self.upper < self.lower):
            raise ValueError("Upper must be at least lower")
        if self.status == "evaluated":
            if not self.evidence or not self.reasoning_summary or self.missing_information:
                raise ValueError("Evaluated assessments require evidence, reasoning and no required missing facts")
            if numeric and self.lower is None:
                raise ValueError("Evaluated numeric assessments require a value")
            if not numeric and self.grade not in tuple(Decimal(i) for i in range(1, 6)):
                raise ValueError("Qualitative grades must be representative integers 1 through 5")
        else:
            if self.grade is not None or self.lower is not None or self.upper is not None:
                raise ValueError("Unresolved assessments cannot carry numeric assessments")
            if not any(x.strip() for x in (*self.missing_information, *self.uncertainties, self.reasoning_summary)):
                raise ValueError("Unresolved assessments require an explanation")
        return self


class Conflict(Contract):
    parameter: Component
    question: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=2)


class SafetyWarning(Contract):
    message: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)


class EvaluationInput(Contract):
    turns: tuple[Turn, ...] = Field(min_length=1)
    assessments: tuple[DraftAssessment, ...] = Field(min_length=6, max_length=6)
    conflicts: tuple[Conflict, ...] = ()
    safety_warnings: tuple[SafetyWarning, ...] = ()

    @model_validator(mode="after")
    def grounded(self):
        sources = {turn.id: turn.text for turn in self.turns}
        if len(sources) != len(self.turns):
            raise ValueError("Turn IDs must be unique")
        if {a.parameter for a in self.assessments} != COMPONENTS:
            raise ValueError("Supply exactly one assessment for each of the six components")
        for item in (*self.assessments, *self.conflicts, *self.safety_warnings):
            for evidence in item.evidence:
                if evidence.source not in sources or evidence.statement not in sources[evidence.source]:
                    raise ValueError("Evidence must be an exact quote from its identified user turn")
        return self


def evaluate(payload: dict | EvaluationInput) -> dict:
    """Validate host judgments and compute grades; no model calls or inference."""
    draft = EvaluationInput.model_validate(payload)
    results = {}
    for item in draft.assessments:
        values = item.model_dump(exclude={"lower", "upper", "currency"})
        values["weight_points"] = WEIGHTS[item.parameter]
        if item.status == "evaluated" and item.parameter in ("money", "time"):
            grader = grade_money if item.parameter == "money" else grade_time
            lower_grade = grader(item.lower)
            upper_grade = grader(item.upper if item.upper is not None else item.lower)
            if lower_grade != upper_grade:
                values.update(status="unresolved", grade=None,
                              missing_information=(f"Clarify the {item.parameter} value: the supplied range crosses grade boundaries.",))
            else:
                values["grade"] = lower_grade
                if item.upper is not None and item.upper != item.lower:
                    values["uncertainties"] = (*item.uncertainties, "A range was supplied; both endpoints receive the same grade.")
        conflicts = [c for c in draft.conflicts if c.parameter == item.parameter]
        if conflicts:
            values.update(status="unresolved", grade=None,
                          missing_information=tuple(c.question for c in conflicts))
        results[item.parameter] = Assessment.model_validate(values)
    effort = EffortAssessment(time=results["time"], energy=results["energy"])
    raw = overall_grade(**{key: value.grade for key, value in results.items()})
    questions = list(dict.fromkeys(q for value in results.values() for q in value.missing_information))
    for value in results.values():
        if value.status != "evaluated" and not value.missing_information:
            questions.append(f"Please clarify {value.parameter}: {value.reasoning_summary or '; '.join(value.uncertainties)}")
    status = "error" if any(x.status == "error" for x in results.values()) else ("complete" if raw is not None else "needs_clarification")
    return {
        "version": "0.1",
        "status": status,
        "grade": None if raw is None else str(raw),
        "display_grade": None if raw is None else str(display_grade(raw)),
        "classification": None if raw is None else classify(raw),
        "weight_points": 40,
        "turns": [turn.model_dump(mode="json") for turn in draft.turns],
        "assessments": [results[key].model_dump(mode="json") for key in ("money","taste","time","energy","nutrition","happiness")],
        "effort": effort.model_dump(mode="json"),
        "questions": questions,
        "conflicts": [x.model_dump(mode="json") for x in draft.conflicts],
        "safety_warnings": [x.model_dump(mode="json") for x in draft.safety_warnings],
        "safe_to_recommend": False if draft.safety_warnings else None,
    }
