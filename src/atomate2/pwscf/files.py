"""PWscf file utilities: write inputs, copy outputs, helpers.

This module uses pymatgen.io.pwscf.PWInput to construct and write
`pw.x` input files. Atomate2 depends on `pymatgen`, so we directly use the
library rather than providing a non-pymatgen fallback.
"""

from __future__ import annotations

from pathlib import Path
import json

from pymatgen.io.pwscf import PWInput

# load default manifold mapping for HUBBARD card generation
_MANIFOLD_FILE = Path(__file__).parent / "hubbard_default_manifolds.json"
try:
    with open(_MANIFOLD_FILE, "r") as _f:
        DEFAULT_MANIFOLDS: dict[str, str] = json.load(_f)
except Exception:
    DEFAULT_MANIFOLDS = {}


def write_pwscf_input_set(structure, input_generator, out_dir: str | Path = ".") -> None:
    """Write pw.x input files to `out_dir` using `input_generator`.

    This constructs a `PWInput` from the provided `structure` and the
    attributes on `input_generator` (expected to be a `PwscfInputGenerator`-like
    object) and writes a properly formatted `pw.in` file.
    """
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    control = getattr(input_generator, "user_control", {}) or {}
    # sensible defaults for common &CONTROL variables when not provided
    # Keep I/O/printing flags off by default; set explicit restart_mode.
    _control_defaults = {
        "calculation": "scf",
        "prefix": "pw",
        "outdir": "./out",
        "pseudo_dir": "./",
        "verbosity": "low",
        "disk_io": "low",
        "restart_mode": "from_scratch",
    }
    for _k, _v in _control_defaults.items():
        control.setdefault(_k, _v)
    system = getattr(input_generator, "user_system", {}) or {}
    electrons = getattr(input_generator, "user_electrons", {}) or {}
    pseudo = getattr(input_generator, "user_pseudos", {}) or {}

    # preserve originals for optional HUBBARD card generation
    orig_hubbard = dict(system).get("Hubbard_U") if isinstance(system, dict) else None
    orig_start_mag = dict(system).get("starting_magnetization") if isinstance(system, dict) else None
    orig_lda_type = dict(system).get("lda_U_type") or dict(system).get("lda_plus_u_type")
    orig_lda_bool = dict(system).get("lda_plus_u")

    # Translate element-keyed Hubbard/U and starting_magnetization dicts into
    # species-indexed namelist keys (Hubbard_U(i), starting_magnetization(i)).
    # Preserve original mapping in case caller needs it, but ensure the
    # writer emits QE-friendly syntax.
    # operate on a copy and remove control keys that shouldn't appear in &SYSTEM
    sys_copy = dict(system)
    # detect hubbard format preference: 'new' (card) or 'old' (namelist)
    hubbard_format = (
        sys_copy.pop("hubbard_format", None)
        or sys_copy.pop("hubbard_card_format", None)
        or "new"
    ).lower()
    # remove explicit toggles so they don't end up in the namelist
    sys_copy.pop("hubbard_card", None)
    sys_copy.pop("hubbard_as_card", None)
    try:
        # build species order (unique elements in order of appearance)
        species_order: list[str] = []
        for site in structure.sites:
            sym = site.specie.symbol if hasattr(site, "specie") else site.species_string
            if sym not in species_order:
                species_order.append(sym)

        symbol_to_index = {s: i + 1 for i, s in enumerate(species_order)}

        # handle Hubbard_U dict mapping element -> U (only for old format)
        hubbard = sys_copy.pop("Hubbard_U", None)
        if isinstance(hubbard, dict) and hubbard_format == "old":
            for el, val in hubbard.items():
                idx = symbol_to_index.get(el)
                if idx is None:
                    # skip unknown species
                    continue
                sys_copy[f"Hubbard_U({idx})"] = val

        # handle starting_magnetization dict mapping element -> mag
        # starting_magnetization is a &SYSTEM namelist variable in QE and
        # should always appear in the namelist (not inside the HUBBARD card).
        start_mag = sys_copy.pop("starting_magnetization", None)
        if isinstance(start_mag, dict):
            for el, val in start_mag.items():
                idx = symbol_to_index.get(el)
                if idx is None:
                    continue
                sys_copy[f"starting_magnetization({idx})"] = val

        # if lda_plus_u present and boolean-like, keep as-is in sys_copy
        if "lda_plus_u" in sys_copy:
            pass
        # map user-friendly lda_U_type or lda_plus_u_type to QE's lda_plus_u_kind
        lda_type = sys_copy.pop("lda_U_type", None) or sys_copy.pop("lda_plus_u_type", None)
        if lda_type is not None:
            # place under the QE-expected key name
            sys_copy["lda_plus_U_kind"] = lda_type
    except Exception:
        # fallback: leave system unchanged on any error
        sys_copy = dict(system)

        # use sys_copy when constructing the PWInput
    # If card format requested, remove lda flags from the namelist so they
    # won't be written into &SYSTEM (they will be placed into the HUBBARD card)
    if hubbard_format == "new":
        # remove any known LDA+U-related namelist keys so they do not
        # appear anywhere in the output when using the modern HUBBARD card
        _lda_keys = [
            "lda_plus_u",
            "lda_plus_u_kind",
            "lda_plus_U_kind",
            "lda_plus_U",
            "lda_U_type",
            "lda_plus_u_type",
            "lda_plus_U_type",
        ]
        for _k in _lda_keys:
            sys_copy.pop(_k, None)

    system = sys_copy

    # Ensure default plane-wave cutoffs appear in &SYSTEM if not provided
    system.setdefault("ecutwfc", 50)
    system.setdefault("ecutrho", 400)

    # move certain electron-related parameters into &SYSTEM when requested
    # QE users often place `degauss` and `smearing` in the system namelist;
    # accept them from `user_electrons` and ensure they appear in &SYSTEM
    for _e_key in ("degauss", "smearing"):
        if _e_key in electrons:
            system[_e_key] = electrons.pop(_e_key)

    # if smearing is provided and occupations not explicitly set, assume
    # the user intends smeared occupations per QE docs
    if "smearing" in system and "occupations" not in system:
        system["occupations"] = "smearing"

    pw_inp = PWInput(
        structure=structure,
        control=control,
        system=system,
        electrons=electrons,
        pseudo=pseudo,
    )

    # Allow generators to produce kpoints based on the provided structure
    user_kpoints = getattr(input_generator, "user_kpoints", {}) or {}
    if hasattr(input_generator, "generate_kpoints"):
        try:
            generated = input_generator.generate_kpoints(structure)
            if generated:
                user_kpoints = generated
                # update generator state for downstream use
                input_generator.user_kpoints = user_kpoints
        except Exception:
            # Avoid failing input writing due to kpoint generation errors
            pass

    pw_inp.write_file(str(out_path / "pw.in"))

    # Optionally append a dedicated &HUBBARD namelist/card for modern QE
    # if the user requested it (via user_system['hubbard_card']=True) and
    # there was an original element-keyed Hubbard or starting magnetization.
    def _format_val(v):
        if isinstance(v, bool):
            return ".TRUE." if v else ".FALSE."
        if isinstance(v, str):
            return f"'{v}'"
        return str(v)

    # decide whether to write a HUBBARD card: respect hubbard_format ('new'|'old')
    hubbard_card_requested = hubbard_format == "new"
    # prefer original mappings when available
    if hubbard_card_requested and (orig_hubbard or orig_start_mag or orig_lda_type):
        # build species order again (best-effort)
        species_order = []
        for site in structure.sites:
            sym = site.specie.symbol if hasattr(site, "specie") else site.species_string
            if sym not in species_order:
                species_order.append(sym)
        symbol_to_index = {s: i + 1 for i, s in enumerate(species_order)}

        # Optionally include a projector type in the header: atomic|ortho-atomic|norm-atomic|wf|pseudo
        # projector is required for the HUBBARD card; default to 'ortho-atomic'
        projector = (
            dict(system).get("hubbard_projector")
            or dict(system).get("hubbard_card_projector")
            or "ortho-atomic"
        )
        hub_lines = [f"HUBBARD {projector}"]

        # In 'new' (card) format, lda flags are not written anywhere by default

        if isinstance(orig_hubbard, dict):
            for el, val in orig_hubbard.items():
                idx = symbol_to_index.get(el)
                if idx is None:
                    continue
                # For 'new' (card) format we only emit card-style paramType label-manifold value lines
                if hubbard_format == "new":
                    manifold = DEFAULT_MANIFOLDS.get(el)
                    if manifold:
                        # numeric formatting without quotes — compute outside f-string
                        _v = _format_val(val)
                        if _v.startswith("'") and _v.endswith("'"):
                            _v = _v[1:-1]
                        # prefix with the parameter type 'U' as required by the HUBBARD card syntax
                        hub_lines.append(f"  U {el}-{manifold} {_v}")
                # For 'old' format the namelist entries are already placed into &SYSTEM

        # starting_magnetization belongs in &SYSTEM namelist, not in the HUBBARD card

        # cards should not be terminated with '/' (that's for namelists)
        with open(out_path / "pw.in", "a") as f:
            f.write("\n\n" + "\n".join(hub_lines) + "\n")

    # Append K_POINTS card when generator supplied kpoints
    if user_kpoints:
        kp_lines: list[str] = []
        mode = (user_kpoints.get("mode") or "automatic").lower()
        if mode == "automatic":
            grid = user_kpoints.get("grid") or user_kpoints.get("automatic") or [1, 1, 1]
            kp_lines.append("K_POINTS automatic")
            kp_lines.append(f"{grid[0]} {grid[1]} {grid[2]} 0 0 0")
        else:
            # explicit kpoints path/list
            pts = user_kpoints.get("kpoints_path") or user_kpoints.get("kpoints_list") or []
            kp_lines.append("K_POINTS crystal")
            kp_lines.append(str(len(pts)))
            for p in pts:
                # expect tuple/list of 3 floats
                kp_lines.append("{:.8f} {:.8f} {:.8f} 1".format(*tuple(p)))

        with open(out_path / "pw.in", "a") as f:
            f.write("\n\n" + "\n".join(kp_lines))


def copy_pwscf_outputs(prev_dir: str | Path, dest: str | Path = ".") -> None:
    """Copy necessary restart files from `prev_dir` into `dest`.

    Placeholder: real implementation should detect `save` directories and
    relevant restart files.
    """
    return
