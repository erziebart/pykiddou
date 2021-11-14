from abc import ABC, abstractmethod
from typing import List
from .exception import TypeException, IndexOutOfBoundsException
from .object import Object
from .value import Value, Undef, Int

class Container(ABC):
  """A container whose elements can be accessed using '[...]'."""
  @abstractmethod
  def get(self, index: Value) -> Value:
    pass

  @abstractmethod
  def set(self, index: Value, value: Value):
    pass


class KiddouList(Container, Value):
  """An ordered list of values."""
  def __init__(self, ls: List[Value]):
    self.ls = ls

  def type_name(self) -> str:
    return "List"

  def stringify(self) -> str:
    return f"[{', '.join([v.stringify() for v in self.ls])}]"

  def get(self, index: Value) -> Value:
    if not isinstance(index, Int):
      raise TypeException(f"List index should be Int, was {index.type_name()}")

    idx = index.val
    return self.ls[idx] if max(~idx, idx) < len(self.ls) else Undef()

  def set(self, index: Value, value: Value):
    if not isinstance(index, Int):
      raise TypeException(f"List index should be Int, was {index.type_name()}")

    idx = index.val
    if max(~idx, idx) < len(self.ls):
      self.ls[idx] = value
    else:
      raise IndexOutOfBoundsException(f"{max(~idx, idx)}>={len(self.ls)}")
