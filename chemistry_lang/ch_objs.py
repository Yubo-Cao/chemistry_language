import itertools
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation, getcontext
from functools import cached_property
from itertools import chain, permutations
from math import lcm
from operator import add, mod, mul, truediv
from typing import Callable, Any, Iterable

from pint import DimensionalityError, Quantity, Unit, Context
from sympy import Integer, symbols, solve_linear_system, Matrix, fraction

from chemistry_lang.ch_handler import handler
from chemistry_lang.ch_periodic_table import periodic_table
from chemistry_lang.ch_token import Token
from chemistry_lang.ch_ureg import ureg

getcontext().rounding = ROUND_HALF_UP


class CHString:
    """
    CHString represents a string in the chemistry helper
    """

    def __init__(self, string: str, sub: bool):
        self.string = string
        self.need_substitute = sub

    def __repr__(self):
        return (
                "<CHString " + ("s'" if self.need_substitute else "'") + self.string + "'>"
        )

    def __str__(self):
        return self.string if not self.need_substitute else self.substituted()

    def substituted(self):
        from chemistry_lang.ch_eval import evaluate
        from ch_interpreter import interpreter

        if self.need_substitute:
            results = [
                interpreter.stringify(evaluate(self.string[sub[0]: sub[1]]))
                for sub in self.extract_subs
            ]
            ret = self.string
            offset = 0
            for sub, res in zip(self.extract_subs, results):
                ret = ret[: sub[0] + offset - 1] + res + ret[sub[1] + offset + 1:]
                offset += len(res) - (sub[1] - sub[0] + 2)
            return ret.replace(r"\}", "}").replace(r"\{", "{")
        else:
            return self.string

    @cached_property
    def extract_subs(self) -> list[tuple[int, int]]:
        stack: list[tuple[str, int]] = []
        to_be_substituted: list[tuple[int, int]] = []
        for idx, char in enumerate(self.string):
            match char:
                case "{":
                    if idx == 0 or idx > 0 and self.string[idx - 1] != "\\":
                        stack.append((char, idx))
                case "}":
                    if idx == 0 or idx > 0 and self.string[idx - 1] != "\\":
                        if (res := stack.pop())[0] != "{":
                            handler.error("Unmatched braces")
                        to_be_substituted.append((res[1] + 1, idx))
                case _:
                    pass
        return to_be_substituted


class CHVariable:
    def __init__(self, name, value):
        self.name = name
        self.value = value


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
            self.formula ** other.formula
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


class EvalDecimal:
    def __init__(self, name):
        self.name = name

    def __get__(self, instance, owner):
        if instance is None:
            return self
        prop = getattr(instance, self.name)
        if isinstance(prop, str):
            from chemistry_lang.ch_eval import ch

            prop = ch.evaluate(prop)
        return self.__check_type(prop)

    def __set__(self, instance, value):
        if not isinstance(value, str) and not isinstance(value, Decimal | int | float):
            raise handler.error(
                "Invalid type %s for property %s"
                % (value.__class__, self.name.removeprefix("_@eval"))
            )
        setattr(instance, self.name, value)

    def __set_name__(self, owner, name):
        self.name = "_@eval" + name

    def __check_type(self, value):
        if not isinstance(value, Decimal | CHQuantity | int | float):
            raise handler.error("Invalid type for property %s" % self.name)
        if isinstance(value, CHQuantity):
            value = value.magnitude
        elif isinstance(value, int) or isinstance(value, float):
            value = Decimal(value)
        return value


class Element:
    symbol: str
    number: Decimal = EvalDecimal("number")
    charge: Decimal = EvalDecimal("charge")

    def __init__(self, symbol, number=Decimal(1), charge=Decimal(0)):
        self.symbol = symbol
        self.number = number
        self.charge = charge

    def __eq__(self, other):
        return (
                self.symbol == other.symbol
                and self.number == other.number
                and self.charge == other.charge
        )

    def __hash__(self):
        return hash((self.symbol, self.number, self.charge))

    def __str__(self):
        sub = "_{%s}" % self.number if self.number != 1 else ""
        sup = "^{%s}" % self.charge if self.charge != 0 else ""
        return f"{self.symbol}{sub}{sup}"

    def __getattr__(self, item):
        try:
            return periodic_table.get(self.symbol).get(item)
        except KeyError:
            raise AttributeError("'Element' object has no attribute '%s'" % item)


class CHFormula:
    terms: tuple[Element, ...]
    number = EvalDecimal("number")
    charge = EvalDecimal("charge")

    def __init__(self, terms, number=Decimal(1), charge=Decimal(0)):
        self.terms = tuple(terms)
        self.number = number
        self.charge = charge

    def __str__(self) -> str:
        return (
                (str(self.number) if self.number != 1 else "")
                + "".join(map(str, self.terms))
                + ("^{%d}" % self.charge if self.charge else "")
        )

    @cached_property
    def count_dict(self):
        """
        Return a dictionary of element symbol and count.
        """

        result = {}
        for term in self.terms:
            if isinstance(term, Element):
                result[term.symbol] = result.get(term.symbol, 0) + term.number
            elif isinstance(term, CHFormula):
                for symbol, count in term.count_dict.items():
                    result[symbol] = result.get(symbol, 0) + count * term.number
        return result

    @cached_property
    def molecular_mass(self):
        """
        Return the molecular mass of the formula.
        """
        return CHQuantity(
            FormulaUnit([self]),
            sum(
                periodic_table.get(element, "AtomicMass") * number
                for element, number in self.count_dict.items()
            ),
            ureg.gram / ureg.mol,
        )

    @cached_property
    def context(self):
        """
        Return a context for the formula.
        """
        c = Context()
        c.add_transformation(
            "[mass]", "[substance]", lambda reg, x: x / self.molecular_mass.quantity
        )
        c.add_transformation(
            "[substance]", "[mass]", lambda reg, x: x * self.molecular_mass.quantity
        )
        return c

    def __contains__(self, item):
        return item in self.count_dict

    def count(self, item):
        return self.count_dict.get(item, 0)

    def __eq__(self, other):
        return (
                self.terms == other.terms
                and self.number == other.number
                and self.charge == other.charge
        )

    def __hash__(self):
        return hash((self.terms, self.number, self.charge))


