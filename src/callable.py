from abc import ABC, abstractmethod
from typing import Optional, Callable as Cbl, Collection
from .environment import Environment
from .exception import NameException, AttributeException
from .object import KiddouModule
from .value import Value


class Callable(ABC):
  """Something that can be called using '(...)'."""
  @abstractmethod
  def call(self, args: Collection[Value], env: Environment) -> Value:
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


class KiddouBlock(Function, KiddouModule):
  """A block of code, which can be run, then treated as an object with attributes."""
  def __init__(
    self, 
    func: Cbl[[Collection[Value], Environment], Value], 
    name: Optional[str],
    env: Environment,
    *args, 
    **kwargs
  ):
    self.env = env
    env_name = name if name is not None else "this"

    def wrapped_func(args: Collection[Value], env: Environment) -> Value:
      try:
        new_env = self.env.copy_retain(set())
        new_env.bind(env_name, self)
        return func(args, new_env)
      except Exception as e:
        raise e
      finally:
        self.env = new_env

    super().__init__(wrapped_func, name, *args, **kwargs)

  def get_attr(self, name: str) -> Value:
    try:
      return self.env.get_local(name)
    except NameException as e:
      raise AttributeException(f"undefined attribute: {name}")

  def set_attr(self, name: str, value: Value):
    self.env.bind(name, value)
