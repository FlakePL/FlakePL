from flakepl import Receive, Send, Tau, parallel, recv, send, stop, transitions


def test_public_sos_api_is_available() -> None:
    process = parallel(
        send("c", "x") >> stop(),
        recv("c", "value") >> stop(),
    )

    available = transitions(process)

    assert any(isinstance(item.action, Send) for item in available)
    assert any(isinstance(item.action, Receive) for item in available)
    assert any(isinstance(item.action, Tau) for item in available)
