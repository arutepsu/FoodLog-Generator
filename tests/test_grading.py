from decimal import Decimal as D

import pytest
from pydantic import ValidationError

from foodlog.grading import (
    classify, display_grade, grade_money, grade_time, effort_grade,
    overall_grade, cost_per_serving, ingredient_cost,
)
from foodlog.models import Assessment, Evidence, EffortAssessment


@pytest.mark.parametrize("price,expected", [(0,1),(3,1),("3.01",2),(6,2),("6.01",3),(12,3),("12.01",4),(20,4),("20.01",5),(30,5)])
def test_money_boundaries(price, expected):
    assert grade_money(price) == D(expected)


@pytest.mark.parametrize("minutes,expected", [(0,1),(14,1),(15,2),(29,2),(30,3),(119,3),(120,4),(240,4),(241,5)])
def test_time_boundaries(minutes, expected):
    assert grade_time(minutes) == D(expected)


@pytest.mark.parametrize("function", [grade_money, grade_time])
@pytest.mark.parametrize("value", [-1, "NaN", "Infinity", "-Infinity", True, "invalid"])
def test_invalid_numeric_inputs(function, value):
    with pytest.raises(ValueError):
        function(value)


def test_unknown_values_are_not_neutral():
    assert grade_money(None) is None
    assert grade_time(None) is None
    assert effort_grade(None, 1) is None
    assert overall_grade(money=None, taste=1, time=1, energy=1, nutrition=1, happiness=1) is None


@pytest.mark.parametrize("raw,display,label", [("1.74","1.7","Very Good"),("1.75","1.8","Good"),("2.55","2.6","OK"),("3.35","3.4","Bad"),("4.05","4.1","Terrible"),(5,"5.0","Terrible")])
def test_classification_uses_half_up_display(raw, display, label):
    assert display_grade(raw) == D(display)
    assert classify(raw) == label


@pytest.mark.parametrize("value", [0, "5.01", "NaN", True])
def test_invalid_grades(value):
    with pytest.raises(ValueError):
        display_grade(value)


def test_overall_uses_fixed_weights_and_unrounded_components():
    assert effort_grade(3, 1) == D(14) / D(6)
    assert overall_grade(money=2,taste=1,time=3,energy=1,nutrition=2,happiness=3) == D(2)
    assert overall_grade(money=1,taste=1,time=3,energy=1,nutrition=1,happiness=1) == D("1.2")


def test_costs_use_consumed_quantities_and_servings():
    assert cost_per_serving(12, 4) == D(3)
    assert cost_per_serving(45, 3) == D(15)
    assert ingredient_cost(3, 200, 1000) == D("0.6")


@pytest.mark.parametrize("total,servings", [(-1,2),(12,0),(12,-1),(12,True),(12,"NaN")])
def test_invalid_cost_allocations(total, servings):
    with pytest.raises(ValueError):
        cost_per_serving(total, servings)


def test_consumption_cannot_exceed_purchase():
    with pytest.raises(ValueError):
        ingredient_cost(3, 1200, 1000)


def evaluated(**changes):
    values = dict(parameter="money",status="evaluated",grade="2",weight_points=12,
                  evidence=[Evidence(source="user_input", statement="Five euros per serving")],
                  reasoning_summary="Price is above 3 and at most 6 euros.")
    values.update(changes)
    return Assessment(**values)


def test_assessment_derives_classification_and_preserves_raw_grade():
    result = evaluated(grade="1.75")
    assert result.grade == D("1.75")
    assert result.display_grade == D("1.8")
    assert result.classification == "Good"


@pytest.mark.parametrize("changes", [dict(grade=None),dict(grade=6),dict(weight_points=8),dict(evidence=[]),dict(status="missing_information"),dict(unexpected=True)])
def test_inconsistent_assessments_are_rejected(changes):
    with pytest.raises(ValidationError):
        evaluated(**changes)


def test_missing_assessment_requires_explanation():
    result = Assessment(parameter="money",status="missing_information",weight_points=12,
                        missing_information=["What was the price per serving?"])
    assert result.grade is None
    assert result.classification is None
    with pytest.raises(ValidationError):
        Assessment(parameter="money",status="missing_information",weight_points=12)


def test_effort_contract_derives_grade_from_components():
    time = evaluated(parameter="time", weight_points=4, grade=3)
    energy = evaluated(parameter="energy", weight_points=2, grade=1)
    result = EffortAssessment(time=time, energy=energy)
    assert result.grade == D(14) / D(6)
    assert result.display_grade == D("2.3")
    assert result.classification == "Good"
    assert result.weight_points == 6
    with pytest.raises(ValidationError):
        EffortAssessment(time=energy, energy=time)


def test_missing_effort_component_blocks_aggregate():
    time = Assessment(parameter="time", weight_points=4, status="missing_information",
                      missing_information=["Total food-related time?"])
    result = EffortAssessment(time=time, energy=evaluated(parameter="energy",weight_points=2,grade=1))
    assert result.grade is None
    assert result.status == "missing_information"
