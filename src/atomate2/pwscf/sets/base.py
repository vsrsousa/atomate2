"""Base input generator for Quantum ESPRESSO (pw.x) under `pwscf`.

This file provides a `PwscfInputGenerator`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PwscfInputGenerator:
    """Minimal PWSCF input generator scaffold.

    Attributes
    ----------
    user_control: dict
        Values to place in the `&CONTROL` namelist.
    user_system: dict
        Values to place in the `&SYSTEM` namelist.
    user_electrons: dict
        Values to place in the `&ELECTRONS` namelist.
    user_kpoints: dict
        Settings for the `K_POINTS` card.
    user_pseudos: dict
        Mapping element -> pseudopotential filename.
    """

    user_control: dict[str, Any] = field(default_factory=dict)
    user_system: dict[str, Any] = field(default_factory=dict)
    user_electrons: dict[str, Any] = field(default_factory=dict)
    user_kpoints: dict[str, Any] = field(default_factory=dict)
    user_pseudos: dict[str, str] = field(default_factory=dict)

    def to_inp(self) -> str:
        """Return a minimal pw.x input string generated from the stored config.

        Produces simple namelists for `&CONTROL`, `&SYSTEM` and `&ELECTRONS`,
        a `K_POINTS` card when `user_kpoints` is set, and a brief pseudopotential
        mapping comment.
        """

        def _format_namelist(name: str, data: dict[str, Any]) -> str:
            if not data:
                return ""
            lines = [f"&{name}"]
            for k, v in data.items():
                # Basic formatting: strings should be quoted in pw.x input
                if isinstance(v, str):
                    lines.append(f"  {k} = '{v}'")
                else:
                    lines.append(f"  {k} = {v}")
            lines.append("/")
            return "\n".join(lines)

        parts: list[str] = []
        c = _format_namelist("CONTROL", self.user_control)
        if c:
            parts.append(c)
        s = _format_namelist("SYSTEM", self.user_system)
        if s:
            parts.append(s)
        e = _format_namelist("ELECTRONS", self.user_electrons)
        if e:
            parts.append(e)

        # K_POINTS handling (minimal): allow automatic and explicit lists
        if self.user_kpoints:
            kp = self.user_kpoints
            mode = kp.get("mode", "automatic")
            if mode.lower() == "automatic":
                # expect grid like [nkx, nky, nkz, 0,0,0]
                grid = kp.get("grid") or kp.get("automatic")
                if grid:
                    parts.append("K_POINTS automatic\n{} {} {} 0 0 0".format(*grid[:3]))
                else:
                    parts.append("K_POINTS automatic\n1 1 1 0 0 0")
            else:
                # fallback: write a comment with provided kpoints
                parts.append("K_POINTS {mode}\n! user provided kpoints".format(mode=mode))

        # Pseudopotential mapping as comments to guide the user
        if self.user_pseudos:
            parts.append("! PSEUDOPOTENTIALS:")
            for el, fn in self.user_pseudos.items():
                parts.append(f"!   {el} -> {fn}")

        return "\n\n".join(parts)
