class TokensError(Exception):
    """No environment variables."""


class RequestError(Exception):
    """Request doesn't work."""


class MessageError(Exception):
    """Message did not send."""


class ResponseKeysError(Exception):
    """Incorrect key(s) in response."""
