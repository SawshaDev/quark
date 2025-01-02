class QuarkException(Exception):
    """Base for all custom exceptions"""

class NodeRefused(QuarkException):
    """Used when connection in Node refuses."""