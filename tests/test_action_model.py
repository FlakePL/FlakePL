from __future__ import annotations

from flake import (
    ActionModel,
    Agent,
    Atom,
    Configuration,
    EpistemicModel,
    GlobalState,
    K,
    ObservationBuilder,
    ProductWorld,
    event,
    observe_local_state,
    stop,
)


def make_world(
    *,
    p: bool,
    alice_view: str,
    bob_view: str,
) -> Configuration:
    alice = Agent.create(
        "alice",
        stop(),
        state={
            "view": alice_view,
        },
    )

    bob = Agent.create(
        "bob",
        stop(),
        state={
            "view": bob_view,
        },
    )

    return Configuration(
        state=GlobalState.from_dict(
            {
                "p": p,
            }
        ),
        agents=(
            alice,
            bob,
        ),
    )


def make_model() -> tuple[
    EpistemicModel,
    Configuration,
    Configuration,
]:
    world_true = make_world(
        p=True,
        alice_view="true",
        bob_view="same",
    )

    world_false = make_world(
        p=False,
        alice_view="false",
        bob_view="same",
    )

    observations = (
        ObservationBuilder()
        .for_agent(
            "alice",
            state=("view",),
        )
        .for_agent(
            "bob",
            state=("view",),
        )
    )

    model = EpistemicModel(
        worlds=(
            world_true,
            world_false,
        ),
        observations=observations,
        actual=world_true,
    )

    return (
        model,
        world_true,
        world_false,
    )


def make_private_learning_action() -> ActionModel:
    p = Atom("p")

    return ActionModel(
        events=(
            event(
                "learn",
                p,
            ),
            event(
                "noop",
                ~p,
            ),
        ),
        actual="learn",
        relations={
            "alice": {
                "learn": {
                    "learn",
                },
                "noop": {
                    "noop",
                },
            },
            "bob": {
                "learn": {
                    "learn",
                    "noop",
                },
                "noop": {
                    "learn",
                    "noop",
                },
            },
        },
    )


def test_action_model_contains_expected_events() -> None:
    action_model = make_private_learning_action()

    assert action_model.event_names == (
        "learn",
        "noop",
    )

    assert action_model.actual == "learn"

    assert action_model.event(
        "learn"
    ).precondition == Atom("p")


def test_action_model_event_relation_for_visible_agent() -> None:
    action_model = make_private_learning_action()

    assert action_model.accessible(
        "alice",
        "learn",
    ) == (
        "learn",
    )

    assert action_model.accessible(
        "alice",
        "noop",
    ) == (
        "noop",
    )


def test_action_model_event_relation_for_uninformed_agent() -> None:
    action_model = make_private_learning_action()

    assert set(
        action_model.accessible(
            "bob",
            "learn",
        )
    ) == {
        "learn",
        "noop",
    }

    assert set(
        action_model.accessible(
            "bob",
            "noop",
        )
    ) == {
        "learn",
        "noop",
    }


def test_product_update_creates_world_event_pairs() -> None:
    model, world_true, world_false = (
        make_model()
    )

    updated = model.product_update(
        make_private_learning_action()
    )

    assert set(
        updated.worlds
    ) == {
        ProductWorld(
            world_true,
            "learn",
        ),
        ProductWorld(
            world_false,
            "noop",
        ),
    }


def test_actual_world_contains_actual_event() -> None:
    model, world_true, _ = (
        make_model()
    )

    updated = model.product_update(
        make_private_learning_action()
    )

    assert updated.actual == ProductWorld(
        world_true,
        "learn",
    )


def test_private_event_changes_alice_knowledge() -> None:
    model, world_true, _ = (
        make_model()
    )

    p = Atom("p")

    updated = model.product_update(
        make_private_learning_action()
    )

    assert updated.check(
        K(
            "alice",
            p,
        )
    )

    assert updated.check(
        K(
            "alice",
            K(
                "alice",
                p,
            ),
        )
    )


def test_private_event_does_not_give_bob_knowledge() -> None:
    model, _, _ = make_model()

    p = Atom("p")

    updated = model.product_update(
        make_private_learning_action()
    )

    assert not updated.check(
        K(
            "bob",
            p,
        )
    )


def test_bob_considers_both_event_outcomes_possible() -> None:
    model, _, _ = make_model()

    updated = model.product_update(
        make_private_learning_action()
    )

    actual = updated.actual

    accessible = updated.accessible(
        "bob",
        actual,
    )

    assert len(accessible) == 2

    assert set(
        world.event
        for world in accessible
    ) == {
        "learn",
        "noop",
    }


def test_public_single_event_preserves_base_epistemic_structure() -> None:
    model, world_true, _ = make_model()

    public_action = ActionModel(
        events=(
            event(
                "announce_p",
                Atom("p"),
            ),
        ),
        actual="announce_p",
    )

    updated = model.product_update(
        public_action
    )

    assert set(
        updated.worlds
    ) == {
        ProductWorld(
            world_true,
            "announce_p",
        ),
    }

    assert updated.check(
        K(
            "bob",
            Atom("p"),
        )
    )


def test_epistemic_precondition_is_evaluated_in_each_base_world() -> None:
    model, world_true, world_false = (
        make_model()
    )

    action = ActionModel(
        events=(
            event(
                "alice_knows_p",
                K(
                    "alice",
                    Atom("p"),
                ),
            ),
            event(
                "alice_does_not_know_p",
                ~K(
                    "alice",
                    Atom("p"),
                ),
            ),
        ),
        actual="alice_knows_p",
    )

    updated = model.product_update(
        action
    )

    assert set(
        updated.worlds
    ) == {
        ProductWorld(
            world_true,
            "alice_knows_p",
        ),
        ProductWorld(
            world_false,
            "alice_does_not_know_p",
        ),
    }