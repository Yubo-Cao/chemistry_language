import sys
from typing import Any

from ch_base import shared_lazy_loading
from ch_error import CHError
from ch_handler import handler
from ch_interpreter import Interpreter
from ch_parser import Parser
from ch_scanner import Scanner


class CH:
    @shared_lazy_loading
    def interpreter(self) -> Interpreter:
        return Interpreter()

    def main(self):
        args = sys.argv[1:]
        if len(args) == 1:
            try:
                with open(args[0], "r") as f:
                    self.run(f.read().strip("\n"))
            except IOError:
                handler.error("Could not open file %s " % args[1])
        else:
            self.repl()

    def run(self, code):
        try:
            scanner = Scanner(code)
            tokens = scanner.scan_tokens()
            if handler.had_error:
                sys.exit(1)
            parser = Parser(tokens)
            ast = parser.parse()
            if handler.had_error:
                sys.exit(1)
            self.interpreter.execute(ast)
        except CHError:
            sys.exit(-1)
        except KeyboardInterrupt:
            sys.exit(1)

    def eval(self, code) -> Any:
        scanner = Scanner(code)
        tokens = scanner.scan_tokens()
        if handler.had_error:
            handler.had_error = False
            return ""
        parser = Parser(tokens)
        ast = parser.parse()
        if handler.had_error:
            handler.had_error = False
            return ""
        return self.interpreter.evaluate(ast)

    def repl(self):
        print("""
Welcome to the Chemistry Helper! 
Type in your code
    - Ctrl+Z + Enter to execute.
    - Enter, nothing will happen but a newline will be added.
    - Ctrl+C, the program will exit.
Complete syntax reference can be found at readme.md (but its totally gibberish with
EBNF notation) See demo.ch for an example.
              """)
        while True:
            try:
                code = []
                while True:
                    # This is some hack to get multi line input. You have to terminate
                    # it manually
                    try:
                        code.append(input(">>> "))
                    except EOFError:
                        break
                scanner = Scanner("\n".join(code) + "\n")
                tokens = scanner.scan_tokens()
                if handler.had_error:
                    handler.had_error = False
                    continue
                parser = Parser(tokens)
                ast = parser.parse()
                if handler.had_error:
                    handler.had_error = False
                    continue
                try:
                    print(self.interpreter.interpret(ast))
                except CHError:
                    handler.had_error = False
                    continue
            except KeyboardInterrupt:
                break


ch = CH()

if __name__ == "__main__":
    ch.main()
