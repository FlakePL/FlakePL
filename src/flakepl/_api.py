"""
Public compatibility API for FlakePL.

The implementation currently lives in the legacy ``flake`` package.
FlakePL re-exports that API while preserving compatibility with older
imports such as ``system_transitions`` and ``Proposition``.
"""

from flake import *
from flake import __all__ as _flake_all

from flake.propositions import (
    Proposition,
)

from flake.semantics import (
    synchronous_system_transitions,
)


# Backward-compatible name used by the original API.
system_transitions = synchronous_system_transitions


__all__ = [
    *_flake_all,
    "Proposition",
    "system_transitions",
]