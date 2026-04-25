"""PWSCF flows (composed makers).

Provide flow makers that compose `jobs` to build higher-level workflows.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from jobflow import Flow, Maker

from atomate2.pwscf.jobs.core import RelaxMaker, StaticMaker


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
        return Flow(jobs, outputs, output=flow_output, name=self.name)
