import pytest

from atomate2.pwscf import powerups
from atomate2.pwscf.flows.core import DoubleRelaxMaker
from atomate2.pwscf.jobs.core import RelaxMaker


@pytest.mark.parametrize(
    "powerup,attribute,settings",
    [
        ("update_user_system_settings", "user_system", {"ecutwfc": 40}),
        ("update_user_pseudos_functional", "user_pseudo_functional", "PBE"),
        ("set_kpoints_density", "user_kpoints", {"reciprocal_density": 150}),
    ],
)
def test_extended_user_settings(powerup, attribute, settings):
    powerup_func = getattr(powerups, powerup)

    # maker
    rm = RelaxMaker()
    rm = powerup_func(rm, settings) if powerup != "set_kpoints_density" else powerup_func(rm, 150)
    assert getattr(rm.input_set_generator, attribute) == settings

    # job
    job = RelaxMaker().make(1)
    job = powerup_func(job, settings) if powerup != "set_kpoints_density" else powerup_func(job, 150)
    assert getattr(job.function.__self__.input_set_generator, attribute) == settings

    # flow maker
    drm = DoubleRelaxMaker()
    drm = powerup_func(drm, settings) if powerup != "set_kpoints_density" else powerup_func(drm, 150)
    assert getattr(drm.relax_maker1.input_set_generator, attribute) == settings

    # flow
    drm = DoubleRelaxMaker()
    flow = drm.make(1)
    flow = powerup_func(flow, settings) if powerup != "set_kpoints_density" else powerup_func(flow, 150)
    assert getattr(flow.jobs[0].function.__self__.input_set_generator, attribute) == settings
