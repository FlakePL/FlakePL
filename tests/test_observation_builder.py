from flake import (
    Agent,
    Configuration,
    GlobalState,
    ObservationBuilder,
    local,
    public,
    stop,
)


def make_configuration(
    *,
    secret: str,
    bob_x: str,
    round_number: int,
) -> Configuration:
    alice = Agent.create(
        "alice",
        process=stop(),
        state={
            "secret": secret,
        },
    )

    bob = Agent.create(
        "bob",
        process=stop(),
        state={
            "x": bob_x,
        },
    )

    return Configuration(
        state=GlobalState.from_dict(
            {
                "round": round_number,
            }
        ),
        agents=(
            alice,
            bob,
        ),
    )


def test_builder_creates_agent_specific_observations() -> None:
    builder = (
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
    )

    observations = builder.build(
        ("alice", "bob")
    )

    world = make_configuration(
        secret="red",
        bob_x="42",
        round_number=1,
    )

    alice_observation = observations["alice"](
        world.agent("alice"),
        world,
    )

    bob_observation = observations["bob"](
        world.agent("bob"),
        world,
    )

    assert alice_observation == (
        (
            "state",
            (
                ("secret", "red"),
            ),
        ),
    )

    assert bob_observation == (
        (
            "state",
            (
                ("x", "42"),
            ),
        ),
        (
            "process",
            world.agent("bob").process,
        ),
    )


def test_public_information_is_visible_to_every_agent() -> None:
    builder = (
        ObservationBuilder()
        .for_agent(
            "alice",
            state=("secret",),
        )
        .for_agent(
            "bob",
            state=("x",),
        )
        .public("round")
    )

    observations = builder.build(
        ("alice", "bob")
    )

    world = make_configuration(
        secret="red",
        bob_x="42",
        round_number=7,
    )

    alice_observation = observations["alice"](
        world.agent("alice"),
        world,
    )

    bob_observation = observations["bob"](
        world.agent("bob"),
        world,
    )

    assert alice_observation == (
        (
            "global",
            (
                ("round", 7),
            ),
        ),
        (
            "state",
            (
                ("secret", "red"),
            ),
        ),
    )

    assert bob_observation == (
        (
            "global",
            (
                ("round", 7),
            ),
        ),
        (
            "state",
            (
                ("x", "42"),
            ),
        ),
    )


def test_builder_can_be_created_from_components() -> None:
    builder = ObservationBuilder.create(
        local(
            "alice",
            state=("secret",),
        ),
        local(
            "bob",
            state=("x",),
        ),
        public("round"),
    )

    observations = builder.build(
        ("alice", "bob")
    )

    assert set(observations) == {
        "alice",
        "bob",
    }