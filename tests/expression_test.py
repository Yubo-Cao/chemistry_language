from chemistry_lang import evaluate
from .utils import initialize, reset, assert_stdout

initialize()


def test_add():
    assert evaluate("1 + 2") == 3
    assert evaluate("1 + 2 + 3") == 6
    assert str(evaluate("1.2 + 3.43")) == "4.6"


def test_format_string():
    assert (
        evaluate(
            """
n = 10
s'You have {n} apples'
    """
        )
        == "You have 1×10¹ apples"
    )
