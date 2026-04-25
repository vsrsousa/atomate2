import pytest

from atomate2.pwscf import powerups
from atomate2.pwscf.flows.core import DoubleRelaxMaker


def test_set_hubbard_and_magnetization_on_double_relax():
    drm = DoubleRelaxMaker()

    hubbard = {"Fe": 4.0}
    mags = {"Fe": 0.5}

    drm2 = powerups.set_hubbard_and_magnetization(drm, hubbard_u=hubbard, starting_magnetization=mags, nspin=2)

    # check first relax maker
    gen1 = drm2.relax_maker1.input_set_generator
    assert gen1.user_system["nspin"] == 2
    assert gen1.user_system["Hubbard_U"]["Fe"] == 4.0
    assert gen1.user_system["starting_magnetization"]["Fe"] == 0.5

    # check second relax maker
    gen2 = drm2.relax_maker2.input_set_generator
    assert gen2.user_system["nspin"] == 2
    assert gen2.user_system["Hubbard_U"]["Fe"] == 4.0
    assert gen2.user_system["starting_magnetization"]["Fe"] == 0.5
