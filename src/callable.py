from abc import abstractmethod
from dataclasses import dataclass
from typing import Optional, Callable as Cbl, Collection
from .environment import Environment
from .exception import NameException, AttributeException
from .value import Value


class Callable:
  """Something that can be called using '(...)'."""
  @abstractmethod
  def call(self, args: Collection[Value], env: Environment) -> Value:
    pass
    

class Object:
  """Something which contains attributes, accessed using '.'."""
  @abstractmethod
  def get_attr(self, name: str) -> Value:
    pass

  @abstractmethod
  def set_attr(self, name: str, value: Value):
    pass


class Function(Value, Callable):
  """A value that can be called as a function."""
  def __init__(
    self, 
    func: Cbl[[Collection[Value], Environment], Value], 
    name: Optional[str]
  ):
    self.func = func
    self.name = name

  def type_name(self) -> str:
    return "Func"

  def stringify(self):
    return f"{{Func: {self.name}}}" if self.name else "{Func}"

  def call(self, args: Collection[Value], env: Environment) -> Value:
    return self.func(args, env)


@dataclass
class LibraryFunction(Function):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)


@dataclass
class KiddouBlock(Function, Object):
  def __init__(
    self, 
    func: Cbl[[Collection[Value], Environment], Value], 
    env: Environment,
    *args, 
    **kwargs
  ):
    self.env = env

    def wrapped_func(args: Collection[Value], env: Environment) -> Value:
      try:
        new_env = self.env.copy_retain(set())
        return func(args, new_env)
      except Exception as e:
        raise e
      finally:
        self.env = new_env

    super().__init__(wrapped_func, *args, **kwargs)

  def get_attr(self, name: str) -> Value:
    try:
      return self.env.get_local(name)
    except NameException as e:
      raise AttributeException(f"undefined attribute: {name}")

  def set_attr(self, name: str, value: Value):
    self.env.bind(name, value)
