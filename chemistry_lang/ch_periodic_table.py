import json
from decimal import Decimal
from functools import cached_property
from pathlib import Path

from chemistry_lang.ch_handler import handler


class PeriodicTable:
    def get(self, symbol: str, key: str) -> Decimal:
        try:
            return Decimal(self.periodic_table[symbol][key])
        except KeyError:
            msg = f"Element '{symbol}' has no '{key}'"
            raise handler.error(msg)

    @cached_property
    def periodic_table(self) -> dict:
        path = Path(__file__).parent / "periodic_table.json"
        try:
            with open(path) as f:
                return json.load(f)
        except IOError as e:
            raise handler.error(f"Failed to read {path}") from e


periodic_table = PeriodicTable()
