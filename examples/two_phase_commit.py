from __future__ import annotations

from flakepl import (
    Atom,
    EpistemicModel,
    F,
    G,
    ObservationBuilder,
    Proposition,
    explore_with,
    Agent,
    Configuration,
    GlobalState,
    recv,
    send,
    stop,
    synchronous_system_transitions,
)


def coordinator_process(
    *,
    buggy: bool = False,
):
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
):
    return (
        recv(
            f"prepare{number}",
            "phase",
        )
        >> send(
            f"ready{number}",
            True,
        )
        >> recv(
            f"commit{number}",
            "decision",
        )
        >> stop()
    )


def make_system(
    *,
    buggy: bool = False,
) -> Configuration:
    coordinator = Agent.create(
        "coordinator",
        coordinator_process(
            buggy=buggy,
        ),
    )

    p1 = Agent.create(
        "p1",
        participant_process(1),
    )

    p2 = Agent.create(
        "p2",
        participant_process(2),
    )

    return Configuration(
        state=GlobalState(),
        agents=(
            coordinator,
            p1,
            p2,
        ),
    )


def make_model(
    initial: Configuration,
) -> tuple[
    EpistemicModel,
    object,
]:
    space = explore_with(
        initial,
        synchronous_system_transitions,
    )

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

    model = EpistemicModel.from_state_space(
        space,
        observations=observations,
        propositions=(
            p1_committed,
            p2_committed,
        ),
    )

    return model, space


def report(
    name: str,
    *,
    buggy: bool,
) -> None:
    model, space = make_model(
        make_system(
            buggy=buggy,
        )
    )

    p1 = Atom(
        "p1_committed"
    )

    p2 = Atom(
        "p2_committed"
    )

    both_commit = model.check(
        F(
            p1 & p2
        )
    )

    partial_commit = model.check(
        F(
            p1 & ~p2
        )
    )

    print()
    print(name)
    print("-" * len(name))
    print(
        "Reachable states:",
        len(space.states),
    )
    print(
        "Transitions:",
        len(space.transitions),
    )
    print(
        "Eventually both commit:",
        both_commit,
    )
    print(
        "Partial commit reachable:",
        partial_commit,
    )


def main() -> None:
    report(
        "Correct 2PC",
        buggy=False,
    )

    report(
        "Buggy coordinator",
        buggy=True,
    )


if __name__ == "__main__":
    main()