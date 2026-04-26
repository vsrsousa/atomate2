from pathlib import Path
from types import SimpleNamespace

from pymatgen.core import Structure, Lattice

from atomate2.pwscf.files import write_pwscf_input_set


def test_hubbard_card_and_namelist(tmp_path):
    s = Structure(Lattice.cubic(3.5), ["Fe", "O"], [[0, 0, 0], [0.5, 0.5, 0.5]])
    gen = SimpleNamespace()
    gen.user_control = {}
    gen.user_system = {
        "Hubbard_U": {"Fe": 4.0},
        "starting_magnetization": {"Fe": 0.5},
        "hubbard_card": True,
        "lda_plus_u": True,
        "lda_plus_u_type": 2,
    }
    gen.user_electrons = {"degauss": 0.02, "smearing": "methfessel-paxton"}
    gen.user_pseudos = {"Fe": "Fe.pseudo", "O": "O.pseudo"}

    out = tmp_path / "pwtest"
    write_pwscf_input_set(s, gen, out_dir=out)
    txt = (out / "pw.in").read_text()

    # card header includes default projector (no parentheses)
    assert "HUBBARD ortho-atomic" in txt
    # default format is 'new' so expect card-style entry and not namelist entries
    assert "Fe-3d 4.0" in txt
    # ensure &SYSTEM namelist does not contain species-indexed Hubbard keys
    assert "&SYSTEM" in txt
    system_block = txt.split("&SYSTEM", 1)[1].split("/", 1)[0]
    assert "Hubbard_U(1)" not in system_block
    # starting_magnetization should remain in &SYSTEM namelist
    assert "starting_magnetization(1)" in system_block
    # degauss and smearing should be present in &SYSTEM (moved from electrons)
    assert "degauss" in system_block
    assert "smearing" in system_block
    # occupations should be set to 'smearing' when smearing provided
    lines = [l.strip() for l in system_block.splitlines()]
    occ_lines = [l for l in lines if l.startswith("occupations")]
    assert occ_lines, "occupations not found in &SYSTEM"
    assert "smearing" in occ_lines[0]
