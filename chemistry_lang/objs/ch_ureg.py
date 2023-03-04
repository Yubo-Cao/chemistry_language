import pint
from pint import UnitRegistry

ureg = UnitRegistry()
ureg.define("atom = 6.02e23 * mole")
pint.set_application_registry(ureg)
