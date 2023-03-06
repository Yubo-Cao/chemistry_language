from .utils import initialize, reset, assert_stdout
from chemistry_lang import evaluate

initialize()


def test_define_work():
    reset()
    src = """
work test()
    exam pass
        "You passed the exam"
    fail
        "You failed the exam"

print(test())
    """
    evaluate(src)

    assert_stdout("You passed the exam\n")


def test_submit():
    reset()
    src = """
work test()
    redo x of 1...10
        exam x % 2 == 0
            print(x)
    submit na

print(test())
    """
    evaluate(src)

    expected = ""
    for i in range(1, 10):
        if i % 2 == 0:
            expected += str(i) + "\n"
    expected += "na\n"
    assert_stdout(expected)


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

    expected = "1\n2\n3\n4\n5\n6\n7\n8\n9\n1×10¹\n"
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


def test_hanoi():
    reset()
    src = """
work move(n, from, buf, to)
    exam n == 1
        print(s"Move {n} from {from} to {to}")
    fail
        move(n - 1, from, to, buf)
        move(1, from, buf, to)
        move(n - 1, buf, from, to)
move(3, 'a', 'b', 'c')
    """
    evaluate(src)

    expected = ""

    def hanoi(n, a, b, c):
        nonlocal expected

        if n == 1:
            expected += f"Move {n} from {a} to {c}"
            expected += "\n"
        else:
            hanoi(n - 1, a, c, b)
            hanoi(1, a, b, c)
            hanoi(n - 1, b, a, c)

    hanoi(3, "a", "b", "c")
    assert_stdout(expected)


def test_fib():
    reset()
    src = """
work fib(n)
    exam n <= 1
        submit 1
    fail
        res = fib(n-1) + fib(n-2)
        submit fib(n - 1) + fib(n - 2)

redo i of 1...10
    print(s'fib({i}) = {fib(i)}')
    """
    evaluate(src)

    expected = ""

    def fib(n):
        if n <= 1:
            return 1
        else:
            return fib(n - 1) + fib(n - 2)

    for i in range(1, 10):
        expected += f"fib({i}) = {fib(i)}\n"
    assert_stdout(expected)
