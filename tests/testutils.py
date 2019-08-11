import re


class MatchesPattern:
    """
    Позволяет проверять соответствие строки определенному паттерну при сравнении
    """
    def __init__(self, pat):
        self.pattern = re.compile(pat)

    def __eq__(self, other):
        return bool(self.pattern.match(other))

    def __repr__(self):
        return f"MatchesPattern({self.pattern!r})"