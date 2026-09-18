from flake import (
    Agent,
    Atom,
    Configuration,
    EpistemicModel,
    GlobalState,
    K,
    Proposition,
    explore_many,
    stop,
)


def make_world(
    *,
    secret: bool,
) -> Configuration:

    alice = Agent.create(
        "alice",
        stop(),
        {
            "secret": secret,
        },
    )

    bob = Agent.create(
        "bob",
        stop(),
        {},
    )

    return Configuration(
        state=GlobalState(),
        agents=(
            alice,
            bob,
        ),
    )


def make_model(
    actual: Configuration,
    alternate: Configuration,
) -> EpistemicModel:

    state_space = explore_many(
        (
            actual,
            alternate,
        )
    )

    proposition = Proposition(
        "alice_secret",
        lambda configuration:
            configuration.agent(
                "alice"
            ).get_state("secret")
            is True,
    )

    return EpistemicModel.from_state_space(
        state_space,
        observations={
            "alice": (
                lambda agent, configuration:
                    configuration.agent(
                        "alice"
                    ).get_state("secret")
            ),
            "bob": (
                lambda agent, configuration:
                    ()
            ),
        },
        actual=actual,
        propositions={
            "alice_secret": proposition,
        },
    )


def test_bob_cannot_distinguish_two_worlds() -> None:

    world_true = make_world(
        secret=True,
    )

    world_false = make_world(
        secret=False,
    )

    model = make_model(
        actual=world_true,
        alternate=world_false,
    )

    bob = world_true.agent("bob")

    accessible = model.accessible(
        bob,
        world_true,
    )

    assert set(accessible) == {
        world_true,
        world_false,
    }


def test_bob_does_not_know_alices_secret() -> None:

    world_true = make_world(
        secret=True,
    )

    world_false = make_world(
        secret=False,
    )

    model = make_model(
        actual=world_true,
        alternate=world_false,
    )

    bob = world_true.agent("bob")

    secret = Atom(
        "alice_secret"
    )

    assert model.check(
        secret,
        at=world_true,
    )

    assert not model.check(
        K(
            bob,
            secret,
        ),
        at=world_true,
    )


def test_alice_knows_her_own_secret() -> None:

    world_true = make_world(
        secret=True,
    )

    world_false = make_world(
        secret=False,
    )

    model = make_model(
        actual=world_true,
        alternate=world_false,
    )

    alice = world_true.agent(
        "alice"
    )

    secret = Atom(
        "alice_secret"
    )

    assert model.check(
        K(
            alice,
            secret,
        ),
        at=world_true,
    )