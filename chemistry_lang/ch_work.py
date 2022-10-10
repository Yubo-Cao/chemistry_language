from ch_ast import Work
from ch_env import Env


class SubmitError(Exception):
    """
    Raised when a submit statement is executed. It is just used to control
    flow, i.e., navigate between stack frames.
    """

    def __init__(self, res):
        self.res = res


class NativeWork:
    def __init__(self, callable, arity):
        self.callable = callable
        self._arity = arity

    @property
    def arity(self):
        return self._arity

    def __str__(self):
        return "<NativeWork: {}>".format(self.callable)

    def __call__(self, interpreter, *args):
        return self.callable(*args)


class CHWork:
    def __init__(self, closure, declaration: Work):
        self.closure = closure
        self.declaration = declaration

    @property
    def arity(self):
        return len(self.declaration.params)

    def __call__(self, interpreter, *args):
        env = Env(
            self.closure,
            {p: a for p, a in zip(self.declaration.params, args)},
        )
        with interpreter.scope(env):
            try:
                return interpreter.execute(self.declaration.body)
            except SubmitError as e:
                return e.res

    def __repr__(self):
        return "<CHWork: {}>".format(self.declaration.identifier)