class CHPartialFormula(CHFormula):
    terms: tuple[CHFormula, ...]
    number = EvalDecimal("number")
    charge = EvalDecimal("charge")

    def __str__(self):
        return (
                ("(%s)" if self.number != 0 else "%s") % "".join(str(e) for e in self.terms)
                + ("_{%s}" % self.number if self.number != 1 else "")
                + ("^{%s}" % self.charge if self.charge else "")
        )

    def __hash__(self) -> int:
        return hash((self.terms, self.number, self.charge))

    def __eq__(self, other: Any) -> bool:
        return (
                isinstance(other, CHPartialFormula)
                and self.terms == other.terms
                and self.number == other.number
                and self.charge == other.charge
        )


class FormulaUnit:
    def __init__(self, formula: Iterable[CHFormula]):
        self.formulas = tuple(formula)

    def __repr__(self):
        if self.formulas:
            return "<FormulaUnit " + ", ".join(map(str, self.formulas)) + ">"
        else:
            return "<FormulaUnit formulaless>"

    def __str__(self):
        if self.formulas:
            return ", ".join(map(str, self.formulas))
        else:
            return "formulaless"

    def __add__(self, other):
        if self.formulas == other.formulas:
            return self
        else:
            raise handler.error("Can not add {} and {}".format(self, other))

    def __sub__(self, other):
        return self + (-other)

    def __mul__(self, other):
        return FormulaUnit([*self.formulas, *other.formulas])

    def __truediv__(self, other):
        result = list(self.formulas)
        for formula in other.formulas:
            try:
                result.remove(formula)
            except ValueError:
                raise handler.error("Can not divide {} by {}".format(self, other))
        return FormulaUnit(result)

    def __pow__(self, other):
        if isinstance(other, int):
            return FormulaUnit(*itertools.chain([self.formulas] * other))
        elif isinstance(other, FormulaUnit) and other.formulas == ():
            return FormulaUnit([])
        else:
            raise handler.error("Can not raise {} to {}".format(self, other))

    def __neg__(self):
        return self

    def __pos__(self):
        return self

    def __inv__(self):
        raise handler.error("Can not invert {}".format(self))

    def __bool__(self):
        return bool(self.formulas)

    def __not__(self):
        return not bool(self)

    def __hash__(self):
        return hash(self.formulas)

    def __eq__(self, other):
        return self.formulas == other.formulas

    @property
    def context(self):
        if len(self.formulas) == 1:
            return self.formulas[0].context
        else:
            raise handler.error("Can not get context of {}".format(self))


@dataclass
class Reaction:
    reactants: list[CHFormula]
    to: Token
    products: list[CHFormula]

    def __str__(self) -> str:
        return (
                " + ".join(map(str, self.reactants))
                + " -> "
                + " + ".join(map(str, self.products))
        )

    @cached_property
    def balanced(self):
        elements = set(
            chain(*(formula.count_dict for formula in self.reactants + self.products))
        )
        matrix = [
            [Integer(reactant.count(element)) for reactant in self.reactants]
            + [Integer(-product.count(element)) for product in self.products]
            + [Integer(0)]
            for element in elements
        ]

        variables = [
            symbols(str(formula)) for formula in self.reactants + self.products
        ]
        result = solve_linear_system(Matrix(matrix), *variables)
        least_common_multiple = lcm(
            *map(lambda x: int(fraction(x)[1]), result.values())
        )
        try:
            simplified_result = [
                result.get(variable, variable).subs(
                    variables[-1], least_common_multiple
                )
                for variable in variables
            ]
        except InvalidOperation:
            raise handler.error("Can not balance {}".format(self))
        result = Reaction(
            [
                CHFormula(reactant.terms, Decimal(str(number)))
                for reactant, number in zip(self.reactants, simplified_result)
            ],
            self.to,
            [
                CHFormula(product.terms, Decimal(str(number)))
                for product, number in zip(
                self.products, simplified_result[len(self.reactants):]
            )
            ],
        )
        return result

    @cached_property
    def context(self) -> dict[tuple[FormulaUnit, FormulaUnit], Decimal]:
        return {
            (
                FormulaUnit([CHFormula(numerator.terms)]),
                FormulaUnit([CHFormula(denominator.terms)]),
            ): Decimal(denominator.number)
               / Decimal(numerator.number)
            for numerator, denominator in permutations(
                self.reactants + self.products, 2
            )
        }
