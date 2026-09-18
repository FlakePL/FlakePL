# FlakePL – MVP Specification

## 1. Identity

Project name:

    FlakePL

Distribution name:

    flakepl

Public Python namespace:

    flakepl

Legacy namespace:

    flake

`flake` remains available temporarily for compatibility with the
prototype API. New documentation and examples should use `flakepl`.

FlakePL is currently implemented as a Python library. The long-term
goal is a dedicated language and runtime, but the current implementation
is an executable semantic prototype.

---

## 2. Core idea

FlakePL combines three layers:

    process behavior
    +
    epistemic state
    +
    formal verification

The system starts from executable interacting processes.

Process execution produces configurations and transitions.

Configurations form a finite state space.

Agent observations induce epistemic relations.

Formulas are evaluated over those relations and over the transition
structure.

---

## 3. Process layer

Current process primitives:

    Nil
    Prefix
    Choice
    Parallel

Current actions:

    Tau
    Send
    Receive

The operational semantics is represented through SystemTransition:

    source
    action
    target

Communication can generate synchronized Tau transitions.

---

## 4. Runtime layer

A Configuration consists of:

    GlobalState
    +
    Agent[]

Each Agent contains:

    name
    process
    local state

StateSpace contains:

    initial worlds
    reachable states
    transitions

State-space exploration currently uses finite BFS.

---

## 5. Observation layer

Each agent has an observation function:

    h_i(w)

Two configurations are epistemically indistinguishable for agent i
when their observations are equal:

    w R_i v  iff  h_i(w) = h_i(v)

Observations can describe:

    local state
    local process
    public state
    combinations of the above

The ObservationBuilder provides the declarative API.

---

## 6. Epistemic layer

Current operators:

    K_i φ
    E_A φ
    D_A φ
    C_A φ

Where:

    K_i     individual knowledge
    E_A     everyone knows
    D_A     distributed knowledge
    C_A     common knowledge

Boolean composition:

    φ & ψ
    φ | ψ
    ~φ

---

## 7. Temporal layer

Current temporal operators:

    X φ
    F φ
    G φ
    φ U ψ

The current temporal semantics is finite-state and universal-path based.

Terminal states use stuttering semantics.

---

## 8. Dynamic epistemic layer

Current dynamic operations:

    PublicAnnouncement
    ActionModel
    ProductUpdate

Public announcement restricts the model to worlds satisfying φ.

Action models describe events with:

    event name
    precondition
    event epistemic relation

Product update creates worlds representing:

    (world, event)

---

## 9. Process-aware epistemic execution

FlakePL now connects process execution with epistemic updates.

A SystemTransition can be converted into a dynamic event:

    ProcessExecutionEvent

The event is based on:

    source configuration
    process action
    target configuration

Post-event epistemic accessibility combines three conditions:

    source epistemic compatibility
    +
    event observation compatibility
    +
    target observation compatibility

Conceptually:

    (w --a--> w')
       ~
    (v --b--> v')

for agent i when:

    w R_i v
    and
    event_obs_i(a) = event_obs_i(b)
    and
    h_i(w') = h_i(v')

The resulting epistemic worlds preserve the fact that an execution
event happened. Internally this is represented using ProductWorld.

---

## 10. Event observations

Default action observations distinguish:

    action kind
    channel

but do not reveal payload values.

Example:

    send("c", "secret")

is observed as:

    kind = send
    channel = c

and not as:

    value = secret

Custom policies are possible.

Examples:

    observe_action(...)
    blind_action()

This allows the model to explicitly represent public, partial and
blind observation of events.

---

## 11. Example

A typical FlakePL workflow is:

    alice = send("c", secret) >> stop()
    bob   = recv("c", "x") >> stop()

    configuration
        ↓
    explore()
        ↓
    StateSpace
        ↓
    EpistemicModel
        ↓
    execute(transition)
        ↓
    updated epistemic model
        ↓
    K("bob", received)

This is the central executable path of the MVP.

---

## 12. Current MVP scope

Implemented:

    process calculus
    SOS transitions
    agents
    local state
    state-space exploration
    multiple initial worlds
    observations
    K / E / D / C
    X / F / G / U
    public announcement
    action models
    product update
    process-aware epistemic execution

Not yet part of MVP:

    dedicated FlakePL parser
    standalone compiler
    LLM runtime
    automatic tool orchestration
    ATL strategies
    distributed model checking
    large-scale symbolic model checking
    full action-model language
    probabilistic semantics

---

## 13. Long-term direction

The intended evolution is:

    Python semantic prototype
            ↓
    stable FlakePL core API
            ↓
    dedicated FlakePL DSL
            ↓
    process + epistemic + temporal programs
            ↓
    strategic agent behavior
            ↓
    AI / LLM agent integration

The core principle is:

    behavior
      +
    information
      +
    verification

should belong to one programming model rather than being implemented
as unrelated layers.