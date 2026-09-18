from __future__ import annotations

from dataclasses import dataclass


class Formula:
    """
    Base class for all FlakePL formulas.

    Formula objects form an immutable abstract syntax tree.

    Boolean composition:

        phi & psi
        phi | psi
        ~phi

    Derived operators:

        phi.implies(psi)
        phi.iff(psi)
    """

    def __and__(
        self,
        other: "Formula",
    ) -> "Formula":
        return And(
            self,
            other,
        )

    def __or__(
        self,
        other: "Formula",
    ) -> "Formula":
        return Or(
            self,
            other,
        )

    def __invert__(self) -> "Formula":
        return Not(
            self
        )

    def implies(
        self,
        other: "Formula",
    ) -> "Formula":
        """
        Logical implication:

            φ → ψ

        represented as:

            ¬φ ∨ ψ
        """

        return Or(
            Not(self),
            other,
        )

    def iff(
        self,
        other: "Formula",
    ) -> "Formula":
        """
        Logical equivalence:

            φ ↔ ψ
        """

        return And(
            self.implies(other),
            other.implies(self),
        )


def implies(
    left: Formula,
    right: Formula,
) -> Formula:
    """
    Functional form of implication.
    """

    return left.implies(
        right
    )


def iff(
    left: Formula,
    right: Formula,
) -> Formula:
    """
    Functional form of logical equivalence.
    """

    return left.iff(
        right
    )


@dataclass(frozen=True, slots=True)
class Atom(Formula):
    """
    Atomic proposition.

    Example:

        Atom("ready")
    """

    name: str

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError(
                "Atom name must not be empty"
            )

    def __repr__(self) -> str:
        return self.name


@dataclass(frozen=True, slots=True)
class Not(Formula):
    """
    Boolean negation.
    """

    operand: Formula

    def __repr__(self) -> str:
        return (
            f"¬({self.operand!r})"
        )


@dataclass(frozen=True, slots=True)
class And(Formula):
    """
    Boolean conjunction.
    """

    left: Formula
    right: Formula

    def __repr__(self) -> str:
        return (
            f"({self.left!r} ∧ "
            f"{self.right!r})"
        )


@dataclass(frozen=True, slots=True)
class Or(Formula):
    """
    Boolean disjunction.
    """

    left: Formula
    right: Formula

    def __repr__(self) -> str:
        return (
            f"({self.left!r} ∨ "
            f"{self.right!r})"
        )