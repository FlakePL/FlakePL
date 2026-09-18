from flakepl import (
    Agent,
    Atom,
    Configuration,
    EpistemicModel,
    GlobalState,
    K,
    observe_global,
    stop,
)


alice = Agent.create(
    "alice",
    stop(),
)

bob = Agent.create(
    "bob",
    stop(),
)


world_true = Configuration(
    state=GlobalState.from_dict(
        {"p": True}
    ),
    agents=(alice, bob),
)

world_false = Configuration(
    state=GlobalState.from_dict(
        {"p": False}
    ),
    agents=(alice, bob),
)


model = EpistemicModel(
    worlds=(
        world_true,
        world_false,
    ),
    observations={
        alice: observe_global("p"),
        bob: lambda agent, configuration: (),
    },
    actual=world_true,
)


p = Atom("p")


print(
    "Alice observes:",
    model.observe(alice, world_true),
)

print(
    "Bob observes:",
    model.observe(bob, world_true),
)

print(
    "Alice accessible worlds:",
    len(
        model.accessible(
            alice,
            world_true,
        )
    ),
)

print(
    "Bob accessible worlds:",
    len(
        model.accessible(
            bob,
            world_true,
        )
    ),
)

print(
    "Alice knows p:",
    model.check(K(alice, p)),
)

print(
    "Bob knows p:",
    model.check(K(bob, p)),
)