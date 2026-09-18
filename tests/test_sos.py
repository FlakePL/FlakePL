from flakepl import Receive, Send, Tau, choice, parallel, recv, send, stop, tau, transitions


def test_choice_exposes_each_branch() -> None:
    process = choice(
        send("a", 1) >> stop(),
        recv("b", "x") >> stop(),
    )

    available = transitions(process)

    assert len(available) == 2
    assert {type(item.action) for item in available} == {Send, Receive}


def test_parallel_exposes_independent_actions() -> None:
    process = parallel(
        send("a", 1) >> stop(),
        tau() >> stop(),
    )

    available = transitions(process)

    assert len(available) == 2
    assert any(isinstance(item.action, Send) for item in available)
    assert any(isinstance(item.action, Tau) for item in available)


def test_parallel_exposes_synchronous_communication() -> None:
    process = parallel(
        send("channel", "secret") >> stop(),
        recv("channel", "value") >> stop(),
    )

    available = transitions(process)

    assert len(available) == 3
    assert sum(isinstance(item.action, Tau) for item in available) == 1


def test_non_matching_channels_do_not_synchronize() -> None:
    process = parallel(
        send("left", 1) >> stop(),
        recv("right", "value") >> stop(),
    )

    available = transitions(process)

    assert len(available) == 2
