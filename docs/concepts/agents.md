# Agents

An agent is an active participant in a Flake system.

An agent may represent:

- a microservice;
- a worker;
- a coordinator;
- a user;
- a robot;
- a software process;
- an autonomous program;
- an LLM-based agent.

An agent is not limited to a neural network. It is an abstract entity that can observe, change state and perform actions.

## Agent behavior

Agent behavior is described through processes.

A process specifies which actions an agent can perform and in what order those actions may occur.

For example:

```python
from flakepl import recv, send, stop


def participant_process():
    return (
        recv("prepare")
        >> send("ready")
        >> recv("commit")
        >> stop()
    )
```

This process describes a participant that:

1. waits for a `prepare` message;
2. sends a `ready` message;
3. waits for a `commit` message;
4. stops after receiving the commit message.

## Coordinator and participants

A system may contain different types of agents.

A coordinator may:

- send commands;
- wait for responses;
- coordinate several participants;
- make decisions;
- stop after completing a protocol;
- recover after failures.

A participant may:

- receive commands;
- perform local work;
- update its local state;
- send a response;
- wait for a final decision.

This structure is useful for modeling distributed protocols and multi-agent workflows.

## Agent state

An agent may have local state.

For example, a participant in a transaction protocol may have the following states:

```text
init
prepared
ready
commit
abort
```

The actual state representation depends on the model.

## Agent actions

An agent may perform different kinds of actions:

- send a message;
- receive a message;
- update its state;
- stop execution;
- interact with another agent;
- perform an operation in the environment.

The available actions depend on the current Flake runtime.

## Agents and knowledge

One of the long-term goals of Flake is to represent not only the physical state of an agent, but also its informational state.

This includes questions such as:

- What does the agent observe?
- What does the agent know?
- What does the agent believe?
- Does the agent know that another agent received a message?
- Can the agent distinguish two possible global states?
- What information is hidden from the agent?

These questions are important for distributed systems, multi-agent reasoning and autonomous software agents.

## LLM-based agents

An LLM can be used as the reasoning component of an agent.

In this architecture, the LLM may propose a decision, while Flake controls:

- available actions;
- state transitions;
- communication;
- permissions;
- protocol constraints;
- formal properties.

This separation allows heuristic reasoning and formal system control to be combined.

## Example: coordinator and participant

A coordinator may send a request to a participant:

```text
Coordinator → Participant: prepare
```

The participant processes the request:

```text
Participant:
    receive prepare
    perform local work
    send ready
```

The coordinator may then continue the protocol after receiving the response:

```text
Participant → Coordinator: ready
```

This pattern can be used to model:

- distributed transactions;
- service orchestration;
- approval workflows;
- resource allocation;
- multi-agent coordination.