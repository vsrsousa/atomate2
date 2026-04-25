from atomate2.pwscf import set_ecut_preset, set_smearing, set_mpi_procs, set_control_verbosity
from atomate2.pwscf.flows.core import DoubleRelaxMaker


def test_imports_and_basic_usage():
    drm = DoubleRelaxMaker()
    new = set_ecut_preset(drm, 45)
    assert new.relax_maker1.input_set_generator.user_system["ecutwfc"] == 45
    new2 = set_smearing(drm, "gaussian", 0.03)
    assert new2.relax_maker1.input_set_generator.user_electrons["degauss"] == 0.03
    m = set_mpi_procs(drm, 2)
    assert m.relax_maker1.run_pwscf_kwargs["mpi"] == "mpirun -n 2"
    v = set_control_verbosity(drm, 2)
    assert v.relax_maker1.input_set_generator.user_control["verbosity"] == 2
