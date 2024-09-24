class ModerationResult:
    """A class-based solution for returning HaSpDe's moderation results.

    The result is by default an integer representing the following levels:
    
    - ACCEPT: 0
    - HIDE: 1
    - REMOVE: 2
    - BAN: 3
    - HUMAN_REVIEW: 4
    
    Usage:
        - ModerationResult(ModerationResult.ACCEPT) -> returns a ModerationResult with ACCEPT (0) value.
    """

    # Define constants for moderation actions
    ACCEPT = 0
    HIDE = 1
    REMOVE = 2
    BAN = 3
    HUMAN_REVIEW = 4
    
    # Map result codes to readable actions
    RESULT_MAPPING = {
        ACCEPT: "ACCEPT",
        HIDE: "HIDE",
        REMOVE: "REMOVE",
        BAN: "BAN",
        HUMAN_REVIEW: "HUMAN_REVIEW"
    }

    def __init__(self, result: str | int | bool | None = None, is_error: bool | None = False) -> 'ModerationResult':
        # Handle boolean input (True -> ACCEPT, False -> BAN)
        if isinstance(result, bool):
            self.result = self.ACCEPT if result else self.BAN
        # Handle string input and convert it to an int result
        elif isinstance(result, str):
            self.result = next((key for key, value in self.RESULT_MAPPING.items() if value.lower() == result.lower()), None)
        # If result is an int, validate that it's a valid moderation result
        elif isinstance(result, int):
            self.result = result if result in self.RESULT_MAPPING else None
        else:
            self.result = None  # Default to None if input is invalid

        self.is_error = is_error

    def __repr__(self) -> str:
        return f"<ModerationResult(result={self.result}, is_error={self.is_error})>"

    def __str__(self) -> str:
        return f"{self.RESULT_MAPPING.get(self.result, 'UNKNOWN')}"

    def __int__(self) -> int:
        return int(self.result) if isinstance(self.result, int) else -1

    def __call__(self, *args: any, **kwds: any) -> any:
        return self.RESULT_MAPPING.get(self.result, 'UNKNOWN')

    def __bool__(self) -> bool:
        # The result is considered False if there's an error or the result is None
        return not self.is_error and self.result is not None
