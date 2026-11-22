"""Fixed grading rules. No network calls or inferred missing values."""
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from types import MappingProxyType

WEIGHTS = MappingProxyType(dict(money=12, taste=8, effort=6, time=4, energy=2, nutrition=8, happiness=6))
LABELS = ("Very Good", "Good", "OK", "Bad", "Terrible")


def number(value) -> Decimal:
    """Convert finite decimal-compatible input; reject boolean pseudo-numbers."""
    if isinstance(value, bool):
        raise ValueError("Boolean is not a number")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError("Expected a finite number") from None
    if not result.is_finite():
        raise ValueError("Expected a finite number")
    return result


def nonnegative(value) -> Decimal:
    result = number(value)
    if result < 0:
        raise ValueError("Value cannot be negative")
    return result


def validated_grade(value) -> Decimal:
    result = number(value)
    if not 1 <= result <= 5:
        raise ValueError("Grade must be between 1 and 5")
    return result


def display_grade(value) -> Decimal:
    return validated_grade(value).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)


def classify(value) -> str:
    displayed = display_grade(value)
    for boundary, label in zip(("1.7", "2.5", "3.3", "4.0", "5.0"), LABELS):
        if displayed <= Decimal(boundary):
            return label
    raise AssertionError("Unreachable grade")


def grade_money(price_eur) -> Decimal | None:
    if price_eur is None:
        return None
    price = nonnegative(price_eur)
    for grade, upper in enumerate((3, 6, 12, 20), 1):
        if price <= upper:
            return Decimal(grade)
    return Decimal(5)


def grade_time(minutes) -> Decimal | None:
    if minutes is None:
        return None
    duration = nonnegative(minutes)
    for grade, upper in enumerate((15, 30, 120), 1):
        if duration < upper:
            return Decimal(grade)
    return Decimal(4 if duration <= 240 else 5)


def effort_grade(time, energy) -> Decimal | None:
    components = [None if x is None else validated_grade(x) for x in (time, energy)]
    if None in components:
        return None
    return (4 * components[0] + 2 * components[1]) / Decimal(6)


def overall_grade(*, money, taste, time, energy, nutrition, happiness) -> Decimal | None:
    """Use subgrades directly to avoid rounding the repeating Effort average."""
    inputs = dict(money=money, taste=taste, time=time, energy=energy, nutrition=nutrition, happiness=happiness)
    grades = {key: None if val is None else validated_grade(val) for key, val in inputs.items()}
    if None in grades.values():
        return None
    return sum((WEIGHTS[key] * val for key, val in grades.items()), Decimal(0)) / Decimal(40)


def cost_per_serving(total_eur, servings) -> Decimal:
    """Shared bills require caller-confirmed appropriate allocation."""
    total, count = nonnegative(total_eur), number(servings)
    if count <= 0:
        raise ValueError("Servings must be positive")
    return total / count


def ingredient_cost(purchase_eur, used_quantity, purchased_quantity) -> Decimal:
    """Quantities must use the same unit; cost covers only the consumed share."""
    price, used, purchased = nonnegative(purchase_eur), nonnegative(used_quantity), number(purchased_quantity)
    if purchased <= 0 or used > purchased:
        raise ValueError("Purchased quantity must be positive and at least the used quantity")
    return price * used / purchased


def validated_component_grade(parameter, value):
    """Taste supports tenths; other component scales retain their fixed anchors."""
    grade = validated_grade(value)
    if parameter == "taste":
        if grade != grade.quantize(Decimal("0.1")):
            raise ValueError("Taste grades must use at most one decimal place")
    elif grade not in tuple(Decimal(i) for i in range(1, 6)):
        raise ValueError("Component grades must use representative integers 1 through 5")
    return grade
