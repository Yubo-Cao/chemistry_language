from functools import cached_property

from chemistry_lang.ch_handler import handler


class CHString:
    """
    CHString represents a string in the chemistry language.
    """

    def __init__(self, string: str, sub: bool):
        self.string = string
        self.need_substitute = sub

    def __repr__(self):
        return (
            "<CHString " + ("s'" if self.need_substitute else "'") + self.string + "'>"
        )

    def __str__(self):
        return self.string if not self.need_substitute else self.substituted()

    def substituted(self):
        from chemistry_lang.ch_eval import evaluate
        from chemistry_lang.ch_interpreter import interpreter

        if self.need_substitute:
            results = [
                interpreter.stringify(evaluate(self.string[sub[0] : sub[1]]))
                for sub in self.extract_subs
            ]
            ret = self.string
            offset = 0
            for sub, res in zip(self.extract_subs, results):
                ret = ret[: sub[0] + offset - 1] + res + ret[sub[1] + offset + 1 :]
                offset += len(res) - (sub[1] - sub[0] + 2)
            return ret.replace(r"\}", "}").replace(r"\{", "{")
        else:
            return self.string

    @cached_property
    def extract_subs(self) -> list[tuple[int, int]]:
        stack: list[tuple[str, int]] = []
        to_be_substituted: list[tuple[int, int]] = []
        for idx, char in enumerate(self.string):
            match char:
                case "{":
                    if idx == 0 or idx > 0 and self.string[idx - 1] != "\\":
                        stack.append((char, idx))
                case "}":
                    if idx == 0 or idx > 0 and self.string[idx - 1] != "\\":
                        if (res := stack.pop())[0] != "{":
                            handler.error("Unmatched braces")
                        to_be_substituted.append((res[1] + 1, idx))
                case _:
                    pass
        return to_be_substituted
