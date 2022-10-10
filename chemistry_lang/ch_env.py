from typing import Any, cast

from ch_handler import handler


class Env:
    """
    This class use dict to store local and global variables. It uses parent reference
    tree to keep track of lexical scope. This is immutable, so closure would feel
    happy about that.
    """

    def __init__(self, parent: "Env" = None, vars: dict = None):
        self.parent = parent
        self.vars: dict[str, Any] = {} if vars is None else vars

    def lookup(self, name: str) -> Any:
        try:
            return (
                self.vars[name]
                if name in self.vars
                else cast("Env", self.parent.lookup(name))  # type: ignore
            )
        except AttributeError:
            raise handler.error(f"Variable '{name}' not found")

    def assign(self, name: str, value: Any) -> "Env":
        """
        Assign a variable to the environment.
        We don't want to mutate the original environment, so we create a new one.
        Since declare and define are implicit,
            - we need to check if the variable is already defined in the outer scope, current scope
            etc. In such case, modify reference that child of such scope holds to the new scope
            - if the variable is not defined in the outer scope, create a new variable in the current scope
            by returning a new environment
        """

        child, parent = None, self
        while parent is not None:
            if name in parent.vars:
                if child is None:
                    # Self
                    copy = parent.vars.copy()
                    copy[name] = value
                    return Env(parent.parent, copy)
                else:
                    # Modify reference
                    copy = parent.vars.copy()
                    copy[name] = value
                    child.parent = Env(parent.parent, copy)
                return self
            child, parent = parent, cast(Env, parent.parent)
        # new variable
        copy = self.vars.copy()
        copy[name] = value
        return Env(self.parent, copy)
