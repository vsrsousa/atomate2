"""QE flows (composed makers).

Provide flow makers that compose `jobs` to build higher-level workflows.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from jobflow import Flow, Maker

from atomate2.qe.jobs.core import RelaxMaker, StaticMaker


@dataclass
class DoubleRelaxMaker(Maker):
    name: str = "double relax"
    relax_maker1: RelaxMaker | None = field(default_factory=RelaxMaker)
    relax_maker2: RelaxMaker = field(default_factory=RelaxMaker)

    def make(self, structure, prev_dir=None) -> Flow:
        """Create a two-step relaxation flow (scaffold)."""
        jobs = []
        if self.relax_maker1:
            r1 = self.relax_maker1.make(structure, prev_dir=prev_dir)
            jobs.append(r1)
            structure = r1.output.structure
            prev_dir = r1.output.dir_name

        r2 = self.relax_maker2.make(structure, prev_dir=prev_dir)
        jobs.append(r2)
        return Flow(jobs, output=r2.output, name=self.name)
