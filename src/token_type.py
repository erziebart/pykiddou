from enum import Enum

_token_type_list = [
  # grouping
  "LPAREN", "RPAREN", "COMMA", "LBRACE", "RBRACE", "ARROW",

  # operators
  "PLUS", "MINUS", "STAR", "SLASH", "DBLSLASH", "PERCENT", "CARET",
  "EQUAL", "BANG_EQUAL", "LESS", "LESS_EQUAL", "GREATER", "GREATER_EQUAL",
  "AND", "OR", "BANG", "QUESTION", "SEMI", "DOT",

  # assignment
  "ASSIGN", "RE_ASSIGN",

  # keywords
  "RUN", "CON", "DEF", "ARG", "USE", "AS", "TYP",
  "UNDEF", "TRUE", "FALSE",

  # literals
  "INT_LIT", "FLOAT_LIT", "STRING_LIT", "IDENTIFIER",

  # end of file
  "EOF"
]
TokenType = Enum("TokenType", " ".join(_token_type_list))