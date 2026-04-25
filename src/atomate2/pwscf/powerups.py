"""Powerups for PWSCF workflows.

Powerups modify makers/flows to adjust input generators or settings.
This module mirrors the pattern used by `vasp.powerups`.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, TypeVar

from jobflow.core.flow import Flow
from jobflow.core.job import Job
from jobflow.core.maker import Maker

from atomate2.common.powerups import add_metadata_to_flow as base_add_metadata_to_flow
from atomate2.common.powerups import update_custodian_handlers as base_custodian_handler
from atomate2.pwscf.jobs.base import BasePwscfMaker

JobType = TypeVar("JobType", Job, Flow, Maker)


def update_pwscf_input_generators(
    flow: JobType,
    dict_mod_updates: dict[str, Any],
    name_filter: str | None = None,
    class_filter: type[Maker] | None = BasePwscfMaker,
) -> JobType:
    """Update PWSCF input generators or makers in a job, flow, or maker.

    Mirrors `update_vasp_input_generators` but targets PWSCF input generator
    attribute names (e.g., `user_control`, `user_kpoints`, `user_pseudos`).
    """
    updated_flow = deepcopy(flow)

    # ensure makers have a non-None input_set_generator so dict_mod can create
    # nested keys. Use plain dict for serialization compatibility, then convert
    # back to SimpleNamespace for attribute-style access after updating.
    from types import SimpleNamespace

    if isinstance(updated_flow, Maker):
        # normalize any existing SimpleNamespace placeholders to dicts so
        # jobflow's dict_mod logic can operate on them
        if getattr(updated_flow, "input_set_generator", None) is None:
            updated_flow.input_set_generator = {}
        elif isinstance(updated_flow.input_set_generator, SimpleNamespace):
            updated_flow.input_set_generator = vars(updated_flow.input_set_generator).copy()

        # also initialize nested Maker attributes (e.g., composite makers)
        for name, val in vars(updated_flow).items():
            try:
                if isinstance(val, Maker):
                    ig = getattr(val, "input_set_generator", None)
                    if ig is None:
                        val.input_set_generator = {}
                    elif isinstance(ig, SimpleNamespace):
                        val.input_set_generator = vars(ig).copy()
            except Exception:
                continue
    else:
        # Flow: iterate jobs and set maker input_set_generator placeholder
        if hasattr(updated_flow, "jobs"):
            for j in getattr(updated_flow, "jobs", []):
                try:
                    maker_obj = j.function.__self__
                    ig = getattr(maker_obj, "input_set_generator", None)
                    if ig is None:
                        maker_obj.input_set_generator = {}
                    elif isinstance(ig, SimpleNamespace):
                        maker_obj.input_set_generator = vars(ig).copy()
                except Exception:
                    # skip jobs that don't expose maker instance
                    pass
        # Single Job: set maker attribute if available
        elif hasattr(updated_flow, "maker"):
            maker_obj = getattr(updated_flow, "maker")
            ig = getattr(maker_obj, "input_set_generator", None)
            if ig is None:
                maker_obj.input_set_generator = {}
            elif isinstance(ig, SimpleNamespace):
                maker_obj.input_set_generator = vars(ig).copy()

    tmp_dict = {
        "update": {"_set": dict_mod_updates},
        "name_filter": name_filter,
        "class_filter": class_filter,
        "dict_mod": True,
    }

    if isinstance(updated_flow, Maker):
        updated_flow = updated_flow.update_kwargs(**tmp_dict)

        # convert any dict input_set_generator to SimpleNamespace for attribute access
        if hasattr(updated_flow, "input_set_generator") and isinstance(
            getattr(updated_flow, "input_set_generator"), dict
        ):
            updated_flow.input_set_generator = SimpleNamespace(**updated_flow.input_set_generator)

        # convert nested makers if present
        for name, val in vars(updated_flow).items():
            try:
                if isinstance(val, Maker) and isinstance(getattr(val, "input_set_generator", None), dict):
                    val.input_set_generator = SimpleNamespace(**val.input_set_generator)
            except Exception:
                continue
    else:
        updated_flow.update_maker_kwargs(**tmp_dict)

        # convert makers' input_set_generator dicts to SimpleNamespace
        makers_list: list[tuple[Maker, str | None]] = []
        if hasattr(updated_flow, "jobs"):
            for j in getattr(updated_flow, "jobs", []):
                try:
                    makers_list.append((j.function.__self__, getattr(j, "name", None)))
                except Exception:
                    continue
        elif hasattr(updated_flow, "maker"):
            maker_obj = getattr(updated_flow, "maker")
            makers_list.append((maker_obj, getattr(maker_obj, "name", None)))

        # ensure nested fields created by dict_mod are represented as attributes
        for maker_obj, job_name in makers_list:
            try:
                val = getattr(maker_obj, "input_set_generator", None)
                # normalize to dict
                if isinstance(val, SimpleNamespace):
                    d = vars(val).copy()
                elif isinstance(val, dict):
                    d = val.copy()
                else:
                    d = {}

                # apply any dict_mod_updates that target input_set_generator
                applied = False
                for k, v in dict_mod_updates.items():
                    toks = [t for t in k.split("->") if t != ""]
                    if not toks or toks[0] != "input_set_generator":
                        continue
                    # respect name_filter if provided
                    if name_filter:
                        if job_name is None or name_filter not in str(job_name):
                            continue
                    # set nested keys after the first token
                    cur = d
                    for tok in toks[1:-1]:
                        if tok not in cur or not isinstance(cur[tok], dict):
                            cur[tok] = {}
                        cur = cur[tok]
                    cur[toks[-1]] = v
                    applied = True
                # only replace the original input_set_generator when:
                # - it was already a dict/SimpleNamespace (we normalized it)
                # - or we actually applied updates targeting it
                if applied or isinstance(val, (dict, SimpleNamespace)):
                    maker_obj.input_set_generator = SimpleNamespace(**d)
            except Exception:
                continue

    return updated_flow


def update_user_control_settings(
    flow: JobType,
    control_updates: dict[str, Any],
    name_filter: str | None = None,
    class_filter: type[Maker] | None = BasePwscfMaker,
) -> JobType:
    """Update `user_control` settings in PWSCF input generators."""
    return update_pwscf_input_generators(
        flow=flow,
        dict_mod_updates={f"input_set_generator->user_control->{k}": v for k, v in control_updates.items()},
        name_filter=name_filter,
        class_filter=class_filter,
    )


def update_user_kpoints_settings(
    flow: JobType,
    kpoints_updates: dict[str, Any],
    name_filter: str | None = None,
    class_filter: type[Maker] | None = BasePwscfMaker,
) -> JobType:
    """Update `user_kpoints` in PWSCF input generators."""
    dict_mod = {f"input_set_generator->user_kpoints->{k}": v for k, v in kpoints_updates.items()}
    return update_pwscf_input_generators(
        flow=flow, dict_mod_updates=dict_mod, name_filter=name_filter, class_filter=class_filter
    )


def update_user_pseudos(
    flow: JobType,
    pseudos: dict[str, str],
    name_filter: str | None = None,
    class_filter: type[Maker] | None = BasePwscfMaker,
) -> JobType:
    """Update `user_pseudos` mapping in PWSCF input generators."""
    dict_mod = {f"input_set_generator->user_pseudos->{k}": v for k, v in pseudos.items()}
    return update_pwscf_input_generators(
        flow=flow, dict_mod_updates=dict_mod, name_filter=name_filter, class_filter=class_filter
    )


def add_metadata_to_flow(flow: Flow, additional_fields: dict, class_filter: type[Maker] = BasePwscfMaker) -> Flow:
    """Add metadata fields to PWSCF task documents in a flow."""
    return base_add_metadata_to_flow(flow=flow, additional_fields=additional_fields, class_filter=class_filter)


def update_pwscf_custodian_handlers(flow: Flow, custom_handlers: tuple, class_filter: type[Maker] = BasePwscfMaker) -> Flow:
    """Update custodian-like handlers for PWSCF jobs in a flow."""
    return base_custodian_handler(flow=flow, custom_handlers=custom_handlers, class_filter=class_filter)


def update_user_system_settings(
    flow: JobType,
    system_updates: dict[str, Any],
    name_filter: str | None = None,
    class_filter: type[Maker] | None = BasePwscfMaker,
) -> JobType:
    """Update `user_system` settings (e.g., `ecutwfc`, `ecutrho`) in PWSCF input generators."""
    dict_mod = {f"input_set_generator->user_system->{k}": v for k, v in system_updates.items()}
    return update_pwscf_input_generators(
        flow=flow, dict_mod_updates=dict_mod, name_filter=name_filter, class_filter=class_filter
    )


def update_user_pseudos_functional(
    flow: JobType,
    functional: str,
    name_filter: str | None = None,
    class_filter: type[Maker] | None = BasePwscfMaker,
) -> JobType:
    """Set the pseudopotential 'functional' marker on input generators (convenience wrapper)."""
    return update_pwscf_input_generators(
        flow=flow,
        dict_mod_updates={"input_set_generator->user_pseudo_functional": functional},
        name_filter=name_filter,
        class_filter=class_filter,
    )


def set_kpoints_density(
    flow: JobType,
    density: int,
    name_filter: str | None = None,
    class_filter: type[Maker] | None = BasePwscfMaker,
) -> JobType:
    """Convenience helper to set a reciprocal density/grid for k-points.

    Accepts an integer `density` and places it under
    `input_set_generator->user_kpoints->reciprocal_density`.
    """
    dict_mod = {"input_set_generator->user_kpoints->reciprocal_density": density}
    return update_pwscf_input_generators(
        flow=flow, dict_mod_updates=dict_mod, name_filter=name_filter, class_filter=class_filter
    )


def set_ecut_preset(
    flow: JobType,
    ecutwfc: int,
    rho_mult: int = 4,
    name_filter: str | None = None,
    class_filter: type[Maker] | None = BasePwscfMaker,
) -> JobType:
    """Convenience helper to set `ecutwfc` and `ecutrho` in `user_system`.

    Args:
        ecutwfc: cutoff for wavefunctions.
        rho_mult: multiplier for `ecutrho` (defaults to 4x ecutwfc).
    """
    dict_mod = {
        "input_set_generator->user_system->ecutwfc": ecutwfc,
        "input_set_generator->user_system->ecutrho": int(ecutwfc * rho_mult),
    }
    return update_pwscf_input_generators(
        flow=flow, dict_mod_updates=dict_mod, name_filter=name_filter, class_filter=class_filter
    )


def set_smearing(
    flow: JobType,
    smearing: str = "marzari-vanderbilt",
    degauss: float = 0.02,
    name_filter: str | None = None,
    class_filter: type[Maker] | None = BasePwscfMaker,
) -> JobType:
    """Set smearing-related `ELECTRONS` settings in input generators.

    Places `smearing` and `degauss` under `input_set_generator->user_electrons`.
    """
    dict_mod = {
        "input_set_generator->user_electrons->smearing": smearing,
        "input_set_generator->user_electrons->degauss": degauss,
    }
    return update_pwscf_input_generators(
        flow=flow, dict_mod_updates=dict_mod, name_filter=name_filter, class_filter=class_filter
    )


def update_run_pwscf_kwargs(
    flow: JobType,
    run_kwargs: dict[str, Any],
    name_filter: str | None = None,
    class_filter: type[Maker] | None = BasePwscfMaker,
) -> JobType:
    """Update the `run_pwscf_kwargs` passed to makers/jobs.

    This updates maker kwargs (not the input generator). Useful to set
    `mpi_args`, `handlers`, or other runner-specific options.
    """
    updated_flow = deepcopy(flow)
    tmp = {
        "update": {"_set": {f"run_pwscf_kwargs->{k}": v for k, v in run_kwargs.items()}},
        "name_filter": name_filter,
        "class_filter": class_filter,
        "dict_mod": True,
    }
    if isinstance(updated_flow, Maker):
        return updated_flow.update_kwargs(**tmp)
    else:
        updated_flow.update_maker_kwargs(**tmp)
        return updated_flow


def set_pseudo_bundle(
    flow: JobType,
    bundle: str = "standard",
    name_filter: str | None = None,
    class_filter: type[Maker] | None = BasePwscfMaker,
) -> JobType:
    """Apply a named pseudopotential bundle mapping.

    Bundles are convenience mappings from element symbol to pseudopotential
    filename. This is intentionally small; users can supply custom mappings
    via `update_user_pseudos` for full control.
    """
    bundles: dict[str, dict[str, str]] = {
        "standard": {"Si": "Si.upf"},
        "pseudo_small": {"Si": "Si.upf"},
    }

    mapping = bundles.get(bundle, {})
    return update_user_pseudos(flow=flow, pseudos=mapping, name_filter=name_filter, class_filter=class_filter)


def apply_preset(
    flow: JobType,
    profile: str = "standard",
    name_filter: str | None = None,
    class_filter: type[Maker] | None = BasePwscfMaker,
) -> JobType:
    """Apply a profile preset (quick/standard/accurate) to input generators.

    This composes existing powerups: `set_ecut_preset`, `set_kpoints_density`,
    and `set_smearing` to create a single-call convenience wrapper.
    """
    presets = {
        "quick": {"ecutwfc": 30, "rho_mult": 4, "kpoints": 50, "smearing": "gaussian", "degauss": 0.05},
        "standard": {"ecutwfc": 50, "rho_mult": 4, "kpoints": 100, "smearing": "marzari-vanderbilt", "degauss": 0.02},
        "accurate": {"ecutwfc": 80, "rho_mult": 6, "kpoints": 200, "smearing": "marzari-vanderbilt", "degauss": 0.01},
    }

    p = presets.get(profile, presets["standard"])
    new = set_ecut_preset(flow, p["ecutwfc"], rho_mult=p["rho_mult"], name_filter=name_filter, class_filter=class_filter)
    new = set_kpoints_density(new, p["kpoints"], name_filter=name_filter, class_filter=class_filter)
    new = set_smearing(new, smearing=p["smearing"], degauss=p["degauss"], name_filter=name_filter, class_filter=class_filter)
    return new


def set_mpi_procs(
    flow: JobType,
    nprocs: int,
    launcher: str = "mpirun -n",
    name_filter: str | None = None,
    class_filter: type[Maker] | None = BasePwscfMaker,
) -> JobType:
    """Set MPI launcher string (convenience) via `run_pwscf_kwargs`.

    Example: `set_mpi_procs(flow, 4)` will set `run_pwscf_kwargs['mpi'] = 'mpirun -n 4'`.
    """
    mpi_str = f"{launcher} {int(nprocs)}"
    return update_run_pwscf_kwargs(flow, {"mpi": mpi_str}, name_filter=name_filter, class_filter=class_filter)


def set_control_verbosity(
    flow: JobType,
    verbosity: int = 1,
    name_filter: str | None = None,
    class_filter: type[Maker] | None = BasePwscfMaker,
) -> JobType:
    """Set `verbosity` under `&CONTROL` namelist (convenience)."""
    return update_user_control_settings(flow, {"verbosity": verbosity}, name_filter=name_filter, class_filter=class_filter)


def set_nspin(
    flow: JobType,
    nspin: int = 1,
    name_filter: str | None = None,
    class_filter: type[Maker] | None = BasePwscfMaker,
) -> JobType:
    """Set `nspin` under `&SYSTEM` namelist."""
    return update_user_system_settings(flow, {"nspin": nspin}, name_filter=name_filter, class_filter=class_filter)


def add_metadata_key(flow: Flow, key: str, value: Any, class_filter: type[Maker] = BasePwscfMaker) -> Flow:
    """Add a single metadata key to task documents (convenience wrapper)."""
    return add_metadata_to_flow(flow, {key: value}, class_filter=class_filter)


def set_hubbard_and_magnetization(
    flow: JobType,
    hubbard_u: dict[str, float] | None = None,
    starting_magnetization: dict[str, float] | None = None,
    nspin: int = 2,
    lda_plus_u: bool = True,
    name_filter: str | None = None,
    class_filter: type[Maker] | None = BasePwscfMaker,
) -> JobType:
    """Convenience powerup to enable DFT+U and initial magnetizations.

    This sets the following keys under `input_set_generator->user_system`:
    - `nspin` (int)
    - `starting_magnetization` (dict mapping species -> value)
    - `lda_plus_u` (bool)
    - `Hubbard_U` (dict mapping species -> U value)

    Notes:
    - The `write_pwscf_input_set` simply writes whatever is present in
      `user_system` into the `&SYSTEM` namelist, so these keys are preserved
      in the produced `pw.in` files.
    - The parser (`parse_pwscf_output`) currently extracts magnetization
      values (via `total_magnetization` / `magnetization`) but does not
      explicitly extract Hubbard parameters from output files. For QE >= 7.1
      there are no breaking changes expected for these parsed magnetization
      fields; if you need to record U-values from outputs, add a parser
      extension.
    """
    updates: dict[str, Any] = {}
    if nspin is not None:
        updates["nspin"] = int(nspin)
    if starting_magnetization:
        updates["starting_magnetization"] = starting_magnetization
    if lda_plus_u is not None:
        updates["lda_plus_u"] = bool(lda_plus_u)
    if hubbard_u:
        # Use 'Hubbard_U' key which will be placed in &SYSTEM namelist
        updates["Hubbard_U"] = hubbard_u

    if not updates:
        return flow

    return update_user_system_settings(flow=flow, system_updates=updates, name_filter=name_filter, class_filter=class_filter)
