from atomate2.pwscf.schemas import parse_pwscf_output


def test_parse_pwscf_output_extra_fields(monkeypatch):
    class DummyPWOut:
        def __init__(self, path):
            self.final_energy = -10.0
            self.total_energy = -9.5
            self.converged = True
            self.structure = "STRUCT"
            self.forces = [[0.0, 0.0, 0.0]]
            self.ionic_steps = [{"step": 1}]
            self.bandgap = 1.234
            self.is_metal = False
            self.total_magnetization = 0.0
            self.stdout = "output text"

    monkeypatch.setattr("atomate2.pwscf.schemas.pwscf_output.PWOutput", DummyPWOut)
    res = parse_pwscf_output("dummy.out")
    assert res["final_energy"] == -10.0
    assert res["total_energy"] == -9.5
    assert res["converged"] is True
    assert res["structure"] == "STRUCT"
    assert res["forces"] == [[0.0, 0.0, 0.0]]
    assert res["ionic_steps"] == [{"step": 1}]
    assert res["band_gap"] == 1.234
    assert res["is_metal"] is False
    assert res["magnetization"] == 0.0
    assert "output text" in res["stdout"]
