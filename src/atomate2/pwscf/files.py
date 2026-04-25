"""PWscf file utilities: write inputs, copy outputs, helpers.

Scaffold implementations to be filled with logic using `pymatgen.io.espresso`.
"""

from __future__ import annotations

from pathlib import Path


def write_pwscf_input_set(structure, input_generator, out_dir: str | Path = ".") -> None:
    """Write pw.x input files to `out_dir` using `input_generator`.

    Placeholder implementation.
    """
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    # Base input from the generator
    base_inp = input_generator.to_inp()

    # If a structure is provided and looks like a pymatgen Structure-like object,
    # append basic CELL_PARAMETERS and ATOMIC_POSITIONS blocks.
    extra = []
    try:
        sites = getattr(structure, "sites", None)
        lattice = getattr(structure, "lattice", None)
        if sites and lattice:
            # write cell parameters (3 vectors)
            extra.append("CELL_PARAMETERS angstrom")
            for v in lattice.matrix:
                extra.append("{:.12f} {:.12f} {:.12f}".format(*v))
            extra.append("")
            extra.append("ATOMIC_POSITIONS angstrom")
            for site in sites:
                specie = site.specie.symbol if hasattr(site, "specie") else str(site.species_string)
                coords = site.coords if hasattr(site, "coords") else site.frac_coords
                extra.append(f"{specie} {coords[0]:.12f} {coords[1]:.12f} {coords[2]:.12f}")
    except Exception:
        # Best-effort: if the provided structure is not compatible, skip extras.
        extra = []

    content = base_inp
    if extra:
        content = content + "\n\n" + "\n".join(extra)

    (out_path / "pw.in").write_text(content)


def copy_pwscf_outputs(prev_dir: str | Path, dest: str | Path = ".") -> None:
    """Copy necessary restart files from `prev_dir` into `dest`.

    Placeholder: real implementation should detect `save` directories and
    relevant restart files.
    """
    return
