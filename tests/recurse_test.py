from .utils import initialize, reset, assert_stdout
from chemistry_lang import evaluate

initialize()


def test_recursive():
    reset()
    src = """
work sum(n)
    exam n == 0
        submit 0
    fail
        submit sum(n-1) + n
print(sum(5))
    """
    evaluate(src)

    assert_stdout("15")
