from __future__ import annotations

from dataclasses import dataclass
from typing import (
    Callable,
    Hashable,
    Iterable,
    Mapping,
    Protocol,
)

from .actions import (
    Action,
    Receive,
    Send,
    Tau,
)
from .agent import Agent
from .epistemic import (
    EpistemicModel,
    ProductWorld,
)
from .runtime import (
    Configuration,
    SystemTransition,
)


class TransitionObservation(Protocol):
    """
    Describes what an agent observes about a runtime transition.

    The returned value must be hashable.

    The observation is intentionally separate from the agent's
    ordinary world observation. It describes the event itself.
    """

    def __call__(
        self,
        agent: Agent,
        transition: SystemTransition,
    ) -> Hashable:
        ...


# ============================================================================
# Action observations
# ============================================================================


@dataclass(frozen=True, slots=True)
class ActionObservation:
    """
    Declarative observation of a process-calculus action.

    By default an agent observes:

        action kind
        channel

    but not the payload.

    Examples:

        send("c", "secret")
        -> ("kind", "send"), ("channel", "c")

        recv("c", "x")
        -> ("kind", "receive"), ("channel", "c")

        tau()
        -> ("kind", "tau")
    """

    include_kind: bool = True
    include_channel: bool = True
    include_value: bool = False

    def __call__(
        self,
        agent: Agent,
        transition: SystemTransition,
    ) -> Hashable:
        action = transition.action

        if isinstance(action, Send):
            kind = "send"

        elif isinstance(action, Receive):
            kind = "receive"

        elif isinstance(action, Tau):
            kind = "tau"

        else:
            kind = type(action).__name__.lower()

        parts: list[tuple[str, Hashable]] = []

        if self.include_kind:
            parts.append(
                (
                    "kind",
                    kind,
                )
            )

        if self.include_channel and isinstance(
            action,
            (
                Send,
                Receive,
            ),
        ):
            parts.append(
                (
                    "channel",
                    action.channel,
                )
            )

        if self.include_value:
            if isinstance(
                action,
                Send,
            ):
                parts.append(
                    (
                        "value",
                        action.value,
                    )
                )

            elif isinstance(
                action,
                Receive,
            ):
                parts.append(
                    (
                        "variable",
                        action.variable,
                    )
                )

        result = tuple(parts)

        hash(result)

        return result


def observe_action(
    *,
    kind: bool = True,
    channel: bool = True,
    value: bool = False,
) -> ActionObservation:
    """
    Create an action observation policy.

    Example:

        observe_action(
            kind=True,
            channel=True,
            value=False,
        )
    """

    return ActionObservation(
        include_kind=kind,
        include_channel=channel,
        include_value=value,
    )


@dataclass(frozen=True, slots=True)
class BlindActionObservation:
    """
    Observation policy where the agent cannot distinguish
    runtime actions based on the event itself.

    Information may still be obtained from the resulting world.
    """

    def __call__(
        self,
        agent: Agent,
        transition: SystemTransition,
    ) -> Hashable:
        return (
            "blind",
        )


def blind_action() -> BlindActionObservation:
    """
    Construct a completely blind action observation.
    """

    return BlindActionObservation()


# ============================================================================
# Observation mapping
# ============================================================================


EventObservationMap = Mapping[
    str | Agent,
    TransitionObservation,
]


def _normalize_event_observations(
    observations: (
        EventObservationMap
        | TransitionObservation
        | None
    ),
    agent_names: Iterable[str],
) -> dict[
    str,
    TransitionObservation,
]:
    names = tuple(agent_names)

    if observations is None:
        default = observe_action()

        return {
            name: default
            for name in names
        }

    if callable(observations) and not isinstance(
        observations,
        Mapping,
    ):
        return {
            name: observations
            for name in names
        }

    if not isinstance(
        observations,
        Mapping,
    ):
        raise TypeError(
            "Event observations must be a mapping, "
            "callable, or None"
        )

    result: dict[
        str,
        TransitionObservation,
    ] = {}

    for key, observation in observations.items():
        name = (
            key.name
            if isinstance(
                key,
                Agent,
            )
            else key
        )

        if not isinstance(
            name,
            str,
        ):
            raise TypeError(
                "Event observation keys must be "
                "strings or Agent objects"
            )

        name = name.strip()

        if not name:
            raise ValueError(
                "Event observation agent name "
                "must not be empty"
            )

        if not callable(observation):
            raise TypeError(
                f"Event observation for {name!r} "
                f"must be callable"
            )

        result[name] = observation

    expected = set(names)
    actual = set(result)

    missing = expected - actual
    extra = actual - expected

    if missing:
        missing_text = ", ".join(
            sorted(missing)
        )

        raise ValueError(
            f"Missing event observations for agents: "
            f"{missing_text}"
        )

    if extra:
        extra_text = ", ".join(
            sorted(extra)
        )

        raise ValueError(
            f"Event observations defined for unknown "
            f"agents: {extra_text}"
        )

    return result


