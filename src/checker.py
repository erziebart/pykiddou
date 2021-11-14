from dataclasses import dataclass
from typing import List, Set, AbstractSet, Optional
from .constructor import Block, Sequence
from .environment import Environment
from .error import ErrorHandler, KiddouError
from .expr import Expr, Binary, Unary, Literal, Variable, Call, Index, Attribute
from .stmt import Stmt, Con, Run


@dataclass
class VisibleNames:
  parent: Optional["VisibleNames"]
  names: AbstractSet[str]


  def __contains__(self, name):
    return name in self.names or (self.parent is not None and name in self.parent)


  def add(self, name):
    self.names.add(name)


@dataclass
class StatementNames:
  names_used: AbstractSet[str]
  name_declared: Optional[str]


class Checker:
  """A semantic checker for a statement."""
  def __init__(self, error_handler: ErrorHandler):
    self.error_handler = error_handler

    self.stmt_handlers = {
      Con: self._check_con,
      Run: self._check_run,
    }
    self.expr_handlers = {
      Binary: self._check_binary,
      Unary: self._check_unary,
      Literal: self._check_literal,
      Variable: self._check_variable,
      Call: self._check_call,
      Index: self._check_index,
      Attribute: self._check_attribute,
      Block: self._check_block,
      Sequence: self._check_sequence,
    }

  
  def check(self, stmts: List[Stmt], environment: Environment):
    """Check some Kiddou statements. This also populates semantic information for each statement."""
    visible_names = VisibleNames(
      parent = None,
      names = { name for name in environment.keys() },
    )

    for stmt in stmts:
      statement_names = self._check_stmt(stmt, visible_names)
      if statement_names.name_declared is not None:
        visible_names.add(statement_names.name_declared)


  #################################################################################################
  ### Statements                                                                                ###
  #################################################################################################

  """
  Functions which check statements. They each take visible_names as an argument
  and return a set of strings which contains all the names from visible_names which 
  are referenced inside the statement. They might also return a declared name, if a new
  name was defined by the statement. 
  """

  def _check_stmt(self, stmt: Stmt, visible_names: VisibleNames) -> StatementNames:
    return self.stmt_handlers[stmt.__class__](stmt, visible_names)


  def _check_con(self, con: Con, visible_names: VisibleNames) -> StatementNames:
    names_used = self._check_expr(con.expr, visible_names)
    return StatementNames(names_used = names_used, name_declared = con.name)


  def _check_run(self, run: Run, visible_names: VisibleNames) -> StatementNames:
    names_used = self._check_expr(run.expr, visible_names)

    receiver = run.receiver
    if receiver is None:
      return StatementNames(names_used = names_used, name_declared = None)

    rcv_type = type(receiver)
    name_declared = None

    if rcv_type is Variable:
      name_declared = receiver.name
      if run.reassign:
        names_used.add(name_declared)
        if name_declared not in visible_names:
          self._report_undefined(name_declared, receiver.line)

    if rcv_type is Attribute:
      if not run.reassign:
        self._report_attribute_creation(receiver.line)
      names_used.update(self._check_expr(receiver, visible_names))

    if rcv_type is Index:
      names_used.update(self._check_expr(receiver, visible_names))

    return StatementNames(names_used = names_used, name_declared = name_declared)


  #################################################################################################
  ### Expressions                                                                               ###
  #################################################################################################

  """
  Functions which check expressions. They each take visible_names as an argument
  and return a set of strings which contains all the names from visible_names which 
  are referenced inside the expression, or inside any subexpressions.
  """

  def _check_expr(self, expr: Expr, visible_names: VisibleNames) -> Set[str]:
    return self.expr_handlers[expr.__class__](expr, visible_names)


  def _check_binary(self, binary: Binary, visible_names: VisibleNames) -> Set[str]:
    left = self._check_expr(binary.left, visible_names)
    right = self._check_expr(binary.right, visible_names)
    return left.union(right)


  def _check_unary(self, unary: Unary, visible_names: VisibleNames) -> Set[str]:
    return self._check_expr(unary.expr, visible_names)


  def _check_literal(self, literal: Literal, visible_names: VisibleNames) -> Set[str]:
    return set()


  def _check_variable(self, variable: Variable, visible_names: VisibleNames) -> Set[str]:
    if variable.name not in visible_names:
      self._report_undefined(variable.name, variable.line)
    return set([variable.name]) 


  def _check_call(self, call: Call, visible_names: VisibleNames) -> Set[str]:
    names_used = self._check_expr(call.callee, visible_names)
    for arg in call.arguments:
      names_used.update(self._check_expr(arg, visible_names))
    return names_used


  def _check_index(self, index: Index, visible_names: VisibleNames) -> Set[str]:
    names_used = self._check_expr(index.container, visible_names)
    names_used.update(self._check_expr(index.index, visible_names))
    return names_used


  def _check_attribute(self, attribute: Attribute, visible_names: VisibleNames) -> Set[str]:
    # note: don't check the attribute name exists, because it's only added at runtime
    return self._check_expr(attribute.obj, visible_names)


  def _check_block(self, block: Block, visible_names: VisibleNames) -> Set[str]:
    if block.is_eager:
      self._report_unsupported_construct("[<block>]", block.line)

    inner_names = VisibleNames(
      parent = visible_names,
      names = set(["this"]),
    )

    names_used = set()

    for stmt in block.stmts:
      statement_names = self._check_stmt(stmt, inner_names)
      names_used.update({name for name in statement_names.names_used if name not in inner_names.names})
      if statement_names.name_declared is not None:
        inner_names.add(statement_names.name_declared)

    if block.expr is not None:
      names = self._check_expr(block.expr, inner_names)
      names_used.update({name for name in names if name not in inner_names.names})

    # populate set of names in the same scope that this block depends on
    block.dependent_names = visible_names.names.intersection(names_used)
    
    return names_used


  def _check_sequence(self, sequence: Sequence, visible_names: VisibleNames) -> Set[str]:
    if not sequence.is_eager:
      self._report_unsupported_construct("{<seq>}", sequence.line)

    names_used = set()

    for expr in sequence.elements:
      names_used.update(self._check_expr(expr, visible_names))

    return names_used


  def _report_undefined(self, name: str, line: int):
    self.error_handler.error(
      KiddouError(
        message = f"undefined variable: {name}",
        line = line,
        col = None,
        text = None
      )
    )


  def _report_unsupported_construct(self, construct: str, line: int):
    self.error_handler.error(
      KiddouError(
        message = f"constructor: {construct} is not supported",
        line = line,
        col = None,
        text = None
      )
    )

  def _report_attribute_creation(self, line: int):
    self.error_handler.error(
      KiddouError(
        message = "attribute creation not allowed, use reassignment (:=) instead",
        line = line,
        col = None,
        text = None
      )
    )
