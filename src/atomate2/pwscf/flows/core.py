"""PWSCF flows (composed makers).

Provide flow makers that compose `jobs` to build higher-level workflows.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from jobflow import Flow, Maker

from atomate2.pwscf.jobs.core import (
    RelaxMaker,
    StaticMaker,
    NonSCFMaker,
    BandStructureMaker,
)


def _as_flow_output(task_job):
    """Return a tuple (flow_output, outputs_dict) for a Job produced by a maker.

    `flow_output` should be the job's primary output (TaskDocument). `outputs_dict`
    is a convenience dict exposing inner `PWOutputSummary` and other useful
    objects for consumers of the Flow.
    """
    td = task_job.output
    outputs = {"task_doc": td, "pw_summary": getattr(td, "output", None)}
    return td, outputs


@dataclass
class DoubleRelaxMaker(Maker):
    name: str = "double relax"
    relax_maker1: RelaxMaker | None = field(default_factory=RelaxMaker)
    relax_maker2: RelaxMaker = field(default_factory=RelaxMaker)

    def make(self, structure, prev_dir=None) -> Flow:
        """Create a two-step relaxation flow (scaffold)."""
        jobs = []
        outputs = {}
        flow_output = None

        if self.relax_maker1:
            r1 = self.relax_maker1.make(structure, prev_dir=prev_dir)
            jobs.append(r1)
            # update structure/prev_dir from TaskDocument
            structure = r1.output.structure
            prev_dir = r1.output.dir_name
            flow_output, outputs = _as_flow_output(r1)

        r2 = self.relax_maker2.make(structure, prev_dir=prev_dir)
        jobs.append(r2)
        flow_output, outputs = _as_flow_output(r2)

        # Flow expects either a single output or an outputs dict; provide both
        return Flow(jobs, outputs, name=self.name)

    @classmethod
    def from_relax_maker(cls, relax_maker: RelaxMaker) -> "DoubleRelaxMaker":
        """Instantiate with two copies of the same relax maker."""
        return cls(relax_maker1=deepcopy(relax_maker), relax_maker2=deepcopy(relax_maker))


# (Full RelaxBandStructureMaker implementation is defined later in this file.)


@dataclass
class ConvergenceStudyMaker(Maker):
    """Maker to run a simple convergence study over `ecutwfc` and k-point grids.

    Parameters
    ----------
    name: str
        Flow name.
    static_maker: StaticMaker
        Maker used to generate each static calculation.
    ecut_list: list[float] | None
        List of plane-wave cutoffs (`ecutwfc`) to test.
    kpoints_list: list[tuple[int,int,int]] | None
        List of Monkhorst-Pack grids to test (triplets).
    """

    name: str = "convergence study"
    static_maker: StaticMaker = field(default_factory=StaticMaker)
    ecut_list: list | None = None
    kpoints_list: list | None = None

    def make(self, structure, prev_dir=None) -> Flow:
        """Create a flow running static calculations for each combination.

        The maker deep-copies the provided `static_maker` and its
        `input_set_generator` for each point, modifying `user_system['ecutwfc']`
        and/or `user_kpoints['grid']` as requested.
        """
        if self.static_maker is None:
            raise RuntimeError("`static_maker` must be provided for ConvergenceStudyMaker")

        base_gen = self.static_maker.input_set_generator
        if base_gen is None:
            raise RuntimeError("`input_set_generator` must be set on `static_maker`")

        e_list = list(self.ecut_list) if self.ecut_list else []
        k_list = list(self.kpoints_list) if self.kpoints_list else []
        if not e_list and not k_list:
            raise ValueError("Provide at least one of `ecut_list` or `kpoints_list`")

        combos = []
        if e_list and k_list:
            for e in e_list:
                for k in k_list:
                    combos.append((e, k))
        elif e_list:
            for e in e_list:
                combos.append((e, None))
        else:
            for k in k_list:
                combos.append((None, k))

        jobs = []
        outputs = {}
        flow_output = None

        for ecut, kgrid in combos:
            maker = deepcopy(self.static_maker)
            gen = deepcopy(base_gen)
            if ecut is not None:
                gen.user_system = dict(getattr(gen, "user_system", {}) or {})
                gen.user_system["ecutwfc"] = ecut
            if kgrid is not None:
                gen.user_kpoints = dict(getattr(gen, "user_kpoints", {}) or {})
                gen.user_kpoints["grid"] = list(kgrid)

            maker.input_set_generator = gen
            job = maker.make(structure, prev_dir=prev_dir)

            label_parts = []
            if ecut is not None:
                label_parts.append(f"ecut={ecut}")
            if kgrid is not None:
                label_parts.append(f"kgrid={kgrid[0]}x{kgrid[1]}x{kgrid[2]}")
            if label_parts:
                job.name += " " + ",".join(label_parts)

            jobs.append(job)
            td, out = _as_flow_output(job)
            outputs[job.name] = out
            flow_output = td

        return Flow(jobs, outputs, name=self.name)


@dataclass
class RelaxBandStructureMaker(Maker):
    """Maker to run Relax -> Static -> NSCF -> Bands sequence.

    This composes the existing makers: `RelaxMaker`, `StaticMaker`,
    `NonSCFMaker` and `BandStructureMaker` to produce a common end-to-end
    band-structure flow after relaxation.
    """

    name: str = "relax and band structure"
    relax_maker: RelaxMaker = field(default_factory=RelaxMaker)
    static_maker: StaticMaker = field(default_factory=StaticMaker)
    nscf_maker: NonSCFMaker = field(default_factory=NonSCFMaker)
    band_maker: BandStructureMaker = field(default_factory=BandStructureMaker)

    def make(self, structure, prev_dir: str | None = None) -> Flow:
        jobs = []
        outputs = {}

        # Relax
        relax_job = self.relax_maker.make(structure, prev_dir=prev_dir)
        jobs.append(relax_job)
        outputs[relax_job.name] = {"task_doc": relax_job.output, "pw_summary": getattr(relax_job.output, "output", None)}

        # Static (on relaxed structure)
        relaxed_struct = relax_job.output.structure
        static_job = self.static_maker.make(relaxed_struct, prev_dir=relax_job.output.dir_name)
        jobs.append(static_job)
        outputs[static_job.name] = {"task_doc": static_job.output, "pw_summary": getattr(static_job.output, "output", None)}

        # Non-SCF (dense uniform k-grid) -- use static output as parent
        nscf_job = self.nscf_maker.make(static_job.output.structure, prev_dir=static_job.output.dir_name)
        jobs.append(nscf_job)
        outputs[nscf_job.name] = {"task_doc": nscf_job.output, "pw_summary": getattr(nscf_job.output, "output", None)}

        # Band-structure (line mode) -- use static as reference for bands generator
        band_job = self.band_maker.make(static_job.output.structure, prev_dir=static_job.output.dir_name)
        jobs.append(band_job)
        outputs[band_job.name] = {"task_doc": band_job.output, "pw_summary": getattr(band_job.output, "output", None)}

        return Flow(jobs, outputs, name=self.name)


@dataclass
class DOSMaker(Maker):
    """Maker to run Static -> NSCF (dense) to produce DOS-related outputs."""

    name: str = "dos"
    static_maker: StaticMaker = field(default_factory=StaticMaker)
    nscf_maker: NonSCFMaker = field(default_factory=NonSCFMaker)

    def make(self, structure, prev_dir: str | None = None) -> Flow:
        jobs = []
        outputs = {}

        # Static calculation
        static_job = self.static_maker.make(structure, prev_dir=prev_dir)
        jobs.append(static_job)
        outputs[static_job.name] = {"task_doc": static_job.output, "pw_summary": getattr(static_job.output, "output", None)}

        # NSCF/dense k-grid for DOS (uses static as parent)
        nscf_job = self.nscf_maker.make(static_job.output.structure, prev_dir=static_job.output.dir_name)
        jobs.append(nscf_job)
        outputs[nscf_job.name] = {"task_doc": nscf_job.output, "pw_summary": getattr(nscf_job.output, "output", None)}

        return Flow(jobs, outputs, name=self.name)


@dataclass
class BandInterpolationMaker(Maker):
    """Maker to run Static -> NSCF -> Wannier prep -> interpolated bands.

    This is a scaffold for Wannier-based interpolation. It reuses the
    `StaticMaker`, `NonSCFMaker` and `BandStructureMaker`. The actual
    Wannier projection/run steps are external; here we assume preparation
    is done by running a dense NSCF and then requesting an interpolated
    band calculation via the bands input generator.
    """

    name: str = "band interpolation"
    static_maker: StaticMaker = field(default_factory=StaticMaker)
    nscf_maker: NonSCFMaker = field(default_factory=NonSCFMaker)
    band_maker: BandStructureMaker = field(default_factory=BandStructureMaker)

    def make(self, structure, prev_dir: str | None = None) -> Flow:
        jobs = []
        outputs = {}

        # Static
        static_job = self.static_maker.make(structure, prev_dir=prev_dir)
        jobs.append(static_job)
        outputs[static_job.name] = {"task_doc": static_job.output, "pw_summary": getattr(static_job.output, "output", None)}

        # Dense NSCF for wannier projection
        nscf_job = self.nscf_maker.make(static_job.output.structure, prev_dir=static_job.output.dir_name)
        jobs.append(nscf_job)
        outputs[nscf_job.name] = {"task_doc": nscf_job.output, "pw_summary": getattr(nscf_job.output, "output", None)}

        # Prepare bands input for interpolation: set a flag on the band's input generator
        # Many real workflows call external Wannier tools between steps; here we assume
        # band_maker.input_set_generator can signal interpolation requirements.
        band_gen = deepcopy(getattr(self.band_maker, "input_set_generator", None))
        if band_gen is None:
            # if none provided, try to create a simple BandsSetGenerator
            from atomate2.pwscf.sets.core import BandsSetGenerator

            band_gen = BandsSetGenerator(user_pseudos={})

        # request interpolation mode via a user flag (interpreted by write_pwscf_input_set)
        band_gen.user_kpoints = dict(getattr(band_gen, "user_kpoints", {}) or {})
        band_gen.user_kpoints["interpolate"] = True

        # assign modified generator and run band interpolation
        self.band_maker.input_set_generator = band_gen
        band_job = self.band_maker.make(static_job.output.structure, prev_dir=static_job.output.dir_name)
        jobs.append(band_job)
        outputs[band_job.name] = {"task_doc": band_job.output, "pw_summary": getattr(band_job.output, "output", None)}

        return Flow(jobs, outputs, name=self.name)
