"""Basic tests for PWSCF input set generation (scaffold)."""

from __future__ import annotations

from atomate2.pwscf.sets.base import PwscfInputGenerator


def test_pwscf_input_generator_to_inp():
    gen = PwscfInputGenerator(user_control={"calculation": "scf"})
    s = gen.to_inp()
    assert isinstance(s, str)
