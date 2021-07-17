from typing import List, Callable, Optional
from .error import ErrorHandler, KiddouError
from .expr import Expr, BinaryOp, Binary, UnaryOp, Unary, Variable, Literal
from .token import Token
from .token_type import TokenType


class ParseError(Exception):
  """An exception thrown when the parser encounters an error."""
  pass


class Parser:
  """A recursive-decent parser to convert tokens into an abstract syntax tree."""
  def __init__(self, tokens: List[Token], error_handler: ErrorHandler):
    self.tokens = tokens
    self.error_handler = error_handler
    self.current = 0

    self.token_type_to_binary_op = {
      TokenType.SEMI: BinaryOp.PIECE,
      TokenType.QUESTION: BinaryOp.DOMAIN,
      TokenType.OR: BinaryOp.OR,
      TokenType.AND: BinaryOp.AND,
      TokenType.EQUAL: BinaryOp.EQUAL,
      TokenType.BANG_EQUAL: BinaryOp.NOT_EQUAL,
      TokenType.LESS: BinaryOp.LESS,
      TokenType.LESS_EQUAL: BinaryOp.LESS_EQUAL,
      TokenType.GREATER: BinaryOp.GREATER,
      TokenType.GREATER_EQUAL: BinaryOp.GREATER_EQUAL,
      TokenType.PLUS: BinaryOp.ADD,
      TokenType.MINUS: BinaryOp.SUBTRACT,
      TokenType.STAR: BinaryOp.MULTIPLY,
      TokenType.SLASH: BinaryOp.DIVIDE,
      TokenType.DBLSLASH: BinaryOp.IDIVIDE,
      TokenType.PERCENT: BinaryOp.MODULUS,
      TokenType.CARET: BinaryOp.POWER,
    }
    self.token_type_unary_op = {
      TokenType.MINUS: UnaryOp.NEGATE,
      TokenType.BANG: UnaryOp.NOT
    }


  def parse(self) -> Optional[Expr]:
    try:
      return self._parse_expression()
    except ParseError as e:
      return None


  def _synchronize(self):
    self._advance()

    while not self._is_at_end():
      if self._previous().token_type == TokenType.SEMI or self._peek().token_type in [
        TokenType.DEF, TokenType.TYP, TokenType.CON, TokenType.ARG, TokenType.RUN, TokenType.USE,
      ]:
        return

      self._advance()


  def _parse_expression(self) -> Expr:
    return self._left_assoc_binary(
      element=self._parse_piece,
      token_types=[TokenType.SEMI]
    )


  def _parse_piece(self) -> Expr:
    return self._left_assoc_binary(
      element=self._parse_logical_or,
      token_types=[TokenType.QUESTION]
    )


  def _parse_logical_or(self) -> Expr:
    return self._left_assoc_binary(
      element=self._parse_logical_and,
      token_types=[TokenType.OR]
    )


  def _parse_logical_and(self) -> Expr:
    return self._left_assoc_binary(
      element=self._parse_equality,
      token_types=[TokenType.AND]
    )


  def _parse_equality(self) -> Expr:
    return self._left_assoc_binary(
      element=self._parse_comparison,
      token_types=[TokenType.EQUAL, TokenType.BANG_EQUAL]
    )


  def _parse_comparison(self) -> Expr:
    return self._left_assoc_binary(
      element=self._parse_sum,
      token_types=[TokenType.LESS, TokenType.LESS_EQUAL, TokenType.GREATER, TokenType.GREATER_EQUAL]
    )


  def _parse_sum(self) ->  Expr:
    return self._left_assoc_binary(
      element=self._parse_term,
      token_types=[TokenType.PLUS, TokenType.MINUS]
    )


  def _parse_term(self) -> Expr:
    return self._left_assoc_binary(
      element=self._parse_factor,
      token_types=[TokenType.STAR, TokenType.SLASH, TokenType.DBLSLASH, TokenType.PERCENT]
    )


  def _parse_factor(self) -> Expr:
    if self._match(TokenType.BANG, TokenType.MINUS):
      token = self._previous()
      operator = self.token_type_unary_op.get(token.token_type)
      right = self._parse_factor()
      return Unary(operator=operator, expr=right, line=token.line)

    expr = self._parse_primary()

    if self._match(TokenType.CARET):
      token = self._previous()
      operator = self.token_type_to_binary_op.get(token.token_type)
      right = self._parse_factor()
      return Binary(left=expr, operator=operator, right=right, line=token.line)

    return expr


  def _parse_primary(self) -> Expr:
    if self._match(
      TokenType.UNDEF, TokenType.TRUE, TokenType.FALSE, 
      TokenType.INT_LIT, TokenType.FLOAT_LIT, TokenType.STRING_LIT,
    ):
      token = self._previous()
      return Literal(value=token.literal, line=token.line)

    if self._match(TokenType.IDENTIFIER):
      token = self._previous()
      return Variable(name=token.lexeme, line=token.line)

    if self._match(TokenType.LPAREN):
      expr = self._parse_expression()
      self._consume(TokenType.RPAREN, "Expected closing ')'.")
      return expr

    raise self._error(self._peek(), "Expected expression.")


  def _left_assoc_binary(self, element: Callable[[], Expr], token_types: List[TokenType]) -> Expr:
    expr = element()

    while self._match(*token_types):
      token = self._previous()
      operator = self.token_type_to_binary_op.get(token.token_type)
      right = element()
      expr = Binary(left=expr, operator=operator, right=right, line=token.line)

    return expr


  def _match(self, *token_types: List[TokenType]) -> bool:
    for token_type in token_types:
      if self._check(token_type):
        self._advance()
        return True
    return False


  def _consume(self, token_type: TokenType, message: str) -> Token:
    if self._check(token_type):
      return self._advance()

    raise self._error(self._peek(), message)


  def _check(self, token_type: TokenType) -> bool:
    return not self._is_at_end() and self._peek().token_type == token_type


  def _advance(self) -> Token:
    if not self._is_at_end():
      self.current += 1
    return self._previous()


  def _is_at_end(self) -> bool:
    return self._peek().token_type == TokenType.EOF


  def _peek(self) -> Token:
    return self.tokens[self.current]


  def _previous(self) -> Token:
    return self.tokens[self.current - 1]


  def _error(self, token: Token, message: str) -> ParseError:
    self.error_handler.error(
      KiddouError(message, token.line, None, None)
    )
    return ParseError()
