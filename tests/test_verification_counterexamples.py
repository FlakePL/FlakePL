from __future__ import annotations

from flake import (
    Agent,
    Atom,
    Configuration,
    EpistemicModel,
    F,
    G,
    GlobalState,
    StateSpace,
    SystemTransition,
    Tau,
    format_verification,
    stop,
    verify,
    verify_always,
    verify_eventually,
)


def make_state(
    *,
    safe: bool,
    name: str,
) -> Configuration:
    return Configuration(
        state=GlobalState.from_dict(
            {
                "name": name,
                "safe": safe,
            }
        ),
        agents=(
            Agent.create(
                "system",
                stop(),
            ),
        ),
    )


def make_model(
    *,
    worlds: tuple[Configuration, ...],
    transitions: tuple[SystemTransition, ...],
) -> EpistemicModel:
    state_space = StateSpace(
        initials=(
            worlds[0],
        ),
        states=worlds,
        transitions=transitions,
    )

    return EpistemicModel.from_state_space(
        state_space,
        observations={
            "system": (
                lambda agent, configuration: ()
            ),
        },
        propositions={
            "safe": (
                lambda configuration: bool(
                    configuration.state.get(
                        "safe",
                        False,
                    )
                )
            ),
        },
    )


def test_broken_safety_property_returns_counterexample() -> None:
    s0 = make_state(
        name="s0",
        safe=True,
    )

    s1 = make_state(
        name="s1",
        safe=False,
    )

    model = make_model(
        worlds=(
            s0,
            s1,
        ),
        transitions=(
            SystemTransition(
                s0,
                Tau(),
                s1,
            ),
        ),
    )

    result = verify(
        model,
        G(
            Atom("safe")
        ),
    )

    assert not result.holds
    assert result.counterexample is not None

    assert result.counterexample.worlds == (
        s0,
        s1,
    )

    assert result.counterexample.actions == (
        Tau(),
    )

    assert (
        result.counterexample.cycle_start
        is None
    )

    rendered = format_verification(
        result
    )

    assert (
        "Verification: FAIL"
        in rendered
    )

    assert (
        "Counterexample:"
        in rendered
    )

    assert "[0]" in rendered
    assert "[1]" in rendered


def test_generic_state_counterexample_finds_shortest_bad_state() -> None:
    s0 = make_state(
        name="s0",
        safe=True,
    )

    s1 = make_state(
        name="s1",
        safe=True,
    )

    s2 = make_state(
        name="s2",
        safe=False,
    )

    model = make_model(
        worlds=(
            s0,
            s1,
            s2,
        ),
        transitions=(
            SystemTransition(
                s0,
                Tau(),
                s1,
            ),
            SystemTransition(
                s1,
                Tau(),
                s2,
            ),
        ),
    )

    result = verify(
        model,
        Atom("safe"),
    )

    assert not result.holds
    assert result.counterexample is not None

    assert result.counterexample.worlds == (
        s0,
        s1,
        s2,
    )

    assert len(
        result.counterexample.actions
    ) == 2


def test_eventuality_counterexample_is_a_lasso() -> None:
    s0 = make_state(
        name="s0",
        safe=False,
    )

    s1 = make_state(
        name="s1",
        safe=False,
    )

    model = make_model(
        worlds=(
            s0,
            s1,
        ),
        transitions=(
            SystemTransition(
                s0,
                Tau(),
                s1,
            ),
            SystemTransition(
                s1,
                Tau(),
                s0,
            ),
        ),
    )

    result = verify_eventually(
        model,
        F(
            Atom("safe")
        ),
    )

    assert not result.holds
    assert result.counterexample is not None

    trace = result.counterexample

    assert trace.cycle_start == 0

    assert trace.worlds == (
        s0,
        s1,
        s0,
    )

    assert trace.actions == (
        Tau(),
        Tau(),
    )

    assert (
        trace.final
        == trace.worlds[
            trace.cycle_start
        ]
    )

    assert trace.is_lasso

    rendered = format_verification(
        result
    )

    assert (
        "Verification: FAIL"
        in rendered
    )

    assert (
        "loop: [2] -> [0]"
        in rendered
    )


def test_eventuality_passes_when_target_is_reachable_on_every_path() -> None:
    s0 = make_state(
        name="s0",
        safe=False,
    )

    s1 = make_state(
        name="s1",
        safe=True,
    )

    model = make_model(
        worlds=(
            s0,
            s1,
        ),
        transitions=(
            SystemTransition(
                s0,
                Tau(),
                s1,
            ),
        ),
    )

    result = verify(
        model,
        F(
            Atom("safe")
        ),
    )

    assert result.holds
    assert result.counterexample is None


def test_eventuality_terminal_false_state_uses_implicit_stuttering() -> None:
    s0 = make_state(
        name="s0",
        safe=False,
    )

    model = make_model(
        worlds=(
            s0,
        ),
        transitions=(),
    )

    result = verify(
        model,
        F(
            Atom("safe")
        ),
    )

    assert not result.holds
    assert result.counterexample is not None

    trace = result.counterexample

    assert trace.cycle_start == 0

    assert trace.worlds == (
        s0,
        s0,
    )

    assert trace.actions == (
        None,
    )

    rendered = format_verification(
        result
    )

    assert (
        "implicit temporal stuttering"
        in rendered
    )


def test_verify_always_accepts_operand_and_temporal_formula() -> None:
    s0 = make_state(
        name="s0",
        safe=True,
    )

    s1 = make_state(
        name="s1",
        safe=False,
    )

    model = make_model(
        worlds=(
            s0,
            s1,
        ),
        transitions=(
            SystemTransition(
                s0,
                Tau(),
                s1,
            ),
        ),
    )

    direct = verify_always(
        model,
        Atom("safe"),
    )

    wrapped = verify_always(
        model,
        G(
            Atom("safe")
        ),
    )

    assert direct == wrapped
    assert not direct.holds