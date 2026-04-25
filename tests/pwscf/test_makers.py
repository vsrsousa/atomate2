import pytest
from monty.json import MSONable
from jobflow import run_locally
from pymatgen.core import Structure, Lattice
from atomate2.pwscf.jobs.core import RelaxMaker, StaticMaker

class DummyInputGenerator(MSONable):
    def __init__(self, **kwargs):
        self.user_control = {}
        self.user_system = {}
        self.user_electrons = {}
        self.user_pseudos = {"Si": "Si.upf"}
        self.user_kpoints = {}

@pytest.fixture
def si_structure():
    return Structure(Lattice.cubic(5.43), ["Si", "Si"], [[0, 0, 0], [0.25, 0.25, 0.25]])

def test_relax_maker_runs_and_parses(monkeypatch, tmp_path, si_structure):
    # mock write_pwscf_input_set to ensure it's called
    called = {}

    def fake_write(structure, gen, out_dir):
        called['write'] = True

    monkeypatch.setattr("atomate2.pwscf.jobs.core.write_pwscf_input_set", fake_write)

    # mock run_pwscf to return a fake out file
    def fake_run(**kwargs):
        # Create a dummy out file so parse_pwscf_output doesn't run the real one
        (tmp_path / "pw.out").touch()
        return {"return_code": 0, "out_file": str(tmp_path / "pw.out")}

    monkeypatch.setattr("atomate2.pwscf.jobs.core.run_pwscf", fake_run)

    # mock parser to return known values
    def fake_parse(path):
        return {"final_energy": -1.0, "converged": True}

    monkeypatch.setattr(
        "atomate2.pwscf.jobs.core.parse_pwscf_output", fake_parse
    )

    maker = RelaxMaker(input_set_generator=DummyInputGenerator(), run_pwscf_kwargs={})
    job = maker.make(structure=si_structure)

    # run the job locally and inspect the response
    responses = run_locally(job, create_folders=True, ensure_success=True)
    resp = list(responses.values())[0][1]
    # makers now return a TaskDocument as the job output
    td = resp.output
    assert td.additional["run"]["return_code"] == 0
    assert td.output.final_energy == -1.0

def test_static_maker_runs_and_parses(monkeypatch, tmp_path, si_structure):
    monkeypatch.setattr("atomate2.pwscf.jobs.core.write_pwscf_input_set", lambda *a, **k: None)
    monkeypatch.setattr("atomate2.pwscf.jobs.core.run_pwscf", lambda **k: {"return_code": 1, "out_file": str(tmp_path / "pw.out")})
    monkeypatch.setattr("atomate2.pwscf.jobs.core.parse_pwscf_output", lambda p: {"final_energy": None})
    (tmp_path / "pw.out").touch()

    maker = StaticMaker(input_set_generator=DummyInputGenerator(), run_pwscf_kwargs={})
    job = maker.make(structure=si_structure)
    responses = run_locally(job, create_folders=True, ensure_success=False)
    resp = list(responses.values())[0][1]
    td = resp.output
    assert td.additional["run"]["return_code"] == 1
