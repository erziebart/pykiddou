import math
from typing import Collection
from .environment import Environment
from .value import Value, Undef, Float
from .callable import Function


def _print(args: Collection[Value], env: Environment) -> Value:
  strings = [val.stringify() for val in args]
  print(*strings)
  return Undef()


pervasives = {
  "inf": Float(math.inf),
  "nan": Float(math.nan),
  "print": Function(func=_print, name="print")
}
