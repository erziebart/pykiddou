from dataclasses import dataclass
from typing import List, Optional, AbstractSet
from .expr import Expr
from .stmt import Stmt

@dataclass
class Constructor(Expr):
  """A lambda constructor for a constructed type."""
  is_eager: bool

@dataclass
class Block(Constructor):
  """A block of executable statements in a closure.""" 
  stmts: List[Stmt]
  expr: Optional[Expr]

  # populated later during semantic check
  dependent_names: Optional[AbstractSet[str]] = None

@dataclass
class Sequence(Constructor):
  """An ordered list of elements."""
  elements: List[Expr]
