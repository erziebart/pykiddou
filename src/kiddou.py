import sys
from .error import ErrorHandler
from .scanner import Scanner

class Kiddou:
  """The main kiddou program, which reads and executes code."""
  def __init__(self):
    self.error_handler = ErrorHandler()

  def run_file(self, path: str) -> None:
    """Run a Kiddou program from a file."""
    with open(path, "r", encoding="utf-8") as f:
      self.run(f.read())

    if self.error_handler.has_error():
      self.error_handler.flush()
      sys.exit(65)

  def run_prompt(self) -> None:
    """Run a kiddou program line-by-line using a REPL."""
    while True:
      try:
        line = input("> ")
      except EOFError:
        print("\nExiting.")
        break
      except KeyboardInterrupt:
        break
      self.run(line)
      self.error_handler.flush()

  def run(self, source: str) -> None:
    """Run some source text."""
    scanner = Scanner(source, self.error_handler)
    tokens = scanner.scan_tokens()

    if self.error_handler.has_error():
      return

    for token in tokens:
      print(token)
