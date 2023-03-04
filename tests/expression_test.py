from chemistry_lang import evaluate
from chemistry_lang.objs.ch_number import CHNumber


def test_expression():
    assert evaluate("1 + 2") == CHNumber("3")
