class ConnectionError(Exception):
    def __init__(self, message) -> None:
        super().__init__(message)


class IncorrectCredentialsError(Exception):
    def __init__(self, message) -> None:
        super().__init__(message)


class OpeningSessionFileError(Exception):
    def __init__(self, message) -> None:
        super().__init__(message)


class SavingSessionFileError(Exception):
    def __init__(self, message) -> None:
        super().__init__(message)


class CorruptedSessionError(Exception):
    def __init__(self, message) -> None:
        super().__init__(message)


class CorruptedHtmlError(Exception):
    def __init__(self, message) -> None:
        super().__init__(message)
