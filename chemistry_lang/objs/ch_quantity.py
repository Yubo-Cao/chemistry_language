from contextlib import suppress
from decimal import Decimal
from typing import ForwardRef

from pint import Unit, DimensionalityError, Quantity, Context

from chemistry_lang.ch_error import CHError
from chemistry_lang.ch_handler import handler
from .ch_number import CHNumber
from .ch_ureg import ureg

SupportedNumber = ForwardRef("CHQuantity") | CHNumber | Decimal | int | float


class CHQuantity:
    """
    A quantity with a formula and a unit.
    """

    def __init__(self, formula, magnitude: CHNumber, unit: Unit):
        self.formula = formula
        self.magnitude = CHNumber(magnitude)
        self.unit = unit

    @property
    def ctx(self):
        ctx = Context()
        try:
            ctx = self.formula.context
        except (ValueError, AttributeError):  # formula-less has no context
            pass
        return ctx

    @property
    def quantity(self):
        return Quantity(self.magnitude, self.unit)

    def __repr__(self):
        return f"CHQuantity(formula={self.formula!r}, magnitude={self.magnitude!r}, unit={self.unit!r})"

    def __str__(self):
        result = [str(self.magnitude)]
        if self.formula:
            result.append(str(self.formula))
        if self.unit and self.unit != ureg.dimensionless:
            result.append(str(self.unit))
        return " ".join(result)

    def __format__(self, _format_spec: str) -> str:
        return f"{{magnitude}}{{unit}}{{formula}}".format(
            magnitude=self.magnitude.__format__(_format_spec),
            unit=" " + self.unit.__format__(_format_spec)
            if self.unit != ureg.dimensionless
            else "",
            formula=" " + self.formula.__format__(_format_spec) if self.formula else "",
        )

    def __add__(self, other: SupportedNumber):
        other = self.ensure_quantity(other)
        a, b = CHQuantity.match_quantity(self, other)
        result = a.quantity + b.quantity

        return CHQuantity(
            self.formula + other.formula if other.formula else self.formula,
            CHNumber(result.magnitude),
            result.units,
        )

    def __radd__(self, other: SupportedNumber):
        return self + other

    def __sub__(self, other: SupportedNumber):
        other = self.ensure_quantity(other)
        a, b = CHQuantity.match_quantity(self, other)
        result = a.quantity - b.quantity

        return CHQuantity(
            self.formula - other.formula if other.formula else self.formula,
            CHNumber(result.magnitude),
            result.units,
        )

    def __rsub__(self, other: SupportedNumber):
        other = self.ensure_quantity(other)
        a, b = CHQuantity.match_quantity(self, other)
        result = b.quantity - a.quantity

        return CHQuantity(
            other.formula - self.formula if other.formula else self.formula,
            CHNumber(result.magnitude),
            result.units,
        )

    def __truediv__(self, other: SupportedNumber):
        other = self.ensure_quantity(other)
        a, b = CHQuantity.match_quantity(self, other)
        result = a.quantity / b.quantity

        return CHQuantity(
            self.formula / other.formula if other.formula else self.formula,
            CHNumber(result.magnitude),
            result.units,
        )

    def __rtruediv__(self, other: SupportedNumber):
        other = self.ensure_quantity(other)
        a, b = CHQuantity.match_quantity(self, other)
        result = b.quantity / a.quantity

        return CHQuantity(
            other.formula / self.formula if other.formula else self.formula,
            CHNumber(result.magnitude),
            result.units,
        )

    def __mul__(self, other: SupportedNumber):
        other = self.ensure_quantity(other)
        a, b = CHQuantity.match_quantity(self, other)
        result = a.quantity * b.quantity

        return CHQuantity(
            self.formula * other.formula if other.formula else self.formula,
            CHNumber(result.magnitude),
            result.units,
        )

    def __rmul__(self, other: SupportedNumber):
        return self * other

    def __mod__(self, other: SupportedNumber):
        other = self.ensure_quantity(other)
        a, b = CHQuantity.match_quantity(self, other)
        result = a.quantity % b.quantity

        return CHQuantity(
            self.formula - other.formula if other.formula else self.formula,
            CHNumber(result.magnitude),
            result.units,
        )

    def __eq__(self, other: SupportedNumber):
        other = self.ensure_quantity(other)
        a, b = CHQuantity.match_quantity(self, other)
        return a.quantity == b.quantity

    def __ne__(self, other: SupportedNumber):
        other = self.ensure_quantity(other)
        a, b = CHQuantity.match_quantity(self, other)
        return a.quantity != b.quantity

    def __lt__(self, other: SupportedNumber):
        other = self.ensure_quantity(other)
        a, b = CHQuantity.match_quantity(self, other)
        return a.quantity < b.quantity

    def __le__(self, other: SupportedNumber):
        other = self.ensure_quantity(other)
        a, b = CHQuantity.match_quantity(self, other)
        return a.quantity <= b.quantity

    def __gt__(self, other: SupportedNumber):
        other = self.ensure_quantity(other)
        a, b = CHQuantity.match_quantity(self, other)
        return a.quantity > b.quantity

    def __ge__(self, other: SupportedNumber):
        other = self.ensure_quantity(other)
        a, b = CHQuantity.match_quantity(self, other)
        return a.quantity >= b.quantity

    def __pow__(self, other: SupportedNumber):
        other = self.ensure_quantity(other)
        if not other.unit == ureg.dimensionless:
            raise handler.error(f"Cannot raise to power {other.unit}")
        if (int(other.magnitude) - other.magnitude) >= 0.0001:  # ε
            raise handler.error(f"Cannot raise to power {other.magnitude}")
        result = 1
        for _ in range(int(other.magnitude)):
            result *= self
        return result

    def __bool__(self):
        return bool(self.magnitude)

    def __neg__(self):
        return CHQuantity(self.formula, -self.magnitude, self.unit)

    def __pos__(self):
        return CHQuantity(self.formula, +self.magnitude, self.unit)

    def __abs__(self):
        return CHQuantity(self.formula, abs(self.magnitude), self.unit)

    def __invert__(self):
        raise handler.error("Bad operand type for unary ~: 'CHQuantity'")

    def __int__(self):
        if self.unit != ureg.dimensionless:
            raise handler.error(f"Cannot convert {self.unit} to int")
        return int(self.magnitude)

    def __float__(self):
        if self.unit != ureg.dimensionless:
            raise handler.error(f"Cannot convert {self.unit} to float")
        return float(self.magnitude)

    def to(
        self,
        target: Unit | ForwardRef("FormulaUnit"),
        reaction_context: dict[
            tuple[ForwardRef("FormulaUnit"), ForwardRef("FormulaUnit")], Decimal
        ] = None,
    ):
        """
        Convert the quantity to the given unit.
        """

        from .ch_chemistry import FormulaUnit  # hack to avoid circular import

        magnitude = self.magnitude
        # unit
        unit = self.unit
        if isinstance(target, Unit) and self.unit != target:
            try:
                magnitude = self.quantity.to(target, self.ctx).magnitude
                unit = target
            except DimensionalityError:
                raise handler.error(f"Cannot convert {self.unit} to {target}")
        # formula unit
        formula = self.formula
        if isinstance(target, FormulaUnit) and self.formula != target:
            if not reaction_context:
                raise handler.error(
                    f"Cannot convert {self.unit} to {target} without reaction context"
                )
            if (
                self.unit.dimensionality != ureg.molar.dimensionality
                and self.unit.dimensionality != ureg.gram.dimensionality
            ):
                raise handler.error(
                    f"Cannot convert {self.unit} to {target} without molar context"
                )
            try:
                magnitude = magnitude * reaction_context[(self.formula, target)]
            except KeyError:
                raise handler.error(f"Cannot convert {self.unit} to {target}")
            formula = target
        return CHQuantity(formula, magnitude, unit)

    @staticmethod
    def ensure_quantity(other: SupportedNumber) -> "CHQuantity":
        if isinstance(other, CHQuantity):
            return other
        elif isinstance(other, (int, float, Decimal)):
            return CHQuantity(None, CHNumber(other), ureg.dimensionless)
        elif isinstance(other, CHNumber):
            other = CHQuantity(None, other, ureg.dimensionless)
        else:
            raise handler.error(f"Cannot convert {other} to CHQuantity")
        return other

    @staticmethod
    def match_quantity(
        a: "CHQuantity",
        b: "CHQuantity",
        reaction_context: dict[
            tuple[ForwardRef("FormulaUnit"), ForwardRef("FormulaUnit")], Decimal
        ] = None,
        _retry=False,
    ) -> tuple["CHQuantity", "CHQuantity"]:
        """
        Make sure that the two quantities have the same unit and context.
        """

        from .ch_chemistry import FormulaUnit  # hack to avoid circular import

        with suppress(DimensionalityError, CHError):
            if a.unit == b.unit:  # same unit
                return a, b
            if (
                b.unit is None
                or b.unit.dimensionality == ureg.dimensionless.dimensionality
            ):  # dimensionless automatic escalate
                if (
                    b.formula is None
                    or b.formula == FormulaUnit.formulaless
                    or b.formula == a.formula
                ):
                    return a, CHQuantity(a.formula, b.magnitude, a.unit)
            return a, b.to(a.unit, reaction_context).to(a.formula, reaction_context)

        if not _retry:
            return CHQuantity.match_quantity(b, a, reaction_context, True)
