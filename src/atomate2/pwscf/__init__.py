"""Quantum ESPRESSO (pw.x) support for atomate2 under `pwscf` name.

This package mirrors the structure used by the `vasp` module and provides
input generators, job makers, run wrappers, flows and utilities for pw.x
calculations.
"""

from __future__ import annotations

__all__ = [
    "run",
    "sets",
    "jobs",
    "flows",
    "powerups",
    "files",
    "schemas",
]

# Re-export commonly used helpers at package level for convenience
from .powerups import *  # noqa: F401,F403

# Extend __all__ with the powerups module symbols (keeps namespace friendly)
__all__.extend([n for n in dir() if not n.startswith("_")])
