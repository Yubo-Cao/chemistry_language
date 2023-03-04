from .utils import initialize, reset, assert_stdout
from chemistry_lang import evaluate
from chemistry_lang.objs import CHNumber

initialize()


def test_loop():
    reset()
    src = """
redo i of 1...10
    redo j of 1...10
        print(i*j)
    """
    evaluate(src)

    assert_stdout('\n'.join(str(CHNumber(i) * CHNumber(j)) for i in range(1, 10) for j in range(1, 10)))
