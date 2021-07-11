import sys
from src.kiddou import Kiddou

def main():
  argv = sys.argv
  argc = len(argv)

  if argc > 2:
    print("Usage: python3 main.py [path]")
    sys.exit(64)
  elif argc == 2:
    path = argv[1]
    Kiddou().run_file(path)
  else:
    Kiddou().run_prompt()

if __name__ == '__main__':
  main()
