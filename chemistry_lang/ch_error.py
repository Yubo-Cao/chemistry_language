from ch_token import Token


class CHError(Exception):
    """
    Base class for all chemical helper errors.
    """

    def __init__(self, msg: str, token: Token = None):
        self.msg = msg
        self.token = token
