from chemistry_lang import evaluate
from .utils import initialize, reset, assert_stdout

initialize()


def condition_test():
    reset()
    src = """
gpa = 2.5
exam gpa > 3.5 
    print("A+") 
makeup gpa > 3.0 
    print("A") 
fail 
    print("F")
    """
    evaluate(src)

    assert_stdout("F\n")
