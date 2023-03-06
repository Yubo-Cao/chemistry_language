import pint
from pint import UnitRegistry

ureg = UnitRegistry()
ureg.define("atom = mole / 6.0221408e+23")
pint.set_application_registry(ureg)
