"""
Counterexample-driven verification helpers for FlakePL.

The verifier operates on an EpistemicModel backed by a finite StateSpace.
It deliberately keeps the model semantics in ``flake.epistemic`` and only
adds diagnostics on top of it:

    Formula -> model checking -> shortest/finite counterexample trace

The trace representation also supports lasso-shaped counterexamples for
liveness properties such as F(phi).
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Callable

from .actions import Action
from .epistemic import EpistemicModel, World
from .formula import Formula
from .runtime import Configuration
from .explorer import StateSpace
from .temporal import Always, Eventually, Next


__all__ = [
    "Trace",
    "VerificationResult",
    "find_path_to",
    "find_state_counterexample",
    "find_next_counterexample",
    "find_always_counterexample",
    "find_eventually_counterexample",
    "verify_always",
    "verify_eventually",
    "verify",
    "format_trace",
    "format_verification",
]


@dataclass(frozen=True, slots=True)
class Trace:
    """
    A finite execution trace.

    ``worlds`` contains the visited configurations/worlds.

    Normally ``actions`` contains exactly ``len(worlds) - 1`` actions.

    For an eventually-property counterexample, ``cycle_start`` marks the
    beginning of the repeated suffix. The final world may equal the world at
    ``cycle_start`` when the cycle is closed by an explicit transition.

    A terminal state with implicit temporal stuttering may instead be
    represented by ending on the terminal world and setting ``cycle_start``
    to its index.
    """

    worlds: tuple[World, ...]
    actions: tuple[Action | None, ...] = ()
    cycle_start: int | None = None

    def __post_init__(self) -> None:
        if not self.worlds:
            raise ValueError(
                "A trace must contain at least one world"
            )

        if len(self.actions) > len(self.worlds) - 1:
            raise ValueError(
                "A trace cannot contain more actions than "
                "world-to-world steps"
            )

        if self.cycle_start is not None and not (
            0 <= self.cycle_start < len(self.worlds)
        ):
            raise ValueError(
                "cycle_start must reference a world in the trace"
            )

    @property
    def initial(self) -> World:
        return self.worlds[0]

    @property
    def final(self) -> World:
        return self.worlds[-1]

    @property
    def is_lasso(self) -> bool:
        return self.cycle_start is not None

    @property
    def is_cyclic(self) -> bool:
        """Compatibility alias for lasso/cyclic traces."""

        return self.is_lasso

    @property
    def states(self) -> tuple[World, ...]:
        """
        Compatibility alias for callers that use the word 'states'.
        """
        return self.worlds


@dataclass(frozen=True, slots=True)
class VerificationResult:
    """
    Result of model checking.

    When ``holds`` is false and a witness can be constructed,
    ``counterexample`` contains it.
    """

    formula: Formula
    holds: bool
    counterexample: Trace | None = None

    @property
    def failed(self) -> bool:
        return not self.holds

    @property
    def passed(self) -> bool:
        return self.holds

    def __bool__(self) -> bool:
        return self.holds


Predicate = Callable[[World], bool]


def _require_state_space(
    model: EpistemicModel,
) -> StateSpace:
    """
    Return the model's state space or fail with a useful error.
    """

    state_space = getattr(
        model,
        "_state_space",
        None,
    )

    if state_space is None:
        raise ValueError(
            "Counterexample search requires an "
            "EpistemicModel backed by a StateSpace"
        )

    return state_space


def _actual_start(
    model: EpistemicModel,
    state_space: StateSpace,
) -> World:
    actual = model.actual

    if actual not in state_space.states:
        raise ValueError(
            "The model's actual world is not present "
            "in its StateSpace"
        )

    return actual


def _explicit_edges(
    state_space: StateSpace,
) -> dict[
    World,
    tuple[tuple[World, Action], ...],
]:
    """
    Build deterministic explicit transition adjacency.
    """

    result: dict[
        World,
        list[tuple[World, Action]],
    ] = {
        world: []
        for world in state_space.states
    }

    for transition in state_space.transitions:
        result.setdefault(
            transition.source,
            [],
        ).append(
            (
                transition.target,
                transition.action,
            )
        )

    return {
        world: tuple(edges)
        for world, edges in result.items()
    }


def _outgoing(
    state_space: StateSpace,
    world: World,
    edges: dict[
        World,
        tuple[tuple[World, Action], ...],
    ],
) -> tuple[
    tuple[World, Action | None],
    ...,
]:
    """
    Return explicit successors plus implicit temporal stuttering at terminals.

    ``EpistemicModel.successors`` uses the same convention for finite models:
    a terminal state has itself as its temporal successor.
    No action is attached to this implicit stuttering step.
    """

    explicit = edges.get(
        world,
        (),
    )

    if explicit:
        return tuple(
            (
                target,
                action,
            )
            for target, action in explicit
        )

    return (
        (
            world,
            None,
        ),
    )


def _reconstruct_trace(
    parent: dict[
        World,
        tuple[World, Action] | None,
    ],
    target: World,
) -> Trace:
    worlds_rev: list[World] = [
        target,
    ]

    actions_rev: list[Action] = []

    current = target

    while parent[current] is not None:
        previous, action = parent[current]

        worlds_rev.append(previous)
        actions_rev.append(action)

        current = previous

    worlds = tuple(
        reversed(worlds_rev)
    )

    actions = tuple(
        reversed(actions_rev)
    )

    return Trace(
        worlds=worlds,
        actions=actions,
    )


def _holds(
    model: EpistemicModel,
    formula: Formula,
    world: World,
) -> bool:
    return bool(
        model.check(
            formula,
            at=world,
        )
    )


def find_path_to(
    model: EpistemicModel,
    formula: Formula,
    *,
    predicate: Predicate | None = None,
) -> Trace | None:
    """
    Find the shortest reachable path to a world satisfying ``formula``.

    A custom ``predicate`` can be supplied when the caller wants to search a
    semantic condition that is not itself a Formula.
    """

    state_space = _require_state_space(model)

    edges = _explicit_edges(
        state_space
    )

    start = _actual_start(
        model,
        state_space,
    )

    if predicate is None:
        predicate = (
            lambda world: _holds(
                model,
                formula,
                world,
            )
        )

    queue: deque[World] = deque(
        [start]
    )

    parent: dict[
        World,
        tuple[World, Action] | None,
    ] = {
        start: None
    }

    while queue:
        world = queue.popleft()

        if predicate(world):
            return _reconstruct_trace(
                parent,
                world,
            )

        for target, action in _outgoing(
            state_space,
            world,
            edges,
        ):
            if action is None and target == world:
                continue

            if target in parent:
                continue

            parent[target] = (
                world,
                action,
            )

            queue.append(target)

    return None


def find_state_counterexample(
    model: EpistemicModel,
    formula: Formula,
) -> Trace | None:
    """
    Find a shortest reachable trace ending in a world that falsifies
    ``formula``.

    This is the generic state-level counterexample finder.
    """

    state_space = _require_state_space(model)

    edges = _explicit_edges(
        state_space
    )

    start = _actual_start(
        model,
        state_space,
    )

    if not _holds(
        model,
        formula,
        start,
    ):
        return Trace(
            (start,)
        )

    queue: deque[World] = deque(
        [start]
    )

    parent: dict[
        World,
        tuple[World, Action] | None,
    ] = {
        start: None
    }

    while queue:
        world = queue.popleft()

        for target, action in _outgoing(
            state_space,
            world,
            edges,
        ):
            if action is None and target == world:
                continue

            if target in parent:
                continue

            parent[target] = (
                world,
                action,
            )

            queue.append(target)

            if not _holds(
                model,
                formula,
                target,
            ):
                return _reconstruct_trace(
                    parent,
                    target,
                )

    return None


def find_next_counterexample(
    model: EpistemicModel,
    formula: Formula,
) -> Trace | None:
    """
    Find a one-step counterexample for X(formula).
    """

    state_space = _require_state_space(model)

    edges = _explicit_edges(
        state_space
    )

    start = _actual_start(
        model,
        state_space,
    )

    successors = _outgoing(
        state_space,
        start,
        edges,
    )

    for target, action in successors:
        if _holds(
            model,
            formula,
            target,
        ):
            continue

        if action is None:
            return Trace(
                (start,)
            )

        return Trace(
            (
                start,
                target,
            ),
            actions=(
                action,
            ),
        )

    return None


def find_always_counterexample(
    model: EpistemicModel,
    formula: Formula,
) -> Trace | None:
    """
    Find a finite prefix witnessing a violation of G(formula).

    ``formula`` may be either the operand itself or an ``Always`` instance.
    """

    operand = (
        formula.operand
        if isinstance(
            formula,
            Always,
        )
        else formula
    )

    state_space = _require_state_space(
        model
    )

    edges = _explicit_edges(
        state_space
    )

    start = _actual_start(
        model,
        state_space,
    )

    if not _holds(
        model,
        operand,
        start,
    ):
        return Trace(
            (start,)
        )

    queue: deque[World] = deque(
        [start]
    )

    parent: dict[
        World,
        tuple[World, Action] | None,
    ] = {
        start: None
    }

    while queue:
        world = queue.popleft()

        for target, action in _outgoing(
            state_space,
            world,
            edges,
        ):
            if action is None and target == world:
                continue

            if target in parent:
                continue

            parent[target] = (
                world,
                action,
            )

            if not _holds(
                model,
                operand,
                target,
            ):
                return _reconstruct_trace(
                    parent,
                    target,
                )

            queue.append(target)

    return None


def _dfs_eventual_counterexample(
    model: EpistemicModel,
    operand: Formula,
    state_space: StateSpace,
    edges: dict[
        World,
        tuple[tuple[World, Action], ...],
    ],
    start: World,
) -> Trace | None:
    """
    DFS over states where ``operand`` is false.

    A counterexample to F(phi) is a path that remains forever in
    not-phi states.

    Because the transition graph is finite, such a path yields either:

    1. a repeated state, giving a lasso, or
    2. a terminal state, which uses implicit stuttering.
    """

    if _holds(
        model,
        operand,
        start,
    ):
        return None

    stack: list[World] = [
        start
    ]

    stack_actions: list[Action] = []

    on_stack: dict[
        World,
        int,
    ] = {
        start: 0,
    }

    visited: set[World] = {
        start,
    }

    def dfs(
        world: World,
    ) -> Trace | None:
        outgoing = _outgoing(
            state_space,
            world,
            edges,
        )

        for target, action in outgoing:
            if action is None and target == world:
                cycle_index = on_stack[
                    world
                ]

                return Trace(
                    worlds=tuple(
                        stack + [world]
                    ),
                    actions=tuple(
                        stack_actions + [None]
                    ),
                    cycle_start=cycle_index,
                )

            if _holds(
                model,
                operand,
                target,
            ):
                continue

            if target in on_stack:
                cycle_index = on_stack[
                    target
                ]

                worlds = tuple(
                    stack + [target]
                )

                actions = tuple(
                    stack_actions + [action]
                )

                return Trace(
                    worlds=worlds,
                    actions=actions,
                    cycle_start=cycle_index,
                )

            if target in visited:
                continue

            visited.add(target)

            on_stack[target] = len(
                stack
            )

            stack.append(target)

            stack_actions.append(
                action
            )

            result = dfs(
                target
            )

            if result is not None:
                return result

            stack_actions.pop()
            stack.pop()

            del on_stack[target]

        return None

    return dfs(
        start
    )


def find_eventually_counterexample(
    model: EpistemicModel,
    formula: Formula,
) -> Trace | None:
    """
    Find a lasso-shaped counterexample to F(formula).
    """

    operand = (
        formula.operand
        if isinstance(
            formula,
            Eventually,
        )
        else formula
    )

    state_space = _require_state_space(
        model
    )

    edges = _explicit_edges(
        state_space
    )

    start = _actual_start(
        model,
        state_space,
    )

    return _dfs_eventual_counterexample(
        model=model,
        operand=operand,
        state_space=state_space,
        edges=edges,
        start=start,
    )


def verify_always(
    model: EpistemicModel,
    formula: Formula,
) -> VerificationResult:
    """
    Verify G(formula) and return a counterexample on failure.
    """

    target = (
        formula
        if isinstance(
            formula,
            Always,
        )
        else Always(formula)
    )

    counterexample = find_always_counterexample(
        model,
        target,
    )

    return VerificationResult(
        formula=target,
        holds=counterexample is None,
        counterexample=counterexample,
    )


def verify_eventually(
    model: EpistemicModel,
    formula: Formula,
) -> VerificationResult:
    """
    Verify F(formula) and return a lasso counterexample on failure.
    """

    target = (
        formula
        if isinstance(
            formula,
            Eventually,
        )
        else Eventually(formula)
    )

    counterexample = find_eventually_counterexample(
        model,
        target,
    )

    return VerificationResult(
        formula=target,
        holds=counterexample is None,
        counterexample=counterexample,
    )


def verify(
    model: EpistemicModel,
    formula: Formula,
) -> VerificationResult:
    """
    Verify a formula using the strongest available counterexample algorithm.

    Specialized temporal handling:

        G(phi) -> finite bad-state prefix
        F(phi) -> lasso that keeps phi false
        X(phi) -> one-step violating prefix

    For other formulas the generic state-level counterexample finder is used.
    """

    if isinstance(
        formula,
        Always,
    ):
        return verify_always(
            model,
            formula,
        )

    if isinstance(
        formula,
        Eventually,
    ):
        return verify_eventually(
            model,
            formula,
        )

    if isinstance(
        formula,
        Next,
    ):
        counterexample = find_next_counterexample(
            model,
            formula.operand,
        )

        return VerificationResult(
            formula=formula,
            holds=counterexample is None,
            counterexample=counterexample,
        )

    counterexample = find_state_counterexample(
        model,
        formula,
    )

    return VerificationResult(
        formula=formula,
        holds=counterexample is None,
        counterexample=counterexample,
    )


def _format_action(
    action: Action | None,
) -> str:
    if action is None:
        return "stutter"

    return repr(action)


def _format_world(
    world: World,
) -> str:
    """
    Produce a compact representation suitable for diagnostics.
    """

    configuration = world
    event = None

    if (
        hasattr(world, "world")
        and isinstance(
            getattr(world, "world"),
            Configuration,
        )
    ):
        configuration = getattr(
            world,
            "world",
        )

        event = getattr(
            world,
            "event",
            None,
        )

    if not isinstance(
        configuration,
        Configuration,
    ):
        return repr(world)

    state = configuration.state.to_dict()

    agent_chunks: list[str] = []

    for agent in configuration.agents:
        process_repr = repr(
            agent.process
        )

        if len(process_repr) > 120:
            process_repr = (
                process_repr[:117]
                + "..."
            )

        local_state = dict(
            agent.state
        )

        agent_chunks.append(
            (
                f"{agent.name}: "
                f"process={process_repr}, "
                f"state={local_state}"
            )
        )

    suffix = (
        f", event={event!r}"
        if event is not None
        else ""
    )

    return (
        "Configuration("
        f"state={state}, "
        "agents=["
        f"{'; '.join(agent_chunks)}"
        "]"
        f"{suffix}"
        ")"
    )


def format_trace(
    trace: Trace,
) -> str:
    """
    Render a trace as a human-readable diagnostic.
    """

    lines: list[str] = [
        "Trace:"
    ]

    for index, world in enumerate(
        trace.worlds
    ):
        marker = (
            " *cycle*"
            if trace.cycle_start == index
            else ""
        )

        lines.append(
            (
                f"  [{index}]"
                f"{marker} "
                f"{_format_world(world)}"
            )
        )

        if index < len(
            trace.actions
        ):
            lines.append(
                (
                    "      -- "
                    f"{_format_action(trace.actions[index])}"
                    " -->"
                )
            )

    if trace.cycle_start is not None:
        implicit_stutter = (
            bool(trace.actions)
            and trace.actions[-1] is None
        )

        if implicit_stutter:
            lines.append(
                (
                    f"  loop: "
                    f"[{len(trace.worlds) - 1}] "
                    f"-> [{trace.cycle_start}] "
                    "(implicit temporal stuttering)"
                )
            )
        elif (
            len(trace.worlds)
            == trace.cycle_start + 1
        ):
            lines.append(
                (
                    f"  loop: "
                    f"[{trace.cycle_start}] "
                    f"-> [{trace.cycle_start}] "
                    "(implicit temporal stuttering)"
                )
            )
        else:
            lines.append(
                (
                    f"  loop: "
                    f"[{len(trace.worlds) - 1}] "
                    f"-> [{trace.cycle_start}]"
                )
            )

    return "\n".join(
        lines
    )


def format_verification(
    result: VerificationResult,
) -> str:
    """
    Render a complete verification result,
    including its counterexample.
    """

    lines = [
        (
            "Verification: "
            f"{'PASS' if result.holds else 'FAIL'}"
        ),
        (
            "Formula: "
            f"{result.formula!r}"
        ),
    ]

    if result.counterexample is None:
        return "\n".join(
            lines
        )

    lines.append(
        "Counterexample:"
    )

    lines.append(
        format_trace(
            result.counterexample
        )
    )

    return "\n".join(
        lines
    )