from decimal import Decimal

from pint import Unit, DimensionalityError, Quantity

from chemistry_lang.ch_handler import handler
from .ch_number import CHNumber
from .ch_ureg import ureg
from typing import ForwardRef

SupportedNumber = ForwardRef("CHQuantity") | CHNumber | Decimal | int | float


class CHQuantity:
    """
    This quantity shall process the following:
    - context: pint.Context: the context in which the quantity is used, i.e., the reaction
    - formula: ch_ast.Reaction: the formula of the quantity
    - unit: pint.Unit: the unit of the quantity, pint
    - magnitude: Decimal: the magnitude of the quantity.

    The quantity object shall be able to do conversion between reactions, simply by
    calling to(Formula) and to(Unit) methods.

    It acts as a wrapper around quantity object. But it adds extra check of formula
    before conversion.
    """

    def __init__(self, formula, magnitude: CHNumber, unit: Unit):
        self.formula = formula
        self.magnitude = magnitude
        self.unit = unit

    def __repr__(self):
        return f'CHQuantity(formula={self.formula!r}, magnitude={self.magnitude!r}, unit={self.unit!r})'

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
        result = self.quantity + other.quantity
        return CHQuantity(
            self.formula + other.formula if other.formula else self.formula,
            CHNumber(result.magnitude),
            result.units,
        )

    def __radd__(self, other: SupportedNumber):
        return self + other

    def __sub__(self, other: SupportedNumber):
        other = self.ensure_quantity(other)
        result = self.quantity - other.quantity
        return CHQuantity(
            self.formula - other.formula if other.formula else self.formula,
            CHNumber(result.magnitude),
            result.units,
        )

    @staticmethod
    def ensure_quantity(other: SupportedNumber | Decimal | int | float) -> "CHQuantity":
        if isinstance(other, CHQuantity):
            return other
        elif isinstance(other, (int, float, Decimal)):
            return CHQuantity(None, CHNumber(other), ureg.dimensionless)
        elif isinstance(other, CHNumber):
            other = CHQuantity(None, other, ureg.dimensionless)
        else:
            raise handler.error(f"Cannot convert {other} to CHQuantity")
        return other

    def __rsub__(self, other: SupportedNumber):
        other = self.ensure_quantity(other)
        result = other.quantity - self.quantity
        return CHQuantity(
            other.formula - self.formula if other.formula else self.formula,
            CHNumber(result.magnitude),
            result.units,
        )

    def __truediv__(self, other: SupportedNumber):
        other = self.ensure_quantity(other)
        result = self.quantity / other.quantity
        return CHQuantity(
            self.formula / other.formula if other.formula else self.formula,
            CHNumber(result.magnitude),
            result.units,
        )

    def __rtruediv__(self, other: SupportedNumber):
        other = self.ensure_quantity(other)
        result = other.quantity / self.quantity
        return CHQuantity(
            other.formula / self.formula if other.formula else self.formula,
            CHNumber(result.magnitude),
            result.units,
        )

    def __mul__(self, other: SupportedNumber):
        other = self.ensure_quantity(other)
        result = self.quantity * other.quantity
        return CHQuantity(
            self.formula * other.formula if other.formula else self.formula,
            CHNumber(result.magnitude),
            result.units,
        )

    def __rmul__(self, other: SupportedNumber):
        return self * other

    def __mod__(self, other: SupportedNumber):
        other = self.ensure_quantity(other)
        result = self.quantity % other.quantity
        return CHQuantity(
            self.formula - other.formula if other.formula else self.formula,
            CHNumber(result.magnitude),
            result.units,
        )

    def __eq__(self, other: SupportedNumber):
        other = self.ensure_quantity(other)
        return self.quantity == other.quantity

    def __ne__(self, other: SupportedNumber):
        other = self.ensure_quantity(other)
        return self.quantity != other.quantity

    def __lt__(self, other: SupportedNumber):
        other = self.ensure_quantity(other)
        return self.quantity < other.quantity

    def __le__(self, other: SupportedNumber):
        other = self.ensure_quantity(other)
        return self.quantity <= other.quantity

    def __gt__(self, other: SupportedNumber):
        other = self.ensure_quantity(other)
        return self.quantity > other.quantity

    def __ge__(self, other: SupportedNumber):
        other = self.ensure_quantity(other)
        return self.quantity >= other.quantity

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

    def to(self, target: Unit, reaction_context):
        """
        Convert the quantity to the given unit.
        """

        from .ch_chemistry import FormulaUnit  # hack to avoid circular import

        magnitude = self.magnitude
        unit = self.unit
        if isinstance(target, Unit) and self.unit != target:
            try:
                if self.formula.formulas:
                    magnitude = self.quantity.to(
                        target, self.formula.context
                    )  # formula-less has no context
                else:
                    magnitude = self.quantity.to(target)
                magnitude = Decimal(magnitude.magnitude)
                unit = target
            except DimensionalityError:
                raise handler.error(f"Cannot convert {self.unit} to {target}")
        formula = self.formula
        if isinstance(target, FormulaUnit) and self.formula != target:
            # molar ratio
            try:
                magnitude = magnitude * reaction_context[(self.formula, target)]
            except KeyError:
                raise handler.error(f"Cannot convert {self.unit} to {target}")
            formula = target
        return CHQuantity(formula, magnitude, unit)

    @property
    def quantity(self):
        return Quantity(self.magnitude, self.unit)
