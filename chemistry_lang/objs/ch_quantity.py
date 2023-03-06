from decimal import Decimal
from typing import ForwardRef

from pint import Unit, DimensionalityError, Quantity, Context

from chemistry_lang.ch_handler import handler
from chemistry_lang.ch_token import Token
from .ch_number import CHNumber
from .ch_ureg import ureg

SupportedNumber = ForwardRef("CHQuantity") | CHNumber | Decimal | int | float


class CHQuantity:
    """
    A quantity with a formula and a unit.
    """

    def __init__(self, formula, magnitude: CHNumber, unit: Unit, token: Token = None):
        self.formula = formula
        self.magnitude = CHNumber(magnitude)
        self.unit = unit
        self.token = token

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
        return f"{self.quantity:~P}" + (f" {self.formula}" if self.formula else "")

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
        a, b = self.match_quantity(self, other)
        result = a.quantity + b.quantity

        return CHQuantity(
            self.formula + other.formula if other.formula else self.formula,
            CHNumber(result.magnitude),
            result.units,
            self.token,
        )

    def __radd__(self, other: SupportedNumber):
        return self + other

    def __sub__(self, other: SupportedNumber):
        other = self.ensure_quantity(other)
        a, b = self.match_quantity(self, other)
        result = a.quantity - b.quantity

        return CHQuantity(
            self.formula - other.formula if other.formula else self.formula,
            CHNumber(result.magnitude),
            result.units,
            self.token,
        )

    def __rsub__(self, other: SupportedNumber):
        other = self.ensure_quantity(other)
        a, b = self.match_quantity(self, other)
        result = b.quantity - a.quantity

        return CHQuantity(
            other.formula - self.formula if other.formula else self.formula,
            CHNumber(result.magnitude),
            result.units,
            self.token,
        )

    def __truediv__(self, other: SupportedNumber):
        other = self.ensure_quantity(other)
        a, b = self.match_quantity(self, other)
        result = a.quantity / b.quantity

        return CHQuantity(
            self.formula / other.formula if other.formula else self.formula,
            CHNumber(result.magnitude),
            result.units,
            self.token,
        )

    def __rtruediv__(self, other: SupportedNumber):
        other = self.ensure_quantity(other)
        a, b = self.match_quantity(self, other)
        result = b.quantity / a.quantity

        return CHQuantity(
            other.formula / self.formula if other.formula else self.formula,
            CHNumber(result.magnitude),
            result.units,
            self.token,
        )

    def __mul__(self, other: SupportedNumber):
        other = self.ensure_quantity(other)
        a, b = self.match_quantity(self, other)
        result = a.quantity * b.quantity

        return CHQuantity(
            self.formula * other.formula if other.formula else self.formula,
            CHNumber(result.magnitude),
            result.units,
            self.token,
        )

    def __rmul__(self, other: SupportedNumber):
        return self * other

    def __mod__(self, other: SupportedNumber):
        other = self.ensure_quantity(other)
        a, b = self.match_quantity(self, other)
        result = a.quantity % b.quantity

        return CHQuantity(
            self.formula - other.formula if other.formula else self.formula,
            CHNumber(result.magnitude),
            result.units,
            self.token,
        )

    def __eq__(self, other: SupportedNumber):
        other = self.ensure_quantity(other)
        a, b = self.match_quantity(self, other)
        return a.quantity == b.quantity

    def __ne__(self, other: SupportedNumber):
        other = self.ensure_quantity(other)
        a, b = self.match_quantity(self, other)
        return a.quantity != b.quantity

    def __lt__(self, other: SupportedNumber):
        other = self.ensure_quantity(other)
        a, b = self.match_quantity(self, other)
        return a.quantity < b.quantity

    def __le__(self, other: SupportedNumber):
        other = self.ensure_quantity(other)
        a, b = self.match_quantity(self, other)
        return a.quantity <= b.quantity

    def __gt__(self, other: SupportedNumber):
        other = self.ensure_quantity(other)
        a, b = self.match_quantity(self, other)
        return a.quantity > b.quantity

    def __ge__(self, other: SupportedNumber):
        other = self.ensure_quantity(other)
        a, b = self.match_quantity(self, other)
        return a.quantity >= b.quantity

    def __pow__(self, other: SupportedNumber):
        other = self.ensure_quantity(other)
        if not other.unit == ureg.dimensionless:
            self._raise(f"Cannot raise to power {other.unit}")
        if (int(other.magnitude) - other.magnitude) >= 0.0001:  # ε
            self._raise(f"Cannot raise to power {other.magnitude}")
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
        self._raise("Bad operand type for unary ~: 'CHQuantity'")

    def __int__(self):
        if self.unit != ureg.dimensionless:
            self._raise(f"Cannot convert {self.unit} to int")
        return int(self.magnitude)

    def __float__(self):
        if self.unit != ureg.dimensionless:
            self._raise(f"Cannot convert {self.unit} to float")
        return float(self.magnitude)

    def _raise(self, message):
        raise handler.error(message, self.token)

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
                magnitude = CHNumber(magnitude, self.magnitude.sig_fig)
                unit = target
            except DimensionalityError:
                self._raise(f"Cannot convert {self.unit} to {target}")
        # formula unit
        formula = self.formula
        if isinstance(target, FormulaUnit) and self.formula != target:
            if not reaction_context:
                self._raise(
                    f"Cannot convert {self.unit} to {target} without reaction context"
                )
            if (
                self.unit.dimensionality != ureg.mole.dimensionality
                and self.unit.dimensionality != ureg.gram.dimensionality
            ):
                self._raise(
                    f"Cannot convert {self.unit} to {target} without mole dimension"
                )
            if self.unit.dimensionality == ureg.gram.dimensionality:
                magnitude = self.quantity.to(ureg.mole, self.ctx).magnitude
                magnitude = CHNumber(magnitude, self.magnitude.sig_fig)
                unit = ureg.mole
            try:
                magnitude = magnitude * reaction_context[(self.formula, target)]
                magnitude = CHNumber(magnitude, self.magnitude.sig_fig)
            except KeyError:
                self._raise(f"Cannot convert {self.unit} to {target}")
            formula = target
        return CHQuantity(formula, magnitude, unit)

    def ensure_quantity(self, other: SupportedNumber) -> "CHQuantity":
        if isinstance(other, CHQuantity):
            return other
        elif isinstance(other, (int, float, Decimal)):
            return CHQuantity(None, CHNumber(other), ureg.dimensionless)
        elif isinstance(other, CHNumber):
            other = CHQuantity(None, other, ureg.dimensionless)
        else:
            self._raise(f"Cannot convert {other} to CHQuantity")
        return other

    def match_quantity(
        self,
        a: "CHQuantity",
        b: "CHQuantity",
        reaction_context: dict[
            tuple[ForwardRef("FormulaUnit"), ForwardRef("FormulaUnit")], Decimal
        ] = None,
    ) -> tuple["CHQuantity", "CHQuantity"]:
        """
        Make sure that the two quantities have the same unit and context.
        """

        from .ch_chemistry import FormulaUnit  # hack to avoid circular import

        # formula must match first
        if a.formula != b.formula:
            if b.formula is None or b.formula == FormulaUnit.formulaless:
                b = CHQuantity(a.formula, b.magnitude, b.unit)
            elif a.formula is None or a.formula == FormulaUnit.formulaless:
                a = CHQuantity(b.formula, a.magnitude, a.unit)
            elif reaction_context is None:
                self._raise(
                    f"Cannot convert {a.formula} to {b.formula} without context"
                )
            else:
                b = b.to(a.formula, reaction_context)
        # same unit
        if a.unit == b.unit:
            return a, b
        # dimensionless automatic escalate
        if b.unit is None or b.unit.dimensionality == ureg.dimensionless.dimensionality:
            return a, CHQuantity(a.formula, b.magnitude, a.unit)
        if a.unit is None or a.unit.dimensionality == ureg.dimensionless.dimensionality:
            return CHQuantity(b.formula, a.magnitude, b.unit), b
        # convert
        return a, b.to(a.unit)
