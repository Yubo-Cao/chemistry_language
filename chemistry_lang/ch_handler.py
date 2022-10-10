import sys
from logging import DEBUG, FileHandler, Logger, StreamHandler
from typing import Any

from colorama import Fore

from ch_error import CHError
from ch_token import Token


class ErrorStream:
    def write(self, msg: str) -> None:
        sys.stderr.write(Fore.RED + msg + Fore.RESET)


class CHErrorHandler:
    logger = Logger("Chemistry Helper")
    logger.addHandler(FileHandler("chem.log"))
    logger.addHandler(StreamHandler(ErrorStream()))
    logger.setLevel(DEBUG)
    had_error = False

    def __init__(self):
        self.had_error = False

    def error(self, msg: str, token: Any = None):
        if token is None:
            self.logger.error(msg)
            self.had_error = True
        elif isinstance(token, Token):
            self.logger.error(f"{token.line}: {msg}")
            self.had_error = True
        elif isinstance(token, int):
            # line number
            self.logger.error(f"{token}: {msg}")
            self.had_error = True
        return CHError(msg)


handler = CHErrorHandler()
