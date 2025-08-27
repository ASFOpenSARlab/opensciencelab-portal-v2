"""Custom exceptions for the API, to add automatic logging."""

from aws_lambda_powertools import Logger


logger = Logger(child=True)


class GenericFatalError(Exception):
    """
    A Generic Exception for our API, that other ones can base from.
    """

    def __init__(self, message, error_code=500, extra_info=None):
        self.error_code = error_code
        self.message = message
        # Initialize this exception:
        super().__init__(message)
        # And add the error + traceback to the event:
        logger.exception(self)
        # If you want something logged, but NOT printed on screen:
        if extra_info:
            # Have extra_info in it's own event in-case it's json:
            logger.error("Extra info:")
            logger.error(extra_info)

    def __str__(self):
        return f"{self.message} (Error Code: {self.error_code})"


class BadSsoToken(GenericFatalError):
    """
    Raised if the SSO Token isn't changed after deploying.
    """

    def __init__(self, message, error_code=403, extra_info=None):
        super().__init__(message, error_code, extra_info)


class DbError(GenericFatalError):
    """
    Raised if there is a problem with the DB.
    """

    # pylint: disable-next=useless-parent-delegation
    def __init__(self, message, error_code=500, extra_info=None):
        super().__init__(message, error_code, extra_info)


class CognitoError(GenericFatalError):
    """
    Raised if there is a problem with the DB.
    """

    # pylint: disable-next=useless-parent-delegation
    def __init__(self, message, error_code=500, extra_info=None):
        super().__init__(message, error_code, extra_info)

class UserNotFound(GenericFatalError):
    """
    Raised if there is a problem with creating a User.
    """

    def __init__(self, message, error_code=404, extra_info=None):
        super().__init__(message, error_code, extra_info)

class LabDoesNotExist(GenericFatalError):
    """
    Raised if a given lab does not exist.
    """

    def __init__(self, message, error_code=404, extra_info=None):
        super().__init__(message, error_code, extra_info)
