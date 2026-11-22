"""Validated contracts for future evaluators; derived fields cannot be supplied."""
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator, model_validator

from foodlog.grading import WEIGHTS, classify, display_grade, effort_grade, validated_grade

Parameter = Literal["money", "taste", "effort", "time", "energy", "nutrition", "happiness"]


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)


class Evidence(Contract):
    source: str = Field(min_length=1)
    statement: str = Field(min_length=1)


class Assessment(Contract):
    parameter: Parameter
    status: Literal["evaluated", "missing_information", "unresolved", "error"]
    grade: Decimal | None = None
    weight_points: int = Field(strict=True)
    evidence: tuple[Evidence, ...] = ()
    reasoning_summary: str = ""
    strengths: tuple[str, ...] = ()
    weaknesses: tuple[str, ...] = ()
    missing_information: tuple[str, ...] = ()
    uncertainties: tuple[str, ...] = ()

    @field_validator("grade", mode="before")
    @classmethod
    def valid_grade(cls, value):
        return None if value is None else validated_grade(value)

    @model_validator(mode="after")
    def consistent(self):
        if self.weight_points != WEIGHTS[self.parameter]:
            raise ValueError("Weight does not match the fixed parameter weight")
        if self.status == "evaluated":
            if self.grade is None or not self.evidence or not self.reasoning_summary:
                raise ValueError("Evaluated results require grade, evidence and reasoning")
            if self.missing_information:
                raise ValueError("Evaluated results cannot have unresolved required information")
        else:
            if self.grade is not None:
                raise ValueError("Unresolved results cannot carry a grade")
            if not any(x.strip() for x in (*self.missing_information, *self.uncertainties, self.reasoning_summary)):
                raise ValueError("Unresolved results require an explanation")
        return self

    @computed_field
    @property
    def display_grade(self) -> Decimal | None:
        return None if self.grade is None else display_grade(self.grade)

    @computed_field
    @property
    def classification(self) -> str | None:
        return None if self.grade is None else classify(self.grade)


class EffortAssessment(Contract):
    time: Assessment
    energy: Assessment
    parameter: Literal["effort"] = "effort"
    weight_points: Literal[6] = 6

    @model_validator(mode="after")
    def correct_components(self):
        if self.time.parameter != "time" or self.energy.parameter != "energy":
            raise ValueError("Effort requires Time and Energy components in their correct fields")
        return self

    @computed_field
    @property
    def status(self) -> str:
        statuses = {self.time.status, self.energy.status}
        for status in ("error", "unresolved", "missing_information"):
            if status in statuses:
                return status
        return "evaluated"

    @computed_field
    @property
    def grade(self) -> Decimal | None:
        return effort_grade(self.time.grade, self.energy.grade)

    @computed_field
    @property
    def display_grade(self) -> Decimal | None:
        return None if self.grade is None else display_grade(self.grade)

    @computed_field
    @property
    def classification(self) -> str | None:
        return None if self.grade is None else classify(self.grade)
