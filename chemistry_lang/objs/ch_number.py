import re
from decimal import Decimal
from typing import Any, ForwardRef

from pint import Quantity

from chemistry_lang.ch_handler import handler

SupportedNumber = int | float | Decimal | Quantity | ForwardRef("SignificantDigits")


class SignificantDigits:
    def __init__(self, value: Any, sig_fig: int = -1):
        if isinstance(value, str):
            self.value = Decimal(value)
        else:
            self.value: Decimal = Decimal(self._extract_value(value))
        self.sig_fig = (
            sig_fig if sig_fig != -1 else self._parse_significant_digits(value)
        )

    def __str__(self):
        if self.sig_fig == 0:
            return "NA"
        return f"{self.value:.{self.sig_fig}g}"

    def __repr__(self):
        return f"SignificantDigits({self.value}, {self.sig_fig})"

    def __add__(self, other: SupportedNumber):
        precision = min(
            self._get_decimal_places(self.value), self._get_decimal_places(other)
        )
        result = self.value + self._extract_value(other)
        return SignificantDigits(
            result, self._parse_significant_digits(f"{result:.0{precision}f}")
        )

    def __radd__(self, other: SupportedNumber):
        return self.__add__(other)

    def __sub__(self, other: SupportedNumber):
        precision = min(
            self._get_decimal_places(self.value), self._get_decimal_places(other)
        )
        result = self.value - self._extract_value(other)
        return SignificantDigits(
            result, self._parse_significant_digits(f"{result:.0{precision}f}")
        )

    def __rsub__(self, other: SupportedNumber):
        precision = min(
            self._get_decimal_places(self.value), self._get_decimal_places(other)
        )
        result = self._extract_value(other) - self.value
        return SignificantDigits(
            result, self._parse_significant_digits(f"{result:.0{precision}f}")
        )

    def __mul__(self, other: SupportedNumber):
        precision = min(
            self._get_significant_digits(self.value),
            self._get_significant_digits(other),
        )
        result = self.value * self._extract_value(other)
        return SignificantDigits(result, precision)

    def __rmul__(self, other: SupportedNumber):
        return self.__mul__(other)

    def __truediv__(self, other):
        precision = min(
            self._get_significant_digits(self.value),
            self._get_significant_digits(other),
        )
        result = self.value / self._extract_value(other)
        return SignificantDigits(result, precision)

    def __rtruediv__(self, other):
        precision = min(
            self._get_significant_digits(self.value),
            self._get_significant_digits(other),
        )
        result = self._extract_value(other) / self.value
        return SignificantDigits(result, precision)

    def __eq__(self, other):
        return self.value == self._extract_value(
            other
        ) and self.sig_fig == self._get_significant_digits(other)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        return self.value < self._extract_value(other)

    def __le__(self, other):
        return self.value <= self._extract_value(other)

    def __gt__(self, other):
        return self.value > self._extract_value(other)

    def __ge__(self, other):
        return self.value >= self._extract_value(other)

    def __hash__(self):
        return hash((self.value, self.sig_fig))

    @staticmethod
    def _get_decimal_places(value: SupportedNumber) -> int:
        val = SignificantDigits._extract_value(value)
        return -val.as_tuple().exponent

    @staticmethod
    def _get_digit(value: SupportedNumber) -> int:
        val = SignificantDigits._extract_value(value)
        return max(len(val.as_tuple().digits) + val.as_tuple().exponent, 0)

    @staticmethod
    def _get_significant_digits(value: SupportedNumber) -> int:
        if isinstance(value, SignificantDigits):
            return value.sig_fig
        return SignificantDigits._parse_significant_digits(
            SignificantDigits._extract_value(value)
        )

    @staticmethod
    def _parse_significant_digits(s: str | SupportedNumber) -> int:
        s = str(s)
        s = s.replace("_", "")  # remove underscores
        if "e" in s or "E" in s:
            significant = re.split(r"[*×]?[eE]", s)
            return len(significant[0].replace(".", ""))

        if "." not in s:
            return len(s.rstrip("0"))

        int_part, decimal_part = s.split(".")

        if int_part == "0":
            return len(decimal_part.lstrip("0"))
        else:
            return len(int_part.lstrip("0")) + len(decimal_part)

    @staticmethod
    def _extract_value(other: SupportedNumber) -> Decimal:
        match other:
            case SignificantDigits():
                other_value = other.value
            case int() | float():
                other_value = Decimal(str(other))
            case Decimal():
                other_value = other
            case Quantity():
                other_value = other.magnitude
            case _:
                raise handler.error(f"Can't extract value from {other}")
        return other_value


CHNumber = SignificantDigits
