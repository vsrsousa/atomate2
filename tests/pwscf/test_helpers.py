from pathlib import Path
from pymatgen.core import Structure, Lattice

from atomate2.pwscf.helpers import (
    build_input_generator,
    set_smearing,
    set_hubbard,
    set_cutoffs,
    set_control,
)
from atomate2.pwscf.files import write_pwscf_input_set


def test_helpers_generate_pw(tmp_path):
    s = Structure(Lattice.cubic(3.5), ["Fe", "O"], [[0, 0, 0], [0.5, 0.5, 0.5]])
    gen = build_input_generator()
    set_control(gen, calculation="scf", prefix="h_test")
    set_cutoffs(gen, ecutwfc=45, ecutrho=360)
    set_smearing(gen, "gauss", 0.01)
    set_hubbard(gen, {"Fe": 4.0}, format="new", projector="ortho-atomic")
    gen.user_pseudos = {"Fe": "Fe.pseudo", "O": "O.pseudo"}

    out = tmp_path / "pwtest"
    write_pwscf_input_set(s, gen, out_dir=out)
    txt = (out / "pw.in").read_text()

    # check cutoffs present
    assert "ecutwfc" in txt
    assert "ecutrho" in txt
    # smearing moved into &SYSTEM
    assert "smearing" in txt
    # occupations should be set to smearing
    system_block = txt.split("&SYSTEM", 1)[1].split("/", 1)[0]
    assert "occupations" in system_block
    # hubbard card present
    assert "HUBBARD ortho-atomic" in txt
