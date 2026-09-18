from flake import (
    Agent,
    Atom,
    Configuration,
    EpistemicModel,
    GlobalState,
    K,
    observe_global,
    stop,
)


def make_worlds() -> tuple[
    Configuration,
    Configuration,
]:
    alice = Agent.create(
        "alice",
        stop(),
    )

    bob = Agent.create(
        "bob",
        stop(),
    )

    world_true = Configuration(
        state=GlobalState.from_dict(
            {
                "p": True,
            }
        ),
        agents=(alice, bob),
    )

    world_false = Configuration(
        state=GlobalState.from_dict(
            {
                "p": False,
            }
        ),
        agents=(alice, bob),
    )

    return world_true, world_false


def test_alice_knows_p_but_bob_does_not() -> None:
    alice = Agent.create(
        "alice",
        stop(),
    )

    bob = Agent.create(
        "bob",
        stop(),
    )

    world_true, world_false = make_worlds()

    model = EpistemicModel(
        worlds=(
            world_true,
            world_false,
        ),
        observations={
            # Alice observes p.
            alice: observe_global("p"),

            # Bob does not observe p.
            bob: lambda agent, configuration: (),
        },
        actual=world_true,
    )

    p = Atom("p")

    assert model.check(
        K(alice, p)
    )

    assert not model.check(
        K(bob, p)
    )


def test_accessibility_relation() -> None:
    alice = Agent.create(
        "alice",
        stop(),
    )

    bob = Agent.create(
        "bob",
        stop(),
    )

    world_true, world_false = make_worlds()

    model = EpistemicModel(
        worlds=(
            world_true,
            world_false,
        ),
        observations={
            alice: observe_global("p"),
            bob: lambda agent, configuration: (),
        },
        actual=world_true,
    )

    alice_accessible = model.accessible(
        alice,
        world_true,
    )

    bob_accessible = model.accessible(
        bob,
        world_true,
    )

    assert alice_accessible == (
        world_true,
    )

    assert set(bob_accessible) == {
        world_true,
        world_false,
    }


def test_formula_boolean_operators() -> None:
    alice = Agent.create(
        "alice",
        stop(),
    )

    bob = Agent.create(
        "bob",
        stop(),
    )

    world_true, world_false = make_worlds()

    model = EpistemicModel(
        worlds=(
            world_true,
            world_false,
        ),
        observations={
            alice: observe_global("p"),
            bob: lambda agent, configuration: (),
        },
        actual=world_true,
    )

    p = Atom("p")

    assert model.check(p)

    assert model.check(
        ~~p
    )

    assert model.check(
        p & p
    )

    assert model.check(
        p | ~p
    )