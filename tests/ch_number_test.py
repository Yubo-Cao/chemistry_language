from decimal import Decimal

from chemistry_lang.objs.ch_number import SignificantDigits


def test_create():
    a = SignificantDigits("1.2345")
    assert a.value == Decimal("1.2345")
    assert a.sig_fig == 5
    b = SignificantDigits(1.2345)
    assert b.value == Decimal("1.2345")
    assert b.sig_fig == 5
    c = SignificantDigits(a)
    assert c.value == Decimal("1.2345")
    assert c.sig_fig == 5
    d = SignificantDigits("1e3")
    assert d.value == Decimal("1000")
    assert d.sig_fig == 1


def test_str():
    c = SignificantDigits(1.2345, 3)
    assert c.value == Decimal("1.2345")
    assert c.sig_fig == 3
    assert str(c) == "1.23"


def test_utils():
    assert SignificantDigits._get_decimal_places(1.2456) == 4
    assert SignificantDigits._get_decimal_places(124) == 0
    assert SignificantDigits._parse_significant_digits("2.200") == 4
    assert SignificantDigits._parse_significant_digits("22.20") == 4
    assert SignificantDigits._parse_significant_digits("22.0") == 3


def test_add():
    a = SignificantDigits("1.2434")
    b = SignificantDigits("1.2")
    r = a + b
    assert r.value == Decimal("2.4434")
    assert r.sig_fig == 2
    assert str(r) == "2.4"

    a = SignificantDigits("1.2")
    b = SignificantDigits("1.3")
    r = a + b
    assert r.value == Decimal("2.5")
    assert r.sig_fig == 2
    assert str(r) == "2.5"


def test_sub():
    a = SignificantDigits("1.2434")
    b = SignificantDigits("1.2")
    r = a - b

    assert r.value == Decimal("0.0434")
    assert r.sig_fig == 0
    assert str(r) == "NA"  # it's useless

    a = SignificantDigits("23.2234")
    b = SignificantDigits("1.2")
    r = a - b
    assert r.value == Decimal("22.0234")
    assert r.sig_fig == 3
    assert str(r) == "22.0"


def test_mul():
    a = SignificantDigits("1.2434")
    b = SignificantDigits("1.2")
    r = a * b

    assert r.value == Decimal("1.49208")
    assert r.sig_fig == 2
    assert str(r) == "1.5"
