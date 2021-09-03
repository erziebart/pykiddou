from dataclasses import dataclass
from typing import List, Set, AbstractSet, Optional
from .environment import Environment
from .error import ErrorHandler, KiddouError
from .expr import Expr, Binary, Unary, Literal, Variable, Call
from .stmt import Stmt, Con, Run


@dataclass
class VisibleNames:
  parent: Optional["VisibleNames"]
  names: AbstractSet[str]


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
    }

  
  def check(self, stmts: List[Stmt], environment: Environment):
    """Check some Kiddou statements. This also populates semantic information for each statement."""
    visible_names = VisibleNames(
      parent = None,
      names = { name for name in environment.keys() },
    )

    for stmt in stmts:
      self._check_stmt(stmt, visible_names)


  #################################################################################################
  ### Statements                                                                                ###
  #################################################################################################

  def _check_stmt(self, stmt: Stmt, visible_names: VisibleNames) -> Set[str]:
    return self.stmt_handlers[stmt.__class__](stmt, visible_names)


  def _check_con(self, con: Con, visible_names: VisibleNames) -> Set[str]:
    names_used = self._check_expr(con.expr, visible_names)
    visible_names.names.add(con.name)
    return names_used


  def _check_run(self, run: Run, visible_names: VisibleNames) -> Set[str]:
    names_used = self._check_expr(run.expr, visible_names)
    
    if run.name is not None:
      if run.reassign:
        if run.name not in visible_names.names:
          self._report_undefined(run.name, run.line_start)
        names_used.add(run.name)
      visible_names.names.add(run.name)
    return names_used


  #################################################################################################
  ### Expressions                                                                               ###
  #################################################################################################

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
    if variable.name not in visible_names.names:
      self._report_undefined(variable.name, variable.line)
    return set(variable.name) 


  def _check_call(self, call: Call, visible_names: VisibleNames) -> Set[str]:
    result = set()
    result.update(self._check_expr(call.callee, visible_names))
    for arg in call.arguments:
      result.update(self._check_expr(arg, visible_names))
    return result


  def _report_undefined(self, name: str, line: int):
    self.error_handler.error(
      KiddouError(
        message = f"undefined variable: {name}.",
        line = line,
        col = None,
        text = None
      )
    )
