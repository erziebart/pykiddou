class Kiddou:
  """The main kiddou program, which reads and executes code."""
  def __init__(self):
    pass

  def run_file(self, path: str) -> None:
    """Run a Kiddou program from a file."""
    with open(path, "r", encoding="utf-8") as f:
      self.run(f.read())

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


  def run(self, source: str) -> None:
    """Run some source text."""
    print(source)
