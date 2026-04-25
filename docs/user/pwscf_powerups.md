PWSCF Powerups
==============

This page documents the convenience "powerups" available for PWSCF (`pw.x`) workflows in the `atomate2.pwscf.powerups` module and their package-level re-exports under `atomate2.pwscf`.

Overview
--------

Powerups are small helpers that mutate `jobflow` Makers, Jobs, or Flows to apply common configuration changes without manually editing each maker. The PWSCF helpers follow the patterns used by `atomate2.vasp.powerups` and are safe to use on Makers, Jobs, and Flows (they return modified copies when appropriate).

Common usage patterns
---------------------

- Apply globally to a `Maker` or `Flow`:

  from atomate2.pwscf import set_ecut_preset
  flow = set_ecut_preset(flow, 50)

- Apply to a single named job in a `Flow` via `name_filter`:

  flow = set_kpoints_density(flow, 200, name_filter="relax")

- Update runner-specific kwargs (e.g., MPI launcher):

  flow = update_run_pwscf_kwargs(flow, {"mpi": "mpirun -n 4"})

Key powerups
-------------

- `update_user_control_settings(flow, {...})`
  Update values in the `&CONTROL` namelist for input generators.

- `update_user_system_settings(flow, {...})`
  Update values in the `&SYSTEM` namelist (e.g., `ecutwfc`, `nspin`).

- `update_user_kpoints_settings(flow, {...})`
  Update k-point settings (reciprocal density or explicit grid).

- `update_user_pseudos(flow, {...})`
  Set element -> pseudopotential filename mappings.

- `set_ecut_preset(flow, ecutwfc, rho_mult=4)`
  Convenience to set `ecutwfc` and `ecutrho` together.

- `set_smearing(flow, smearing, degauss)`
  Set smearing flags under the `ELECTRONS` namelist.

- `set_kpoints_density(flow, density)`
  Shortcut to set `user_kpoints.reciprocal_density`.

- `update_run_pwscf_kwargs(flow, {...})`
  Update runner kwargs passed to `run_pwscf` such as `mpi`.

- `set_pseudo_bundle(flow, bundle_name)`
  Apply a small named bundle of pseudos (convenience; extend as needed).

- `apply_preset(flow, profile)`
  Composite preset (quick/standard/accurate) that applies sensible `ecut`, `kpoints`, and smearing settings.

- `set_mpi_procs(flow, nprocs)`
  Convenience to set the MPI launcher string.

- `set_control_verbosity(flow, level)`
  Shorthand for setting `verbosity` in `&CONTROL`.

- `set_nspin(flow, nspin)`
  Shorthand for setting `nspin` in `&SYSTEM`.

Package exports
---------------

All powerup helpers are re-exported from the `atomate2.pwscf` package root, so you can import them directly:

  from atomate2.pwscf import set_ecut_preset, set_smearing

Examples
--------

1) Apply a standard preset to a flow:

  from atomate2.pwscf import apply_preset
  flow = apply_preset(flow, "standard")

2) Set MPI and add metadata to a particular job name:

  flow = set_mpi_procs(flow, 8)
  flow = add_metadata_key(flow, "project", "battery_study")

Extending
---------

If you want additional presets or pseudos, extend `set_pseudo_bundle` or the `presets` dictionary in `apply_preset` located at `src/atomate2/pwscf/powerups.py`.
