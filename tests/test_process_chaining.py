from flakepl import (
    Receive,
    Send,
    Tau,
    recv,
    send,
    stop,
    tau,
)
from flake.sos import transitions


def test_prefix_chaining_preserves_all_actions() -> None:
    process = (
        send(
            "a",
            1,
        )
        >> recv(
            "b",
            "x",
        )
        >> tau()
        >> stop()
    )

    first = transitions(
        process
    )

    assert len(first) == 1

    assert isinstance(
        first[0].action,
        Send,
    )

    second = transitions(
        first[0].target
    )

    assert len(second) == 1

    assert isinstance(
        second[0].action,
        Receive,
    )

    third = transitions(
        second[0].target
    )

    assert len(third) == 1

    assert isinstance(
        third[0].action,
        Tau,
    )


def test_two_step_chaining() -> None:
    process = (
        send(
            "a",
            "hello",
        )
        >> recv(
            "b",
            "x",
        )
        >> stop()
    )

    first = transitions(
        process
    )

    assert len(first) == 1

    assert isinstance(
        first[0].action,
        Send,
    )

    second = transitions(
        first[0].target
    )

    assert len(second) == 1

    assert isinstance(
        second[0].action,
        Receive,
    )


def test_chaining_send_receive_tau() -> None:
    process = (
        send(
            "prepare",
            "yes",
        )
        >> recv(
            "ready",
            "ack",
        )
        >> tau()
        >> stop()
    )

    current = process

    actions = []

    for _ in range(3):
        available = transitions(
            current
        )

        assert len(available) == 1

        transition = available[0]

        actions.append(
            transition.action
        )

        current = transition.target

    assert isinstance(
        actions[0],
        Send,
    )

    assert isinstance(
        actions[1],
        Receive,
    )

    assert isinstance(
        actions[2],
        Tau,
    )

    assert transitions(
        current
    ) == ()