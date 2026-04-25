"""Runner utilities for PWSCF (pw.x) under `pwscf` name.

This file provides a thin wrapper `run_pwscf` that mirrors the shape of
`vasp.run.run_vasp` but is intentionally minimal here as a scaffold.
"""

from __future__ import annotations

import logging
import subprocess
from typing import Sequence, Any

logger = logging.getLogger(__name__)


def run_pwscf(
    qe_cmd: str = "pw.x < pw.in > pw.out",
    validators: Sequence = (),
    handlers: Sequence = (),
    max_errors: int | None = None,
    scratch_dir: str | None = None,
    qe_job_kwargs: dict[str, Any] | None = None,
    custodian_kwargs: dict[str, Any] | None = None,
) -> None:
    """Run a Quantum ESPRESSO pw.x job (scaffold).

    Minimal direct execution for scaffold.
    """
    qe_job_kwargs = qe_job_kwargs or {}
    custodian_kwargs = custodian_kwargs or {}

    logger.info("Running PWSCF: %s", qe_cmd)
    return_code = subprocess.call(qe_cmd, shell=True)  # noqa: S602
    logger.info("%s finished with return code: %s", qe_cmd, return_code)
