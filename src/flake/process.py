from __future__ import annotations

from dataclasses import dataclass

from .actions import (
    Action,
    Receive,
    Send,
    Tau,
)


# ============================================================================
# Process nodes
# ============================================================================


@dataclass(frozen=True, slots=True)
class Nil:
    """
    Terminating process.

        0
    """

    def __rshift__(
        self,
        continuation: Process,
    ) -> Process:
        """
        Appending a process after Nil simply returns
        the continuation.

        This makes:

            stop() >> P

        equivalent to:

            P
        """

        return continuation


@dataclass(frozen=True, slots=True)
class Prefix:
    """
    Process prefix:

        action . continuation
    """

    action: Action
    continuation: Process

    def __rshift__(
        self,
        continuation: Process,
    ) -> Process:
        """
        Append a continuation to the END of this process.

        This is deliberately recursive.

        Example:

            send("a", 1)
            >> recv("b", "x")
            >> tau()
            >> stop()

        becomes:

            Prefix(
                send,
                Prefix(
                    recv,
                    Prefix(
                        tau,
                        Nil()
                    )
                )
            )
        """

        return Prefix(
            action=self.action,
            continuation=_append(
                self.continuation,
                continuation,
            ),
        )


@dataclass(frozen=True, slots=True)
class Choice:
    """
    Nondeterministic choice:

        P + Q + ...
    """

    options: tuple[Process, ...]

    def __post_init__(self) -> None:
        if not self.options:
            raise ValueError(
                "Choice requires at least one process"
            )


@dataclass(frozen=True, slots=True)
class Parallel:
    """
    Parallel composition:

        P | Q | ...
    """

    processes: tuple[Process, ...]

    def __post_init__(self) -> None:
        if not self.processes:
            raise ValueError(
                "Parallel requires at least one process"
            )


# ============================================================================
# Process type
# ============================================================================


Process = (
    Nil
    | Prefix
    | Choice
    | Parallel
)


# ============================================================================
# Internal sequence composition
# ============================================================================


def _append(
    process: Process,
    continuation: Process,
) -> Process:
    """
    Append continuation to the terminal position of process.

    Supported sequential structure:

        Nil
        Prefix

    Choice and Parallel are deliberately not rewritten here because
    sequencing after a branching/composed process needs explicit
    process-calculus semantics and should not be guessed implicitly.

    Examples:

        _append(
            Nil(),
            P,
        )
        -> P

        _append(
            Prefix(a, Nil()),
            P,
        )
        -> Prefix(a, P)

        _append(
            Prefix(
                a,
                Prefix(
                    b,
                    Nil(),
                ),
            ),
            P,
        )
        -> Prefix(
               a,
               Prefix(
                   b,
                   P,
               ),
           )
    """

    if isinstance(
        process,
        Nil,
    ):
        return continuation

    if isinstance(
        process,
        Prefix,
    ):
        return Prefix(
            action=process.action,
            continuation=_append(
                process.continuation,
                continuation,
            ),
        )

    raise TypeError(
        "Sequential composition can only append "
        "to Nil or Prefix processes; "
        f"got {type(process).__name__}"
    )


# ============================================================================
# Constructors
# ============================================================================


def stop() -> Nil:
    """
    Construct the terminating process.
    """

    return Nil()


def send(
    channel: str,
    value: object,
) -> Prefix:
    """
    Construct a send prefix.

        send("c", value)
    """

    if not channel.strip():
        raise ValueError(
            "channel must not be empty"
        )

    return Prefix(
        action=Send(
            channel=channel,
            value=value,
        ),
        continuation=Nil(),
    )


def recv(
    channel: str,
    variable: str,
) -> Prefix:
    """
    Construct a receive prefix.

        recv("c", "x")
    """

    if not channel.strip():
        raise ValueError(
            "channel must not be empty"
        )

    if not variable.strip():
        raise ValueError(
            "variable must not be empty"
        )

    return Prefix(
        action=Receive(
            channel=channel,
            variable=variable,
        ),
        continuation=Nil(),
    )


def tau() -> Prefix:
    """
    Construct an internal action.

        tau()
    """

    return Prefix(
        action=Tau(),
        continuation=Nil(),
    )


def choice(
    *processes: Process,
) -> Choice:
    """
    Construct a nondeterministic choice.

        choice(
            send("a", 1),
            send("b", 2),
        )
    """

    if not processes:
        raise ValueError(
            "choice() requires at least one process"
        )

    return Choice(
        options=tuple(processes)
    )


def parallel(
    *processes: Process,
) -> Parallel:
    """
    Construct a parallel composition.

        parallel(
            alice,
            bob,
        )
    """

    if not processes:
        raise ValueError(
            "parallel() requires at least one process"
        )

    return Parallel(
        processes=tuple(processes)
    )