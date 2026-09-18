# Flake: Practical Python API Examples

Flake allows you to describe systems as interacting agents, define their state and behavior, and verify properties of the resulting model.

This page focuses on practical usage of the library: how to create agents, define state, compose processes, exchange messages, build logical formulas, model observations, create epistemic models, and verify system properties.

> The examples below should match the public API of the installed Flake version. If an import or constructor differs in your version, use the corresponding implementation from the current source code or tests.

## Creating Agents

An agent is a participant in the modeled system.

An agent can represent a payment service, warehouse, CRM, user, authorization service, transaction coordinator, external API, or an LLM-based module.

```python
from flake import Agent

payment_service = Agent("payment_service")
warehouse_service = Agent("warehouse_service")
crm_service = Agent("crm_service")
```

The agent name identifies the agent inside the model.

```python
customer = Agent("customer")
payment = Agent("payment")
warehouse = Agent("warehouse")
```

This represents the following interaction:

```text
customer → payment → warehouse
```

## Defining System State

The state contains the data that determines how the system behaves.

For example, an order can have the following state:

```python
from flake import GlobalState

state = GlobalState(
    order_created=False,
    payment_confirmed=False,
    item_reserved=False,
    order_shipped=False,
)
```

After some operations, the state may become:

```python
state = GlobalState(
    order_created=True,
    payment_confirmed=True,
    item_reserved=True,
    order_shipped=False,
)
```

This means that the order has been created, the payment has been confirmed, the item has been reserved, and the order has not been shipped yet.

A domain-oriented state can look like this:

```python
state = GlobalState(
    order_status="created",
    payment_status="confirmed",
    inventory_status="reserved",
    shipment_status="pending",
)
```

State should contain the information required to describe current system conditions, possible transitions, agent decisions, safety properties, liveness properties, permissions, and business rules.

## Defining Processes

A process describes the behavior of an agent.

A typical order-processing workflow looks like this:

```text
receive an order
→ validate payment
→ reserve an item
→ notify the warehouse
→ finish processing
```

Processes can be composed from smaller operations:

```python
process = (
    receive_order
    >> validate_payment
    >> reserve_item
    >> notify_warehouse
    >> stop()
)
```

The `>>` operator represents sequential composition: execute the left operation and then execute the right operation.

For example:

```python
prepare >> commit
```

means:

```text
prepare
→ commit
```

Sequential composition does not automatically make a workflow atomic. Between two operations, the system may experience a failure, timeout, lost message, agent crash, state change by another agent, or unexpected transition.

For this reason, intermediate states should be checked explicitly.

## Sending and Receiving Messages

Agents can communicate by sending and receiving messages.

```python
from flake import send, recv, stop
```

A payment service process may look like this:

```python
payment_process = (
    recv("payment_request")
    >> send("warehouse_service", "payment_confirmed")
    >> stop()
)
```

The process means:

```text
receive a payment request
→ send a payment confirmation to the warehouse
→ stop
```

A warehouse process may look like this:

```python
warehouse_process = (
    recv("payment_confirmed")
    >> send("warehouse_service", "prepare_shipment")
    >> stop()
)
```

This represents a simple service interaction:

```text
Payment Service
    ↓ payment_confirmed
Warehouse Service
    ↓ prepare_shipment
Shipment Service
```

Message-based models can be used to investigate lost messages, duplicated messages, messages arriving in the wrong order, blocked processes, premature actions, invalid transitions, and incomplete workflows.

## Example: Order Processing

Consider the following workflow:

```text
1. Create an order.
2. Confirm the payment.
3. Reserve the item.
4. Ship the order.
```

The system may contain four agents:

```python
from flake import Agent

crm = Agent("crm")
payment = Agent("payment")
inventory = Agent("inventory")
warehouse = Agent("warehouse")
```

The initial state can be described as:

```python
from flake import GlobalState

state = GlobalState(
    order_created=False,
    payment_confirmed=False,
    item_reserved=False,
    order_shipped=False,
)
```

The workflow contains the following actions:

```text
create_order
confirm_payment
reserve_item
ship_order
```

The main business rule is:

```text
An order must not be shipped before its payment is confirmed.
```

This can be expressed as:

```text
G(shipped(order) → paid(order))
```

The meaning is:

> On every valid execution trace, a shipped order must be paid.

Other useful properties include:

