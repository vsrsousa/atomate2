import pytest

from atomate2.pwscf import powerups
from atomate2.pwscf.flows.core import DoubleRelaxMaker
from atomate2.pwscf.jobs.core import RelaxMaker


def test_apply_preset_and_bundle_and_mpi():
    drm = DoubleRelaxMaker()

    # apply preset
    new = powerups.apply_preset(drm, "quick")
    assert new.relax_maker1.input_set_generator.user_system["ecutwfc"] == 30
    assert new.relax_maker1.input_set_generator.user_electrons["degauss"] == 0.05

    # pseudo bundle
    b = powerups.set_pseudo_bundle(drm, "standard")
    assert b.relax_maker1.input_set_generator.user_pseudos["Si"] == "Si.upf"

    # mpi procs
    m = powerups.set_mpi_procs(drm, 4)
    assert m.relax_maker1.run_pwscf_kwargs["mpi"] == "mpirun -n 4"

    # job object
    job = RelaxMaker().make(1)
    job2 = powerups.apply_preset(job, "accurate")
    assert job2.function.__self__.input_set_generator.user_system["ecutwfc"] == 80
