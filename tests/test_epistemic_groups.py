from flake import (
    Agent,
    Atom,
    C,
    Configuration,
    D,
    E,
    EpistemicModel,
    GlobalState,
    K,
    ObservationBuilder,
    local,
    stop,
)


def make_world(
    *,
    alice_view: str,
    bob_view: str,
    proposition: bool,
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
                "p": proposition,
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
    Configuration,
]:
    world_0 = make_world(
        alice_view="a0",
        bob_view="b0",
        proposition=True,
    )

    world_1 = make_world(
        alice_view="a0",
        bob_view="b1",
        proposition=False,
    )

    world_2 = make_world(
        alice_view="a1",
        bob_view="b0",
        proposition=False,
    )

    builder = (
        ObservationBuilder()
        .add(
            local(
                "alice",
                state=("view",),
            )
        )
        .add(
            local(
                "bob",
                state=("view",),
            )
        )
    )

    model = EpistemicModel(
        worlds=(
            world_0,
            world_1,
            world_2,
        ),
        observations=builder,
        actual=world_0,
    )

    return (
        model,
        world_0,
        world_1,
        world_2,
    )


def test_everyone_knows() -> None:
    model, world_0, _, _ = make_model()

    p = Atom("p")

    assert not model.check(
        E(
            ("alice", "bob"),
            p,
        ),
        at=world_0,
    )


def test_distributed_knowledge() -> None:
    model, world_0, _, _ = make_model()

    p = Atom("p")

    assert model.check(
        D(
            ("alice", "bob"),
            p,
        ),
        at=world_0,
    )


def test_distributed_knowledge_does_not_imply_individual_knowledge() -> None:
    model, world_0, _, _ = make_model()

    p = Atom("p")

    assert not model.check(
        K(
            "alice",
            p,
        ),
        at=world_0,
    )

    assert not model.check(
        K(
            "bob",
            p,
        ),
        at=world_0,
    )

    assert model.check(
        D(
            ("alice", "bob"),
            p,
        ),
        at=world_0,
    )


def test_common_knowledge() -> None:
    model, world_0, world_1, world_2 = make_model()

    p = Atom("p")

    closure = model.common_knowledge_closure(
        ("alice", "bob"),
        world_0,
    )

    assert set(closure) == {
        world_0,
        world_1,
        world_2,
    }

    assert not model.check(
        C(
            ("alice", "bob"),
            p,
        ),
        at=world_0,
    )


def test_everyone_knows_matches_conjunction_of_knowledge() -> None:
    model, world_0, _, _ = make_model()

    p = Atom("p")

    expected = (
        model.check(
            K(
                "alice",
                p,
            ),
            at=world_0,
        )
        and model.check(
            K(
                "bob",
                p,
            ),
            at=world_0,
        )
    )

    actual = model.check(
        E(
            ("alice", "bob"),
            p,
        ),
        at=world_0,
    )

    assert actual == expected