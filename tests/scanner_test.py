import sys

sys.path.append(r"C:\Users\Cao20\work\SchoolUtils\src\chemistry")
from ch_scanner import *
from pprint import pprint
from ch_handler import CHErrorHandler


def test(str):
    scanner = Scanner(str, CHErrorHandler())
    pprint(scanner.scan_tokens())


test(r"Ca(Cl_2H_{2}O)_{3}^{+3}")
