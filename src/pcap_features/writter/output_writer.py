from typing import Protocol


class OutputWriter(Protocol):
    def write(self, data: dict) -> None:
        raise NotImplementedError