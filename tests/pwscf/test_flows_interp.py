import pytest
from jobflow import run_locally
from pymatgen.core import Structure, Lattice

from atomate2.pwscf.flows.core import BandInterpolationMaker
from atomate2.pwscf.jobs.core import StaticMaker, NonSCFMaker, BandStructureMaker
from atomate2.pwscf.sets.core import StaticSetGenerator, BandsSetGenerator


@pytest.fixture
def si_structure():
    return Structure(Lattice.cubic(5.43), ["Si", "Si"], [[0, 0, 0], [0.25, 0.25, 0.25]])


def test_band_interpolation_flow(monkeypatch, tmp_path, si_structure):
    monkeypatch.setattr("atomate2.pwscf.jobs.core.write_pwscf_input_set", lambda *a, **k: None)

    def fake_run(**kwargs):
        (tmp_path / "pw.out").touch()
        return {"return_code": 0, "out_file": str(tmp_path / "pw.out")}

    # final parse returns an interpolated bands key to indicate interpolation ran
    def fake_parse(path):
        return {"final_energy": -4.0, "interpolated_bands": True}

    monkeypatch.setattr("atomate2.pwscf.jobs.core.run_pwscf", fake_run)
    monkeypatch.setattr("atomate2.pwscf.jobs.core.parse_pwscf_output", fake_parse)

    base_set = StaticSetGenerator(user_pseudos={"Si": "Si.upf"})
    bands_set = BandsSetGenerator(user_pseudos={"Si": "Si.upf"})

    static_maker = StaticMaker(input_set_generator=base_set, run_pwscf_kwargs={})
    nscf_maker = NonSCFMaker(input_set_generator=base_set, run_pwscf_kwargs={})
    band_maker = BandStructureMaker(input_set_generator=bands_set, run_pwscf_kwargs={})

    maker = BandInterpolationMaker(static_maker=static_maker, nscf_maker=nscf_maker, band_maker=band_maker)

    flow = maker.make(si_structure)
    responses = run_locally(flow, create_folders=True, ensure_success=True)

    last = list(responses.values())[-1][1]
    td = last.output
    assert td.output and getattr(td.output, "interpolated_bands", True) is True
