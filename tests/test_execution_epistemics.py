from __future__ import annotations

import pytest

from flakepl import (
    Agent,
    Atom,
    Configuration,
    EpistemicModel,
    F,
    GlobalState,
    K,
    ObservationBuilder,
    Proposition,
    ProductWorld,
    Tau,
    blind_action,
    execute,
    execute_transition,
    explore,
    observe_action,
    recv,
    send,
    stop,
)
from flakepl.runtime import (
    SystemTransition,
)


def make_communication_system() -> tuple[
    Configuration,
    object,
]:
    alice = Agent.create(
        "alice",
        send(
            "c",
            "secret",
        ) >> stop(),
    )

    bob = Agent.create(
        "bob",
        recv(
            "c",
            "x",
        ) >> stop(),
    )

    initial = Configuration(
        state=GlobalState(),
        agents=(
            alice,
            bob,
        ),
    )

    return initial, explore(initial)


def find_communication(
    space,
) -> SystemTransition:
    for transition in space.transitions:
        if not isinstance(
            transition.action,
            Tau,
        ):
            continue

        bob_state = transition.target.agent(
            "bob"
        )

        if bob_state.get_state(
            "x"
        ) == "secret":
            return transition

    raise AssertionError(
        "Communication transition not found"
    )


def make_model(
    space,
) -> EpistemicModel:
    received = Proposition(
        "bob_received",
        lambda configuration: (
            configuration
            .agent("bob")
            .get_state("x")
            == "secret"
        ),
    )

    observations = (
        ObservationBuilder()
        .for_agent(
            "alice",
            process=True,
        )
        .for_agent(
            "bob",
            state=("x",),
            process=True,
        )
    )

    return EpistemicModel.from_state_space(
        space,
        observations=observations,
        propositions=(
            received,
        ),
    )


def test_action_observation_hides_send_payload() -> None:
    initial, space = make_communication_system()

    transition = next(
        transition
        for transition in space.transitions
        if transition.action.__class__.__name__
        == "Send"
    )

    observation = observe_action()

    value = observation(
        initial.agent("alice"),
        transition,
    )

    assert value == (
        (
            "kind",
            "send",
        ),
        (
            "channel",
            "c",
        ),
    )


def test_action_observation_can_include_payload() -> None:
    initial, space = make_communication_system()

    transition = next(
        transition
        for transition in space.transitions
        if transition.action.__class__.__name__
        == "Send"
    )

    observation = observe_action(
        value=True,
    )

    value = observation(
        initial.agent("alice"),
        transition,
    )

    assert value == (
        (
            "kind",
            "send",
        ),
        (
            "channel",
            "c",
        ),
        (
            "value",
            "secret",
        ),
    )


def test_blind_action_observation() -> None:
    initial, space = make_communication_system()

    transition = space.transitions[0]

    observation = blind_action()

    assert observation(
        initial.agent("alice"),
        transition,
    ) == (
        "blind",
    )


def test_execute_requires_state_space() -> None:
    initial, space = make_communication_system()

    transition = space.transitions[0]

    model = EpistemicModel(
        worlds=(initial,),
        observations={
            "alice": lambda agent, world: (),
            "bob": lambda agent, world: (),
        },
        actual=initial,
    )

    with pytest.raises(
        ValueError,
        match="StateSpace",
    ):
        execute(
            model,
            transition,
        )


def test_execute_requires_transition_from_actual_world() -> None:
    initial, space = make_communication_system()

    model = make_model(space)

    other_transition = next(
        transition
        for transition in space.transitions
        if transition.source != initial
    )

    with pytest.raises(
        ValueError,
        match="actual world",
    ):
        execute(
            model,
            other_transition,
        )


def test_execution_creates_product_worlds() -> None:
    initial, space = make_communication_system()

    model = make_model(space)

    communication = find_communication(
        space
    )

    updated = execute(
        model,
        communication,
    )

    assert isinstance(
        updated.actual,
        ProductWorld,
    )

    assert (
        updated.actual.world
        == communication.target
    )

    assert updated.worlds

    assert all(
        isinstance(
            world,
            ProductWorld,
        )
        for world in updated.worlds
    )


def test_execution_moves_formula_evaluation_to_target_world() -> None:
    initial, space = make_communication_system()

    model = make_model(space)

    communication = find_communication(
        space
    )

    updated = execute(
        model,
        communication,
    )

    assert updated.proposition_holds(
        "bob_received",
        updated.actual,
    )

    assert updated.check(
        F(
            Atom("bob_received")
        )
    )


def test_bob_knows_received_secret_after_communication() -> None:
    initial, space = make_communication_system()

    model = make_model(space)

    communication = find_communication(
        space
    )

    updated = execute(
        model,
        communication,
    )

    assert updated.check(
        K(
            "bob",
            Atom("bob_received"),
        )
    )


def test_blind_event_observation_can_preserve_uncertainty() -> None:
    initial, space = make_communication_system()

    model = make_model(space)

    communication = find_communication(
        space
    )

    updated = execute(
        model,
        communication,
        observations={
            "alice": blind_action(),
            "bob": blind_action(),
        },
    )

    # Alice observes only her own process.
    # Under a fully blind event policy, another transition
    # may be compatible with her resulting local observation.
    assert not updated.check(
        K(
            "alice",
            Atom("bob_received"),
        )
    )


def test_execute_does_not_mutate_original_model() -> None:
    initial, space = make_communication_system()

    model = make_model(space)

    communication = find_communication(
        space
    )

    original_worlds = tuple(
        model.worlds
    )

    updated = execute(
        model,
        communication,
    )

    assert tuple(
        model.worlds
    ) == original_worlds

    assert model.actual == initial

    assert updated.actual != model.actual


def test_execute_transition_returns_dynamic_event() -> None:
    initial, space = make_communication_system()

    communication = find_communication(
        space
    )

    event = execute_transition(
        communication
    )

    assert event.transition == communication