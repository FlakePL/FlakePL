from __future__ import annotations

from dataclasses import dataclass

from .actions import Action, Receive, Send, Tau
from .process import Choice, Nil, Parallel, Prefix, Process


@dataclass(frozen=True, slots=True)
class Transition:
    """One process-level operational transition: P --action--> P'."""

    action: Action
    target: Process


def transitions(process: Process) -> tuple[Transition, ...]:
    """Generate all one-step SOS transitions for a process.

    The MVP supports prefix, nondeterministic choice, parallel composition,
    and synchronous communication between matching send/receive prefixes.
    """

    if isinstance(process, Nil):
        return ()

    if isinstance(process, Prefix):
        return (Transition(process.action, process.continuation),)

    if isinstance(process, Choice):
        result: list[Transition] = []
        for option in process.options:
            result.extend(transitions(option))
        return tuple(result)

    if isinstance(process, Parallel):
        result: list[Transition] = []
        processes = process.processes

        # Independent actions.
        for index, current in enumerate(processes):
            for transition in transitions(current):
                updated = list(processes)
                updated[index] = transition.target
                result.append(
                    Transition(
                        transition.action,
                        Parallel(tuple(updated)),
                    )
                )

        # Pairwise synchronous communication.
        for left_index in range(len(processes)):
            for right_index in range(left_index + 1, len(processes)):
                left = processes[left_index]
                right = processes[right_index]

                left_transitions = transitions(left)
                right_transitions = transitions(right)

                for left_transition in left_transitions:
                    left_action = left_transition.action
                    for right_transition in right_transitions:
                        right_action = right_transition.action

                        if isinstance(left_action, Send) and isinstance(right_action, Receive):
                            if left_action.channel != right_action.channel:
                                continue
                            updated = list(processes)
                            updated[left_index] = left_transition.target
                            updated[right_index] = right_transition.target
                            result.append(
                                Transition(
                                    Tau(),
                                    Parallel(tuple(updated)),
                                )
                            )

                        elif isinstance(left_action, Receive) and isinstance(right_action, Send):
                            if left_action.channel != right_action.channel:
                                continue
                            updated = list(processes)
                            updated[left_index] = left_transition.target
                            updated[right_index] = right_transition.target
                            result.append(
                                Transition(
                                    Tau(),
                                    Parallel(tuple(updated)),
                                )
                            )

        return tuple(result)

    raise TypeError(f"Unsupported process type: {type(process).__name__}")


__all__ = ["Transition", "transitions"]
