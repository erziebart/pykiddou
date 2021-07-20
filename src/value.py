from abc import ABC, abstractmethod
from dataclasses import dataclass

class Value(ABC):
  """A value in the kiddou language."""
  @abstractmethod
  def type_name(self) -> str:
    return self.__class__.__name__

  @abstractmethod
  def stringify(self) -> str:
    return str(self)

class Undef(Value):
  """A value representing undefined."""
  def type_name(self) -> str:
    return super().type_name()

  def stringify(self) -> str:
    return "undef"

@dataclass
class Bool(Value):
  """A value representing a boolean."""
  val: bool

  def type_name(self) -> str:
    return super().type_name()

  def stringify(self) -> str:
    return "true" if self.val else "false"

@dataclass
class Int(Value):
  """A value representing an integer."""
  val: int

  def type_name(self) -> str:
    return super().type_name()

  def stringify(self) -> str:
    return str(self.val)

@dataclass
class Float(Value):
  """A value representing a floating-point number."""
  val: float

  def type_name(self) -> str:
    return super().type_name()

  def stringify(self) -> str:
    return str(self.val)

@dataclass
class String(Value):
  """A value representing a string."""
  val: str

  def type_name(self) -> str:
    return super().type_name()

  def stringify(self) -> str:
    return self.val
