from decimal import Decimal
from operator import add, mul, truediv, mod
from typing import Callable

from pint import Unit, Quantity, DimensionalityError

from chemistry_lang.ch_handler import handler
from .ch_ureg import ureg


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

    def __init__(self, formula, magnitude: Decimal, unit: Unit):
        self.formula = formula
        self.magnitude = magnitude
        self.unit = unit

    def __repr__(self):
        return self.__format__("")

    def __format__(self, _format_spec: str) -> str:
        return f"{{magnitude}}{{unit}}{{formula}}".format(
            magnitude=self.magnitude.__format__(_format_spec),
            unit=" " + self.unit.__format__(_format_spec)
            if self.unit != ureg.dimensionless
            else "",
            formula=" " + self.formula.__format__(_format_spec) if self.formula else "",
        )

    def binary_operation(
        self,
        other,
        operator: Callable[[Quantity | Decimal, Quantity | Decimal], Quantity],
    ) -> tuple[Unit, Decimal]:
        try:
            if isinstance(other, CHQuantity):
                res = operator(self.unit * self.magnitude, other.unit * other.magnitude)
            elif isinstance(other, Quantity):
                res = operator(self.unit * self.magnitude, other)
            elif (
                isinstance(other, int)
                or isinstance(other, float)
                or isinstance(other, Decimal)
            ):
                res = operator(self.magnitude, other) * self.unit
            else:
                raise TypeError(f"Cannot perform operation with {type(other)}")
            unit = res.units
            magnitude = res.magnitude
        except DimensionalityError:
            raise handler.error(f"Cannot {operator.__name__} {self} and {other}")
        return unit, magnitude

    def __add__(self, other):
        unit, mag = self.binary_operation(other, add)
        return CHQuantity(
            self.formula + other.formula
            if isinstance(other, CHQuantity)
            else self.formula,
            mag,
            unit,
        )

    __radd__ = __add__

    def __sub__(self, other):
        return self + (-other)

    def __rsub__(self, other):
        return -self + other

    def __mul__(self, other):
        unit, mag = self.binary_operation(other, mul)
        return CHQuantity(
            self.formula * other.formula
            if isinstance(other, CHQuantity)
            else self.formula,
            mag,
            unit,
        )

    __rmul__ = __mul__

    def __truediv__(self, other):
        unit, mag = self.binary_operation(other, truediv)
        return CHQuantity(
            self.formula / other.formula
            if isinstance(other, CHQuantity)
            else self.formula,
            mag,
            unit,
        )

    def __rtruediv__(self, other):
        unit, mag = self.binary_operation(other, lambda a, b: b / a)
        return CHQuantity(
            self.formula / other.formula
            if isinstance(other, CHQuantity)
            else self.formula,
            mag,
            unit,
        )

    def __pow__(self, other):
        unit, mag = self.binary_operation(other, pow)
        return CHQuantity(
            self.formula**other.formula
            if isinstance(other, CHQuantity)
            else self.formula,
            mag,
            unit,
        )

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

    def extract_magnitude(self, other):
        msg = f"Cannot compare {self} and {other}"
        if isinstance(other, CHQuantity):
            if self.unit != other.unit:
                raise handler.error(msg)
            elif self.formula != other.formula:
                raise handler.error(msg)
            return other.magnitude
        elif other.__class__ not in {int, float, Decimal}:
            raise handler.error(msg)
        return other

    def __ge__(self, other):
        return self.magnitude >= self.extract_magnitude(other)

    def __le__(self, other):
        return self.magnitude <= self.extract_magnitude(other)

    def __lt__(self, other):
        return self.magnitude < self.extract_magnitude(other)

    def __gt__(self, other):
        return self.magnitude > self.extract_magnitude(other)

    def __ne__(self, other):
        return self.magnitude != self.extract_magnitude(other)

    def __eq__(self, other):
        return self.magnitude == self.extract_magnitude(other)

    def __mod__(self, other):
        unit, mag = self.binary_operation(other, mod)
        return CHQuantity(self.formula, mag, unit)

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
                    magnitude = (self.magnitude * self.unit).to(
                        target, self.formula.context
                    )  # formula-less has no context
                else:
                    magnitude = (self.magnitude * self.unit).to(target)
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
        return self.magnitude * self.unit