```text
G(shipped(order) → created(order))
```

A shipped order must exist.

```text
G(shipped(order) → reserved(order))
```

An order can be shipped only after the item has been reserved.

```text
G(refunded(order) → paid(order))
```

A refund can be performed only for a paid order.

If an incorrect protocol allows:

```text
create_order
→ ship_order
```

then the model may violate:

```text
G(shipped(order) → paid(order))
```

The property can be checked with:

```python
result = model.check(formula)

print(result)
```

If the result is:

```python
True
```

the property holds in the modeled system.

If the result is:

```python
False
```

the model allows a behavior that violates the property.

## Example: Access Control

Consider a corporate system where only authorized users can issue refunds.

```python
from flake import Agent

user = Agent("user")
authorization_service = Agent("authorization_service")
order_service = Agent("order_service")
audit_service = Agent("audit_service")
```

The state may contain:

```python
from flake import GlobalState

state = GlobalState(
    user_role="customer",
    order_exists=True,
    order_paid=True,
    order_refunded=False,
)
```

The `refund_order` operation should depend on several conditions:

```text
The order exists.
The order has been paid.
The order has not already been refunded.
The user has permission to issue a refund.
```

The main property is:

```text
G(refund(order) → authorized(user))
```

The meaning is:

> Every refund must be performed by an authorized user.

Additional properties include:

```text
G(refund(order) → exists(order))
```

A nonexistent order cannot be refunded.

```text
G(refund(order) → paid(order))
```

An unpaid order cannot be refunded.

```text
G(refund(order) → not refunded(order))
```

The same refund cannot be executed twice.

```text
G(refund(order) → audit_event_exists(order))
```

Every refund must produce an audit event.

This type of model is useful for CRM systems, ERP systems, banking operations, administrative panels, corporate APIs, multi-tenant SaaS, and document-management systems.

## Example: Two-Phase Commit

Consider a distributed operation involving two services:

```text
Service A
Service B
```

Both services must prepare successfully before the operation can be committed.

The state may be:

```python
from flake import GlobalState

state = GlobalState(
    prepared_a=False,
    prepared_b=False,
    committed_a=False,
    committed_b=False,
)
```

The relevant actions are:

```text
prepare_a
prepare_b
commit_a
commit_b
```

An incorrect execution may look like this:

```text
1. prepare_a
2. prepare_b
3. commit_a
4. The coordinator fails.
5. commit_b is never executed.
```

The resulting state is:

```text
committed_a = True
committed_b = False
```

If this state is forbidden, the system should satisfy:

```text
G(not (committed_a and not committed_b))
```

The meaning is:

> One participant must not commit while the other participant remains uncommitted.

A separate liveness property can be:

```text
F(committed_a and committed_b)
```

The meaning is:

> Eventually, both participants commit.

These properties check different aspects of the system.

`G(...)` checks that a forbidden state is never reached.

`F(...)` checks that a desired state is eventually reached.

An important distinction is that eventual completion does not imply atomicity.

A system may eventually reach:

```text
committed_a = True
committed_b = True
```

while still passing through the unsafe intermediate state:

```text
committed_a = True
committed_b = False
```

This example is relevant to distributed transactions, payment systems, inventory reservations, microservice coordination, multi-database updates, and enterprise workflows.

## Logical Atoms

An atomic logical statement can be created with `Atom`.

```python
from flake import Atom

paid = Atom("paid")
shipped = Atom("shipped")
created = Atom("created")
```

An atom represents a simple proposition about the system.

For example:

```python
paid = Atom("paid")
```

can be read as:

```text
The order has been paid.
```

Atoms can be combined using logical operators.

```python
formula = paid & ~shipped
```

This means:

```text
The order is paid and has not been shipped.
```

Other examples:

```python
formula = paid | shipped
```

The order is paid or shipped.

```python
formula = ~(paid & shipped)
```

It is not the case that the order is both paid and shipped.

The exact set of supported operators depends on the current Flake implementation.

## Temporal Properties

The `F` operator represents "eventually".

For example:

```python
from flake import Atom, F

order_completed = Atom("order_completed")

formula = F(order_completed)
```

The meaning is:

> The order will eventually be completed.

This is a liveness property.

Other examples:

```text
F(order_completed)
```

The order eventually completes.

```text
F(payment_confirmed)
```

