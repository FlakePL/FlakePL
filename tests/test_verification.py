from __future__ import annotations

from flakepl import (
    Agent,
    Always,
    Atom,
    Configuration,
    EpistemicModel,
    F,
    G,
    GlobalState,
    K,
    StateSpace,
    SystemTransition,
    Tau,
    U,
    X,
    find_always_counterexample,
    find_eventually_counterexample,
    find_path_to,
    format_trace,
    iff,
    implies,
    observe_global,
    stop,
    verify_always,
    verify_eventually,
)


def make_world(
    name: str,
    *,
    safe: bool,
    done: bool,
) -> Configuration:
    agent = Agent.create(
        "alice",
        stop(),
        state={
            "name": name,
        },
    )

    return Configuration(
        state=GlobalState.from_dict(
            {
                "name": name,
                "safe": safe,
                "done": done,
            }
        ),
        agents=(
            agent,
        ),
    )


def make_model(
    worlds: tuple[Configuration, ...],
    transitions: tuple[SystemTransition, ...],
    *,
    initials: tuple[Configuration, ...],
) -> EpistemicModel:
    space = StateSpace(
        initials=initials,
        states=worlds,
        transitions=transitions,
    )

    return EpistemicModel.from_state_space(
        space,
        observations={
            "alice": observe_global(
                "name",
            ),
        },
    )


def test_formula_implies() -> None:
    p = Atom("p")
    q = Atom("q")

    formula = implies(
        p,
        q,
    )

    assert repr(formula) == (
        "(¬(p) ∨ q)"
    )


def test_formula_iff() -> None:
    p = Atom("p")
    q = Atom("q")

    formula = iff(
        p,
        q,
    )

    assert "¬(p)" in repr(formula)
    assert "¬(q)" in repr(formula)


def test_formula_method_implies() -> None:
    p = Atom("p")
    q = Atom("q")

    assert repr(
        p.implies(q)
    ) == "(¬(p) ∨ q)"


def test_find_path_to_goal() -> None:
    initial = make_world(
        "initial",
        safe=True,
        done=False,
    )

    final = make_world(
        "final",
        safe=True,
        done=True,
    )

    transition = SystemTransition(
        source=initial,
        action=Tau(),
        target=final,
    )

    model = make_model(
        (
            initial,
            final,
        ),
        (
            transition,
        ),
        initials=(
            initial,
        ),
    )

    trace = find_path_to(
        model,
        Atom("done"),
    )

    assert trace is not None

    assert trace.worlds == (
        initial,
        final,
    )

    assert trace.actions == (
        Tau(),
    )

    assert not trace.is_cyclic


def test_find_always_counterexample() -> None:
    initial = make_world(
        "initial",
        safe=True,
        done=False,
    )

    bad = make_world(
        "bad",
        safe=False,
        done=False,
    )

    transition = SystemTransition(
        source=initial,
        action=Tau(),
        target=bad,
    )

    model = make_model(
        (
            initial,
            bad,
        ),
        (
            transition,
        ),
        initials=(
            initial,
        ),
    )

    trace = find_always_counterexample(
        model,
        Atom("safe"),
    )

    assert trace is not None

    assert trace.worlds == (
        initial,
        bad,
    )

    assert trace.final == bad


def test_verify_always_returns_counterexample() -> None:
    initial = make_world(
        "initial",
        safe=True,
        done=False,
    )

    bad = make_world(
        "bad",
        safe=False,
        done=False,
    )

    transition = SystemTransition(
        source=initial,
        action=Tau(),
        target=bad,
    )

    model = make_model(
        (
            initial,
            bad,
        ),
        (
            transition,
        ),
        initials=(
            initial,
        ),
    )

    result = verify_always(
        model,
        Atom("safe"),
    )

    assert not result.holds
    assert result.counterexample is not None

    assert result.formula == G(
        Atom("safe")
    )


def test_verify_always_succeeds() -> None:
    initial = make_world(
        "initial",
        safe=True,
        done=False,
    )

    final = make_world(
        "final",
        safe=True,
        done=True,
    )

    transition = SystemTransition(
        source=initial,
        action=Tau(),
        target=final,
    )

    model = make_model(
        (
            initial,
            final,
        ),
        (
            transition,
        ),
        initials=(
            initial,
        ),
    )

    result = verify_always(
        model,
        Atom("safe"),
    )

    assert result.holds
    assert result.counterexample is None


def test_find_eventually_counterexample_with_cycle() -> None:
    first = make_world(
        "first",
        safe=True,
        done=False,
    )

    second = make_world(
        "second",
        safe=True,
        done=False,
    )

    first_to_second = SystemTransition(
        source=first,
        action=Tau(),
        target=second,
    )

    second_to_first = SystemTransition(
        source=second,
        action=Tau(),
        target=first,
    )

    model = make_model(
        (
            first,
            second,
        ),
        (
            first_to_second,
            second_to_first,
        ),
        initials=(
            first,
        ),
    )

    trace = find_eventually_counterexample(
        model,
        Atom("done"),
    )

    assert trace is not None
    assert trace.is_cyclic

    assert trace.worlds[-1] == (
        trace.worlds[
            trace.cycle_start
        ]
    )


def test_verify_eventually_finds_lasso() -> None:
    first = make_world(
        "first",
        safe=True,
        done=False,
    )

    second = make_world(
        "second",
        safe=True,
        done=False,
    )

    transitions = (
        SystemTransition(
            source=first,
            action=Tau(),
            target=second,
        ),
        SystemTransition(
            source=second,
            action=Tau(),
            target=first,
        ),
    )

    model = make_model(
        (
            first,
            second,
        ),
        transitions,
        initials=(
            first,
        ),
    )

    result = verify_eventually(
        model,
        Atom("done"),
    )

    assert not result.holds
    assert result.counterexample is not None
    assert result.counterexample.is_cyclic


def test_verify_eventually_succeeds() -> None:
    initial = make_world(
        "initial",
        safe=True,
        done=False,
    )

    final = make_world(
        "final",
        safe=True,
        done=True,
    )

    transition = SystemTransition(
        source=initial,
        action=Tau(),
        target=final,
    )

    model = make_model(
        (
            initial,
            final,
        ),
        (
            transition,
        ),
        initials=(
            initial,
        ),
    )

    result = verify_eventually(
        model,
        Atom("done"),
    )

    assert result.holds
    assert result.counterexample is None


def test_terminal_state_stuttering_produces_eventuality_counterexample() -> None:
    terminal = make_world(
        "terminal",
        safe=True,
        done=False,
    )

    model = make_model(
        (
            terminal,
        ),
        (),
        initials=(
            terminal,
        ),
    )

    trace = find_eventually_counterexample(
        model,
        Atom("done"),
    )

    assert trace is not None
    assert trace.is_cyclic
    assert trace.worlds == (
        terminal,
        terminal,
    )

    assert trace.actions == (
        None,
    )


def test_format_trace() -> None:
    initial = make_world(
        "initial",
        safe=True,
        done=False,
    )

    final = make_world(
        "final",
        safe=True,
        done=True,
    )

    transition = SystemTransition(
        source=initial,
        action=Tau(),
        target=final,
    )

    model = make_model(
        (
            initial,
            final,
        ),
        (
            transition,
        ),
        initials=(
            initial,
        ),
    )

    trace = find_path_to(
        model,
        Atom("done"),
    )

    assert trace is not None

    rendered = format_trace(
        trace
    )

    assert "Trace:" in rendered
    assert "initial" in rendered
    assert "final" in rendered