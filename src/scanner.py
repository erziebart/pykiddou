from typing import List, Optional, Any
from.error import ErrorHandler, KiddouError
from .token import Token
from .token_type import TokenType

def is_digit(char: str) -> bool:
    """Return True iff the given character is a digit."""
    return char >= "0" and char <= "9"


def is_alpha(char: str) -> bool:
  """Return True iff the given character is a letter or underscore."""
  return (
      (char >= "a" and char <= "z")
      or (char >= "A" and char <= "Z")
      or (char == "_")
  )


def is_alphanumeric(char: str) -> bool:
  """Return True iff the given character is alphanumeric."""
  return is_digit(char) or is_alpha(char)

class Scanner:
  """A lexical scanner of input text into tokens."""
  def __init__(self, source: str, error_handler: ErrorHandler):
    self.source = source
    self.error_handler = error_handler
    self.tokens = []
    self.line = 1
    self.col = 0
    self.start = 0
    self.current = 0

    self.one_char_tokens = {
      "\"": lambda: self._scan_string(),
      "#": lambda: self._scan_comment(),
      "(": lambda: self._add_token(TokenType.LPAREN),
      ")": lambda: self._add_token(TokenType.RPAREN),
      "+": lambda: self._add_token(TokenType.PLUS),
      "-": lambda: self._add_token(TokenType.MINUS),
      "*": lambda: self._add_token(TokenType.STAR),
      "/": lambda: self._add_token(TokenType.SLASH),
      "%": lambda: self._add_token(TokenType.PERCENT),
      "^": lambda: self._add_token(TokenType.CARET),
      "<": lambda: self._add_token(TokenType.LESS),
      ">": lambda: self._add_token(TokenType.GREATER),
      "!": lambda: self._add_token(TokenType.BANG),
      "?": lambda: self._add_token(TokenType.QUESTION),
      ";": lambda: self._add_token(TokenType.SEMI),
      ".": lambda: self._add_token(TokenType.DOT),
      " ": lambda: None,
      "\t": lambda: None,
      "\r": lambda: None,
      "\n": lambda: self._newline(),
      "&": lambda: self._error("use && for logical AND"),
      "|": lambda: self._error("use || for logical OR"),
    }
    self.two_char_tokens = {
      "//": lambda: self._add_token(TokenType.DBLSLASH),
      "==": lambda: self._add_token(TokenType.EQUAL),
      "!=": lambda: self._add_token(TokenType.BANG_EQUAL),
      "<=": lambda: self._add_token(TokenType.LESS_EQUAL),
      ">=": lambda: self._add_token(TokenType.GREATER_EQUAL),
      "&&": lambda: self._add_token(TokenType.AND),
      "||": lambda: self._add_token(TokenType.OR),
    }
    self.reserved_keywords = {
      "true": lambda: self._add_token(TokenType.TRUE), 
      "false": lambda: self._add_token(TokenType.FALSE), 
      "undef": lambda: self._add_token(TokenType.UNDEF),
    }


  def scan_tokens(self) -> List[Token]:
    """Convert this scanner into tokens."""
    while not self._is_at_end():
      self.start = self.current
      self._scan_token()

    self.tokens.append(Token(token_type=TokenType.EOF, line=self.line, lexeme=""))
    return self.tokens


  def _is_at_end(self) -> bool:
    """Returns True iff the end of the source text has been reached."""
    return self.current >= len(self.source)


  def _scan_token(self) -> None:
    """Scan for the next token in the source string."""
    char = self._advance()

    # check for number literals
    if is_digit(char):
      return self._scan_number()

    # check for identifiers
    if is_alpha(char):
      return self._scan_identifier()

    # check for 2-character matches at the scanner head
    token_lambda = self.two_char_tokens.get(char + self._peek())
    if token_lambda:
      self._advance()
      return token_lambda()

    # check for 1-character matches at the scanner head
    token_lambda = self.one_char_tokens.get(char)
    if token_lambda:
      return token_lambda()

    # unknown character
    return self._error(f"unknown character \'{char}\'")


  def _advance(self) -> str:
    """Advance to the next character in the source."""
    res = self.source[self.current]
    self.current += 1
    self.col += 1
    return res


  def _peek(self) -> str:
    """Peek at the next character in the source (without advancing the scanner)."""
    if self._is_at_end():
      return '\0'
    return self.source[self.current]


  def _peek_next(self) -> str:
    """Peek at the character one ahead of the current position (lookahead of 1)."""
    if self.current + 1 >= len(self.source):
      return '\0'
    return self.source[self.current+1]


  def _scan_number(self) -> None:
    """Scan a number literal. Handles both integers and floats."""
    is_float = False
    has_exponent = False

    # before decimal point
    while is_digit(self._peek()):
      self._advance()

    # optional decimal point
    if self._peek() == '.' and is_digit(self._peek_next()):
      is_float = True
      self._advance()
      while is_digit(self._peek()):
        self._advance()

    # optional exponent
    if self._peek() == 'E':
      is_float = True
      self._advance()
      if self._peek() in ['+', '-']:
        self._advance()
      while is_digit(self._peek()):
        has_exponent = True
        self._advance()
      if not has_exponent:
        literal = self.source[self.start:self.current]
        self._error(f"invalid float \'{literal}\'")
        return self._add_token(TokenType.FLOAT_LIT, float(literal.split('E')[0]))

    literal = self.source[self.start:self.current]
    if is_float:
      return self._add_token(TokenType.FLOAT_LIT, float(literal))
    else:
      return self._add_token(TokenType.INT_LIT, int(literal))


  def _scan_identifier(self) -> None:
    """Scan an identifier. Includes a check for reserved keywords."""
    while is_alphanumeric(self._peek()):
      self._advance()

    text = self.source[self.start:self.current]
    token_lambda = self.reserved_keywords.get(text)
    if token_lambda:
      return token_lambda()
    
    return self._add_token(TokenType.IDENTIFIER)


  def _scan_string(self) -> None:
    """Scan a string literal."""
    # advance to the end of the inner text
    while self._peek() != '\"' and not self._is_at_end():
      if self._peek() == '\n':
        self.line += 1
      self._advance()

    # error: unterminated string
    if self._is_at_end():
      self._error("unterminated string")

    # consume the closing \"
    self._advance()

    # trim the quotes
    literal = self.source[self.start+1:self.current-1]
    self._add_token(TokenType.STRING_LIT, literal)


  def _scan_comment(self) -> None:
    """Scan a comment, which involves ignoring all remaining text on this line."""
    while self._peek() != '\n' and not self._is_at_end():
      self._advance()


  def _add_token(self, token_type: TokenType, literal: Optional[Any] = None) -> None:
    lexeme = self.source[self.start:self.current]
    token = Token(token_type=token_type, line=self.line, lexeme=lexeme, literal=literal)
    self.tokens.append(token)


  def _newline(self) -> None:
    self.line += 1
    self.col = 0


  def _error(self, message: str) -> None:
    self.error_handler.error(
      KiddouError(message, self.line, self.col, None)
    )
