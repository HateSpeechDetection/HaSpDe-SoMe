class ModerationResult:
    """A class for representing moderation outcomes in HaSpDe.

    Moderation results are represented by the following constants:
    
    - ACCEPT: 0
    - HIDE: 1
    - REMOVE: 2
    - BAN: 3
    - HUMAN_REVIEW: 4

    Example:
        result = ModerationResult(ModerationResult.ACCEPT)  # Creates an instance with ACCEPT (0)
    """

    # Define constants for moderation actions
    ACCEPT = 0
    HIDE = 1
    REMOVE = 2
    BAN = 3
    HUMAN_REVIEW = 4
    
    # Mapping from result codes to descriptive names
    RESULT_MAPPING = {
        ACCEPT: "ACCEPT",
        HIDE: "HIDE",
        REMOVE: "REMOVE",
        BAN: "BAN",
        HUMAN_REVIEW: "HUMAN_REVIEW"
    }

    def __init__(self, result: str | int | bool | None = None, is_error: bool = False):
        """Initialize a ModerationResult instance.

        Args:
            result (str | int | bool | None): The result of moderation.
            is_error (bool): Indicates if there was an error.
        """
        self.result = self._resolve_result(result)
        self.is_error = is_error

    def _resolve_result(self, result: str | int | bool | None) -> int | None:
        """Resolve the provided result into a valid moderation result.

        Args:
            result (str | int | bool | None): The input to resolve.

        Returns:
            int | None: A valid moderation result or None if invalid.
        """
        if isinstance(result, bool):
            return self.ACCEPT if result else self.HIDE  # False now resolves to HIDE
        elif isinstance(result, str):
            return next((key for key, value in self.RESULT_MAPPING.items() if value.lower() == result.lower()), None)
        elif isinstance(result, int) and result in self.RESULT_MAPPING:
            return result
        return None  # Return None for invalid inputs

    def __repr__(self) -> str:
        return f"<ModerationResult(result={self.result}, is_error={self.is_error})>"

    def __str__(self) -> str:
        return self.RESULT_MAPPING.get(self.result, 'UNKNOWN')

    def __int__(self) -> int:
        return int(self.result) if isinstance(self.result, int) else -1

    def __call__(self, *args: any, **kwds: any) -> str:
        """Return the string representation of the result."""
        return self.__str__()

    def __bool__(self) -> bool:
        """Determine the truth value of the result."""
        return not self.is_error and self.result is not None