# ============================================================================
# Helpers
# ============================================================================


def _observe_configuration(
    model: EpistemicModel,
    agent_name: str,
    configuration: Configuration,
) -> Hashable:
    """
    Evaluate an ordinary world observation on an arbitrary
    Configuration.

    This is used for successor states that do not yet belong
    to the old epistemic model.
    """

    runtime_agent = configuration.agent(
        agent_name
    )

    value = model._observations[
        agent_name
    ](
        runtime_agent,
        configuration,
    )

    hash(value)

    return value


def _action_kind(
    action: Action,
) -> str:
    if isinstance(
        action,
        Send,
    ):
        return "send"

    if isinstance(
        action,
        Receive,
    ):
        return "receive"

    if isinstance(
        action,
        Tau,
    ):
        return "tau"

    return type(action).__name__.lower()


def _event_name(
    transition_index: int,
    transition: SystemTransition,
) -> str:
    """
    Produce a stable human-readable event identifier.

    The transition index makes otherwise identical transitions
    distinguishable.
    """

    return (
        f"transition:"
        f"{transition_index}:"
        f"{_action_kind(transition.action)}"
    )


# ============================================================================
# Process execution event
# ============================================================================


@dataclass(frozen=True, slots=True)
class ProcessExecutionEvent:
    """
    Dynamic epistemic event generated from an actual
    process-calculus transition.

    This is the bridge between:

        Process calculus
                ↓
        runtime transition
                ↓
        epistemic update

    The resulting epistemic worlds are ProductWorld objects:

        ProductWorld(
            world=target_configuration,
            event=transition_id,
        )

    The event relation combines:

        1. source-world epistemic indistinguishability
        2. event indistinguishability
        3. target-world observations
    """

    transition: SystemTransition

    observations: (
        EventObservationMap
        | TransitionObservation
        | None
    ) = None

    def apply(
        self,
        model: EpistemicModel,
    ) -> EpistemicModel:
        return _apply_process_execution(
            model=model,
            transition=self.transition,
            observations=self.observations,
        )

    def __repr__(self) -> str:
        return (
            f"ProcessExecutionEvent("
            f"action={self.transition.action!r}, "
            f"source={self.transition.source!r}, "
            f"target={self.transition.target!r}"
            f")"
        )


# ============================================================================
# Execution
# ============================================================================


def execute_transition(
    transition: SystemTransition,
    observations: (
        EventObservationMap
        | TransitionObservation
        | None
    ) = None,
) -> ProcessExecutionEvent:
    """
    Convert a runtime SystemTransition into a dynamic event.

    Example:

        event = execute_transition(
            communication,
        )

        updated = model.update(event)
    """

    return ProcessExecutionEvent(
        transition=transition,
        observations=observations,
    )


def execute(
    model: EpistemicModel,
    transition: SystemTransition,
    observations: (
        EventObservationMap
        | TransitionObservation
        | None
    ) = None,
) -> EpistemicModel:
    """
    Execute a process-calculus transition and update
    the epistemic model.

    Equivalent to:

        model.update(
            execute_transition(
                transition,
                observations,
            )
        )
    """

    return model.update(
        execute_transition(
            transition,
            observations,
        )
    )


def step(
    model: EpistemicModel,
    transition: SystemTransition,
    observations: (
        EventObservationMap
        | TransitionObservation
        | None
    ) = None,
) -> EpistemicModel:
    """
    Short alias for execute().
    """

    return execute(
        model,
        transition,
        observations,
    )


# ============================================================================
# Internal implementation
# ============================================================================