The payment is eventually confirmed.

```text
F(message_delivered)
```

The message is eventually delivered.

Temporal properties are useful for detecting blocked workflows.

For example:

```text
The order is created.
The process waits for a message.
The message never arrives.
The order never completes.
```

A property such as:

```text
F(order_completed)
```

can reveal that the desired completion state is not reachable.

## Checking a Model

After defining agents, state, and processes, the system model can be created.

For example:

```python
model = Configuration(
    agents=[
        crm,
        payment,
        warehouse,
    ],
)
```

A logical property can then be defined:

```python
formula = Atom("safe")
```

The property is checked with:

```python
result = model.check(formula)

print(result)
```

The result is a Boolean value:

```python
True
```

or:

```python
False
```

A value of `True` means that the formula holds in the model.

A value of `False` means that the model contains behavior that does not satisfy the formula.

A basic verification pattern is therefore:

```python
formula = Atom("safe")

if model.check(formula):
    print("Property holds")
else:
    print("Property does not hold")
```

## Building a Complete Model

A complete application typically follows this structure:

```python
from flake import (
    Agent,
    Configuration,
    GlobalState,
    Atom,
    F,
    send,
    recv,
    stop,
)

crm = Agent("crm")
payment = Agent("payment")
warehouse = Agent("warehouse")

state = GlobalState(
    order_created=False,
    payment_confirmed=False,
    item_reserved=False,
    order_shipped=False,
)

payment_process = (
    recv("payment_request")
    >> send("warehouse", "payment_confirmed")
    >> stop()
)

warehouse_process = (
    recv("payment_confirmed")
    >> send("warehouse", "prepare_shipment")
    >> stop()
)

model = Configuration(
    agents=[
        crm,
        payment,
        warehouse,
    ],
)

order_completed = Atom("order_completed")

formula = F(order_completed)

result = model.check(formula)

print(result)
```

The general structure is:

```text
create agents
→ define state
→ define processes
→ compose the system
→ define a property
→ check the model
```

## Observations

Different agents may see different parts of the global state.

For example, a CRM system may see customer data, a payment service may see payment information, a warehouse may see inventory state, and a user may see only their own order.

`ObservationBuilder` can be used to describe the information available to an agent.

```python
from flake import ObservationBuilder

observation = ObservationBuilder(
    visible_fields=[
        "order_status",
        "payment_status",
    ]
)
```

This represents an observation containing:

```text
order_status
payment_status
```

while other internal information may remain hidden from that agent.

Observations are useful when the model needs to represent what an agent can actually distinguish from what exists in the global state.

Typical questions include:

```text
Does the agent know that the order is paid?
Can the agent distinguish two system states?
Does the agent have enough information to make a decision?
Can the agent observe that another service has already completed an action?
```

## Epistemic Models

Flake can represent knowledge through observations and state indistinguishability.

An epistemic model can be created with `EpistemicModel`.

```python
from flake import EpistemicModel

epistemic_model = EpistemicModel(
    observations=observation
)
```

If two states produce the same observation for an agent, those states are indistinguishable from that agent's point of view.

For example, a warehouse may observe:

```text
payment_status = confirmed
```

while not observing:

```text
who confirmed the payment
which payment provider was used
the internal payment risk score
```

The epistemic model therefore captures the difference between the complete system state and the information available to a particular agent.

This is useful for distributed systems, multi-agent systems, access control, coordination problems, incomplete-information protocols, and agent-based decision making.

The exact syntax for epistemic formulas depends on the current Flake implementation.

## Example: Distributed Knowledge

Suppose two agents observe different parts of the system.

```python
from flake import Agent

payment = Agent("payment")
warehouse = Agent("warehouse")
```

The payment agent may observe:

```text
payment_status
transaction_id
```

while the warehouse agent may observe:

```text
inventory_status
order_status
```

Neither agent necessarily has access to the complete global state.

This distinction matters in distributed protocols.

For example, a coordinator may know:

```text
payment = confirmed
inventory = reserved
```

while the payment service knows only:

```text
payment = confirmed
```

and the warehouse knows only:

```text
inventory = reserved
```

An epistemic model allows these information boundaries to be represented explicitly.

## Example: Permissioned Agent System

A permissioned agent system can combine agents, state, observations, and logical verification.

