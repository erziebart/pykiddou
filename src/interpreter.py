import math
from typing import List, Mapping
from .callable import Function
from .error import ErrorHandler, KiddouError
from .exception import RuntimeException, TypeException, DivisionException
from .expr import Expr, BinaryOp, Binary, UnaryOp, Unary, Literal, Variable, Call
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
    self.globals = pervasives.copy()

    self.expr_handlers = {
      Binary: self._evaluate_binary,
      Unary: self._evaluate_unary,
      Literal: self._evaluate_literal,
      Variable: self._evaluate_variable,
      Call: self._evaluate_call,
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


  def interpret(self, expr: Expr):
    """Interpret some Kiddou code."""
    try:
      value = self._evaluate_expr(expr)
    except KiddouError as e:
      self.error_handler.runtime_error(e)
    else:
      print(value.stringify())


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
    return self.globals.get(variable.name) or Undef()


  def _evaluate_call(self, call: Call) -> Value:
    callee = self._evaluate_expr(call.callee)
    arguments = [self._evaluate_expr(arg) for arg in call.arguments]
    if isinstance(callee, Function):
      return callee.call(arguments)
    raise TypeException(f"can only make calls to functions, found <{callee.type_name()}>")
