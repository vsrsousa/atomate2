from types import SimpleNamespace
from typing import Optional


def build_input_generator(
    user_control: Optional[dict] = None,
    user_system: Optional[dict] = None,
    user_electrons: Optional[dict] = None,
    user_pseudos: Optional[dict] = None,
) -> SimpleNamespace:
    """Create a minimal input-generator-like object used by the writer.

    The returned object exposes the attributes expected by
    ``write_pwscf_input_set``: `user_control`, `user_system`,
    `user_electrons`, `user_pseudos`.
    """
    gen = SimpleNamespace()
    gen.user_control = dict(user_control or {})
    gen.user_system = dict(user_system or {})
    gen.user_electrons = dict(user_electrons or {})
    gen.user_pseudos = dict(user_pseudos or {})
    return gen


def set_smearing(gen: SimpleNamespace, smearing: str, degauss: float) -> None:
    """Set smearing and degauss on the generator (moved to &SYSTEM by writer)."""
    gen.user_electrons = gen.user_electrons or {}
    gen.user_electrons["smearing"] = smearing
    gen.user_electrons["degauss"] = degauss


def set_hubbard(
    gen: SimpleNamespace, hubbard: dict, format: str = "new", projector: str = "ortho-atomic"
) -> None:
    """Configure Hubbard settings on the generator.

    - `hubbard` should be a mapping element->value (e.g., {"Fe": 4.0}).
    - `format` is 'new' (HUBBARD card) or 'old' (namelist style).
    """
    gen.user_system = gen.user_system or {}
    gen.user_system["Hubbard_U"] = dict(hubbard)
    gen.user_system["hubbard_format"] = format
    gen.user_system["hubbard_projector"] = projector


def set_cutoffs(gen: SimpleNamespace, ecutwfc: Optional[float] = None, ecutrho: Optional[float] = None) -> None:
    gen.user_system = gen.user_system or {}
    if ecutwfc is not None:
        gen.user_system["ecutwfc"] = ecutwfc
    if ecutrho is not None:
        gen.user_system["ecutrho"] = ecutrho


def set_control(gen: SimpleNamespace, **kwargs) -> None:
    gen.user_control = gen.user_control or {}
    gen.user_control.update(kwargs)


__all__ = [
    "build_input_generator",
    "set_smearing",
    "set_hubbard",
    "set_cutoffs",
    "set_control",
]
