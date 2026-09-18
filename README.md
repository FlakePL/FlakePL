# FlakePL

FlakePL is a small Python library for modeling and exploring finite multi-agent systems with process semantics, epistemic logic, temporal properties, dynamic epistemic updates, and executable protocol transitions.

The current goal is deliberately modest: provide a clean, testable MVP library. A dedicated FlakePL programming language is a later stage and is not part of the current release.

## MVP capabilities

- process algebra: `Nil`, `Prefix`, `Choice`, `Parallel`
- actions: `Tau`, `Send`, `Receive`
- executable system configurations and immutable agent state
- finite state-space exploration
- observations and epistemic relations
- `K`, `E`, `D`, `C` knowledge operators
- boolean formulas
- temporal operators `X`, `F`, `G`, `U`
- public announcements and action-model product updates
- process-aware epistemic execution
- counterexample traces for temporal verification

## Installation

```bash
python -m pip install flakepl
```

The public API is:

```python
from flakepl import ...
```

The old `flake` namespace remains available temporarily for compatibility with the prototype.

## Quick example

```python
from flakepl import Agent, Configuration, GlobalState, explore, recv, send, stop

alice = Agent.create(
    "alice",
    send("channel", "secret") >> stop(),
)

bob = Agent.create(
    "bob",
    recv("channel", "value") >> stop(),
)

initial = Configuration(
    state=GlobalState(),
    agents=(alice, bob),
)

space = explore(initial)

print("states:", len(space.states))
print("transitions:", len(space.transitions))
```

## Epistemic model

```python
from flakepl import Atom, EpistemicModel, K, observe_local_state

model = EpistemicModel.from_state_space(
    space,
    observations={
        "alice": observe_local_state(),
        "bob": observe_local_state(),
    },
)

# Evaluate a registered proposition with model.check(...).
```

See `examples/` for complete runnable programs, including a two-phase-commit verification example.

## Development

Run the full test suite:

```bash
python -m pytest -q
```

Compile all sources:

```bash
python -m compileall -q src tests
```

## Project layout

```text
src/flake/       implementation and legacy compatibility API
src/flakepl/     public FlakePL API
examples/        runnable MVP examples
tests/           unit, semantic, integration, and example tests
```

## Status

FlakePL is alpha software. The MVP API is intentionally small and may evolve before 1.0.

## License

The repository license will be added before the first public release.
