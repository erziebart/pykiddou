import sys

def main():
  argv = sys.argv
  argc = len(argv)

  if argc > 1:
    print("Usage: python3 main.py")
    sys.exit(64)
  else:
    print("Hello Interpreter")

if __name__ == '__main__':
  main()