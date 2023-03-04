from chemistry_lang import evaluate, parse, tokenize
from chemistry_lang.objs.ch_number import CHNumber


def test_expression():
    assert evaluate("1 + 2") == 3
    assert evaluate("1 + 2 + 3") == 6
    assert str(evaluate("1.2 + 3.43")) == "4.6"
