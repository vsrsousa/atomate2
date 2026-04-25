"""Parsers for PWSCF (pw.x) outputs using pymatgen PWOutput.

Provides a small wrapper that extracts commonly needed fields from a
`pymatgen.io.pwscf.PWOutput` instance.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from pymatgen.io.pwscf import PWOutput


def parse_pwscf_output(out_file: str | Path) -> Dict[str, Any]:
    """Parse a pw.x output file and return a dict with extracted results.

    The parser returns a conservative set of fields that are commonly useful
    for downstream consumers. Missing attributes on `PWOutput` will be
    returned as `None` rather than raising.

    Returned keys include (where available):
    - `final_energy`, `total_energy`
    - `converged`
    - `structure` (or `final_structure`)
    - `forces`
    - `ionic_steps`
    - `band_gap` (or `bandgap`)
    - `is_metal`
    - `magnetization` / `total_magnetization`
    - `stdout` (raw output text, if present)
    """
    pwout = PWOutput(str(out_file))

    def _get(*names):
        for n in names:
            if hasattr(pwout, n):
                return getattr(pwout, n)
        return None

    res: Dict[str, Any] = {}
    res["final_energy"] = _get("final_energy", "total_energy")
    res["total_energy"] = _get("total_energy", "final_energy")
    res["converged"] = _get("converged",)
    res["structure"] = _get("structure", "final_structure")
    res["forces"] = _get("forces",)
    res["ionic_steps"] = _get("ionic_steps", "ionic_steps_info")
    res["band_gap"] = _get("band_gap", "bandgap")
    res["is_metal"] = _get("is_metal",)
    res["magnetization"] = _get("total_magnetization", "magnetization")
    res["stdout"] = _get("stdout", "output")

    # Advanced extractions (best-effort): per-step energies/forces, pressures,
    # stress, SCF iterations, band/dos/eigen information, and timings.
    ionic = res.get("ionic_steps")
    if ionic and isinstance(ionic, list):
        per_energies = []
        per_forces = []
        for step in ionic:
            if isinstance(step, dict):
                per_energies.append(step.get("energy") or step.get("total_energy"))
                per_forces.append(step.get("forces"))
        res["per_step_energies"] = per_energies or None
        res["per_step_forces"] = per_forces or None
    else:
        res["per_step_energies"] = None
        res["per_step_forces"] = None

    res["pressures"] = _get("pressures", "pressure", "press")
    res["stress"] = _get("stress", "stresses")
    res["scf_iterations"] = _get("scf_iterations", "scf_history", "scf")

    res["band_structure"] = _get("band_structure", "bands")
    res["dos"] = _get("dos",)
    res["eigenvalues"] = _get("eigenvalues", "eigs")
    res["occupations"] = _get("occupations",)

    # timings: wall / cpu if available
    timings = _get("timings", "time", "timing")
    res["timings"] = timings

    return res
