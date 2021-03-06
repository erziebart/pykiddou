from typing import List, Callable, Optional
from .constructor import Constructor, Block, Sequence
from .error import ErrorHandler, KiddouError
from .expr import Expr, BinaryOp, Binary, UnaryOp, Unary, Variable, Literal, Call, Index, Attribute
from .token import Token
from .token_type import TokenType
from .stmt import Stmt, Con, Run


def is_valid_receiver(expr: Expr) -> bool:
  """Returns True iff the given expression is a valid receiver for the LHS of an assignment."""
  return type(expr) in [Variable, Index, Attribute]


class ParseError(Exception):
  """An exception thrown when the parser encounters an error."""
  pass


class Parser:
  """A recursive-decent parser to convert tokens into an abstract syntax tree."""
  def __init__(self, tokens: List[Token], error_handler: ErrorHandler):
    self.tokens = tokens
    self.error_handler = error_handler
    self.current = 0

    self.stmt_keywords = {
      TokenType.CON: self._parse_con,
      TokenType.RUN: self._parse_run,
    }
    self.assignment_token_types = [
      TokenType.ASSIGN, 
      TokenType.RE_ASSIGN
    ]
    self.statement_boundary_token_types = {
      TokenType.DEF, 
      TokenType.TYP, 
      TokenType.CON, 
      TokenType.ARG, 
      TokenType.RUN, 
      TokenType.USE, 
      TokenType.ARROW,
    }
    self.constructor_boundary_token_types = {
      TokenType.RBRACE, 
      TokenType.RBRACKET,
    }
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


  def parse(self) -> List[Stmt]:
    statements = []
    while not self._is_at_end():
      stmt = self._parse_statement()
      if stmt is not None:
        # print(stmt)
        statements.append(stmt)
      
    return statements


  # def parse(self) -> Optional[Expr]:
  #   try:
  #     return self._parse_expression()
  #   except ParseError as e:
  #     return None


  def _parse_statement(self) -> Optional[Stmt]:
    try:
      token = self._advance()
      stmt_lambda = self.stmt_keywords.get(token.token_type)
      if stmt_lambda is None:
        raise self._error(token, "Expected a statement header keyword.")
      return stmt_lambda()

    except ParseError as e:
      self._synchronize()
      return None


  def _parse_con(self) -> Con:
    line_start = self._previous().line
    identifier = self._consume(TokenType.IDENTIFIER, "Expected identifier.")

    assignment = self._peek()
    if assignment.token_type not in self.assignment_token_types:
      raise self._error(assignment, "Expected assignment.")
    self._advance()

    # forbid reassignment for con statements
    if assignment.token_type is not TokenType.ASSIGN:
      self._error(assignment, "Reassignment not allowed.")

    expr = self._parse_expression()

    line_end = self._previous().line
    return Con(
      line_start = line_start,
      line_end = line_end,
      name = identifier.lexeme,
      expr = expr
    )


  def _parse_run(self) -> Run:
    line_start = self._previous().line
    receiver = None
    assignment = None
    expr = self._parse_expression()

    # if this is an assignment, reinterpret LHS as receiver
    if self._match(*self.assignment_token_types):
      if is_valid_receiver(expr):
        receiver = expr
        assignment = self._previous()
        expr = self._parse_expression()
      else:
        self._error(self._previous(), "Invalid assignment target.")
        self._parse_expression()

    reassign = False
    if assignment is not None:
      reassign = assignment.token_type is not TokenType.ASSIGN

    line_end = self._previous().line
    return Run(
      line_start = line_start,
      line_end = line_end,
      receiver = receiver,
      expr = expr,
      reassign = reassign
    )


  def _synchronize(self):
    while not self._is_at_end():
      if self._peek().token_type in self.statement_boundary_token_types:
        return

      if self._peek().token_type in self.constructor_boundary_token_types:
        return

      try:
        if self._match(TokenType.LBRACE):
          self._parse_constructor(is_eager=False)
          if self._match(TokenType.RBRACKET):
            raise self._error("Closing ']' does not match opening '{'.")
          self._consume(TokenType.RBRACE, "Expected closing '}'.")
        elif self._match(TokenType.LBRACKET):
          self._parse_constructor(is_eager=True)
          if self._match(TokenType.RBRACE):
            raise self._error("Closing '}' does not match opening '['.")
          self._consume(TokenType.RBRACKET, "Expected closing ']'.")
        else:
          self._advance()
      except ParseError as e:
        pass


  def _left_assoc_binary(self, element: Callable[[], Expr], token_types: List[TokenType]) -> Expr:
    expr = element()

    while self._match(*token_types):
      token = self._previous()
      operator = self.token_type_to_binary_op.get(token.token_type)
      right = element()
      expr = Binary(left=expr, operator=operator, right=right, line=token.line)

    return expr


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

    expr = self._parse_call()

    if self._match(TokenType.CARET):
      token = self._previous()
      operator = self.token_type_to_binary_op.get(token.token_type)
      right = self._parse_factor()
      return Binary(left=expr, operator=operator, right=right, line=token.line)

    return expr


  def _parse_call(self) -> Expr:
    expr = self._parse_primary()

    while True:
      if self._match(TokenType.LPAREN):
        arguments = []
        if not self._check(TokenType.RPAREN):
          arguments = self._parse_arguments()
        rparen = self._consume(TokenType.RPAREN, "Expected closing ')' after arguments.")
        expr = Call(callee=expr, arguments=arguments, line=rparen.line)
      elif self._match(TokenType.LBRACKET):
        index = self._parse_expression()
        rbracket = self._consume(TokenType.RBRACKET, "Expected closing ']' after index.")
        expr = Index(container=expr, index=index, line=rbracket.line)
      elif self._match(TokenType.DOT):
        name = self._consume(TokenType.IDENTIFIER, "Expected attribute name after '.'.")
        expr = Attribute(obj=expr, name=name.lexeme, line=name.line)
      else:
        break

    return expr


  def _parse_arguments(self) -> List[Expr]:
    result = [self._parse_expression()]

    while self._match(TokenType.COMMA):
      if len(result) > 255:
        self._error(self._peek(), "Can't pass more than 255 arguments.")
      result.append(self._parse_expression())

    return result


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

    if self._match(TokenType.LBRACE):
      constructor = self._parse_constructor(is_eager=False)
      if self._match(TokenType.RBRACKET):
        raise self._error(self._previous(), "Closing ']' does not match opening '{'.")
      self._consume(TokenType.RBRACE, "Expected closing '}'.")
      return constructor

    if self._match(TokenType.LBRACKET):
      constructor = self._parse_constructor(is_eager=True)
      if self._match(TokenType.RBRACE):
        raise self._error(self._previous(), "Closing '}' does not match opening '['.")
      self._consume(TokenType.RBRACKET, "Expected closing ']'.")
      return constructor

    raise self._error(self._peek(), "Expected expression.")


  def _parse_constructor(self, is_eager: bool) -> Constructor:
    line = self._previous().line

    if self._peek().token_type in self.constructor_boundary_token_types:
      self._error(self._previous(), "Empty constructor not allowed.")
      return Block(line=line, stmts=[], expr=None, is_eager=is_eager)

    if self._peek().token_type in self.statement_boundary_token_types:
      return self._parse_block(is_eager, line)

    expr = self._parse_expression()
    return self._parse_sequence(is_eager, line, expr)


  def _parse_block(self, is_eager: bool, line: int) -> Block:
    stmts = []
    while not (
      self._check(TokenType.RBRACE) or self._check(TokenType.RBRACKET) or self._check(TokenType.ARROW)
    ) and not self._is_at_end():
      stmt = self._parse_statement()
      if stmt is not None:
        stmts.append(stmt)

    # match a body with no expression
    if self._is_at_end() or self._check(TokenType.RBRACE) or self._check(TokenType.RBRACKET):
      return Block(line=line, stmts=stmts, expr=None, is_eager=is_eager)

    has_arrow = self._match(TokenType.ARROW)
    token = self._peek()
    expr = self._parse_expression()

    # forbid statements then expression with no separating arrow
    if not has_arrow and stmts:
      self._error(token, "Expected '->' before expression.")

    return Block(line=line, stmts=stmts, expr=expr, is_eager=is_eager)


  def _parse_sequence(self, is_eager: bool, line:int, first_element: Expr) -> Sequence:
    elements = [first_element]

    while self._match(TokenType.COMMA):
      elements.append(self._parse_expression())

    return Sequence(line=line, elements=elements, is_eager=is_eager)


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
