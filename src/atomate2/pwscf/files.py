"""PWscf file utilities: write inputs, copy outputs, helpers.

This module uses pymatgen.io.pwscf.PWInput to construct and write
`pw.x` input files. Atomate2 depends on `pymatgen`, so we directly use the
library rather than providing a non-pymatgen fallback.
"""

from __future__ import annotations

from pathlib import Path

from pymatgen.io.pwscf import PWInput


def write_pwscf_input_set(structure, input_generator, out_dir: str | Path = ".") -> None:
    """Write pw.x input files to `out_dir` using `input_generator`.

    This constructs a `PWInput` from the provided `structure` and the
    attributes on `input_generator` (expected to be a `PwscfInputGenerator`-like
    object) and writes a properly formatted `pw.in` file.
    """
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    control = getattr(input_generator, "user_control", {})
    system = getattr(input_generator, "user_system", {})
    electrons = getattr(input_generator, "user_electrons", {})
    pseudo = getattr(input_generator, "user_pseudos", {})

    pw_inp = PWInput(
        structure=structure,
        control=control,
        system=system,
        electrons=electrons,
        pseudo=pseudo,
    )

    pw_inp.write_file(str(out_path / "pw.in"))


def copy_pwscf_outputs(prev_dir: str | Path, dest: str | Path = ".") -> None:
    """Copy necessary restart files from `prev_dir` into `dest`.

    Placeholder: real implementation should detect `save` directories and
    relevant restart files.
    """
    return
