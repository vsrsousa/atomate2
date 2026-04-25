import pytest

from atomate2.pwscf.schemas import parse_pwscf_output


def test_parse_pwscf_output_monkeypatch(monkeypatch):
    class DummyPWOut:
        def __init__(self, path):
            self.path = path
            self.final_energy = -123.456
            self.converged = True
            self.structure = "DUMMY_STRUCTURE"
            self.forces = [[0.0, 0.0, 0.0]]

    # Replace the PWOutput used inside our parser with the dummy
    monkeypatch.setattr(
        "atomate2.pwscf.schemas.pwscf_output.PWOutput", DummyPWOut
    )

    res = parse_pwscf_output("does_not_matter.out")
    assert res["final_energy"] == -123.456
    assert res["converged"] is True
    assert res["structure"] == "DUMMY_STRUCTURE"
    assert res["forces"] == [[0.0, 0.0, 0.0]]
