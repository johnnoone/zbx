"""
    zbx.exceptions
    ~~~~~~~~~~~~~~
"""


class ValidationError(ValueError):
    pass


class RPCException(Exception):
    def __init__(self, message, code, data=None):
        message = '%s(%d): %s' % (message, code, data)
        super(RPCException, self).__init__(message)
        self.code = code
        self.data = data
