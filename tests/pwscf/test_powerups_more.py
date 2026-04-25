import pytest

from atomate2.pwscf import powerups
from atomate2.pwscf.flows.core import DoubleRelaxMaker
from atomate2.pwscf.jobs.core import RelaxMaker


def test_set_ecut_and_smearing_and_run_kwargs():
    drm = DoubleRelaxMaker()

    # ecut preset
    drm2 = powerups.set_ecut_preset(drm, 50, rho_mult=6)
    assert drm2.relax_maker1.input_set_generator.user_system["ecutwfc"] == 50
    assert drm2.relax_maker1.input_set_generator.user_system["ecutrho"] == 300

    # smearing
    drm3 = powerups.set_smearing(drm, smearing="gaussian", degauss=0.05)
    assert drm3.relax_maker1.input_set_generator.user_electrons["smearing"] == "gaussian"
    assert drm3.relax_maker1.input_set_generator.user_electrons["degauss"] == 0.05

    # run kwargs
    drm4 = powerups.update_run_pwscf_kwargs(drm, {"mpi": "mpirun -n 4"})
    assert drm4.relax_maker1.run_pwscf_kwargs["mpi"] == "mpirun -n 4"

    # job object
    job = RelaxMaker().make(1)
    job2 = powerups.set_ecut_preset(job, 40)
    assert job2.function.__self__.input_set_generator.user_system["ecutwfc"] == 40


@pytest.mark.parametrize("density", [40, 100])
def test_set_ecut_name_filter(density):
    drm = DoubleRelaxMaker()
    flow = drm.make(1)
    # name_filter should match job names ('relax') for pwscf DoubleRelaxMaker
    new_flow = powerups.set_ecut_preset(flow, density, name_filter="relax")
    assert new_flow.jobs[0].function.__self__.input_set_generator.user_system["ecutwfc"] == density
    assert new_flow.jobs[1].function.__self__.input_set_generator.user_system["ecutwfc"] == density
