import subprocess

from pathlib import Path

import pytest

from pymatgen.core import Structure, Lattice

from atomate2.pwscf.files import write_pwscf_input_set
from atomate2.pwscf.run import run_pwscf
from atomate2.pwscf.sets.base import PwscfInputGenerator
from atomate2.pwscf.schemas import parse_pwscf_output


class DummyInputGenerator:
    def __init__(self):
        self.user_control = {"prefix": "test", "restart_mode": "from_scratch"}
        self.user_system = {}
        self.user_electrons = {}
        self.user_pseudos = {"Si": "Si.upf"}
        self.user_kpoints = {"mode": "automatic", "grid": [1, 1, 1]}


def test_write_pwscf_input_set_creates_pw_in(tmp_path):
    struct = Structure(Lattice.cubic(5.43), ["Si", "Si"], [[0, 0, 0], [0.25, 0.25, 0.25]])
    gen = DummyInputGenerator()
    write_pwscf_input_set(struct, gen, out_dir=tmp_path)
    pw = tmp_path / "pw.in"
    assert pw.exists()
    content = pw.read_text()
    assert "ATOMIC_POSITIONS" in content or "CELL_PARAMETERS" in content


def test_run_pwscf_returns_metadata(monkeypatch, tmp_path):
    # monkeypatch subprocess.call to create pw.out and return 0
    def fake_call(cmd, shell):
        (tmp_path / "pw.out").write_text("dummy output")
        return 0

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(subprocess, "call", fake_call)
    res = run_pwscf(pwscf_cmd="echo noop")
    assert isinstance(res, dict)
    assert res["return_code"] == 0
    assert res["out_file"] is not None


def test_pwscf_input_generator_to_inp_formats():
    gen = PwscfInputGenerator(
        user_control={"calculation": "scf", "prefix": "abc"},
        user_system={"ecutwfc": 30},
        user_electrons={"conv_thr": 1e-6},
        user_kpoints={"mode": "automatic", "grid": [2, 2, 2]},
    )
    s = gen.to_inp()
    assert "&CONTROL" in s
    assert "&SYSTEM" in s
    assert "ecutwfc" in s or "ecutwfc" in s.lower()


def test_parse_pwscf_output_handles_missing_attributes(monkeypatch, tmp_path):
    class MinimalPWOut:
        def __init__(self, path):
            self.path = path

    monkeypatch.setattr("atomate2.pwscf.schemas.pwscf_output.PWOutput", MinimalPWOut)
    # should not raise
    res = parse_pwscf_output(tmp_path / "does_not_exist.out")
    assert "final_energy" in res and "converged" in res


def test_run_pwscf_validators_and_handlers(monkeypatch, tmp_path):
    # simulate subprocess.call behavior that writes different outputs per call
    calls = {"n": 0}

    def fake_call(cmd, shell):
        calls["n"] += 1
        if calls["n"] == 1:
            (tmp_path / "pw.out").write_text("BAD")
            return 0
        else:
            (tmp_path / "pw.out").write_text("GOOD")
            return 0

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("subprocess.call", fake_call)

    # validator: return True only when out_file contains GOOD
    def validator(result):
        out = result.get("out_file")
        if not out:
            return False
        try:
            text = Path(out).read_text()
        except Exception:
            return False
        return "GOOD" in text

    # handler: no-op (we allow subprocess.call second invocation to produce GOOD)
    def handler(result, attempt, cmd):
        # record that handler ran
        result.setdefault("_handler_runs", 0)
        result["_handler_runs"] += 1

    res = run_pwscf(pwscf_cmd="echo noop", validators=(validator,), handlers=(handler,), custodian_kwargs={"backoff": 0, "max_retries": 3})
    assert res["return_code"] == 0
    assert res["out_file"] is not None
    # validator should have passed after retry
    assert Path(res["out_file"]).read_text() == "GOOD"
