from .utils import initialize, reset, assert_stdout
from chemistry_lang import evaluate

initialize()


def test_recursive_sum():
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


def test_recursive_count():
    reset()
    src = """
work `count`(n)
    ps: This function count from n to 1
    exam n != 1
        `count`(n - 1)
    print(n)

`count`(10)
    """
    evaluate(src)

    expected = "1\n2\n3\n4\n5\n6\n7\n8\n9\n1e+1\n"
    assert_stdout(expected)


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
