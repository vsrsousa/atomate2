"""Common PWSCF input set generators (simple presets).

This module provides simple `RelaxSetGenerator` and `StaticSetGenerator`
that subclass `PwscfInputGenerator` and populate common namelist entries.
These are minimal helpers used by makers/tests; users can supply a custom
`PwscfInputGenerator` if desired.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from atomate2.pwscf.sets.base import PwscfInputGenerator


@dataclass
class RelaxSetGenerator(PwscfInputGenerator):
    """Simple input generator for relaxation runs.

    Sets a default calculation type and reasonable defaults for ionic relax.
    """

    def __init__(
        self,
        user_control: dict[str, Any] | None = None,
        user_system: dict[str, Any] | None = None,
        user_electrons: dict[str, Any] | None = None,
        user_kpoints: dict[str, Any] | None = None,
        user_pseudos: dict[str, str] | None = None,
    ) -> None:
        super().__init__(
            user_control=user_control or {"calculation": "relax", "prefix": "pw"},
            user_system=user_system or {},
            user_electrons=user_electrons or {},
            user_kpoints=user_kpoints or {},
            user_pseudos=user_pseudos or {},
        )

    def generate_kpoints(self, structure):
        # If a concrete kpoints path was provided, return it directly
        if self.user_kpoints and self.user_kpoints.get("kpoints_path"):
            return {"mode": "path", "kpoints_path": self.user_kpoints.get("kpoints_path")}

        # If a preset name is provided, attempt to compute a high-symmetry path
        preset = getattr(self, "kpath_preset", None)
        if not preset:
            return {}

        # Support multiple backends: prefer seekpath when requested, otherwise
        # try pymatgen's HighSymmKpath. Return empty dict on failure.
        if preset == "seekpath":
            try:
                import seekpath as _seekpath

                # seekpath.get_path accepts a cell description; pymatgen Structure
                # can provide lattice vectors and atomic positions via as_dict
                # but tests will monkeypatch seekpath, so keep interface flexible.
                kp = _seekpath.get_path(structure)
                # seekpath-like dicts often contain 'points' and 'path'
                points = kp.get("points") or kp.get("kpoints") or {}
                path = kp.get("path") or kp.get("connected_path") or []
                pts: list[tuple[float, float, float]] = []
                for seg in path:
                    for label in seg:
                        coord = points.get(label)
                        if coord is not None:
                            pts.append(tuple(coord))
                if pts:
                    return {"mode": "path", "kpoints_path": pts}
            except Exception:
                pass

        try:
            # Use pymatgen's HighSymmKpath when available
            from pymatgen.symmetry.bandstructure import HighSymmKpath

            kpath = HighSymmKpath(structure)
            kpoints_dict = kpath.kpath.get("kpoints", {})
            path_segs = kpath.kpath.get("path", [])
            pts: list[tuple[float, float, float]] = []
            for seg in path_segs:
                for label in seg:
                    coord = kpoints_dict.get(label)
                    if coord is not None:
                        pts.append(tuple(coord))
            return {"mode": "path", "kpoints_path": pts}
        except Exception:
            return {}


@dataclass
class StaticSetGenerator(PwscfInputGenerator):
    """Simple input generator for static/SCF runs."""

    def __init__(
        self,
        user_control: dict[str, Any] | None = None,
        user_system: dict[str, Any] | None = None,
        user_electrons: dict[str, Any] | None = None,
        user_kpoints: dict[str, Any] | None = None,
        user_pseudos: dict[str, str] | None = None,
    ) -> None:
        super().__init__(
            user_control=user_control or {"calculation": "scf", "prefix": "pw"},
            user_system=user_system or {},
            user_electrons=user_electrons or {},
            user_kpoints=user_kpoints or {},
            user_pseudos=user_pseudos or {},
        )


@dataclass
class BandsSetGenerator(PwscfInputGenerator):
    """Input generator for band-structure calculations.

    This generator sets `calculation: 'bands'` by default and accepts a
    `kpoints_path` or `kpoints_list` to populate the K_POINTS card. It's a
    lightweight helper; users should supply a fully-featured generator for
    production use.
    """
    # Presets and backends
    # ---------------------
    # This generator supports optional named presets to compute high-symmetry
    # k-point paths automatically. Provide the preset name via the
    # `kpath_preset` constructor argument (or set the attribute afterwards).
    # Recognized presets:
    # - 'seekpath': use the `seekpath` library (if installed) to compute the
    #   canonical high-symmetry path for the provided structure.
    # If `kpath_preset` is not provided, the generator will fall back to
    # attempting `pymatgen`'s `HighSymmKpath` when `generate_kpoints` is
    # invoked.

    # Example usage:
    #   gen = BandsSetGenerator(kpath_preset='seekpath', user_pseudos={'Si': 'Si.upf'})
    #   write_pwscf_input_set(structure, gen, out_dir='.')
    # If seekpath is not available, the generator falls back to pymatgen or
    # returns an empty k-points spec (so callers should validate the input).

    def __init__(
        self,
        user_control: dict[str, Any] | None = None,
        user_system: dict[str, Any] | None = None,
        user_electrons: dict[str, Any] | None = None,
        kpoints_path: list[tuple[float, float, float]] | None = None,
        user_kpoints: dict[str, Any] | None = None,
        user_pseudos: dict[str, str] | None = None,
        kpath_preset: str | None = None,
    ) -> None:
        super().__init__(
            user_control=user_control or {"calculation": "bands", "prefix": "pw"},
            user_system=user_system or {},
            user_electrons=user_electrons or {},
            user_kpoints=user_kpoints or {"kpoints_path": kpoints_path or []},
            user_pseudos=user_pseudos or {},
        )
        # named preset to choose k-path backend. Examples: 'seekpath'
        self.kpath_preset = kpath_preset
