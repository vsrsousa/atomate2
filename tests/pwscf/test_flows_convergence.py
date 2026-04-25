import pytest
from jobflow import run_locally
from pymatgen.core import Structure, Lattice

from atomate2.pwscf.flows.core import ConvergenceStudyMaker
from atomate2.pwscf.jobs.core import StaticMaker
from atomate2.pwscf.sets.core import StaticSetGenerator


@pytest.fixture
def si_structure():
    return Structure(Lattice.cubic(5.43), ["Si", "Si"], [[0, 0, 0], [0.25, 0.25, 0.25]])


def test_convergence_study(monkeypatch, tmp_path, si_structure):
    # capture calls to write_pwscf_input_set to inspect modified generators
    written = []

    def fake_write(structure, gen, out_dir):
        ecut = getattr(gen, "user_system", {}).get("ecutwfc")
        grid = getattr(gen, "user_kpoints", {}).get("grid")
        written.append((ecut, tuple(grid) if grid else None))

    monkeypatch.setattr("atomate2.pwscf.jobs.core.write_pwscf_input_set", fake_write)

    # mock runner and parser to avoid calling external pw.x
    def fake_run(**kwargs):
        (tmp_path / "pw.out").touch()
        return {"return_code": 0, "out_file": str(tmp_path / "pw.out")}

    monkeypatch.setattr("atomate2.pwscf.jobs.core.run_pwscf", fake_run)
    monkeypatch.setattr("atomate2.pwscf.jobs.core.parse_pwscf_output", lambda p: {"final_energy": -1.0})

    base_set = StaticSetGenerator(user_pseudos={"Si": "Si.upf"})
    static_maker = StaticMaker(input_set_generator=base_set, run_pwscf_kwargs={})

    maker = ConvergenceStudyMaker(
        static_maker=static_maker, ecut_list=[30, 40], kpoints_list=[(2, 2, 2), (3, 3, 3)]
    )

    job = maker.make(si_structure)
    responses = run_locally(job, create_folders=True, ensure_success=True)

    # Expect 4 runs (2 ecuts x 2 k-grids)
    assert len(written) == 4
    # ensure each ecut appears
    ecuts = sorted(set(e for e, g in written))
    assert ecuts == [30, 40]
