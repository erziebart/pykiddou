from dataclasses import dataclass
from typing import Set
from .exception import NameException, ImmutableException
from .value import Value

@dataclass
class Reference:
  val: Value
  mutable: bool = False


class Environment:
  """An environment for variables in a Kiddou program."""

  def __init__(self):
    self.env = dict()


  def keys(self) -> Set[str]:
    return self.env.keys()


  def bind(self, name: str, value: Value, mutable: bool = False):
    """Bind the given name to given value in this environment."""
    self.env[name] = Reference(val=value, mutable=mutable)


  def overwrite(self, name: str, value: Value):
    """
    Overwrite the given name to the given value in this environment.

    This produces an error if the name is unset or the current value is immutable. 
    """
    if name not in self.env:
      raise NameException(f"undefined variable: {name}.")

    cur_value = self.env.get(name)
    if not cur_value.mutable:
      raise ImmutableException(f"immutable variable: {name}.")

    cur_value.val = value


  def get(self, name: str) -> Value:
    """Get the current value for the given name in this environment."""
    ref = self.env.get(name)
    if ref is None:
      raise NameException(f"undefined variable: {name}.")
    return ref.val
