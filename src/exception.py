class RuntimeException(RuntimeError):
  """A runtime exception raised while executing a Kiddou program."""
  def __init__(self, message):
    super(RuntimeException, self).__init__(message)


class TypeException(RuntimeException):
  """A exception for reporting when the wrong type is used."""
  def __init__(self, message):
    super(TypeException, self).__init__("TypeException: " + message)


class DivisionException(object):
  """docstring for ZeroDivisionException"""
  def __init__(self, message):
    super(DivisionException, self).__init__("DivisionException: " + message)
    
    
    