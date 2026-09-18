from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .actions import Action, Receive, Send, Tau
from .agent import Agent
from .process import Process
from .sos import transitions


@dataclass(frozen=True, slots=True)
class GlobalState:
    """
    Environment-level state.

    Agent-local state is stored in Agent.state.
    """

    values: tuple[tuple[str, Any], ...] = ()

    @classmethod
    def from_dict(
        cls,
        values: dict[str, Any],
    ) -> GlobalState:

        return cls(
            values=tuple(
                sorted(
                    values.items(),
                    key=lambda item: item[0],
                )
            )
        )

    def to_dict(self) -> dict[str, Any]:
        return dict(
            self.values
        )

    def get(
        self,
        name: str,
        default: Any = None,
    ) -> Any:

        return dict(
            self.values
        ).get(
            name,
            default,
        )

    def with_value(
        self,
        name: str,
        value: Any,
    ) -> GlobalState:

        values = self.to_dict()

        values[name] = value

        return GlobalState.from_dict(
            values
        )


@dataclass(frozen=True, slots=True)
class Configuration:
    """
    Global system configuration.

    Conceptually:

        C = (s, A)

    where:

        s = global state
        A = tuple of agents
    """

    state: GlobalState
    agents: tuple[Agent, ...]

    def __post_init__(self) -> None:

        names = [
            agent.name
            for agent in self.agents
        ]

        if len(names) != len(set(names)):
            raise ValueError(
                "Configuration contains "
                "duplicate agent names"
            )

    def agent(
        self,
        name: str,
    ) -> Agent:

        for agent in self.agents:

            if agent.name == name:
                return agent

        raise KeyError(
            f"Unknown agent: {name}"
        )

    @property
    def processes(
        self,
    ) -> tuple[Process, ...]:

        return tuple(
            agent.process
            for agent in self.agents
        )

    def with_agent(
        self,
        updated: Agent,
    ) -> Configuration:

        if not any(
            agent.name == updated.name
            for agent in self.agents
        ):
            raise KeyError(
                f"Unknown agent: "
                f"{updated.name}"
            )

        updated_agents = tuple(
            updated
            if agent.name == updated.name
            else agent
            for agent in self.agents
        )

        return Configuration(
            state=self.state,
            agents=updated_agents,
        )


@dataclass(frozen=True, slots=True)
class SystemTransition:
    """
    Global transition:

        C --action--> C'
    """

    source: Configuration
    action: Action
    target: Configuration


def _replace_two_agents(
    agents: tuple[Agent, ...],
    first: Agent,
    second: Agent,
) -> tuple[Agent, ...]:

    if first.name == second.name:
        raise ValueError(
            "Cannot replace the same agent twice"
        )

    result: list[Agent] = []

    found_first = False
    found_second = False

    for agent in agents:

        if agent.name == first.name:

            result.append(first)
            found_first = True

        elif agent.name == second.name:

            result.append(second)
            found_second = True

        else:

            result.append(agent)

    if not found_first:
        raise KeyError(
            f"Unknown agent: {first.name}"
        )

    if not found_second:
        raise KeyError(
            f"Unknown agent: {second.name}"
        )

    return tuple(result)


def system_transitions(
    configuration: Configuration,
) -> tuple[SystemTransition, ...]:
    """
    Generate all system-level transitions.

    Includes:

        1. Independent agent actions.
        2. Synchronous communication.

    Communication:

        send(c, v) | recv(c, x)
        ---------------------
                  τ

    The sender advances its process.

    The receiver advances its process and stores
    v in local variable x.
    """

    result: list[SystemTransition] = []

    agents = configuration.agents

    # ========================================================
    # Independent actions
    # ========================================================

    for index, agent in enumerate(agents):

        for transition in transitions(
            agent.process
        ):

            updated_agent = (
                agent.with_process(
                    transition.target
                )
            )

            updated_agents = tuple(
                updated_agent
                if i == index
                else other
                for i, other in enumerate(
                    agents
                )
            )

            target = Configuration(
                state=configuration.state,
                agents=updated_agents,
            )

            result.append(
                SystemTransition(
                    source=configuration,
                    action=transition.action,
                    target=target,
                )
            )

    # ========================================================
    # Synchronous communication
    # ========================================================

    for sender_index, sender in enumerate(
        agents
    ):

        sender_transitions = transitions(
            sender.process
        )

        for sender_transition in (
            sender_transitions
        ):

            if not isinstance(
                sender_transition.action,
                Send,
            ):
                continue

            for receiver_index, receiver in enumerate(
                agents
            ):

                if sender_index == receiver_index:
                    continue

                receiver_transitions = transitions(
                    receiver.process
                )

                for receiver_transition in (
                    receiver_transitions
                ):

                    if not isinstance(
                        receiver_transition.action,
                        Receive,
                    ):
                        continue

                    send_action = (
                        sender_transition.action
                    )

                    receive_action = (
                        receiver_transition.action
                    )

                    if (
                        send_action.channel
                        != receive_action.channel
                    ):
                        continue

                    updated_sender = (
                        sender.with_process(
                            sender_transition.target
                        )
                    )

                    updated_receiver = (
                        receiver
                        .with_process(
                            receiver_transition.target
                        )
                        .with_state(
                            receive_action.variable,
                            send_action.value,
                        )
                    )

                    updated_agents = (
                        _replace_two_agents(
                            agents,
                            updated_sender,
                            updated_receiver,
                        )
                    )

                    target = Configuration(
                        state=configuration.state,
                        agents=updated_agents,
                    )

                    result.append(
                        SystemTransition(
                            source=configuration,
                            action=Tau(),
                            target=target,
                        )
                    )

    return tuple(result)