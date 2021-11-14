from abc import ABC, abstractmethod
from typing import Optional
from .environment import Environment
from .exception import NameException, AttributeException
from .value import Value


class Object(ABC):
  """Something which contains attributes, accessed using '.'."""
  @abstractmethod
  def get_attr(self, name: str) -> Value:
    pass

  @abstractmethod
  def set_attr(self, name: str, value: Value):
    pass


class KiddouModule(Object, Value):
  """A module inside a kiddou program, usually representing an input file."""
  def __init__(self, env: Environment, name: Optional[str]):
    self.env = env
    self.name = name

  def get_attr(self, name: str) -> Value:
    try:
      return self.env.get_local(name)
    except NameException as e:
      raise AttributeException(f"undefined attribute: {name}")

  def set_attr(self, name: str, value: Value):
    try:
      self.env.overwrite_local(name, value)
    except NameException as e:
      raise AttributeException(f"undefined attribute: {name}")

  def type_name(self) -> str:
    return "Module"

  def stringify(self):
    return f"{{Module: {self.name}}}" if self.name else "{Module}"
    