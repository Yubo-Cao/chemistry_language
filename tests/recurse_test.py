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


def test_closure():
    reset()
    src = """
work counter()
    i = 0
    work impl()
        print(i)
        i += 1
    submit impl

i = counter()
i()
i()
    """
    evaluate(src)

    assert_stdout("0\n1\n")
