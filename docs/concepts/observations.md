# Observations and Knowledge

An agent does not necessarily see the entire global state.

In a distributed system, each agent may have access to only a limited part of the environment.

For example, a payment service may know the payment status, but may not know whether the inventory service has completed its own operation.

## Global state and local observation

There is an important difference between:

```text
The actual global state
```

and:

```text
The state visible to a particular agent
```

An agent may observe only a subset of the information contained in the global state.

For example:

```text
Global state:

Payment: authorized
Inventory: reserved
Order: pending
Coordinator: waiting
```

A payment service may observe only:

```text
Payment: authorized
```

It may not know whether inventory has been reserved or whether the order has been completed.

## Observations

An observation describes what information is available to an agent.

Two different global states may look identical to an agent if the agent cannot observe the difference.

For example:

```text
Global state A:
Payment: authorized
Inventory: reserved

Global state B:
Payment: authorized
Inventory: unavailable
```

If the payment service cannot observe inventory, both global states may appear identical to it.

## Why observations matter

Limited observations are important for:

- distributed systems;
- multi-agent coordination;
- partially observable environments;
- autonomous agents;
- security and access control;
- reasoning under incomplete information;
- decision-making with incomplete data.

An agent may make a decision based on incomplete information.

A formal model can help investigate whether that decision is safe in every state compatible with the agent's observations.

## Epistemic modeling

Flake includes an experimental epistemic layer.

Its purpose is to represent possible states and reason about:

- what an agent knows;
- what an agent does not know;
- which states an agent can distinguish;
- whether an agent knows another agent's state;
- whether information is common or private.

This direction is inspired by epistemic logic and multi-agent reasoning.

## Example

Suppose a coordinator sends a message to Participant 1.

Participant 1 may know:

```text
I received the message.
```

But Participant 1 may not know:

```text
Participant 2 also received the message.
```

The distinction is important for protocols that require coordinated decisions.

## Example: incomplete information

Suppose an agent observes:

```text
Payment: authorized
```

The actual system may be in one of two states:

```text
State A:
Payment: authorized
Inventory: reserved
```

or:

```text
State B:
Payment: authorized
Inventory: unavailable
```

If the agent cannot observe inventory, it must reason under uncertainty.

A safe decision may require checking whether the desired property holds in all states compatible with the observation.

## Current status

The epistemic layer is still under development.

Its API and semantics may change as the project evolves.