```python
from flake import Agent, GlobalState, ObservationBuilder

admin = Agent("admin")
user = Agent("user")
service = Agent("service")

state = GlobalState(
    user_role="user",
    resource_exists=True,
    resource_deleted=False,
)

user_observation = ObservationBuilder(
    visible_fields=[
        "resource_exists",
    ]
)
```

The user may be able to observe that a resource exists without observing internal administrative information.

A system property can then be used to verify that an unauthorized operation cannot occur.

For example:

```text
G(delete(resource) → authorized(user))
```

The intended meaning is:

> Every delete operation must be authorized.

## Example: Microservice Protocol

Consider a three-service workflow:

```text
API
 ↓
Payment
 ↓
Warehouse
```

The agents can be represented as:

```python
from flake import Agent

api = Agent("api")
payment = Agent("payment")
warehouse = Agent("warehouse")
```

The payment service waits for a request:

```python
payment_process = (
    recv("payment_request")
    >> send("warehouse", "payment_confirmed")
    >> stop()
)
```

The warehouse receives the confirmation:

```python
warehouse_process = (
    recv("payment_confirmed")
    >> send("warehouse", "prepare_shipment")
    >> stop()
)
```

A verification model can then be used to check protocol properties such as:

```text
A shipment request cannot occur before payment confirmation.
A payment confirmation cannot be produced without the corresponding request.
A workflow eventually reaches completion.
A participant cannot commit independently of the required protocol state.
```

## Example: Detecting a Broken Protocol

Suppose a protocol contains:

```text
prepare_a
prepare_b
commit_a
commit_b
```

The correct protocol requires both participants to prepare before either participant commits.

An incorrect implementation may allow:

```text
prepare_a
→ commit_a
→ prepare_b
→ commit_b
```

A safety property such as:

```text
G(commit_a → prepared_b)
```

can express that participant A must not commit until participant B has prepared.

Another property can require the final state:

```text
F(commit_a and commit_b)
```

The first property checks safety.

The second property checks eventual completion.

Both properties are useful because a protocol can satisfy one and violate the other.

## Example: State Invariants

Suppose an inventory system tracks:

```python
state = GlobalState(
    stock=10,
    reserved=3,
    sold=2,
)
```

A basic invariant is:

```text
reserved + sold ≤ stock
```

The purpose of the invariant is to ensure that the system never allocates more inventory than exists.

Other examples include:

```text
balance >= 0
```

```text
reserved_items <= available_items
```

```text
active_sessions <= max_sessions
```

```text
shipped_orders <= created_orders
```

```text
refunded_orders <= paid_orders
```

A model checker can be used to test these kinds of constraints across the reachable states of the modeled system.

## Example: Workflow Verification

A document approval workflow may contain:

```text
created
→ submitted
→ reviewed
→ approved
→ archived
```

The corresponding agents might be:

```python
from flake import Agent

author = Agent("author")
reviewer = Agent("reviewer")
manager = Agent("manager")
archive = Agent("archive")
```

The workflow can be understood as a sequence of state transitions.

Useful properties include:

```text
G(approved(document) → reviewed(document))
```

A document cannot be approved before review.

```text
G(archived(document) → approved(document))
```

A document cannot be archived before approval.

```text
F(archived(document))
```

A valid document should eventually reach the archived state.

These properties expose both safety violations and liveness failures.

## Example: LLM Agent Verification

Flake can also be used around agentic or LLM-based systems.

An LLM agent may propose:

```text
refund_order
```

The formal model can represent the state:

```python
state = GlobalState(
    order_exists=True,
    order_paid=True,
    order_refunded=False,
)
```

The system can then verify constraints such as:

```text
G(refund(order) → exists(order))
```

```text
G(refund(order) → paid(order))
```

```text
G(refund(order) → not refunded(order))
```

The LLM is responsible for proposing an action.

The formal model is responsible for checking whether the action is compatible with the modeled state and rules.

This creates a useful separation:

```text
LLM / agent
    ↓
proposed action
    ↓
Flake model
    ↓
formal verification
    ↓
allowed / rejected transition
```

This pattern can be used for autonomous workflows, tool-using agents, enterprise automation, multi-agent coordination, and safety-constrained AI systems.

## Example: Complete Two-Agent Model

A simple two-agent system can be organized as follows:

