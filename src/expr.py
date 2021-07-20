from dataclasses import dataclass
from enum import Enum
from typing import List
from .value import Value

@dataclass
class Expr:
  """An expression in the abstract syntax tree."""
  line: int

BinaryOp = Enum("BinaryOp", " ".join([
  "ADD", "SUBTRACT", "MULTIPLY", "DIVIDE", "IDIVIDE", "MODULUS", "POWER",
  "EQUAL", "NOT_EQUAL", "LESS", "LESS_EQUAL", "GREATER", "GREATER_EQUAL",
  "AND", "OR", "DOMAIN", "PIECE"
]))

@dataclass
class Binary(Expr):
  """A binary operation on two expressions."""
  left: Expr
  operator: BinaryOp
  right: Expr

UnaryOp = Enum("UnaryOp", " ".join([
  "NEGATE", "NOT"
]))

@dataclass
class Unary(Expr):
  """A unary operation on an expr."""
  operator: UnaryOp
  expr: Expr

@dataclass
class Variable(Expr):
  """A named variable."""
  name: str

@dataclass
class Literal(Expr):
  """A literal value."""
  value: Value

@dataclass
class Call(Expr):
  """A call to a function."""
  callee: Expr
  arguments: List[Expr]
