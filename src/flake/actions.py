from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class Tau:
    """
    Internal action.

    Represents:
        τ
    """


@dataclass(frozen=True, slots=True)
class Send:
    """
    Output action:

        channel!value
    """

    channel: str
    value: Any


@dataclass(frozen=True, slots=True)
class Receive:
    """
    Input action:

        channel?variable
    """

    channel: str
    variable: str


Action = Tau | Send | Receive