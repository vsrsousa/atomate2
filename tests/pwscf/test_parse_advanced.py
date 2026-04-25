from atomate2.pwscf.schemas import parse_pwscf_output


def test_parse_advanced_fields(monkeypatch):
    class DummyPWOut:
        def __init__(self, path):
            self.ionic_steps = [
                {"energy": -1.0, "forces": [[0, 0, 0]]},
                {"energy": -0.9, "forces": [[0.1, 0, 0]]},
            ]
            self.pressure = 5.0
            self.stress = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
            self.scf_history = [{"it": 1}, {"it": 2}]
            self.bands = "BANDOBJ"
            self.dos = "DOSOBJ"
            self.eigenvalues = [[1.0, 2.0], [1.1, 2.1]]
            self.occupations = [[1, 0], [1, 0]]
            self.timings = {"wall": 1.23}

    monkeypatch.setattr("atomate2.pwscf.schemas.pwscf_output.PWOutput", DummyPWOut)
    res = parse_pwscf_output("dummy.out")
    assert res["per_step_energies"] == [-1.0, -0.9]
    assert res["per_step_forces"] == [[[0, 0, 0]], [[0.1, 0, 0]]]
    assert res["pressures"] == 5.0
    assert res["stress"] == [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
    assert res["scf_iterations"] == [{"it": 1}, {"it": 2}]
    assert res["band_structure"] == "BANDOBJ"
    assert res["dos"] == "DOSOBJ"
    assert res["eigenvalues"] == [[1.0, 2.0], [1.1, 2.1]]
    assert res["occupations"] == [[1, 0], [1, 0]]
    assert res["timings"]["wall"] == 1.23
