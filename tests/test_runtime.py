from flake import (
    Agent,
    Configuration,
    GlobalState,
    Tau,
    explore,
    recv,
    send,
    stop,
)
from flake.runtime import system_transitions


def make_configuration() -> Configuration:
    alice = Agent.create(
        "alice",
        send("c", "hello") >> stop(),
    )

    bob = Agent.create(
        "bob",
        recv("c", "x") >> stop(),
    )

    return Configuration(
        state=GlobalState.from_dict(
            {
                "counter": 0,
            }
        ),
        agents=(alice, bob),
    )


def test_configuration_keeps_state() -> None:
    configuration = make_configuration()

    assert configuration.state.get("counter") == 0

    alice = configuration.agent("alice")

    assert alice.name == "alice"


def test_configuration_contains_agents() -> None:
    configuration = make_configuration()

    assert len(configuration.agents) == 2

    assert configuration.agent("alice").name == "alice"
    assert configuration.agent("bob").name == "bob"


def test_parallel_system_has_transitions() -> None:
    configuration = make_configuration()

    result = system_transitions(configuration)

    # Alice can send.
    # Bob can receive.
    # They can synchronize.
    assert len(result) == 3


def test_parallel_system_has_tau_transition() -> None:
    configuration = make_configuration()

    result = system_transitions(configuration)

    assert any(
        isinstance(
            transition.action,
            Tau,
        )
        for transition in result
    )


def test_explorer_finds_communication_state() -> None:
    configuration = make_configuration()

    space = explore(configuration)

    # We have:
    #
    # C0
    # ├── Alice sends  -> C1
    # │                    └── Bob receives -> C3
    # ├── Bob receives -> C2
    # │                    └── Alice sends -> C4
    # └── communication -> C3
    #
    # Hence 5 reachable states.

    assert len(space.states) == 5
    assert len(space.transitions) == 5


def test_communication_updates_receiver_state() -> None:
    configuration = make_configuration()

    result = system_transitions(configuration)

    communication_target = None

    for transition in result:

        if not isinstance(
            transition.action,
            Tau,
        ):
            continue

        target = transition.target

        bob = target.agent("bob")

        if bob.get_state("x") == "hello":
            communication_target = target
            break

    assert communication_target is not None


def test_communication_updates_both_processes() -> None:
    configuration = make_configuration()

    result = system_transitions(configuration)

    communication_target = None

    for transition in result:

        if not isinstance(
            transition.action,
            Tau,
        ):
            continue

        target = transition.target

        alice = target.agent("alice")
        bob = target.agent("bob")

        if (
            alice.process == stop()
            and bob.process == stop()
            and bob.get_state("x") == "hello"
        ):
            communication_target = target
            break

    assert communication_target is not None