import math
from contextlib import contextmanager
from typing import List, Mapping, Collection
from .callable import Callable, KiddouBlock
from .checker import Checker
from .environment import Environment
from .error import ErrorHandler, KiddouError
from .exception import RuntimeException, TypeException, DivisionException
from .expr import Expr, BinaryOp, Binary, UnaryOp, Unary, Literal, Variable, Call, Attribute, Block
from .object import Object, KiddouModule
from .stmt import Stmt, Con, Run
from .value import Value, Undef, Bool, Int, Float, String


def is_number(value: Value) -> bool:
  return isinstance(value, Int) or isinstance(value, Float)


def type_exception(operator: str, *values: List[Value]) -> TypeException:
  type_strings = [f"<{value.type_name()}>" for value in values]
  return TypeException(f"'{operator}' operation not defined for types: {', '.join(type_strings)}")


def is_falsey(value: Value) -> bool:
  return isinstance(value, Undef) or isinstance(value, Bool) and value.val == False


def is_truthy(value: Value) -> bool:
  return not is_falsey(value)


class Interpreter:
  """An interpreter for evaluating a program."""
  def __init__(self, error_handler: ErrorHandler, pervasives: Mapping[str, Value]):
    self.error_handler = error_handler
    self.globals = Environment()
    for name, value in pervasives.items():
      self.globals.bind(name, value)
    self.module = KiddouModule(self.globals, None)
    self.globals.bind("this", self.module)
    self.env = self.globals
    self.checker = Checker(error_handler)

    self.stmt_handlers = {
      Con: self._execute_con,
      Run: self._execute_run,
    }
    self.expr_handlers = {
      Binary: self._evaluate_binary,
      Unary: self._evaluate_unary,
      Literal: self._evaluate_literal,
      Variable: self._evaluate_variable,
      Call: self._evaluate_call,
      Attribute: self._evaluate_attribute,
      Block: self._evaluate_block,
    }
    self.binary_handlers = {
      BinaryOp.ADD: self._evaluate_add,
      BinaryOp.SUBTRACT: self._evaluate_subtract,
      BinaryOp.MULTIPLY: self._evaluate_multiply,
      BinaryOp.DIVIDE: self._evaluate_divide,
      BinaryOp.IDIVIDE: self._evaluate_idivide,
      BinaryOp.MODULUS: self._evaluate_modulus,
      BinaryOp.POWER: self._evaluate_power,
      BinaryOp.EQUAL: self._evaluate_equal,
      BinaryOp.NOT_EQUAL: self._evaluate_not_equal,
      BinaryOp.LESS: self._evaluate_less,
      BinaryOp.LESS_EQUAL: self._evaluate_less_equal,
      BinaryOp.GREATER: self._evaluate_greater,
      BinaryOp.GREATER_EQUAL: self._evaluate_greater_equal,
      BinaryOp.AND: self._evaluate_and,
      BinaryOp.OR: self._evaluate_or,
      BinaryOp.DOMAIN: self._evaluate_domain,
      BinaryOp.PIECE: self._evaluate_piece,
    }
    self.unary_handlers = {
      UnaryOp.NEGATE: self._evaluate_negate,
      UnaryOp.NOT: self._evaluate_not,
    }


  def interpret(self, stmts: List[Stmt]):
    """Interpret some Kiddou code."""
    self._check(stmts)

    if self.error_handler.has_error():
      return

    try:
      for stmt in stmts:
        self._execute_stmt(stmt)
    except KiddouError as e:
      self.error_handler.runtime_error(e)


  # def interpret(self, expr: Expr):
  #   """Interpret some Kiddou code."""
  #   try:
  #     value = self._evaluate_expr(expr)
  #   except KiddouError as e:
  #     self.error_handler.runtime_error(e)
  #   else:
  #     print(value.stringify())


  def _check(self, stmts: List[Stmt]):
    self.checker.check(stmts, self.globals)


  #################################################################################################
  ### Statements                                                                                ###
  #################################################################################################

  def _execute_stmt(self, stmt: Stmt):
    """Execute a statement."""
    try:
      return self.stmt_handlers[stmt.__class__](stmt)
    except RuntimeException as e:
      runtime_error = KiddouError(message=str(e), line=stmt.line_start, col=None, text=None)
      raise runtime_error


  def _execute_con(self, con: Con):
    value = self._evaluate_expr(con.expr)
    self.env.bind(con.name, value, False)


  def _execute_run(self, run: Run):
    value = self._evaluate_expr(run.expr)
    receiver = run.receiver
    if receiver is None:
      return

    rcv_type = type(receiver)

    if rcv_type is Variable:
      if run.reassign:
        self.env.overwrite(receiver.name, value)
      else:
        self.env.bind(receiver.name, value, True)

    if rcv_type is Attribute:
      obj_val = self._evaluate_expr(receiver.obj)
      if not isinstance(obj_val, Object):
        raise TypeException(f"type: <{obj_val.type_name()}> does not have attributes")
      obj_val.set_attr(receiver.name, value)


  #################################################################################################
  ### Expressions                                                                               ###
  #################################################################################################

  def _evaluate_expr(self, expr: Expr) -> Value:
    """Evaluate an expression and return the result."""
    try:
      return self.expr_handlers[expr.__class__](expr)
    except RuntimeException as e:
      runtime_error = KiddouError(message=str(e), line=expr.line, col=None, text=None)
      raise runtime_error


  def _evaluate_binary(self, binary: Binary) -> Value:
    """Evaluate a binary operation and return the result."""
    return self.binary_handlers[binary.operator](binary.left, binary.right)


  def _evaluate_add(self, left: Expr, right: Expr) -> Value:
    left_val = self._evaluate_expr(left)
    right_val = self._evaluate_expr(right)
    if isinstance(left_val, Undef) or isinstance(right_val, Undef):
      return Undef()
    if isinstance(left_val, Int) and isinstance(right_val, Int):
      return Int(left_val.val + right_val.val)
    if is_number(left_val) and is_number(right_val):
      return Float(left_val.val + right_val.val)
    if isinstance(left_val, String) and isinstance(right_val, String):
      return String(left_val.val + right_val.val)
    raise type_exception("+", left_val, right_val)


  def _evaluate_subtract(self, left: Expr, right: Expr) -> Value:
    left_val = self._evaluate_expr(left)
    right_val = self._evaluate_expr(right)
    if isinstance(left_val, Undef) or isinstance(right_val, Undef):
      return Undef()
    if isinstance(left_val, Int) and isinstance(right_val, Int):
      return Int(left_val.val - right_val.val)
    if is_number(left_val) and is_number(right_val):
      return Float(left_val.val - right_val.val)
    raise type_exception("-", left_val, right_val)


  def _evaluate_multiply(self, left: Expr, right: Expr) -> Value:
    left_val = self._evaluate_expr(left)
    right_val = self._evaluate_expr(right)
    if isinstance(left_val, Undef) or isinstance(right_val, Undef):
      return Undef()
    if isinstance(left_val, Int) and isinstance(right_val, Int):
      return Int(left_val.val * right_val.val)
    if is_number(left_val) and is_number(right_val):
      return Float(left_val.val * right_val.val)
    raise type_exception("*", left_val, right_val)


  def _evaluate_divide(self, left: Expr, right: Expr) -> Value:
    left_val = self._evaluate_expr(left)
    right_val = self._evaluate_expr(right)
    if isinstance(left_val, Undef) or isinstance(right_val, Undef):
      return Undef()
    if is_number(left_val) and is_number(right_val):
      try:
        return Float(float(left_val.val) / float(right_val.val))
      except ZeroDivisionError:
        result = math.nan if left_val.val in [0, math.nan] else math.copysign(math.inf, left_val.val)
        return Float(result)
    raise type_exception("/", left_val, right_val)


  def _evaluate_idivide(self, left: Expr, right: Expr) -> Value:
    left_val = self._evaluate_expr(left)
    right_val = self._evaluate_expr(right)
    if isinstance(left_val, Undef) or isinstance(right_val, Undef):
      return Undef()
    if is_number(left_val) and is_number(right_val):
      try:
        result = int(left_val.val // right_val.val)
      except ZeroDivisionError:
        raise DivisionException("cannot integer divide by 0")
      except ValueError:
        # raised if the numerator is infinite or NaN
        raise DivisionException(f"cannot integer divide into {left_val}")
      else:
        return Int(result)
    raise type_exception("//", left_val, right_val)


  def _evaluate_modulus(self, left: Expr, right: Expr) -> Value:
    left_val = self._evaluate_expr(left)
    right_val = self._evaluate_expr(right)
    if isinstance(left_val, Undef) or isinstance(right_val, Undef):
      return Undef()
    if isinstance(left_val, Int) and isinstance(right_val, Int):
      try:
        return Int(left_val.val % right_val.val)
      except ZeroDivisionError:
        raise DivisionException("cannot integer divide by 0")
    if is_number(left_val) and is_number(right_val):
      try:
        return Float(left_val.val % right_val.val)
      except ZeroDivisionError:
        result = math.nan if left_val.val in [0, math.nan] else math.copysign(math.inf, left_val.val)
        return Float(result)
    raise type_exception("%", left_val, right_val)


  def _evaluate_power(self, left: Expr, right: Expr) -> Value:
    left_val = self._evaluate_expr(left)
    right_val = self._evaluate_expr(right)
    if isinstance(left_val, Undef) or isinstance(right_val, Undef):
      return Undef()
    if isinstance(left_val, Int) and isinstance(right_val, Int):
      return Int(left_val.val ** right_val.val)
    if is_number(left_val) and is_number(right_val):
      try:
        return Float(math.pow(left_val.val, right_val.val))
      except ValueError:
        # raised if the result is a complex number
        return Float(math.nan)
    raise type_exception("^", left_val, right_val)


  def _evaluate_equal(self, left: Expr, right: Expr) -> Value:
    left_val = self._evaluate_expr(left)
    right_val = self._evaluate_expr(right)
    if isinstance(left_val, Undef) or isinstance(right_val, Undef):
      return Undef()
    return Bool(left_val.val == right_val.val)


  def _evaluate_not_equal(self, left: Expr, right: Expr) -> Value:
    left_val = self._evaluate_expr(left)
    right_val = self._evaluate_expr(right)
    if isinstance(left_val, Undef) or isinstance(right_val, Undef):
      return Undef()
    return Bool(left_val.val != right_val.val)


  def _evaluate_less(self, left: Expr, right: Expr) -> Value:
    left_val = self._evaluate_expr(left)
    right_val = self._evaluate_expr(right)
    if isinstance(left_val, Undef) or isinstance(right_val, Undef):
      return Undef()
    if is_number(left_val) and is_number(right_val):
      return Bool(left_val.val < right_val.val)
    raise type_exception("<", left_val, right_val)


  def _evaluate_less_equal(self, left: Expr, right: Expr) -> Value:
    left_val = self._evaluate_expr(left)
    right_val = self._evaluate_expr(right)
    if isinstance(left_val, Undef) or isinstance(right_val, Undef):
      return Undef()
    if is_number(left_val) and is_number(right_val):
      return Bool(left_val.val <= right_val.val)
    raise type_exception("<=", left_val, right_val)


  def _evaluate_greater(self, left: Expr, right: Expr) -> Value:
    left_val = self._evaluate_expr(left)
    right_val = self._evaluate_expr(right)
    if isinstance(left_val, Undef) or isinstance(right_val, Undef):
      return Undef()
    if is_number(left_val) and is_number(right_val):
      return Bool(left_val.val > right_val.val)
    raise type_exception(">", left_val, right_val)


  def _evaluate_greater_equal(self, left: Expr, right: Expr) -> Value:
    left_val = self._evaluate_expr(left)
    right_val = self._evaluate_expr(right)
    if isinstance(left_val, Undef) or isinstance(right_val, Undef):
      return Undef()
    if is_number(left_val) and is_number(right_val):
      return Bool(left_val.val >= right_val.val)
    raise type_exception(">=", left_val, right_val)


  def _evaluate_and(self, left: Expr, right: Expr) -> Value:
    left_val = self._evaluate_expr(left)
    return left_val if is_falsey(left_val) else self._evaluate_expr(right)


  def _evaluate_or(self, left: Expr, right: Expr) -> Value:
    left_val = self._evaluate_expr(left)
    return left_val if is_truthy(left_val) else self._evaluate_expr(right)


  def _evaluate_domain(self, left: Expr, right: Expr) -> Value:
    right_val = self._evaluate_expr(right)
    return Undef() if is_falsey(right_val) else self._evaluate_expr(left)


  def _evaluate_piece(self, left: Expr, right: Expr) -> Value:
    left_val = self._evaluate_expr(left)
    return self._evaluate_expr(right) if isinstance(left_val, Undef) else left_val


  def _evaluate_unary(self, unary: Unary) -> Value:
    return self.unary_handlers[unary.operator](unary.expr)


  def _evaluate_negate(self, expr: Expr) -> Value:
    expr_val = self._evaluate_expr(expr)
    if isinstance(expr_val, Undef):
      return Undef()
    if isinstance(expr_val, Int):
      return Int(-expr_val.val)
    if isinstance(expr_val, Float):
      return Float(-expr_val.val)
    raise type_exception("- (unary)", expr_val)


  def _evaluate_not(self, expr: Expr) -> Value:
    expr_val = self._evaluate_expr(expr)
    if isinstance(expr_val, Undef):
      return Undef()
    if isinstance(expr_val, Bool):
      return Bool(not expr_val.val)
    raise type_exception("!", expr_val)


  def _evaluate_literal(self, literal: Literal) -> Value:
    return literal.value


  def _evaluate_variable(self, variable: Variable) -> Value:
    return self.env.get(variable.name)


  def _evaluate_call(self, call: Call) -> Value:
    callee = self._evaluate_expr(call.callee)
    if not isinstance(callee, Callable):
      raise TypeException(f"type: <{callee.type_name()}> is not callable")
    arguments = [self._evaluate_expr(arg) for arg in call.arguments]
    return callee.call(arguments, self.env)


  def _evaluate_attribute(self, attribute: Attribute) -> Value:
    obj_val = self._evaluate_expr(attribute.obj)
    if not isinstance(obj_val, Object):
      raise TypeException(f"type: <{obj_val.type_name()}> does not have attributes")
    return obj_val.get_attr(attribute.name)


  def _evaluate_block(self, block: Block) -> Value:
    # define the block function
    def run_block(args: Collection[Value], env: Environment) -> Value:
      with self._switch_env(env):
        # exec stmts
        for stmt in block.stmts:
          self._execute_stmt(stmt)

        # eval result
        result = Undef()
        if block.expr is not None:
          result = self._evaluate_expr(block.expr)

        return result
    
    # return the block
    block_env = self.env.copy_retain(block.dependent_names)
    return KiddouBlock(func=run_block, name=None, env=block_env)


  @contextmanager
  def _switch_env(self, new_env: Environment):
    try:
      # transition to new env
      old_env = self.env
      self.env = new_env

      yield None
    except Exception as e:
      raise e
    finally:
      # restore previous env
      self.env = old_env
