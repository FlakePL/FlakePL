# Verification

Flake is designed not only to execute agent processes, but also to check properties of the modeled system.

A model describes possible states and transitions.

A formula describes a requirement about those states.

The verification process checks whether the modeled system satisfies the specified formula.

## Properties

A property is a logical statement about the system.

Examples:

> Both participants eventually commit.

> A participant cannot commit before receiving approval.

> A forbidden state must never be reached.

> Two agents must not make conflicting decisions.

> If a coordinator stops, the system must not silently report successful completion to every participant.

## Safety

A safety property describes something bad that must never happen.

Examples:

- two participants cannot hold conflicting decisions;
- a payment cannot be confirmed twice;
- a participant cannot commit without authorization;
- the system cannot reach an inconsistent state;
- a resource cannot be allocated to two owners at once;
- an agent cannot perform an action without permission.

A safety violation is demonstrated by a reachable state in which the forbidden condition is true.

Conceptually:

```text
Initial state
      ↓
Valid transition
      ↓
Valid transition
      ↓
Forbidden state
```

## Liveness

A liveness property describes something good that should eventually happen.

Examples:

- a valid transaction eventually completes;
- a participant eventually receives a response;
- a request does not remain blocked forever;
- all participants eventually reach a final state;
- a service eventually releases a reserved resource.

Liveness is concerned with progress over time.

## Safety and liveness are different

The following two statements are different:

```text
Both participants eventually commit.
```

and:

```text
The system never passes through a state
where only one participant has committed.
```

The first is a liveness-style requirement.

The second is a safety requirement.

A sequential protocol may satisfy the first while violating the second because one participant can commit before the other.

## Checking a property

The current checking interface returns a boolean result:

```python
result = model.check(formula)
```

A successful result means that the formula holds under the semantics implemented by the current model.

A failed result means that the formula is violated.

```python
assert model.check(formula) is True
```

or:

```python
assert model.check(formula) is False
```

## Example of a proposition

A proposition may describe the state of an agent:

```python
participant_1_committed = (
    configuration.agent("participant_1")
    .get_state("decision") == "commit"
)
```

A formula can then use this proposition to describe a requirement about the system.

## Verification of distributed protocols

Flake can be used to investigate:

- message ordering;
- coordinator failures;
- participant failures;
- partial completion;
- deadlocks;
- inconsistent decisions;
- unreachable states;
- protocol violations;
- blocked processes;
- incorrect assumptions about agent knowledge.

The goal is to find problematic scenarios before they appear in production.

## Example: transaction consistency

Suppose a transaction involves two participants.

A property may state:

```text
If Participant 1 commits,
then Participant 2 must also eventually commit.
```

Another property may state:

```text
There must never be a reachable state
where only Participant 1 has committed.
```

These formulas express different requirements and must be checked separately.

## Current limitations

Flake is currently an experimental library.

The supported formulas, temporal semantics, state-space exploration and counterexample facilities are still evolving.

The exact meaning of a verification result depends on the semantics implemented by the current version.