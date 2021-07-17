from dataclasses import dataclass

class Value:
  """A value in the kiddou language."""
  pass

class Undef(Value):
  """A value representing undefined."""
  pass

@dataclass
class Bool(Value):
  """A value representing a boolean."""
  val: bool

@dataclass
class Int(Value):
  """A value representing an integer."""
  val: int

@dataclass
class Float(Value):
  """A value representing a floating-point number."""
  val: float

@dataclass
class String(Value):
  """A value representing a string."""
  val: str
