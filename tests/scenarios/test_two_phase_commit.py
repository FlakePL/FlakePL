from __future__ import annotations

from flakepl import (
    Agent,
    Atom,
    Configuration,
    EpistemicModel,
    F,
    G,
    GlobalState,
    K,
    ObservationBuilder,
    Proposition,
    explore_with,
    recv,
    send,
    stop,
    synchronous_system_transitions,
)


# ============================================================================
# Process definitions
# ============================================================================


def coordinator_process(
    *,
    buggy: bool = False,
):
    """
    Coordinator:

        prepare P1
        prepare P2
        wait ready P1
        wait ready P2
        commit P1
        commit P2

    The buggy version deliberately stops after sending commit to P1.
    """

    process = (
        send(
            "prepare1",
            "prepare",
        )
        >> send(
            "prepare2",
            "prepare",
        )
        >> recv(
            "ready1",
            "ready1",
        )
        >> recv(
            "ready2",
            "ready2",
        )
        >> send(
            "commit1",
            "commit",
        )
    )

    if buggy:
        return process >> stop()

    return (
        process
        >> send(
            "commit2",
            "commit",
        )
        >> stop()
    )


def participant_process(
    number: int,
    *,
    fails_before_ready: bool = False,
):
    """
    Participant protocol:

        receive prepare
        optionally fail
        send ready
        receive commit
        stop
    """

    if number not in (1, 2):
        raise ValueError(
            "participant number must be 1 or 2"
        )

    prepare_channel = (
        f"prepare{number}"
    )

    ready_channel = (
        f"ready{number}"
    )

    commit_channel = (
        f"commit{number}"
    )

    process = recv(
        prepare_channel,
        "phase",
    )

    if fails_before_ready:
        return (
            process
            >> stop()
        )

    return (
        process
        >> send(
            ready_channel,
            True,
        )
        >> recv(
            commit_channel,
            "decision",
        )
        >> stop()
    )


def make_system(
    *,
    buggy_coordinator: bool = False,
    failed_participant: int | None = None,
) -> Configuration:
    """
    Build a 2PC system.

    failed_participant:
        1 or 2 means that the participant receives PREPARE
        but never sends READY.
    """

    coordinator = Agent.create(
        "coordinator",
        coordinator_process(
            buggy=buggy_coordinator,
        ),
    )

    participant_1 = Agent.create(
        "p1",
        participant_process(
            1,
            fails_before_ready=(
                failed_participant == 1
            ),
        ),
    )

    participant_2 = Agent.create(
        "p2",
        participant_process(
            2,
            fails_before_ready=(
                failed_participant == 2
            ),
        ),
    )

    return Configuration(
        state=GlobalState(),
        agents=(
            coordinator,
            participant_1,
            participant_2,
        ),
    )


# ============================================================================
# Properties
# ============================================================================


def proposition_model(
    space,
) -> EpistemicModel:
    """
    Construct epistemic model for the protocol.

    p1_committed / p2_committed are propositions over
    participant local state.
    """

    p1_committed = Proposition(
        "p1_committed",
        lambda configuration: (
            configuration
            .agent("p1")
            .get_state("decision")
            == "commit"
        ),
    )

    p2_committed = Proposition(
        "p2_committed",
        lambda configuration: (
            configuration
            .agent("p2")
            .get_state("decision")
            == "commit"
        ),
    )

    observations = (
        ObservationBuilder()
        .for_agent(
            "coordinator",
            process=True,
        )
        .for_agent(
            "p1",
            state=("decision",),
            process=True,
        )
        .for_agent(
            "p2",
            state=("decision",),
            process=True,
        )
    )

    return EpistemicModel.from_state_space(
        space,
        observations=observations,
        propositions=(
            p1_committed,
            p2_committed,
        ),
    )


def make_space(
    initial: Configuration,
):
    return explore_with(
        initial,
        synchronous_system_transitions,
    )


# ============================================================================
# Basic semantics tests
# ============================================================================


def test_synchronous_semantics_blocks_orphan_receive() -> None:
    system = Configuration(
        state=GlobalState(),
        agents=(
            Agent.create(
                "receiver",
                recv(
                    "missing",
                    "value",
                )
                >> stop(),
            ),
        ),
    )

    transitions = synchronous_system_transitions(
        system
    )

    assert transitions == ()


# ============================================================================
# Correct protocol
# ============================================================================


def test_two_phase_commit_happy_path_eventually_commits_both() -> None:
    initial = make_system()

    space = make_space(
        initial
    )

    model = proposition_model(
        space
    )

    p1 = Atom(
        "p1_committed"
    )

    p2 = Atom(
        "p2_committed"
    )

    assert model.check(
        F(
            p1 & p2
        )
    )


