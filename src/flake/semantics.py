from __future__ import annotations

from typing import Iterable

from .actions import (
    Receive,
    Send,
    Tau,
)
from .agent import Agent
from .runtime import (
    Configuration,
    SystemTransition,
)
from .sos import transitions


def _replace_agents(
    configuration: Configuration,
    updates: Iterable[Agent],
) -> Configuration:
    """
    Return a configuration with the supplied agents replaced.
    """

    result = configuration

    for agent in updates:
        result = result.with_agent(agent)

    return result


def synchronous_system_transitions(
    configuration: Configuration,
) -> tuple[SystemTransition, ...]:
    """
    Strict synchronous process semantics.

    Tau transitions are executed independently.

    Send and Receive transitions never execute independently.
    They must synchronize on the same channel.

    Therefore:

        send(c, v) | recv(c, x)

    becomes one transition where:

        receiver.x = v

    while the two processes advance simultaneously.

    This semantics is useful for modeling protocols where
    communication is synchronous, such as the examples in
    the FlakePL benchmark suite.
    """

    result: list[SystemTransition] = []

    agents = configuration.agents

    # ------------------------------------------------------------------
    # Independent internal transitions.
    # ------------------------------------------------------------------

    for agent in agents:
        for transition in transitions(
            agent.process
        ):
            if not isinstance(
                transition.action,
                Tau,
            ):
                continue

            updated_agent = agent.with_process(
                transition.target
            )

            target = configuration.with_agent(
                updated_agent
            )

            result.append(
                SystemTransition(
                    source=configuration,
                    action=transition.action,
                    target=target,
                )
            )

    # ------------------------------------------------------------------
    # Synchronous communication.
    #
    # We inspect each pair only once.
    # ------------------------------------------------------------------

    for left_index in range(
        len(agents)
    ):
        for right_index in range(
            left_index + 1,
            len(agents),
        ):
            left_agent = agents[left_index]
            right_agent = agents[right_index]

            left_transitions = transitions(
                left_agent.process
            )

            right_transitions = transitions(
                right_agent.process
            )

            for left_transition in left_transitions:
                left_action = left_transition.action

                for right_transition in right_transitions:
                    right_action = right_transition.action

                    # --------------------------------------------------
                    # left sends, right receives
                    # --------------------------------------------------

                    if (
                        isinstance(
                            left_action,
                            Send,
                        )
                        and isinstance(
                            right_action,
                            Receive,
                        )
                        and left_action.channel
                        == right_action.channel
                    ):
                        updated_left = (
                            left_agent.with_process(
                                left_transition.target
                            )
                        )

                        updated_right = (
                            right_agent
                            .with_process(
                                right_transition.target
                            )
                            .with_state(
                                right_action.variable,
                                left_action.value,
                            )
                        )

                        target = _replace_agents(
                            configuration,
                            (
                                updated_left,
                                updated_right,
                            ),
                        )

                        result.append(
                            SystemTransition(
                                source=configuration,
                                action=Tau(),
                                target=target,
                            )
                        )

                    # --------------------------------------------------
                    # left receives, right sends
                    # --------------------------------------------------

                    elif (
                        isinstance(
                            left_action,
                            Receive,
                        )
                        and isinstance(
                            right_action,
                            Send,
                        )
                        and left_action.channel
                        == right_action.channel
                    ):
                        updated_left = (
                            left_agent
                            .with_process(
                                left_transition.target
                            )
                            .with_state(
                                left_action.variable,
                                right_action.value,
                            )
                        )

                        updated_right = (
                            right_agent.with_process(
                                right_transition.target
                            )
                        )

                        target = _replace_agents(
                            configuration,
                            (
                                updated_left,
                                updated_right,
                            ),
                        )

                        result.append(
                            SystemTransition(
                                source=configuration,
                                action=Tau(),
                                target=target,
                            )
                        )

    return tuple(result)