from dataclasses import dataclass
from typing import Optional, Any
from .token_type import TokenType
from .value import Value

@dataclass
class Token:
  token_type: TokenType
  line: int
  lexeme: str
  literal: Optional[Value] = None
