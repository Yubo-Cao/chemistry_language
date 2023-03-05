import itertools
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from functools import cached_property
from itertools import chain, permutations
from math import lcm
from typing import Any, Iterable

from pint import Context
from sympy import Integer, symbols, solve_linear_system, Matrix, fraction

from chemistry_lang.ch_handler import handler
from chemistry_lang.ch_periodic_table import periodic_table
from chemistry_lang.ch_token import Token
from chemistry_lang.objs.ch_ureg import ureg
from chemistry_lang.ch_error import CHError
from .ch_quantity import CHQuantity
from .ch_number import CHNumber


class EvalDecimal:
    """
    This class create a descriptor that evaluates a string to a Decimal
    """

    def __init__(self, name):
        self.name = name

    def __get__(self, instance, owner):
        if instance is None:
            return self
        prop = getattr(instance, self.name)
        if isinstance(prop, str):
            from chemistry_lang.ch_eval import evaluate

            prop = evaluate(prop)
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

    def __check_type(self, value) -> Decimal:
        try:
            if isinstance(value, CHNumber):
                value = value.value
            print(type(value))
            return Decimal(value)
        except (CHError, InvalidOperation) as e:
            raise handler.error("Invalid type for property %s" % self.name)


class Element:
    """
    This class represents an element in the chemistry language
    """

    symbol: str
    # infinite sig figs, so we use Decimal
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
    """
    This class represents a chemical formula in the chemistry language
    """

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
    """
    This class represents a partial chemical formula in the chemistry language
    """

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
    """
    This class represents a formula unit in the chemistry language
    """

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
    """
    This class represents a chemical reaction in the chemistry language
    """

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
            ): CHNumber(Decimal(denominator.number)
                        / Decimal(numerator.number), 999) # molar ratio has infinite significant digits
            for numerator, denominator in permutations(
                self.reactants + self.products, 2
            )
        }
