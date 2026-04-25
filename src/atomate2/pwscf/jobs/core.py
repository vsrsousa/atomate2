"""Core PWSCF makers (relax, static, bands).

These are scaffolds that follow the naming and signatures used by the VASP
makers. Implementation details should call `write_pwscf_input_set` and
`run_pwscf` from the `files` and `run` modules respectively.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from jobflow import Response

from atomate2.pwscf.jobs.base import BaseQEMaker, qe_job

if TYPE_CHECKING:
    from pymatgen.core.structure import Structure


@dataclass
class RelaxMaker(BaseQEMaker):
    name: str = "relax"

    @qe_job
    def make(self, structure: "Structure", prev_dir: str | None = None) -> Response:
        raise NotImplementedError()


@dataclass
class StaticMaker(BaseQEMaker):
    name: str = "static"

    @qe_job
    def make(self, structure: "Structure", prev_dir: str | None = None) -> Response:
        raise NotImplementedError()
