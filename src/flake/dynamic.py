from __future__ import annotations

from dataclasses import dataclass
from typing import (
    Iterable,
    Mapping,
    Protocol,
    TYPE_CHECKING,
)

from .formula import Formula

if TYPE_CHECKING:
    from .epistemic import EpistemicModel


class DynamicEvent(Protocol):
    """
    Dynamic epistemic event.

    Applying an event creates a new epistemic model.
    """

    def apply(
        self,
        model: "EpistemicModel",
    ) -> "EpistemicModel":
        ...


# ============================================================================
# Public announcement
# ============================================================================


@dataclass(frozen=True, slots=True)
class PublicAnnouncement:
    """
    Public Announcement Logic event.

    Every world where the formula is false is removed.

    The original model is never mutated.
    """

    formula: Formula

    def apply(
        self,
        model: "EpistemicModel",
    ) -> "EpistemicModel":
        return model._apply_public_announcement(
            self.formula
        )

    def __repr__(self) -> str:
        return (
            f"PublicAnnouncement({self.formula!r})"
        )


def announce(
    formula: Formula,
) -> PublicAnnouncement:
    """
    Construct a public announcement.

    Example:

        model2 = model.update(
            announce(p)
        )
    """

    return PublicAnnouncement(
        formula
    )


def public_announcement(
    formula: Formula,
) -> PublicAnnouncement:
    """
    Explicit alias for announce().
    """

    return announce(formula)


# ============================================================================
# Action events
# ============================================================================


@dataclass(frozen=True, slots=True)
class ActionEvent:
    """
    One event point of an epistemic action model.

    name:
        Event identifier.

    precondition:
        Formula that must hold for the event to be executable.

        None means that the event is executable in every world.
    """

    name: str
    precondition: Formula | None = None

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError(
                "ActionEvent name must not be empty"
            )

    def enabled(
        self,
        model: "EpistemicModel",
        world,
    ) -> bool:
        """
        Check whether this event is executable at a world.
        """

        if self.precondition is None:
            return True

        return model.check(
            self.precondition,
            at=world,
        )

    def __repr__(self) -> str:
        if self.precondition is None:
            return (
                f"ActionEvent({self.name!r})"
            )

        return (
            f"ActionEvent("
            f"{self.name!r}, "
            f"precondition={self.precondition!r}"
            f")"
        )


def event(
    name: str,
    precondition: Formula | None = None,
) -> ActionEvent:
    """
    Construct an action-model event.

    Examples:

        event("learn", K("alice", p))

        event("noop")
    """

    return ActionEvent(
        name=name,
        precondition=precondition,
    )


def action_event(
    name: str,
    precondition: Formula | None = None,
) -> ActionEvent:
    """
    Explicit alias for event().
    """

    return event(
        name,
        precondition,
    )


# ============================================================================
# Action model
# ============================================================================


@dataclass(slots=True)
class ActionModel:
    """
    Finite epistemic action model.

    An ActionModel contains:

        events
        preconditions
        actual event
        event indistinguishability relations

    relations:

        relations[agent][event] = events that agent
        considers possible after observing that event.

    If no relation is supplied for an agent, all events are
    considered indistinguishable for that agent.

    Example:

        action_model = ActionModel(
            events=(
                event("learn", p),
                event("noop", ~p),
            ),
            actual="learn",
            relations={
                "alice": {
                    "learn": {"learn"},
                    "noop": {"noop"},
                },
                "bob": {
                    "learn": {"learn", "noop"},
                    "noop": {"learn", "noop"},
                },
            },
        )
    """

    events: tuple[ActionEvent, ...]
    actual: str
    relations: (
        Mapping[
            str,
            Mapping[
                str,
                Iterable[str],
            ],
        ]
        | None
    ) = None

    def __post_init__(self) -> None:
        self.events = tuple(
            self.events
        )

        if not self.events:
            raise ValueError(
                "ActionModel requires at least one event"
            )

        names = [
            item.name
            for item in self.events
        ]

        if len(names) != len(set(names)):
            raise ValueError(
                "ActionEvent names must be unique"
            )

        if self.actual not in names:
            raise ValueError(
                f"Unknown actual event {self.actual!r}"
            )

        event_names = set(names)

        normalized: dict[
            str,
            dict[
                str,
                frozenset[str],
            ],
        ] = {}

        if self.relations is not None:
            for agent, relation in self.relations.items():
                if not isinstance(agent, str):
                    raise TypeError(
                        "ActionModel agent names must be strings"
                    )

                agent_name = agent.strip()

                if not agent_name:
                    raise ValueError(
                        "ActionModel agent name must not be empty"
                    )

                if agent_name in normalized:
                    raise ValueError(
                        f"Duplicate action relation for "
                        f"{agent_name!r}"
                    )

                source_map: dict[
                    str,
                    frozenset[str],
                ] = {}

                for source, targets in relation.items():
                    if source not in event_names:
                        raise ValueError(
                            f"Unknown event {source!r} "
                            f"in relation for {agent_name!r}"
                        )

                    target_set = frozenset(
                        targets
                    )

                    unknown_targets = (
                        target_set - event_names
                    )

                    if unknown_targets:
                        unknown_text = ", ".join(
                            sorted(unknown_targets)
                        )

                        raise ValueError(
                            f"Unknown target event(s) "
                            f"{unknown_text!r} "
                            f"in relation for {agent_name!r}"
                        )

                    source_map[source] = (
                        target_set
                    )

                missing_sources = (
                    event_names - set(source_map)
                )

                if missing_sources:
                    missing_text = ", ".join(
                        sorted(missing_sources)
                    )

                    raise ValueError(
                        f"Missing action relation(s) "
                        f"for {agent_name!r}: "
                        f"{missing_text}"
                    )

                normalized[agent_name] = (
                    source_map
                )

        self.relations = normalized

    # ---------------------------------------------------------------------
    # Event API
    # ---------------------------------------------------------------------

    @property
    def event_names(
        self,
    ) -> tuple[str, ...]:
        return tuple(
            item.name
            for item in self.events
        )

    def event(
        self,
        name: str,
    ) -> ActionEvent:
        for item in self.events:
            if item.name == name:
                return item

        raise ValueError(
            f"Unknown action event {name!r}"
        )

    # ---------------------------------------------------------------------
    # Event epistemic relation
    # ---------------------------------------------------------------------

    def accessible(
        self,
        agent: str,
        event_name: str,
    ) -> tuple[str, ...]:
        """
        Return events that the agent considers possible
        after observing event_name.

        If no relation is defined for this agent, all events
        are considered indistinguishable.
        """

        self.event(event_name)

        relation = self.relations.get(
            agent
        )

        if relation is None:
            return self.event_names

        return tuple(
            target
            for target in self.event_names
            if target in relation[event_name]
        )

    # ---------------------------------------------------------------------
    # DynamicEvent protocol
    # ---------------------------------------------------------------------

    def apply(
        self,
        model: "EpistemicModel",
    ) -> "EpistemicModel":
        return model._apply_action_model(
            self
        )

    def __repr__(self) -> str:
        names = ", ".join(
            self.event_names
        )

        return (
            f"ActionModel("
            f"events=[{names}], "
            f"actual={self.actual!r}"
            f")"
        )


def product_update(
    model: "EpistemicModel",
    action_model: ActionModel,
) -> "EpistemicModel":
    """
    Functional helper for product update.

    Equivalent to:

        model.product_update(action_model)
    """

    return model.product_update(
        action_model
    )