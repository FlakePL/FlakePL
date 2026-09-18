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
    Proposition,
    StateSpace,
    SystemTransition,
    Tau,
    observe_global,
    stop,
)


def make_world(
    *,
    secret: bool,
    public_phase: str = "stable",
) -> Configuration:
    alice = Agent.create(
        "alice",
        stop(),
        state={
            "secret": secret,
        },
    )

    bob = Agent.create(
        "bob",
        stop(),
        state={},
    )

    return Configuration(
        state=GlobalState.from_dict(
            {
                "phase": public_phase,
            }
        ),
        agents=(
            alice,
            bob,
        ),
    )


def secret_proposition() -> Proposition:
    return Proposition(
        "secret",
        lambda configuration: (
            configuration.agent(
                "alice"
            ).get_state("secret")
            is True
        ),
    )


def make_model(
    *,
    actual: Configuration,
    worlds: tuple[Configuration, ...],
    bob_observation,
    state_space: StateSpace | None = None,
) -> EpistemicModel:
    kwargs = {}
    if state_space is not None:
        kwargs["state_space"] = state_space

    return EpistemicModel(
        worlds=worlds,
        observations={
            "alice": (
                lambda agent, configuration: (
                    configuration.agent(
                        "alice"
                    ).get_state("secret"),
                )
            ),
            "bob": bob_observation,
        },
        actual=actual,
        propositions={
            "secret": secret_proposition(),
        },
        **kwargs,
    )


def test_adversary_cannot_distinguish_secret() -> None:
    world_true = make_world(secret=True)
    world_false = make_world(secret=False)

    model = make_model(
        actual=world_true,
        worlds=(
            world_true,
            world_false,
        ),
        bob_observation=lambda agent, configuration: (),
    )

    accessible = model.accessible(
        "bob",
        world_true,
    )

    assert set(accessible) == {
        world_true,
        world_false,
    }

    assert not model.check(
        K(
            "bob",
            Atom("secret"),
        ),
        at=world_true,
    )


def test_broken_observation_leaks_secret() -> None:
    world_true = make_world(secret=True)
    world_false = make_world(secret=False)

    model = make_model(
        actual=world_true,
        worlds=(
            world_true,
            world_false,
        ),
        bob_observation=lambda agent, configuration: (
            configuration.agent(
                "alice"
            ).get_state("secret"),
        ),
    )

    assert model.accessible(
        "bob",
        world_true,
    ) == (
        world_true,
    )

    assert model.check(
        K(
            "bob",
            Atom("secret"),
        ),
        at=world_true,
    )


def test_public_state_does_not_automatically_reveal_private_state() -> None:
    world_true = make_world(
        secret=True,
        public_phase="stable",
    )
    world_false = make_world(
        secret=False,
        public_phase="stable",
    )

    model = make_model(
        actual=world_true,
        worlds=(
            world_true,
            world_false,
        ),
        bob_observation=observe_global(
            "phase",
        ),
    )

    assert model.observe(
        "bob",
        world_true,
    ) == model.observe(
        "bob",
        world_false,
    )

    assert set(
        model.accessible(
            "bob",
            world_true,
        )
    ) == {
        world_true,
        world_false,
    }


def test_secrecy_can_be_expressed_as_a_temporal_property() -> None:
    world_true = make_world(secret=True)
    world_false = make_world(secret=False)

    space = StateSpace(
        initials=(
            world_true,
        ),
        states=(
            world_true,
            world_false,
        ),
        transitions=(),
    )

    model = make_model(
        actual=world_true,
        worlds=(
            world_true,
            world_false,
        ),
        bob_observation=lambda agent, configuration: (),
        state_space=space,
    )

    secrecy = ~K(
        "bob",
        Atom("secret"),
    )

    assert model.check(
        G(secrecy),
        at=world_true,
    )


def test_secret_owner_knows_secret() -> None:
    world_true = make_world(secret=True)
    world_false = make_world(secret=False)

    model = make_model(
        actual=world_true,
        worlds=(
            world_true,
            world_false,
        ),
        bob_observation=lambda agent, configuration: (),
    )

    assert model.check(
        K(
            "alice",
            Atom("secret"),
        ),
        at=world_true,
    )
