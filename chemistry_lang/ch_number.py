from decimal import Decimal

from ch_handler import handler


class CHNumber:
    """
    This number following the significant figures rules, see this as reference:
    https://chem.libretexts.org/Bookshelves/Analytical_Chemistry/Supplemental_Modules_(Analytical_Chemistry)/Quantifying_Nature/Significant_Digits

    """

    @property
    def sig_figs(self):
        return self._sig_figs

    @property
    def decimal_digits(self):
        if self.value.as_tuple().exponent == 0:
            return 0
        else:
            _, digits, exp = self.value.as_tuple()
            return self.sig_figs - (len(digits) + exp)

    @decimal_digits.setter
    def decimal_digits(self, value):
        _, digits, exp = self.value.as_tuple()
        self._sig_figs = (len(digits) + exp) + value

    def __init__(self, value: str | Decimal | int | float, sig_figs: int | float = -1):
        if isinstance(value, Decimal) and sig_figs != -1:
            self.value = value
            if sig_figs != -1:
                self._sig_figs = sig_figs
            else:
                self._sig_figs = self.get_sig_figs(value)
        elif isinstance(value, str):
            self.value = Decimal(value)
            self._sig_figs = (
                self.get_sig_figs(self.value) if sig_figs == -1 else sig_figs
            )
        elif isinstance(value, int) or isinstance(value, float):
            self.value = Decimal(value)
            self._sig_figs = self.guess_sig_figs(value) if sig_figs == -1 else sig_figs
        else:
            raise ValueError("Can't create CHNumber from " + str(type(value)))

    def get_sig_figs(self, value: Decimal):
        if value.as_tuple().exponent >= 0:
            # In such case, all trailing zeros are not significant
            return len(
                list(dropwhile(lambda c: c == 0, reversed(value.as_tuple().digits)))
            )
        else:
            return len(value.as_tuple().digits)

    def __repr__(self):
        return self.__format__(None)

    def __format__(self, _format_spec: str) -> str:
        rounded = self.value.quantize(Decimal("1") / Decimal(10) ** self.decimal_digits)
        result = str(rounded)
        if "." in result or result[-1] != "0":
            return result
        else:
            exp = self.value.adjusted()
            rounded = self.value / Decimal(10) ** exp
            base = f"{{:0.{self.decimal_digits}f}}".format(rounded)
            match _format_spec:
                case "L":
                    return base + rf" \times 10^{{{exp}}}"
                case _:  # "D"
                    return base + " * 10 ** " + str(exp)

    def guess_decimal_digits(self, val):
        try:
            val = Decimal(val)
            return max(-val.as_tuple().exponent, 0)
        except InvalidOperation:
            try:
                return len(str(val).split(".")[1])
            except IndexError:
                return 0

    def guess_sig_figs(self, val):
        try:
            val = Decimal(val)
            return self.get_sig_figs(val)
        except InvalidOperation:
            val = str(val)
            if "." in val:
                return len(list(dropwhile(lambda c: c == "0" or c == ".", val)))
            else:
                return len(val.strip("0"))

    def __add__(self, other):
        if isinstance(other, CHNumber):
            num = CHNumber(self.value + other.value, 0)
            num.decimal_digits = min(self.decimal_digits, other.decimal_digits)
            return num
        elif (
                isinstance(other, int)
                or isinstance(other, Decimal)
                or isinstance(other, float)
        ):
            num = CHNumber(self.value + other, 0)
            num.decimal_digits = min(
                self.decimal_digits, self.guess_decimal_digits(other)
            )
            return num
        else:
            raise handler.error("Can't add CHNumber to " + str(type(other)) + ".")

    def __radd__(self, other):
        return self.__add__(other)

    def __sub__(self, other):
        return self + (-other)

    def __rsub__(self, other):
        return -self + other

    def __mul__(self, other):
        if isinstance(other, CHNumber):
            num = CHNumber(self.value * other.value, min(self.sig_figs, other.sig_figs))
            return num
        elif (
                isinstance(other, int)
                or isinstance(other, Decimal)
                or isinstance(other, float)
        ):
            num = CHNumber(
                self.value * other, min(self.sig_figs, self.guess_sig_figs(other))
            )
            return num
        else:
            raise handler.error("Can only multiply CHNumber to CHNumber")

    def __rmul__(self, other):
        return self.__mul__(other)

    def __truediv__(self, other):
        if isinstance(other, CHNumber):
            num = CHNumber(self.value / other.value, min(self.sig_figs, other.sig_figs))
            return num
        elif (
                isinstance(other, int)
                or isinstance(other, Decimal)
                or isinstance(other, float)
        ):
            num = CHNumber(
                self.value / other, min(self.sig_figs, self.guess_decimal_digits(other))
            )
            return num
        else:
            raise handler.error("Can only divide CHNumber to CHNumber")

    def __rtruediv__(self, other):
        return (1 / self) * other

    def __abs__(self):
        return CHNumber(abs(self.value), self.sig_figs)

    def __eq__(self, other):
        if isinstance(other, CHNumber):
            return self.value == other.value
        return self.value == other

    def __hash__(self):
        return hash((self.value, self.sig_figs))

    def __neg__(self):
        return CHNumber(-self.value, self.sig_figs)

    def __pos__(self):
        return CHNumber(+self.value, self.sig_figs)

    def __bool__(self):
        return self.value != 0
