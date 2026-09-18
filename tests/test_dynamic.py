from __future__ import annotations

from flake import (
    Agent,
    Atom,
    Configuration,
    EpistemicModel,
    K,
    GlobalState,
    ObservationBuilder,
    PublicAnnouncement,
    StateSpace,
    SystemTransition,
    Tau,
    announce,
    observe_local_state,
    stop,
)


def make_world(
    *,
    p: bool,
    alice_view: object,
    bob_view: object,
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
    world_0 = make_world(
        p=True,
        alice_view=True,
        bob_view="same",
    )

    world_1 = make_world(
        p=False,
        alice_view=False,
        bob_view="same",
    )

    model = EpistemicModel(
        worlds=(
            world_0,
            world_1,
        ),
        observations=(
            ObservationBuilder()
            .for_agent(
                "alice",
                state=("view",),
            )
            .for_agent(
                "bob",
                state=("view",),
            )
        ),
        actual=world_0,
    )

    return (
        model,
        world_0,
        world_1,
    )


def test_public_announcement_changes_knowledge() -> None:
    model, world_0, _ = make_model()

    p = Atom("p")

    # Alice sees p directly.
    assert model.check(
        K("alice", p),
        at=world_0,
    )

    # Bob cannot distinguish world_0 from world_1.
    assert not model.check(
        K("bob", p),
        at=world_0,
    )

    updated = model.announce(p)

    # After the public announcement, world_1 is removed.
    assert updated.check(
        K("bob", p),
        at=world_0,
    )


def test_public_announcement_removes_incompatible_worlds() -> None:
    model, world_0, world_1 = make_model()

    updated = model.announce(
        Atom("p")
    )

    assert updated.worlds == (
        world_0,
    )

    assert world_1 not in updated.worlds
    assert updated.actual == world_0


def test_public_announcement_requires_true_actual_world() -> None:
    model, _, _ = make_model()

    p = Atom("p")

    try:
        model.announce(~p)
    except ValueError as exc:
        assert (
            "false in the actual world"
            in str(exc)
        )
    else:
        raise AssertionError(
            "Expected ValueError"
        )


def test_update_accepts_event_object() -> None:
    model, world_0, _ = make_model()

    event = PublicAnnouncement(
        Atom("p")
    )

    updated = model.update(
        event
    )

    assert updated.worlds == (
        world_0,
    )


def test_public_announcement_filters_multiple_initials() -> None:
    world_0 = make_world(
        p=True,
        alice_view=True,
        bob_view="same",
    )

    world_1 = make_world(
        p=False,
        alice_view=False,
        bob_view="same",
    )

    state_space = StateSpace(
        initials=(
            world_0,
            world_1,
        ),
        states=(
            world_0,
            world_1,
        ),
        transitions=(),
    )

    model = EpistemicModel.from_state_space(
        state_space,
        observations={
            "alice": observe_local_state(
                "view",
            ),
            "bob": observe_local_state(
                "view",
            ),
        },
        actual=world_0,
    )

    updated = model.announce(
        Atom("p")
    )

    assert updated.worlds == (
        world_0,
    )

    assert updated.state_space is not None

    assert updated.state_space.initials == (
        world_0,
    )


def test_public_announcement_preserves_valid_transitions() -> None:
    world_0 = make_world(
        p=True,
        alice_view="0",
        bob_view="same",
    )

    world_1 = make_world(
        p=True,
        alice_view="1",
        bob_view="same",
    )

    transition = SystemTransition(
        source=world_0,
        action=Tau(),
        target=world_1,
    )

    state_space = StateSpace(
        initials=(world_0,),
        states=(
            world_0,
            world_1,
        ),
        transitions=(
            transition,
        ),
    )

    model = EpistemicModel.from_state_space(
        state_space,
        observations={
            "alice": observe_local_state(
                "view",
            ),
            "bob": observe_local_state(
                "view",
            ),
        },
    )

    updated = model.announce(
        Atom("p")
    )

    assert updated.state_space is not None

    assert updated.state_space.transitions == (
        transition,
    )

    assert updated.successors(
        world_0
    ) == (
        world_1,
    )


def test_public_announcement_can_use_epistemic_precondition() -> None:
    model, world_0, world_1 = make_model()

    condition = K(
        "alice",
        Atom("p"),
    )

    # Alice observes p, so she knows p in world_0.
    # She does not know p in world_1.
    assert model.check(
        condition,
        at=world_0,
    )

    assert not model.check(
        condition,
        at=world_1,
    )

    updated = model.announce(
        condition
    )

    assert updated.worlds == (
        world_0,
    )


def test_update_does_not_mutate_original_model() -> None:
    model, world_0, world_1 = make_model()

    p = Atom("p")

    assert len(model.worlds) == 2

    assert not model.check(
        K("bob", p),
        at=world_0,
    )

    updated = model.announce(p)

    assert len(updated.worlds) == 1

    # Original model remains untouched.
    assert len(model.worlds) == 2

    assert set(model.worlds) == {
        world_0,
        world_1,
    }

    assert not model.check(
        K("bob", p),
        at=world_0,
    )