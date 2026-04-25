"""Core PWSCF makers (relax, static, bands).

These are scaffolds that follow the naming and signatures used by the VASP
makers. Implementation details should call `write_pwscf_input_set` and
`run_pwscf` from the `files` and `run` modules respectively.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from jobflow import Response
from pathlib import Path

from atomate2.pwscf.jobs.base import BasePwscfMaker, pwscf_job
from atomate2.pwscf.files import write_pwscf_input_set
from atomate2.pwscf.run import run_pwscf
from atomate2.pwscf.schemas import parse_pwscf_output, TaskDocument

if TYPE_CHECKING:
    from pymatgen.core.structure import Structure


@dataclass
class RelaxMaker(BasePwscfMaker):
    name: str = "relax"

    @pwscf_job
    def make(self, structure: "Structure", prev_dir: str | None = None) -> Response:
        if self.input_set_generator is None:
            raise RuntimeError("`input_set_generator` must be provided for RelaxMaker")

        # write input files
        write_pwscf_input_set(structure, self.input_set_generator, out_dir=".")

        # run pw.x
        run_res = run_pwscf(**self.run_pwscf_kwargs)

        # parse outputs if available
        parsed = {}
        out_file = run_res.get("out_file")
        if out_file is None:
            p = Path("pw.out")
            if p.exists():
                out_file = str(p)

        if out_file:
            parsed = parse_pwscf_output(out_file)

        # build TaskDocument from parsed results and include run metadata
        task_doc = TaskDocument.from_parsed(parsed, dir_name=".", run=run_res)
        return Response(output=task_doc)


@dataclass
class StaticMaker(BasePwscfMaker):
    name: str = "static"

    @pwscf_job
    def make(self, structure: "Structure", prev_dir: str | None = None) -> Response:
        if self.input_set_generator is None:
            raise RuntimeError("`input_set_generator` must be provided for StaticMaker")

        write_pwscf_input_set(structure, self.input_set_generator, out_dir=".")
        run_res = run_pwscf(**self.run_pwscf_kwargs)

        parsed = {}
        out_file = run_res.get("out_file")
        if out_file is None:
            p = Path("pw.out")
            if p.exists():
                out_file = str(p)

        if out_file:
            parsed = parse_pwscf_output(out_file)

        task_doc = TaskDocument.from_parsed(parsed, dir_name=".", run=run_res)
        return Response(output=task_doc)


@dataclass
class NonSCFMaker(BasePwscfMaker):
    name: str = "nscf"

    @pwscf_job
    def make(self, structure: "Structure", prev_dir: str | None = None) -> Response:
        if self.input_set_generator is None:
            raise RuntimeError("`input_set_generator` must be provided for NonSCFMaker")

        # allow prev_dir to provide previous outputs/pseudos; caller may copy
        write_pwscf_input_set(structure, self.input_set_generator, out_dir=".")
        run_res = run_pwscf(**self.run_pwscf_kwargs)

        parsed = {}
        out_file = run_res.get("out_file")
        if out_file is None:
            p = Path("pw.out")
            if p.exists():
                out_file = str(p)

        if out_file:
            parsed = parse_pwscf_output(out_file)

        task_doc = TaskDocument.from_parsed(parsed, dir_name=".", run=run_res)
        return Response(output=task_doc)


@dataclass
class BandStructureMaker(BasePwscfMaker):
    name: str = "bands"

    @pwscf_job
    def make(self, structure: "Structure", prev_dir: str | None = None) -> Response:
        if self.input_set_generator is None:
            raise RuntimeError("`input_set_generator` must be provided for BandStructureMaker")

        write_pwscf_input_set(structure, self.input_set_generator, out_dir=".")
        run_res = run_pwscf(**self.run_pwscf_kwargs)

        parsed = {}
        out_file = run_res.get("out_file")
        if out_file is None:
            p = Path("pw.out")
            if p.exists():
                out_file = str(p)

        if out_file:
            parsed = parse_pwscf_output(out_file)

        # Band-structure specific data (bands eigenvalues, kpoints) should be
        # present in the parsed output; TaskDocument will ingest available data.
        task_doc = TaskDocument.from_parsed(parsed, dir_name=".", run=run_res)
        return Response(output=task_doc)
