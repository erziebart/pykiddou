class RuntimeException(RuntimeError):
  """A runtime exception raised while executing a Kiddou program."""
  def __init__(self, message):
    super(RuntimeException, self).__init__(message)


class TypeException(RuntimeException):
  """An exception for reporting when the wrong type is used."""
  def __init__(self, message):
    super(TypeException, self).__init__("TypeException: " + message)


class DivisionException(RuntimeException):
  """An exception for when attempting to divide by 0."""
  def __init__(self, message):
    super(DivisionException, self).__init__("DivisionException: " + message)
    

class NameException(RuntimeException):
  """An exception for accessing a variable that is not defined."""
  def __init__(self, message):
    super(NameException, self).__init__("NameException: " + message)

class ImmutableException(RuntimeException):
  """An exception for modifying an immutable value."""
  def __init__(self, message):
    super(ImmutableException, self).__init__("ImmutableException: " + message)

class AttributeException(RuntimeException):
  """An exception for accessing an undefined attribute."""
  def __init__(self, message):
    super(AttributeException, self).__init__("AttributeException: " + message)

class IndexOutOfBoundsException(RuntimeException):
  """An exception for trying to modify a non-existant index in a list."""
  def __init__(self, message):
    super(IndexOutOfBoundsException, self).__init__("IndexOutOfBoundsException: " + message)
