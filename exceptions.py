class NoTokensError(Exception):
    """Raises when we do not have token(s)."""

    pass


class RequestError(Exception):
    """Something worng with request."""

    pass


class AnswerNot200Error(Exception):
    """Raises only when answer not 200."""

    pass
