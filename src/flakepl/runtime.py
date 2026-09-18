"""
Runtime API for FlakePL.

The current implementation is provided by the legacy `flake` package.
This module exposes it through the public `flakepl` namespace.
"""

from flake.runtime import (
    Configuration,
    GlobalState,
    SystemTransition,
    system_transitions,
)

__all__ = [
    "Configuration",
    "GlobalState",
    "SystemTransition",
    "system_transitions",
]