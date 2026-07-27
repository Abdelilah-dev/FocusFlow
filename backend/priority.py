class Priority:
    VALID_PRIORITIES = {"High", "Medium", "Low"}

    def __init__(self, priority: str = "Medium"):
        self.priority = self._normalize(priority)

    def _normalize(self, value: str) -> str:
        clean = str(value).strip().title()
        if clean in self.VALID_PRIORITIES:
            return clean
        return "Medium"

    @property
    def priority(self) -> str:
        return self._priority

    @priority.setter
    def priority(self, value: str):
        self._priority = self._normalize(value)

    def __str__(self) -> str:
        return self._priority

    def __repr__(self) -> str:
        return f"Priority(priority='{self._priority}')"

    def __eq__(self, other) -> bool:
        if isinstance(other, Priority):
            return self._priority == other._priority
        if isinstance(other, str):
            return self._priority == self._normalize(other)
        return False

    def __hash__(self) -> int:
        return hash(self._priority)