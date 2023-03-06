import pytest

from chemistry_lang import CHError, handler
from chemistry_lang.objs import (
    CHQuantity,
    FormulaUnit,
    CHFormula,
    Element,
    CHNumber,
    ureg,
)

water = FormulaUnit((CHFormula((Element("H", 2), Element("O"))),))
oxygen = FormulaUnit((CHFormula((Element("O", 2),)),))
methane = FormulaUnit((CHFormula((Element("C"), Element("H", 4))),))


def test_add():
    a = CHQuantity(water, CHNumber(1), ureg.mol)
    b = CHQuantity(water, CHNumber(1), ureg.mol)
    c = a + b
    assert c.magnitude == CHNumber(2)
    assert c.unit == ureg.mol
    assert c.formula == water


def test_sub():
    a = CHQuantity(water, CHNumber(1), ureg.mol)
    b = CHQuantity(water, CHNumber(1), ureg.mol)
    c = a - b
    assert c.magnitude == CHNumber(0)
    assert c.unit == ureg.mol
    assert c.formula == water


def test_mul():
    a = CHQuantity(water, CHNumber(2), ureg.mol)
    b = CHQuantity(water, CHNumber(1), ureg.mol)
    c = a * b
    assert c.magnitude == CHNumber(2)
    assert c.unit == ureg.mol ** 2
    assert c.formula == water ** 2


def test_div():
    a = CHQuantity(water, CHNumber(2), ureg.mol)
    b = CHQuantity(water, CHNumber(1), ureg.mol)
    c = a / b
    assert c.magnitude == CHNumber(2)
    assert c.unit == ureg.dimensionless
    assert c.formula == FormulaUnit.formulaless


def test_error():
    a = CHQuantity(water, CHNumber(2), ureg.mol)
    b = CHQuantity(oxygen, CHNumber(1), ureg.mol)
    with pytest.raises(CHError):
        a + b
    handler.had_error = False


def test_molar_mass():
    a = CHQuantity(water, CHNumber(2), ureg.gram)
    b = CHQuantity(water, CHNumber(1), ureg.mol)
    c = a + b

    assert c.unit == ureg.gram
    assert c.magnitude == CHNumber("20.01300000000000034461322684", 1)
    assert c.formula == water
