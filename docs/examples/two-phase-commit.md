# Two-Phase Commit

Two-phase commit is a distributed coordination protocol.

A coordinator communicates with several participants and attempts to make them reach a common decision.

The protocol is commonly divided into two phases:

1. prepare;
2. commit.

## Prepare phase

The coordinator asks participants whether they are ready.

Participants respond with readiness messages.

```text
Coordinator → Participant 1: prepare
Coordinator → Participant 2: prepare

Participant 1 → Coordinator: ready
Participant 2 → Coordinator: ready
```

## Commit phase

If the required participants are ready, the coordinator sends commit commands.

```text
Coordinator → Participant 1: commit
Coordinator → Participant 2: commit
```

## Modeling a participant

A simplified participant process may look like this:

```python
from flakepl import recv, send, stop


def participant_process(number):
    return (
        recv(f"prepare{number}")
        >> send(f"ready{number}")
        >> recv(f"commit{number}")
        >> stop()
    )
```

The participant:

1. waits for a prepare message;
2. sends a ready message;
3. waits for a commit message;
4. stops after receiving the commit message.

## Modeling the coordinator

A simplified coordinator process may look like this:

```python
from flakepl import recv, send, stop


def coordinator_process():
    return (
        send("prepare1")
        >> send("prepare2")
        >> recv("ready1")
        >> recv("ready2")
        >> send("commit1")
        >> send("commit2")
        >> stop()
    )
```

The coordinator:

1. prepares Participant 1;
2. prepares Participant 2;
3. waits for both ready messages;
4. sends commit to Participant 1;
5. sends commit to Participant 2;
6. stops.

## Failure scenario

Consider a coordinator that stops after sending `commit1` but before sending `commit2`.

The resulting system may look like this:

```text
Participant 1: committed
Participant 2: not committed
Coordinator: stopped
```

This is a partial commit.

A model can be used to check whether such a state is reachable.

## Eventual completion

One possible requirement is:

```text
Both participants eventually commit.
```

This is a liveness-style requirement.

A correct execution may eventually reach:

```text
Participant 1: committed
Participant 2: committed
```

## Atomicity requirement

A stronger requirement is:

```text
The system must never pass through a state
where only one participant has committed.
```

This is a safety property.

A sequential implementation with separate `commit1` and `commit2` transitions may violate this property, even if both participants eventually commit.

## Intermediate state

For example, the protocol may pass through the following states.

Before the first commit:

```text
Participant 1: ready
Participant 2: ready
```

After the first commit:

```text
Participant 1: committed
Participant 2: ready
```

After the second commit:

```text
Participant 1: committed
Participant 2: committed
```

The intermediate state is important.

It shows that eventual completion and atomic commit are different requirements.

## What this example demonstrates

The example shows how Flake can be used to investigate:

- message ordering;
- coordinator failures;
- participant failures;
- partial completion;
- reachable states;
- safety properties;
- liveness properties;
- distributed protocol behavior;
- inconsistent intermediate states.

It also demonstrates an important modeling distinction.

A protocol may eventually commit all participants, while still passing through an intermediate state where only one participant has committed.

Whether this is acceptable depends on the property that the system is required to satisfy.