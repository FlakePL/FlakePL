from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .runtime import Configuration


Predicate = Callable[[Configuration], bool]


@dataclass(frozen=True, slots=True)
class Proposition:
    """
    Semantic proposition over a system configuration.

    A proposition consists of:

        name
        predicate(Configuration) -> bool
    """

    name: str
    predicate: Predicate

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError(
                "Proposition name cannot be empty"
            )

    def holds(
        self,
        configuration: Configuration,
    ) -> bool:
        """
        Check whether the proposition is true
        in a configuration.
        """

        return bool(
            self.predicate(configuration)
        )

    def __repr__(self) -> str:
        return self.name