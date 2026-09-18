from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Callable, Iterable

from .runtime import (
    Configuration,
    SystemTransition,
    system_transitions,
)


TransitionProvider = Callable[
    [Configuration],
    Iterable[SystemTransition],
]


@dataclass(frozen=True, slots=True)
class StateSpace:
    """
    Finite reachable state space.

    initials:
        Initial configurations.

    states:
        All discovered configurations.

    transitions:
        Reachable transitions between configurations.
    """

    initials: tuple[Configuration, ...]
    states: tuple[Configuration, ...]
    transitions: tuple[SystemTransition, ...]

    @property
    def initial(self) -> Configuration:
        """
        Convenience accessor for a single-initial state space.
        """

        if len(self.initials) != 1:
            raise ValueError(
                "StateSpace.initial requires exactly one "
                "initial configuration"
            )

        return self.initials[0]


def _explore_many(
    initials: Iterable[Configuration],
    transition_provider: TransitionProvider,
    max_states: int | None = None,
) -> StateSpace:
    initial_tuple = tuple(
        initials
    )

    if not initial_tuple:
        raise ValueError(
            "At least one initial configuration is required"
        )

    if max_states is not None:
        if max_states <= 0:
            raise ValueError(
                "max_states must be positive"
            )

    visited: set[Configuration] = set(
        initial_tuple
    )

    queue: deque[Configuration] = deque(
        initial_tuple
    )

    transitions_result: list[
        SystemTransition
    ] = []

    while queue:
        current = queue.popleft()

        for transition in transition_provider(
            current
        ):
            transitions_result.append(
                transition
            )

            target = transition.target

            if target in visited:
                continue

            if (
                max_states is not None
                and len(visited) >= max_states
            ):
                continue

            visited.add(
                target
            )

            queue.append(
                target
            )

    states = tuple(
        visited
    )

    return StateSpace(
        initials=initial_tuple,
        states=states,
        transitions=tuple(
            transitions_result
        ),
    )


def explore(
    initial: Configuration,
    max_states: int | None = None,
) -> StateSpace:
    """
    Explore using the default runtime semantics.
    """

    return _explore_many(
        (initial,),
        system_transitions,
        max_states=max_states,
    )


def explore_many(
    initials: Iterable[Configuration],
    max_states: int | None = None,
) -> StateSpace:
    """
    Explore multiple initial configurations using the
    default runtime semantics.
    """

    return _explore_many(
        initials,
        system_transitions,
        max_states=max_states,
    )


def explore_with(
    initial: Configuration,
    transition_provider: TransitionProvider,
    max_states: int | None = None,
) -> StateSpace:
    """
    Explore using explicitly supplied operational semantics.

    Example:

        space = explore_with(
            initial,
            synchronous_system_transitions,
        )
    """

    return _explore_many(
        (initial,),
        transition_provider,
        max_states=max_states,
    )


def explore_many_with(
    initials: Iterable[Configuration],
    transition_provider: TransitionProvider,
    max_states: int | None = None,
) -> StateSpace:
    """
    Explore multiple initial configurations using explicitly
    supplied operational semantics.
    """

    return _explore_many(
        initials,
        transition_provider,
        max_states=max_states,
    )