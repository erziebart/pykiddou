from enum import Enum

_token_type_list = [
  # grouping
  "LPAREN", "RPAREN", "COMMA",

  # operators
  "PLUS", "MINUS", "STAR", "SLASH", "DBLSLASH", "PERCENT", "CARET",
  "EQUAL", "BANG_EQUAL", "LESS", "LESS_EQUAL", "GREATER", "GREATER_EQUAL",
  "AND", "OR", "BANG", "QUESTION", "SEMI", "DOT",

  # keywords
  "RUN", "CON", "DEF", "ARG", "USE", "AS", "TYP",
  "UNDEF", "TRUE", "FALSE", "THIS",

  # literals
  "INT_LIT", "FLOAT_LIT", "STRING_LIT", "IDENTIFIER",

  # end of file
  "EOF"
]
TokenType = Enum("TokenType", " ".join(_token_type_list))