from flakepl import Agent, Configuration, GlobalState, explore, recv, send, stop


alice = Agent.create("alice", send("channel", "secret") >> stop())
bob = Agent.create("bob", recv("channel", "x") >> stop())

initial = Configuration(
    state=GlobalState(),
    agents=(alice, bob),
)

space = explore(initial)

print(f"Reachable states: {len(space.states)}")
print(f"Transitions: {len(space.transitions)}")
print()

for index, state in enumerate(space.states):
    print(f"STATE {index}")
    print(f"  global state: {state.state}")
    for agent in state.agents:
        print(f"  {agent.name}:")
        print(f"    process = {agent.process!r}")
        print(f"    state   = {dict(agent.state)!r}")
    print()

print("TRANSITIONS")
for transition in space.transitions:
    print(
        f"{transition.source.processes}"
        f" -- {transition.action!r} --> "
        f"{transition.target.processes}"
    )
