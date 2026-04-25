"""Runner utilities for PWSCF (pw.x) under `pwscf` name.

This file provides a thin wrapper `run_pwscf` that mirrors the shape of
`vasp.run.run_vasp` but is intentionally minimal here as a scaffold.
"""

from __future__ import annotations

import logging
import subprocess
import shutil
from pathlib import Path
from typing import Sequence, Any

logger = logging.getLogger(__name__)


def run_pwscf(
    pwscf_cmd: str = "pw.x < pw.in > pw.out",
    validators: Sequence = (),
    handlers: Sequence = (),
    max_errors: int | None = None,
    scratch_dir: str | None = None,
    pwscf_job_kwargs: dict[str, Any] | None = None,
    custodian_kwargs: dict[str, Any] | None = None,
) -> dict:
    """Run a Quantum ESPRESSO pw.x job (scaffold).

    Minimal direct execution for scaffold.
    """
    pwscf_job_kwargs = pwscf_job_kwargs or {}
    custodian_kwargs = custodian_kwargs or {}

    logger.info("Running PWSCF: %s", pwscf_cmd)

    # If `pw.x` isn't available on PATH, avoid attempting to run external
    # binary during tests or on systems without PWSCF (pw.x) installed.
    if "pw.x" in pwscf_cmd and shutil.which("pw.x") is None:
        logger.warning("pw.x not found on PATH; skipping execution")
        return {"return_code": 127, "out_file": None}

    # Run the command and return metadata so callers can parse outputs.
    return_code = subprocess.call(pwscf_cmd, shell=True)  # noqa: S602
    logger.info("%s finished with return code: %s", pwscf_cmd, return_code)

    out_path = None
    # common default output filename when using shell redirection
    p = Path("pw.out")
    if p.exists():
        out_path = str(p)

    return {"return_code": return_code, "out_file": out_path}
