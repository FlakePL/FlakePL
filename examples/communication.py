from flakepl import parallel, recv, send, stop, transitions


alice = send("channel", "secret") >> stop()
bob = recv("channel", "x") >> stop()
system = parallel(alice, bob)

print("Initial process:")
print(system)
print()

print("Available transitions:")
for transition in transitions(system):
    print(f"action={transition.action!r}")
    print(f"target={transition.target!r}")
    print()
