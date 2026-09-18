from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .process import Process


@dataclass(frozen=True, slots=True)
class Agent:
    """
    Runtime agent.

    Agent identity is its logical name.

    Runtime state consists of:

        process
        local state
    """

    name: str
    process: Process
    state: tuple[tuple[str, Any], ...] = ()

    @classmethod
    def create(
        cls,
        name: str,
        process: Process,
        state: dict[str, Any] | None = None,
    ) -> Agent:

        if not name:
            raise ValueError(
                "Agent name cannot be empty"
            )

        if state is None:
            state = {}

        return cls(
            name=name,
            process=process,
            state=tuple(
                sorted(
                    state.items(),
                    key=lambda item: item[0],
                )
            ),
        )

    def get_state(
        self,
        key: str,
        default: Any = None,
    ) -> Any:
        """
        Read one local state variable.
        """

        return dict(
            self.state
        ).get(
            key,
            default,
        )

    def with_state(
        self,
        key: str,
        value: Any,
    ) -> Agent:
        """
        Return a new agent with updated local state.
        """

        state = dict(
            self.state
        )

        state[key] = value

        return Agent(
            name=self.name,
            process=self.process,
            state=tuple(
                sorted(
                    state.items(),
                    key=lambda item: item[0],
                )
            ),
        )

    def with_process(
        self,
        process: Process,
    ) -> Agent:
        """
        Return a new agent with updated process.
        """

        return Agent(
            name=self.name,
            process=process,
            state=self.state,
        )