"""Core QE input set generators (relax, static, bands).

These classes should produce namelists/cards appropriate for pw.x runs.
"""

from __future__ import annotations

from dataclasses import dataclass
from .base import QeInputGenerator


@dataclass
class RelaxSetGenerator(QeInputGenerator):
    """Generator for relaxation (geometry optimization) inputs."""

    @property
    def namelists(self) -> dict:
        return {
            "CONTROL": {"calculation": "relax"},
            "SYSTEM": {"ibrav": 0},
            "ELECTRONS": {},
        }


@dataclass
class StaticSetGenerator(QeInputGenerator):
    """Generator for static (single-point) calculations."""

    @property
    def namelists(self) -> dict:
        return {"CONTROL": {"calculation": "scf"}, "SYSTEM": {}, "ELECTRONS": {}}


@dataclass
class BandsSetGenerator(QeInputGenerator):
    """Generator for band structure calculations (non-SCF)."""

    @property
    def namelists(self) -> dict:
        return {"CONTROL": {"calculation": "bands"}, "SYSTEM": {}, "ELECTRONS": {}}
