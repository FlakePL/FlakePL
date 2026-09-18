"""
Process calculus API for FlakePL.
"""

from flake.process import (
    Choice,
    Nil,
    Parallel,
    Prefix,
    Process,
    choice,
    parallel,
    recv,
    send,
    stop,
    tau,
)

__all__ = [
    "Choice",
    "Nil",
    "Parallel",
    "Prefix",
    "Process",
    "choice",
    "parallel",
    "recv",
    "send",
    "stop",
    "tau",
]