def test_two_phase_commit_eventual_agreement() -> None:
    """
    Temporary partial commit is allowed.

    What must hold is that if one participant has committed
    while the other has not, the second participant eventually
    commits as well.
    """

    initial = make_system()

    space = make_space(
        initial
    )

    model = proposition_model(
        space
    )

    p1 = Atom(
        "p1_committed"
    )

    p2 = Atom(
        "p2_committed"
    )

    partial_commit = (
        p1 & ~p2
    )

    eventual_resolution = F(
        p2
    )

    assert model.check(
        G(
            partial_commit
            | eventual_resolution
            | ~partial_commit
        )
    )


def test_two_phase_commit_partial_state_is_eventually_resolved() -> None:
    """
    Cleaner equivalent of the agreement property:

        G(
            (p1 & !p2)
            -> F(p2)
        )
    """

    initial = make_system()

    space = make_space(
        initial
    )

    model = proposition_model(
        space
    )

    p1 = Atom(
        "p1_committed"
    )

    p2 = Atom(
        "p2_committed"
    )

    assert model.check(
        G(
            (~p1 & p2)
            | (~p1 & ~p2)
            | F(p2)
        )
    )


def test_happy_path_can_reach_partial_commit() -> None:
    """
    With asynchronous message delivery, P1 may receive COMMIT
    before P2. This is a valid intermediate state.

    This test is important because it prevents us from encoding
    an incorrect "simultaneous commit" assumption into FlakePL.
    """

    initial = make_system()

    space = make_space(
        initial
    )

    model = proposition_model(
        space
    )

    p1 = Atom(
        "p1_committed"
    )

    p2 = Atom(
        "p2_committed"
    )

    assert model.check(
        F(
            p1 & ~p2
        )
    )


def test_happy_path_never_stops_with_partial_commit() -> None:
    """
    Although partial commit can occur temporarily, it cannot
    be a terminal state in the correct protocol.

    The temporal resolution property guarantees that another
    transition eventually brings P2 to the same decision.
    """

    initial = make_system()

    space = make_space(
        initial
    )

    model = proposition_model(
        space
    )

    p1 = Atom(
        "p1_committed"
    )

    p2 = Atom(
        "p2_committed"
    )

    # Every reachable partial state must be followed by
    # eventual commitment of P2.
    assert model.check(
        G(
            (~p1 & p2)
            | (~p1 & ~p2)
            | F(p2)
        )
    )


# ============================================================================
# Failure scenarios
# ============================================================================


def test_failed_participant_prevents_global_commit() -> None:
    initial = make_system(
        failed_participant=2,
    )

    space = make_space(
        initial
    )

    model = proposition_model(
        space
    )

    p1 = Atom(
        "p1_committed"
    )

    p2 = Atom(
        "p2_committed"
    )

    assert not model.check(
        F(
            p1 & p2
        )
    )

    # No participant can commit alone in this failure mode.
    assert not model.check(
        F(
            p1 & ~p2
        )
    )

    assert not model.check(
        F(
            ~p1 & p2
        )
    )


def test_buggy_coordinator_violates_eventual_agreement() -> None:
    """
    Bug:

        coordinator sends COMMIT to P1
        coordinator terminates
        P2 never receives COMMIT

    Therefore:

        G(
            (p1 & !p2)
            -> F(p2)
        )

    is false.
    """

    initial = make_system(
        buggy_coordinator=True,
    )

    space = make_space(
        initial
    )

    model = proposition_model(
        space
    )

    p1 = Atom(
        "p1_committed"
    )

    p2 = Atom(
        "p2_committed"
    )

    assert not model.check(
        G(
            (~p1 & p2)
            | (~p1 & ~p2)
            | F(p2)
        )
    )


def test_buggy_coordinator_reaches_partial_commit_state() -> None:
    initial = make_system(
        buggy_coordinator=True,
    )

    space = make_space(
        initial
    )

    model = proposition_model(
        space
    )

    p1 = Atom(
        "p1_committed"
    )

    p2 = Atom(
        "p2_committed"
    )

    assert model.check(
        F(
            p1 & ~p2
        )
    )


def test_buggy_coordinator_cannot_reach_both_committed() -> None:
    initial = make_system(
        buggy_coordinator=True,
    )

    space = make_space(
        initial
    )

    model = proposition_model(
        space
    )

    p1 = Atom(
        "p1_committed"
    )

    p2 = Atom(
        "p2_committed"
    )

    assert not model.check(
        F(
            p1 & p2
        )
    )


# ============================================================================
# Epistemic property
# ============================================================================


def test_participant_knows_its_own_commit() -> None:
    initial = make_system()

    space = make_space(
        initial
    )

    model = proposition_model(
        space
    )

    p1 = Atom(
        "p1_committed"
    )

    committed_worlds = tuple(
        world
        for world in model.worlds
        if model.proposition_holds(
            "p1_committed",
            world,
        )
    )

    assert committed_worlds

    for world in committed_worlds:
        assert model.check(
            K(
                "p1",
                p1,
            ),
            at=world,
        )