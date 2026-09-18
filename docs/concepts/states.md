# States and Configurations

Flake models a system through states and configurations.

A state describes the current situation of a system.

A configuration describes the agents in the system and their current states.

## Global state

The global state describes the state of the entire system.

It may include:

- the state of each agent;
- shared resources;
- messages;
- protocol decisions;
- external environment data;
- completed operations;
- pending operations;
- failures;
- permissions.

A global state answers the question:

> What is the current situation of the whole system?

## Local agent state

Each agent may have its own local state.

For example, a participant in a transaction protocol may have a decision state:

```text
init
prepared
ready
commit
abort
```

A payment service may have states such as:

```text
created
processing
authorized
captured
failed
refunded
```

The exact state representation depends on the model.

## Configuration

A configuration connects agents with their current states.

It describes:

- which agents exist;
- the local state of each agent;
- the current global state;
- the relationships between system components.

A configuration can be used to express propositions about a particular agent:

```python
configuration.agent("participant_1")
```

A proposition may then inspect a value in that agent's state:

```python
configuration.agent("participant_1").get_state("decision")
```

## State transitions

A process changes the system by performing actions.

Each action may produce a new state.

Conceptually:

```text
State A
   │
   │ action
   ▼
State B
```

For example:

```text
Participant: init
      │
      │ receive prepare
      ▼
Participant: prepared
      │
      │ send ready
      ▼
Participant: ready
      │
      │ receive commit
      ▼
Participant: commit
```

## Reachable states

A state is reachable if the system can arrive at that state through a sequence of valid transitions.

State-space exploration investigates which states can be reached from an initial configuration.

This is useful for finding:

- forbidden states;
- deadlocks;
- partial completion;
- inconsistent decisions;
- unexpected message orderings;
- protocol failures;
- blocked agents;
- unreleased resources.

## Example: partial completion

Consider two participants:

```text
Participant 1: committed
Participant 2: ready
```

This may be a reachable intermediate state if the coordinator sends a commit command to the first participant before sending it to the second participant.

Whether this state is acceptable depends on the property that the system must satisfy.

## Example: inconsistent information

A system may contain two agents with different views:

```text
Payment service: payment authorized
Inventory service: item unavailable
```

The global state may contain both facts simultaneously.

A formal model can be used to investigate whether this combination is allowed and what actions the agents may perform next.

## Why state modeling matters

State modeling makes it possible to investigate situations that are difficult to cover with ordinary examples.

For example:

- one agent has committed;
- another agent has not committed;
- a message is waiting to be delivered;
- a coordinator has stopped;
- a participant is blocked;
- a resource has been reserved but not released;
- two services have conflicting information;
- an operation has been performed twice;
- an agent has insufficient information to make a safe decision.

These situations can then be described using logical properties and checked automatically.