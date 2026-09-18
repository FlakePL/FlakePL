from flake import (
    Agent,
    Atom,
    Configuration,
    EpistemicModel,
    GlobalState,
    K,
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


def test_epistemic_model_can_be_built_from_state_space() -> None:

    initial = make_initial_configuration()

    space = explore(initial)

    model = EpistemicModel.from_state_space(
        space,
        observations={
            "alice": observe_local_state(),
            "bob": observe_local_state(),
        },
    )

    assert model.actual == initial

    assert {
        agent.name
        for agent in model.agents
    } == {
        "alice",
        "bob",
    }


def test_local_observation_induces_relation() -> None:

    initial = make_initial_configuration()

    space = explore(initial)

    model = EpistemicModel.from_state_space(
        space,
        observations={
            "alice": observe_local_state(),
            "bob": observe_local_state(),
        },
    )

    alice = initial.agent(
        "alice"
    )

    accessible = model.accessible(
        alice,
        initial,
    )

    assert len(accessible) >= 1


def test_knowledge_formula_is_evaluated() -> None:

    initial = make_initial_configuration()

    space = explore(initial)

    model = EpistemicModel.from_state_space(
        space,
        observations={
            "alice": observe_local_state(),
            "bob": observe_local_state(),
        },
    )

    bob = initial.agent(
        "bob"
    )

    # `p` is not registered and does not exist
    # in GlobalState, so it is simply false.
    p = Atom("p")

    result = model.check(
        K(
            bob,
            p,
        ),
        at=initial,
    )

    assert isinstance(
        result,
        bool,
    )