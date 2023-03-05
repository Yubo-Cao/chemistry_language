from chemistry_lang import evaluate
from chemistry_lang.objs import CHNumber
from .utils import initialize, reset, assert_stdout

initialize()


def test_loop():
    reset()
    src = """
redo i of 1...5
    redo j of 1...5
        print(i * j)
    """
    evaluate(src)

    expected = ""
    for i in range(1, 5):
        for j in range(1, 5):
            expected += str(CHNumber(i) * CHNumber(j)) + "\n"
    assert_stdout(expected)