def _apply_process_execution(
    model: EpistemicModel,
    transition: SystemTransition,
    observations: (
        EventObservationMap
        | TransitionObservation
        | None
    ),
) -> EpistemicModel:
    if model.state_space is None:
        raise ValueError(
            "Process execution requires an attached StateSpace"
        )

    if not isinstance(
        model.actual,
        Configuration,
    ):
        raise ValueError(
            "Process execution currently requires "
            "a Configuration as the actual world"
        )

    transitions = tuple(
        model.state_space.transitions
    )

    try:
        actual_index = transitions.index(
            transition
        )
    except ValueError as exc:
        raise ValueError(
            "The transition does not belong "
            "to the model StateSpace"
        ) from exc

    if transition.source != model.actual:
        raise ValueError(
            "The executed transition must start "
            "at the actual world"
        )

    event_observations = (
        _normalize_event_observations(
            observations,
            model._agent_names,
        )
    )

    actual_source = transition.source
    actual_target = transition.target

    # ---------------------------------------------------------------------
    # Generate candidate histories.
    #
    # A transition can remain possible for at least one agent when:
    #
    #   source is epistemically possible
    #   AND
    #   event is observationally equivalent
    #   AND
    #   resulting observation is equivalent
    #
    # ---------------------------------------------------------------------

    candidates: list[
        tuple[
            int,
            SystemTransition,
        ]
    ] = []

    for index, candidate in enumerate(
        transitions
    ):
        # Only transitions whose source is itself
        # an epistemically possible current world matter.
        if candidate.source not in model.worlds:
            continue

        possible_for_some_agent = False

        for agent_name in model._agent_names:
            source_accessible = model.accessible(
                agent_name,
                actual_source,
            )

            if candidate.source not in source_accessible:
                continue

            actual_event_observation = (
                event_observations[
                    agent_name
                ](
                    actual_source.agent(
                        agent_name
                    ),
                    transition,
                )
            )

            candidate_event_observation = (
                event_observations[
                    agent_name
                ](
                    candidate.source.agent(
                        agent_name
                    ),
                    candidate,
                )
            )

            hash(actual_event_observation)
            hash(candidate_event_observation)

            if (
                actual_event_observation
                != candidate_event_observation
            ):
                continue

            actual_target_observation = (
                _observe_configuration(
                    model,
                    agent_name,
                    actual_target,
                )
            )

            candidate_target_observation = (
                _observe_configuration(
                    model,
                    agent_name,
                    candidate.target,
                )
            )

            if (
                actual_target_observation
                != candidate_target_observation
            ):
                continue

            possible_for_some_agent = True
            break

        if possible_for_some_agent:
            candidates.append(
                (
                    index,
                    candidate,
                )
            )

    actual_candidate = next(
        (
            item
            for item in candidates
            if item[0] == actual_index
        ),
        None,
    )

    if actual_candidate is None:
        raise ValueError(
            "The actual transition is not "
            "epistemically executable"
        )

    # ---------------------------------------------------------------------
    # Materialize ProductWorld histories.
    # ---------------------------------------------------------------------

    product_worlds: list[
        ProductWorld
    ] = []

    by_index: dict[
        int,
        ProductWorld,
    ] = {}

    transition_by_index: dict[
        int,
        SystemTransition,
    ] = {}

    for index, candidate in candidates:
        product = ProductWorld(
            world=candidate.target,
            event=_event_name(
                index,
                candidate,
            ),
        )

        product_worlds.append(
            product
        )

        by_index[index] = product
        transition_by_index[index] = candidate

    product_worlds_tuple = tuple(
        product_worlds
    )

    actual_product = by_index[
        actual_index
    ]

    # ---------------------------------------------------------------------
    # Build post-event epistemic relations.
    # ---------------------------------------------------------------------

    relation_overrides: dict[
        str,
        dict[
            ProductWorld,
            tuple[
                ProductWorld,
                ...,
            ],
        ],
    ] = {}

    for agent_name in model._agent_names:
        source_map: dict[
            ProductWorld,
            tuple[
                ProductWorld,
                ...,
            ],
        ] = {}

        for source_index, source_candidate in (
            transition_by_index.items()
        ):
            source_product = by_index[
                source_index
            ]

            source_accessible = set(
                model.accessible(
                    agent_name,
                    source_candidate.source,
                )
            )

            source_event_observation = (
                event_observations[
                    agent_name
                ](
                    source_candidate.source.agent(
                        agent_name
                    ),
                    source_candidate,
                )
            )

            hash(
                source_event_observation
            )

            source_target_observation = (
                _observe_configuration(
                    model,
                    agent_name,
                    source_candidate.target,
                )
            )

            targets: list[
                ProductWorld
            ] = []

            for candidate_index, candidate in (
                transition_by_index.items()
            ):
                if (
                    candidate.source
                    not in source_accessible
                ):
                    continue

                candidate_event_observation = (
                    event_observations[
                        agent_name
                    ](
                        candidate.source.agent(
                            agent_name
                        ),
                        candidate,
                    )
                )

                if (
                    candidate_event_observation
                    != source_event_observation
                ):
                    continue

                candidate_target_observation = (
                    _observe_configuration(
                        model,
                        agent_name,
                        candidate.target,
                    )
                )

                if (
                    candidate_target_observation
                    != source_target_observation
                ):
                    continue

                target_product = by_index[
                    candidate_index
                ]

                if target_product not in targets:
                    targets.append(
                        target_product
                    )

            source_map[
                source_product
            ] = tuple(
                targets
            )

        relation_overrides[
            agent_name
        ] = source_map

    return EpistemicModel(
        worlds=product_worlds_tuple,
        observations=model._observations,
        actual=actual_product,
        propositions=model._propositions,
        state_space=None,
        relations=relation_overrides,
    )