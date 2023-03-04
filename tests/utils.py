from chemistry_lang import interpreter
from chemistry_lang.objs import NativeWork

stdout = ""


def initialize():
    def _fake_print(x):
        global stdout
        stdout += interpreter.stringify(x)
        stdout += "\n"

    interpreter.global_env = interpreter.global_env.assign("print", NativeWork(_fake_print, 1))
    interpreter.env = interpreter.global_env

def reset():
    global stdout
    stdout = ""


def assert_stdout(expected):
    print(stdout)
    assert stdout.strip() == expected.strip()
