from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Hashable, Iterable, Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from .agent import Agent
    from .runtime import Configuration


class Observation(Protocol):
    """
    Describes what an agent can observe in a configuration.

    The returned value must be hashable because observations
    induce epistemic equivalence classes over worlds.
    """

    def __call__(
        self,
        agent: "Agent",
        configuration: "Configuration",
    ) -> Hashable:
        ...


def _normalize_keys(
    keys: str | Iterable[str],
) -> tuple[str, ...]:
    if isinstance(keys, str):
        return (keys,)

    return tuple(keys)


def _ensure_hashable(value: Any) -> Hashable:
    hash(value)
    return value


# ============================================================================
# Declarative observation components
# ============================================================================


@dataclass(frozen=True, slots=True)
class LocalObservation:
    """
    Observation of one particular agent's local information.

    Examples:

        local("bob", state=("x",))

        local("bob", state=("x",), process=True)

    The observation is represented as a tuple of tagged fragments:

        (
            ("state", ...),
            ("process", ...),
        )
    """

    agent_name: str
    state_keys: tuple[str, ...] = ()
    include_process: bool = False

    def __post_init__(self) -> None:
        if not self.agent_name.strip():
            raise ValueError(
                "agent_name must not be empty"
            )

        for key in self.state_keys:
            if not isinstance(key, str) or not key.strip():
                raise ValueError(
                    "state observation keys must be non-empty strings"
                )

    def __call__(
        self,
        agent: "Agent",
        configuration: "Configuration",
    ) -> Hashable:
        if agent.name != self.agent_name:
            raise ValueError(
                f"Local observation for {self.agent_name!r} "
                f"was applied to {agent.name!r}"
            )

        fragments: list[tuple[str, Hashable]] = []

        if self.state_keys:
            local_state = tuple(
                (key, agent.get_state(key))
                for key in self.state_keys
            )

            _ensure_hashable(local_state)

            fragments.append(
                ("state", local_state)
            )

        if self.include_process:
            process = _ensure_hashable(
                agent.process
            )

            fragments.append(
                ("process", process)
            )

        return _ensure_hashable(
            tuple(fragments)
        )


def local(
    agent_name: str,
    *,
    state: str | Iterable[str] = (),
    process: bool = False,
) -> LocalObservation:
    """
    Declare an observation of one agent's local information.

    Example:

        local(
            "bob",
            state=("x",),
            process=True,
        )
    """

    return LocalObservation(
        agent_name=agent_name,
        state_keys=_normalize_keys(state),
        include_process=process,
    )


@dataclass(frozen=True, slots=True)
class GlobalObservation:
    """
    Observation of globally visible information.

    Example:

        public("round")
    """

    keys: tuple[str, ...]

    def __post_init__(self) -> None:
        for key in self.keys:
            if not isinstance(key, str) or not key.strip():
                raise ValueError(
                    "global observation keys must be non-empty strings"
                )

    def __call__(
        self,
        agent: "Agent",
        configuration: "Configuration",
    ) -> Hashable:
        value = tuple(
            (key, configuration.state.get(key))
            for key in self.keys
        )

        _ensure_hashable(value)

        return _ensure_hashable(
            (
                ("global", value),
            )
        )


def global_(
    *keys: str,
) -> GlobalObservation:
    """
    Declare globally observable variables.
    """

    return GlobalObservation(
        tuple(keys)
    )


def public(
    *keys: str,
) -> GlobalObservation:
    """
    Semantic alias for global_().
    """

    return global_(*keys)


# ============================================================================
# Combined observation
# ============================================================================


@dataclass(frozen=True, slots=True)
class _CombinedObservation:
    """
    Composition of declarative observation components.

    Declarative components return tuples of tagged fragments.
    We flatten those fragments here so that:

        local(...) + public(...)

    becomes:

        (
            ("global", ...),
            ("state", ...),
        )

    rather than introducing accidental nested tuples.
    """

    components: tuple[Observation, ...]

    def __call__(
        self,
        agent: "Agent",
        configuration: "Configuration",
    ) -> Hashable:
        fragments: list[Hashable] = []

        for component in self.components:
            value = component(
                agent,
                configuration,
            )

            if isinstance(
                component,
                (
                    LocalObservation,
                    GlobalObservation,
                ),
            ):
                # Both declarative components return
                # tuples of tagged fragments.
                fragments.extend(value)
            else:
                # Preserve arbitrary custom observations.
                fragments.append(
                    (
                        "component",
                        _ensure_hashable(value),
                    )
                )

        return _ensure_hashable(
            tuple(fragments)
        )


