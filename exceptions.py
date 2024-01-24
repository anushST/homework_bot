class NoTokensError(Exception):
    """Raises when we do not have token(s)."""

    pass


class RequestError(Exception):
    """Something worng with request."""

    pass


class AnswerNot200Error(Exception):
    """Raises only when answer not 200."""

    pass


class JsonError(Exception):
    """Error while parse json to python types."""

    pass


class CurrentDateError(Exception):
    """Raises when CurrentDate is unusual."""

    pass
