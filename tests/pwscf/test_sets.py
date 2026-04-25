"""Basic tests for PWSCF input set generation (scaffold)."""

from __future__ import annotations

from atomate2.pwscf.sets.base import PwscfInputGenerator


def test_pwscf_input_generator_to_inp():
    gen = PwscfInputGenerator(user_control={"calculation": "scf"})
    s = gen.to_inp()
    assert isinstance(s, str)


def test_bands_set_generator_high_symmetry(monkeypatch, tmp_path):
    from pymatgen.core import Structure, Lattice

    # patch the generator to return a predictable kpath without invoking pymatgen

    struct = Structure(Lattice.cubic(5.43), ["Si", "Si"], [[0, 0, 0], [0.25, 0.25, 0.25]])
    gen = PwscfInputGenerator()
    # wrap with BandsSetGenerator behavior
    from atomate2.pwscf.sets.core import BandsSetGenerator

    bgen = BandsSetGenerator(kpath_preset="seekpath")
    bgen.user_pseudos = {"Si": "Si.upf"}
    # simulate seekpath returning a known path by monkeypatching the generator
    bgen.generate_kpoints = lambda struct: {"mode": "path", "kpoints_path": [(0.0, 0.0, 0.0), (0.5, 0.0, 0.0)]}

    # write pw.in and ensure K_POINTS appended
    from atomate2.pwscf.files import write_pwscf_input_set

    write_pwscf_input_set(struct, bgen, out_dir=tmp_path)
    content = (tmp_path / "pw.in").read_text()
    assert "K_POINTS" in content
    assert "0.00000000 0.00000000 0.00000000" in content
