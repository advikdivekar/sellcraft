class AppError(Exception):
    """Error safe to show to the user (no secrets, no raw prompts)."""

    def __init__(self, code: str, message: str, *, retryable: bool = False, status: int = 400):
        super().__init__(message)
        self.code, self.message, self.retryable, self.status = code, message, retryable, status