@dataclass(frozen=True, slots=True)
class ObservationBuilder:
    """
    Declarative builder for per-agent observations.

    Example:

        observations = (
            ObservationBuilder()
            .for_agent(
                "alice",
                state=("secret",),
            )
            .for_agent(
                "bob",
                state=("x",),
                process=True,
            )
            .public("round")
            .build(("alice", "bob"))
        )
    """

    components: tuple[Observation, ...] = ()

    @classmethod
    def create(
        cls,
        *components: Observation,
    ) -> "ObservationBuilder":
        return cls(
            tuple(components)
        )

    def add(
        self,
        component: Observation,
    ) -> "ObservationBuilder":
        return ObservationBuilder(
            self.components + (component,)
        )

    def for_agent(
        self,
        agent_name: str,
        *,
        state: str | Iterable[str] = (),
        process: bool = False,
    ) -> "ObservationBuilder":
        return self.add(
            local(
                agent_name,
                state=state,
                process=process,
            )
        )

    def global_(
        self,
        *keys: str,
    ) -> "ObservationBuilder":
        return self.add(
            global_(*keys)
        )

    def public(
        self,
        *keys: str,
    ) -> "ObservationBuilder":
        return self.add(
            public(*keys)
        )

    def build(
        self,
        agent_names: Iterable[str],
    ) -> dict[str, Observation]:
        names = tuple(agent_names)

        if not names:
            raise ValueError(
                "ObservationBuilder requires at least one agent"
            )

        if len(names) != len(set(names)):
            raise ValueError(
                "agent_names must be unique"
            )

        global_components: list[Observation] = []

        local_components: dict[
            str,
            list[Observation],
        ] = {
            name: []
            for name in names
        }

        for component in self.components:
            if isinstance(
                component,
                LocalObservation,
            ):
                if component.agent_name not in local_components:
                    raise ValueError(
                        f"Unknown agent "
                        f"{component.agent_name!r} "
                        f"in observation builder"
                    )

                local_components[
                    component.agent_name
                ].append(component)

            else:
                global_components.append(
                    component
                )

        result: dict[str, Observation] = {}

        for name in names:
            components = tuple(
                global_components
                + local_components[name]
            )

            if not components:
                raise ValueError(
                    f"No observation defined for agent {name!r}"
                )

            result[name] = _CombinedObservation(
                components
            )

        return result


# ============================================================================
# Compatibility helpers
# ============================================================================


def same_observation(
    agent: "Agent",
    first: "Configuration",
    second: "Configuration",
    observation: Observation,
) -> bool:
    return (
        observation(agent, first)
        == observation(agent, second)
    )


def observe_global(
    *keys: str,
) -> Observation:
    """
    Backward-compatible global observation.

    No keys means an empty public observation.
    """

    def observation(
        agent: "Agent",
        configuration: "Configuration",
    ) -> Hashable:
        value = tuple(
            (key, configuration.state.get(key))
            for key in keys
        )

        return _ensure_hashable(value)

    return observation


def observe_local_state(
    *keys: str,
) -> Observation:
    """
    Backward-compatible local-state observation.

    With explicit keys:

        observe_local_state("x", "y")

    observes exactly those variables.

    Without keys:

        observe_local_state()

    observes the complete local agent state.
    """

    def observation(
        agent: "Agent",
        configuration: "Configuration",
    ) -> Hashable:
        if keys:
            value = tuple(
                (key, agent.get_state(key))
                for key in keys
            )

        else:
            # Agent.state is already a canonical immutable tuple.
            value = tuple(agent.state)

        return _ensure_hashable(value)

    return observation


def observe_local_process() -> Observation:
    """
    Backward-compatible process observation.
    """

    def observation(
        agent: "Agent",
        configuration: "Configuration",
    ) -> Hashable:
        return _ensure_hashable(
            agent.process
        )

    return observation