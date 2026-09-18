from __future__ import annotations

from dataclasses import dataclass

from .formula import Formula


@dataclass(frozen=True, slots=True)
class Next(Formula):
    """
    X φ

    φ must hold in every immediate next state.
    """

    operand: Formula

    def __repr__(self) -> str:
        return f"X({self.operand!r})"


def X(
    operand: Formula,
) -> Next:
    """
    Factory for X φ.
    """

    return Next(operand)


@dataclass(frozen=True, slots=True)
class Eventually(Formula):
    """
    F φ

    φ must eventually become true on every possible execution.
    """

    operand: Formula

    def __repr__(self) -> str:
        return f"F({self.operand!r})"


def F(
    operand: Formula,
) -> Eventually:
    """
    Factory for F φ.
    """

    return Eventually(operand)


@dataclass(frozen=True, slots=True)
class Always(Formula):
    """
    G φ

    φ must remain true on every possible execution.
    """

    operand: Formula

    def __repr__(self) -> str:
        return f"G({self.operand!r})"


def G(
    operand: Formula,
) -> Always:
    """
    Factory for G φ.
    """

    return Always(operand)


@dataclass(frozen=True, slots=True)
class Until(Formula):
    """
    φ U ψ

    On every possible execution, ψ eventually becomes true,
    and φ remains true until that happens.
    """

    left: Formula
    right: Formula

    def __repr__(self) -> str:
        return (
            f"({self.left!r} U {self.right!r})"
        )


def U(
    left: Formula,
    right: Formula,
) -> Until:
    """
    Factory for φ U ψ.
    """

    return Until(
        left=left,
        right=right,
    )