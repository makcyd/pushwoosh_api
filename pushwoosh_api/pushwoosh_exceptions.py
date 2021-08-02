class PushwooshException(Exception):
    """
    Base class for exceptions
    """
    pass


class EmptyJsonResponse(PushwooshException):
    """
    Exception raised when response from Pushwoosh API does not contain JSON data
    """
    def __init__(self, response, message):
        self.response = response
        self.message = message

class HttpError(PushwooshException):
    """
    Exception raised when response from Pushwoosh API has non-OK status
    """
    def __init__(self, status_code, reason, message):
        self.status_code = status_code
        self.reason = reason
        self.message = message