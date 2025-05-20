import traceback

from aws_lambda_powertools import Logger

logger = Logger(service="APP")

class GenericFatalError(Exception):
    """
    A Generic Exception for our API, that other ones can base from.
    """
    def __init__(self, message, error_code=500):
        self.error_code = error_code
        self.message = message
        # If this gets created/raised, log the message:
        # logger.error(traceback.format_exc())
        # logger.error(message)
        super().__init__(message)
        logger.exception(self)

    def __str__(self):
        return f"{self.message} (Error Code: {self.error_code})"

class BadSsoToken(GenericFatalError):
    """
    Raised if the SSO Token isn't changed after deploying.
    """
