from flakepl import (
    Agent,
    Atom,
    C,
    D,
    E,
    K,
    stop,
)


def test_public_flakepl_namespace() -> None:
    agent = Agent.create(
        "alice",
        stop(),
    )

    p = Atom("p")

    assert agent.name == "alice"

    assert K(
        agent,
        p,
    ).agent == "alice"

    assert E(
        ("alice",),
        p,
    ).agents == (
        "alice",
    )

    assert D(
        ("alice",),
        p,
    ).agents == (
        "alice",
    )

    assert C(
        ("alice",),
        p,
    ).agents == (
        "alice",
    )


def test_legacy_flake_namespace_remains_available() -> None:
    # This test intentionally uses the already-existing public
    # API through the legacy compatibility package.
    from flake import Agent as LegacyAgent

    agent = LegacyAgent.create(
        "alice",
        stop(),
    )

    assert agent.name == "alice"