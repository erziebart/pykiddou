from abc import abstractmethod
from dataclasses import dataclass
from typing import Optional, Callable, Collection
from .value import Value


class Function(Value):
  """A value that can be called as a function."""
  def type_name(self) -> str:
    return "Func"

  def stringify(self):
    return "{Func}"

  @abstractmethod
  def call(self, args: Collection[Value]) -> Value:
    pass


@dataclass
class LibraryFunction(Function):
  func: Callable[[Collection[Value]], Value]
  name: Optional[str]

  def type_name(self) -> str:
    return super().type_name()

  def stringify(self):
    return f"{{Func: {self.name}}}" if self.name else super().stringify()

  def call(self, args: Collection[Value]) -> Value:
    return self.func(args)
