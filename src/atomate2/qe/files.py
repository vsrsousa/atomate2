"""QE file utilities: write inputs, copy outputs, helpers.

Scaffold implementations to be filled with logic using `pymatgen.io.espresso`.
"""

from __future__ import annotations

from pathlib import Path


def write_qe_input_set(structure, input_generator, out_dir: str | Path = ".") -> None:
    """Write pw.x input files to `out_dir` using `input_generator`.

    Placeholder implementation.
    """
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    (out_path / "pw.in").write_text(input_generator.to_inp())


def copy_qe_outputs(prev_dir: str | Path, dest: str | Path = ".") -> None:
    """Copy necessary restart files from `prev_dir` into `dest`.

    Placeholder: real implementation should detect `save` directories and
    relevant restart files.
    """
    return
