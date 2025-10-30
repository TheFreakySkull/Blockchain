class ChainException(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message

class ChainLengthError(ChainException):
    pass

class ChainValidationError(ChainException):
    pass

class ChainNotFound(ChainException):
    pass
