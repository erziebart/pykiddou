from dataclasses import dataclass
from typing import Optional
import sys

@dataclass
class KiddouError(Exception):
  """A Kiddou error."""
  message: str
  line: int
  col: Optional[int]
  text: Optional[str]

class ErrorHandler:
  """A handler for Kiddou errors."""
  def __init__(self):
    self.error_list = []
    self.had_runtime_error = False

  def has_error(self) -> bool:
    """Returns True iff this handler has errors to report."""
    return bool(self.error_list)

  def error(self, error: KiddouError) -> None:
    """Report an error to the handler."""
    self.error_list.append(error)

  def runtime_error(self, error: KiddouError) -> None:
    self.print_error(error)
    self.had_runtime_error = True

  def flush(self) -> None:
    """Print out all the errors that have been reported, and reset the handler."""
    for error in self.error_list:
      self.print_error(error)

    self.error_list = []
    self.had_runtime_error = False

  def print_error(self, error: KiddouError) -> None:
    """Print the the contents of an error to stderr."""
    msg = f"Error: \"{error.message}\""
    loc = f"on line {error.line}, column {error.col}" if error.col else f"on line {error.line}"
    text = f"at {error.text}" if error.text else ""
    print(msg, loc, text, file=sys.stderr)