```python
from flake import (
    Agent,
    Configuration,
    GlobalState,
    Atom,
    F,
)

alice = Agent("alice")
bob = Agent("bob")

state = GlobalState(
    request_sent=False,
    response_received=False,
)

request_sent = Atom("request_sent")
response_received = Atom("response_received")

formula = F(response_received)

model = Configuration(
    agents=[
        alice,
        bob,
    ],
)

result = model.check(formula)

print(result)
```

The important parts are:

```text
Agent
```

creates participants.

```text
GlobalState
```

describes the state.

```text
Atom
```

creates logical propositions.

```text
F
```

describes eventuality.

```text
Configuration
```

creates the system model.

```text
model.check(...)
```

verifies a property.

## Example: Safety and Liveness Together

A realistic distributed system usually needs both safety and liveness properties.

Consider a payment system.

Safety:

```text
G(charged(order) → authorized(order))
```

A charge must always be authorized.

Liveness:

```text
F(payment_confirmed(order))
```

A valid payment should eventually be confirmed.

Another safety property:

```text
G(charged(order) → not already_charged(order))
```

The same order must not be charged twice.

Another liveness property:

```text
F(order_completed(order))
```

The order should eventually complete.

Together these properties describe both what must never happen and what should eventually happen.

## Example: A Minimal Verification Workflow

The smallest useful workflow is:

```python
from flake import Atom, Configuration, Agent

agent = Agent("agent")

model = Configuration(
    agents=[agent],
)

safe = Atom("safe")

result = model.check(safe)

print(result)
```

The general pattern is always:

```python
# Create entities.
agent = Agent("agent")

# Build the model.
model = Configuration(
    agents=[agent],
)

# Define a property.
property = Atom("safe")

# Verify it.
result = model.check(property)

# Use the result.
print(result)
```

## Main Public Concepts

The main Flake concepts used by applications are:

```text
Agent
```

Represents a participant in the system.

```text
Configuration
```

Represents a configured model containing the system components.

```text
GlobalState
```

Represents the state of the modeled system.

```text
send
```

Represents message transmission.

```text
recv
```

Represents message reception.

```text
stop
```

Terminates a process.

```text
>>
```

Composes operations sequentially.

```text
Atom
```

Represents an atomic logical proposition.

```text
Proposition
```

Represents a logical property.

```text
F
```

Represents eventuality.

```text
ObservationBuilder
```

Defines the information observable by an agent.

```text
EpistemicModel
```

Represents knowledge through observations and state indistinguishability.

```text
model.check(...)
```

Checks whether a logical property holds in the model.

## Typical Application Structure

A typical Flake application can therefore be organized like this:

```python
from flake import (
    Agent,
    Configuration,
    GlobalState,
    ObservationBuilder,
    EpistemicModel,
    Atom,
    Proposition,
    F,
    send,
    recv,
    stop,
)

# Agents
client = Agent("client")
service = Agent("service")
worker = Agent("worker")

# State
state = GlobalState(
    request_created=False,
    request_processed=False,
    request_completed=False,
)

# Processes
service_process = (
    recv("request")
    >> send("worker", "process")
    >> stop()
)

worker_process = (
    recv("process")
    >> send("service", "completed")
    >> stop()
)

# Logical property
request_completed = Atom("request_completed")
eventual_completion = F(request_completed)

# Model
model = Configuration(
    agents=[
        client,
        service,
        worker,
    ],
)

# Verification
result = model.check(eventual_completion)

print(result)
```

The central idea is simple:

```text
Define the system
        ↓
Define its possible behavior
        ↓
Define what agents can observe
        ↓
Define properties of the system
        ↓
Verify the properties
```

Flake is therefore used to describe and verify agent-based systems rather than merely execute a single deterministic program.

## Why Use Flake?

Flake is useful when the important question is not only:

```text
"What does this function do?"
```

but also:

```text
"What behaviors are possible for the whole system?"
```

The same approach can be applied to:

```text
distributed systems
microservices
workflow engines
authorization systems
transaction protocols
multi-agent systems
LLM-based agents
coordination protocols
state machines
formal verification experiments
```

A typical application combines several Flake concepts:

```text
Agents
+
State
+
Processes
+
Messages
+
Observations
+
Logical Properties
+
Model Checking
```

The resulting model can be used to explore whether a system is safe, whether required events eventually occur, whether agents have sufficient information, and whether a protocol permits invalid intermediate states.