# Flake

**Flake** is an experimental agent-oriented framework for modeling,
coordinating and formally verifying multi-agent systems.

The project is currently implemented as a Python library.
In the future, Flake is planned to evolve into a dedicated
agent-oriented programming language.

## What is Flake?

Flake explores a programming model where agents, their states,
observations, actions and interactions can be described as
a formal system.

The goal is to combine:

- agent-oriented programming;
- logical programming;
- formal logic;
- epistemic models;
- state-space exploration;
- verification of system properties;
- interaction with LLM-based agents.

Flake is not only intended to execute agent workflows.
It is also intended to help investigate whether a system
can reach an unwanted or inconsistent state.

## What can Flake model?

Flake can be used to model systems involving:

- multiple cooperating agents;
- coordinators and participants;
- distributed protocols;
- message passing;
- shared and local state;
- service orchestration;
- transaction workflows;
- autonomous software agents;
- LLM-based multi-agent systems.

For example, a system may contain a coordinator,
a payment service, an inventory service and an order service.

The model can help investigate what happens when:

- a message is lost;
- an agent stops responding;
- a coordinator crashes;
- one participant confirms an operation;
- another participant does not confirm it;
- the system reaches a partially completed state.

## Current status

Flake is in early development.

The current implementation is focused on the Python library
and its underlying formal model. The long-term goal is to
build a dedicated programming language for describing and
controlling agent-oriented systems.

## Documentation

- [Getting Started](getting-started.md)
- [Agents](concepts/agents.md)
- [States and Configurations](concepts/states.md)
- [Observations and Knowledge](concepts/observations.md)
- [Verification](concepts/verification.md)
- [Two-Phase Commit](examples/two-phase-commit.md)