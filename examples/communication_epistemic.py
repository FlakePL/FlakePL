from flakepl import (
    Agent,
    Atom,
    Configuration,
    EpistemicModel,
    GlobalState,
    K,
    Proposition,
    explore,
    observe_local_state,
    recv,
    send,
    stop,
)


alice = Agent.create(
    "alice",
    send("channel", "secret") >> stop(),
)

bob = Agent.create(
    "bob",
    recv("channel", "x") >> stop(),
)


initial = Configuration(
    state=GlobalState(),
    agents=(
        alice,
        bob,
    ),
)


# ------------------------------------------------------------
# 1. Execute the process calculus.
# ------------------------------------------------------------

state_space = explore(initial)

print(
    f"Reachable configurations: "
    f"{len(state_space.states)}"
)

print(
    f"Transitions: "
    f"{len(state_space.transitions)}"
)


# ------------------------------------------------------------
# 2. Define epistemic observations.
# ------------------------------------------------------------

observations = {
    "alice": observe_local_state(),
    "bob": observe_local_state(),
}


# ------------------------------------------------------------
# 3. Define a semantic proposition.
# ------------------------------------------------------------

received_secret = Proposition(
    "bob.received_secret",
    lambda configuration:
        configuration.agent("bob").get_state("x")
        == "secret",
)


# ------------------------------------------------------------
# 4. Build the epistemic model from the state space.
# ------------------------------------------------------------

model = EpistemicModel.from_state_space(
    state_space,
    observations=observations,
    propositions={
        "bob.received_secret": received_secret,
    },
)


# ------------------------------------------------------------
# 5. Find the configuration where Bob received the secret.
# ------------------------------------------------------------

received_world = next(
    world
    for world in model.worlds
    if received_secret.holds(world)
)


print()
print("Received world:")
print(received_world)


# ------------------------------------------------------------
# 6. Check the proposition.
# ------------------------------------------------------------

received = Atom(
    "bob.received_secret"
)

print()
print(
    "Bob received secret:",
    model.check(
        received,
        at=received_world,
    ),
)


# ------------------------------------------------------------
# 7. Check Bob's knowledge.
# ------------------------------------------------------------

print(
    "Bob knows that he received secret:",
    model.check(
        K(
            bob,
            received,
        ),
        at=received_world,
    ),
)