from dataclasses import dataclass
from typing import Optional
from .expr import Expr

@dataclass
class Stmt:
  """A statement in the abstract syntax tree."""
  line_start: int
  line_end: int

@dataclass
class Con(Stmt):
  """A construct statement using the 'con' keyword."""
  name: str
  expr: Expr

@dataclass
class Run(Stmt):
  """A run statement using the 'run' keyword."""
  receiver: Optional[Expr]
  expr: Expr
  reassign: bool
