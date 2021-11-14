from dataclasses import dataclass
from typing import AbstractSet, Optional, Dict
from .exception import NameException, ImmutableException
from .value import Value

@dataclass
class Reference:
  val: Value
  mutable: bool = False


class Environment:
  """An environment for variables in a Kiddou program."""

  def __init__(self, env: Optional[Dict[str, Reference]] = None):
    self.env = env if env is not None else dict()
    self.locals = dict()


  def copy_retain(self, names: AbstractSet[str]):
    """
    Create a shallow copy of this Environment which retains the given bindings (names).

    Once the names have been retained once, they are permanent. So copies of the copy will
    still retain the given names, even if the names are not provided again as argmuments. 
    """
    env_copy = { k:v for (k,v) in self.locals.items() if k in names }
    env_copy.update(self.env)
    return Environment(env_copy)


  def keys(self) -> AbstractSet[str]:
    for key in self.env.keys():
      yield key
    for key in self.locals.keys():
      yield key


  def bind(self, name: str, value: Value, mutable: bool = False):
    """Bind the given name to given value in this environment."""
    self.locals[name] = Reference(val=value, mutable=mutable)


  def overwrite(self, name: str, value: Value):
    """
    Overwrite the given name to the given value in this environment.

    This produces an error if the name is unset or the current value is immutable. 
    """
    ref = self.locals.get(name)
    if ref is None:
      ref = self.env.get(name)

    if ref is None:
      raise NameException(f"undefined variable: {name}.")

    if not ref.mutable:
      raise ImmutableException(f"immutable variable: {name}.")

    ref.val = value


  def overwrite_local(self, name: str, value: Value):
    """
    Overwrite the given name to the given value, searching only the local environment.

    This produces an error if the name is not found or the current value is immutable. 
    """
    ref = self.locals.get(name)

    if ref is None:
      raise NameException(f"undefined variable: {name}.")

    if not ref.mutable:
      raise ImmutableException(f"immutable variable: {name}.")

    ref.val = value


  def get(self, name: str) -> Value:
    """Get the current value for the given name in this environment."""
    ref = self.locals.get(name)
    if ref is None:
      ref = self.env.get(name)
    if ref is None:
      raise NameException(f"undefined variable: {name}.")
    return ref.val


  def get_local(self, name: str) -> Value:
    """Get the current value for the given name, searching only the local environment."""
    ref = self.locals.get(name)
    if ref is None:
      raise NameException(f"undefined variable: {name}.")
    return ref.val
