"""Basic tests for QE input set generation (scaffold)."""

from __future__ import annotations

from atomate2.qe.sets.base import QeInputGenerator


def test_qe_input_generator_to_inp():
    gen = QeInputGenerator(user_control={"calculation": "scf"})
    s = gen.to_inp()
    assert isinstance(s, str)
