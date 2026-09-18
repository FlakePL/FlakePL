from flake import (
    Agent,
    Atom,
    Configuration,
    EpistemicModel,
    GlobalState,
    K,
    Proposition,
    explore,
    observe_local_state,
    recv,
    send,
    stop,
)


def make_initial_configuration() -> Configuration:
    alice = Agent.create(
        "alice",
        send("c", "secret") >> stop(),
    )

    bob = Agent.create(
        "bob",
        recv("c", "x") >> stop(),
    )

    return Configuration(
        state=GlobalState(),
        agents=(
            alice,
            bob,
        ),
    )


def make_model() -> EpistemicModel:
    initial = make_initial_configuration()

    space = explore(initial)

    received_secret = Proposition(
        "bob.received_secret",
        lambda configuration:
            configuration.agent(
                "bob"
            ).get_state("x")
            == "secret",
    )

    return EpistemicModel.from_state_space(
        space,
        observations={
            "alice": observe_local_state(),
            "bob": observe_local_state(),
        },
        propositions={
            "bob.received_secret":
                received_secret,
        },
    )


def test_received_message_becomes_proposition() -> None:
    model = make_model()

    received = Atom(
        "bob.received_secret"
    )

    received_world = next(
        world
        for world in model.worlds
        if model.proposition_holds(
            "bob.received_secret",
            world,
        )
    )

    assert model.check(
        received,
        at=received_world,
    )


def test_bob_knows_his_local_state() -> None:
    model = make_model()

    bob = model.actual.agent("bob")

    received = Atom(
        "bob.received_secret"
    )

    received_worlds = tuple(
        world
        for world in model.worlds
        if model.proposition_holds(
            "bob.received_secret",
            world,
        )
    )

    assert received_worlds

    for world in received_worlds:
        assert model.check(
            K(bob, received),
            at=world,
        )


def test_alice_and_bob_have_different_observations() -> None:
    model = make_model()

    actual = model.actual

    alice = actual.agent("alice")
    bob = actual.agent("bob")

    alice_observation = model.observe(
        alice,
        actual,
    )

    bob_observation = model.observe(
        bob,
        actual,
    )

    assert alice_observation == ()
    assert bob_observation == ()