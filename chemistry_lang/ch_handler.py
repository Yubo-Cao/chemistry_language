import sys
from logging import DEBUG, FileHandler, getLogger, StreamHandler
from typing import Optional

from colorama import Fore

from chemistry_lang.ch_error import CHError
from chemistry_lang.ch_token import Token


class ErrorStream:
    def write(self, msg: str) -> None:
        sys.stderr.write(Fore.RED + msg + Fore.RESET)

logger = getLogger("Chemistry Helper")
logger.addHandler(FileHandler("chem.log"))
logger.addHandler(StreamHandler(ErrorStream()))
logger.setLevel(DEBUG)

class CHErrorHandler:
    had_error = False

    def __init__(self):
        self.had_error = False

    def error(self, msg: str, token: Optional[Token | int] = None):
        """Report an error"""
        
        match token:
            case Token():
                msg = f'{token.line}: {msg}'
            case int():
                msg = f'{token}: {msg}'
        logger.error(msg)
        self.had_error = True
        return CHError(msg)


handler = CHErrorHandler()
