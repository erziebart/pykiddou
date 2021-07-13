from dataclasses import dataclass
from typing import Optional, Any
from .token_type import TokenType

@dataclass
class Token:
  token_type: TokenType
  line: int
  lexeme: str
  literal: Optional[Any] = None
