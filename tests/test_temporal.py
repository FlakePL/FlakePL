from __future__ import annotations

from flake import (
    Agent,
    Atom,
    Configuration,
    EpistemicModel,
    F,
    G,
    GlobalState,
    K,
    StateSpace,
    SystemTransition,
    U,
    X,
    observe_global,
    stop,
    Tau,
)


def make_world(
    phase: str,
    *,
    done: bool,
    safe: bool,
    ready: bool,
) -> Configuration:
    agent = Agent.create(
        "alice",
        stop(),
        state={
            "role": "worker",
        },
    )

    return Configuration(
        state=GlobalState.from_dict(
            {
                "phase": phase,
                "done": done,
                "safe": safe,
                "ready": ready,
            }
        ),
        agents=(agent,),
    )


def make_chain() -> tuple[
    StateSpace,
    Configuration,
    Configuration,
    Configuration,
]:
    world_0 = make_world(
        "start",
        done=False,
        safe=True,
        ready=True,
    )

    world_1 = make_world(
        "middle",
        done=False,
        safe=True,
        ready=True,
    )

    world_2 = make_world(
        "finish",
        done=True,
        safe=True,
        ready=False,
    )

    transitions = (
        SystemTransition(
            source=world_0,
            action=Tau(),
            target=world_1,
        ),
        SystemTransition(
            source=world_1,
            action=Tau(),
            target=world_2,
        ),
    )

    space = StateSpace(
        initials=(world_0,),
        states=(
            world_0,
            world_1,
            world_2,
        ),
        transitions=transitions,
    )

    return (
        space,
        world_0,
        world_1,
        world_2,
    )


def make_model(
    space: StateSpace,
) -> EpistemicModel:
    return EpistemicModel.from_state_space(
        space,
        observations={
            "alice": observe_global(
                "phase",
            ),
        },
    )


def test_next() -> None:
    space, world_0, _, _ = make_chain()

    model = make_model(space)

    assert model.check(
        X(
            Atom("done") | ~Atom("done")
        ),
        at=world_0,
    )

    assert not model.check(
        X(
            Atom("done")
        ),
        at=world_0,
    )


def test_next_uses_stuttering_for_terminal_world() -> None:
    space, _, _, world_2 = make_chain()

    model = make_model(space)

    assert model.check(
        X(
            Atom("done")
        ),
        at=world_2,
    )

    assert model.check(
        X(
            G(Atom("done"))
        ),
        at=world_2,
    )


def test_eventually() -> None:
    space, world_0, _, _ = make_chain()

    model = make_model(space)

    assert model.check(
        F(
            Atom("done")
        ),
        at=world_0,
    )


def test_eventually_fails_when_property_is_unreachable() -> None:
    space, world_0, _, _ = make_chain()

    model = make_model(space)

    # "unreachable" is not true in any world of the state space.
    # Therefore F(unreachable) must be false.
    assert not model.check(
        F(
            Atom("unreachable")
        ),
        at=world_0,
    )


def test_always() -> None:
    space, world_0, _, _ = make_chain()

    model = make_model(space)

    assert model.check(
        G(
            Atom("safe")
        ),
        at=world_0,
    )

    assert not model.check(
        G(
            Atom("ready")
        ),
        at=world_0,
    )


def test_until() -> None:
    space, world_0, _, _ = make_chain()

    model = make_model(space)

    assert model.check(
        U(
            Atom("ready"),
            Atom("done"),
        ),
        at=world_0,
    )


def test_until_fails_without_left_condition() -> None:
    world_0 = make_world(
        "start",
        done=False,
        safe=True,
        ready=False,
    )

    world_1 = make_world(
        "finish",
        done=True,
        safe=True,
        ready=False,
    )

    space = StateSpace(
        initials=(world_0,),
        states=(
            world_0,
            world_1,
        ),
        transitions=(
            SystemTransition(
                source=world_0,
                action=Tau(),
                target=world_1,
            ),
        ),
    )

    model = make_model(space)

    assert not model.check(
        U(
            Atom("ready"),
            Atom("done"),
        ),
        at=world_0,
    )


def test_epistemic_and_temporal_formulas_can_be_nested() -> None:
    world_0 = make_world(
        "shared_start",
        done=False,
        safe=True,
        ready=True,
    )

    world_1 = make_world(
        "shared_finish",
        done=True,
        safe=True,
        ready=False,
    )

    transitions = (
        SystemTransition(
            source=world_0,
            action=Tau(),
            target=world_1,
        ),
    )

    space = StateSpace(
        initials=(world_0,),
        states=(
            world_0,
            world_1,
        ),
        transitions=transitions,
    )

    model = EpistemicModel.from_state_space(
        space,
        observations={
            "alice": observe_global(
                "phase",
            ),
        },
    )

    assert model.check(
        K(
            "alice",
            F(
                Atom("done")
            ),
        ),
        at=world_0,
    )