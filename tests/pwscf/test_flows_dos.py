import pytest
from jobflow import run_locally
from pymatgen.core import Structure, Lattice

from atomate2.pwscf.flows.core import DOSMaker
from atomate2.pwscf.jobs.core import StaticMaker, NonSCFMaker
from atomate2.pwscf.sets.core import StaticSetGenerator


@pytest.fixture
def si_structure():
    return Structure(Lattice.cubic(5.43), ["Si", "Si"], [[0, 0, 0], [0.25, 0.25, 0.25]])


def test_dos_flow(monkeypatch, tmp_path, si_structure):
    monkeypatch.setattr("atomate2.pwscf.jobs.core.write_pwscf_input_set", lambda *a, **k: None)

    def fake_run(**kwargs):
        (tmp_path / "pw.out").touch()
        return {"return_code": 0, "out_file": str(tmp_path / "pw.out")}

    monkeypatch.setattr("atomate2.pwscf.jobs.core.run_pwscf", fake_run)
    monkeypatch.setattr("atomate2.pwscf.jobs.core.parse_pwscf_output", lambda p: {"final_energy": -3.0, "dos": [0.1, 0.2]})

    base_set = StaticSetGenerator(user_pseudos={"Si": "Si.upf"})

    static_maker = StaticMaker(input_set_generator=base_set, run_pwscf_kwargs={})
    nscf_maker = NonSCFMaker(input_set_generator=base_set, run_pwscf_kwargs={})

    maker = DOSMaker(static_maker=static_maker, nscf_maker=nscf_maker)
    flow = maker.make(si_structure)

    responses = run_locally(flow, create_folders=True, ensure_success=True)
    last = list(responses.values())[-1][1]
    td = last.output
    assert td.additional["run"]["return_code"] == 0
