"""Operational semantics exposed through the public FlakePL namespace."""

from flake.semantics import synchronous_system_transitions

system_transitions = synchronous_system_transitions

__all__ = ["system_transitions", "synchronous_system_transitions"]
