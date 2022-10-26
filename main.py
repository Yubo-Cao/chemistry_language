import sys
from typing import Any

from chemistry_lang.ch_error import CHError
from chemistry_lang.ch_handler import handler
from chemistry_lang.ch_interpreter import interpreter
from chemistry_lang.ch_parser import parse
from chemistry_lang.ch_tokenizer import tokenize


def run(code: str):
    try:
        tokens = tokenize(code)
        if handler.had_error:
            sys.exit(1)
        ast = parse(tokens)
        if handler.had_error:
            sys.exit(1)
        interpreter.execute(ast)
    except CHError:
        sys.exit(-1)
    except KeyboardInterrupt:
        sys.exit(1)


class CH:
    def main(self) -> None:
        args = sys.argv[1:]
        if len(args) == 1:
            try:
                with open(args[0], "r") as f:
                    run(f.read().strip("\n"))
            except IOError:
                handler.error("Could not open file %s " % args[1])
        else:
            self.repl()

    @staticmethod
    def evaluate(code) -> Any:
        tokens = tokenize(code)
        if handler.had_error:
            handler.had_error = False
            return ""
        ast = parse(tokens)
        if handler.had_error:
            handler.had_error = False
            return ""
        return interpreter.evaluate(ast)

    @staticmethod
    def repl():
        print(
            """
Welcome to the Chemistry Language! 
Type in your code
    - Ctrl+Z + Enter to execute.
    - Enter, nothing will happen but a newline will be added.
    - Ctrl+C, the program will exit.
Complete syntax reference can be found at readme.md
              """
        )
        while True:
            try:
                code = []
                while True:
                    try:
                        code.append(input(">>> "))
                    except EOFError:
                        break
                try:
                    print(CH.evaluate("\n".join(code) + "\n"))
                except CHError:
                    handler.had_error = False
                    continue
            except KeyboardInterrupt:
                break


ch = CH()

if __name__ == "__main__":
    ch.main()
