class DeserializeReportError(Exception):
    def __init__(self, message) -> None:
        super().__init__(message)


class InvalidColumnNameError(DeserializeReportError):
    def __init__(self, message) -> None:
        super().__init__(message)
