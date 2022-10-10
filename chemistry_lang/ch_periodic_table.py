import json
from decimal import Decimal

from ch_base import shared_lazy_loading
from ch_handler import handler


class PeriodicTable:
    def get(self, symbol: str, key: str) -> Decimal:
        try:
            return Decimal(self.periodic_table[symbol][key])
        except KeyError:
            msg = f"Element '{symbol}' has no '{key}'"
            raise handler.error(msg)

    @shared_lazy_loading
    def periodic_table(self) -> dict:
        try:
            with open("periodic_table.json") as f:
                return json.load(f)
        except IOError as e:
            raise handler.error("Failed to read 'atomic_mass'.json") from e


periodic_table = PeriodicTable()
