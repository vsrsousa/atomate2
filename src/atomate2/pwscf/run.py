"""Runner utilities for PWSCF (pw.x) under `pwscf` name.

This file provides a thin wrapper `run_pwscf` that mirrors the shape of
`vasp.run.run_vasp` but is intentionally minimal here as a scaffold.
"""

from __future__ import annotations

import logging
import subprocess
import shutil
import time
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

    attempts = 0
    backoff = float(custodian_kwargs.get("backoff", 0))
    max_retries = custodian_kwargs.get("max_retries", None)

    while True:
        logger.info("Running PWSCF: %s (attempt %s)", pwscf_cmd, attempts + 1)

        # If `pw.x` isn't available on PATH, avoid attempting to run external
        # binary during tests or on systems without PWSCF (pw.x) installed.
        if "pw.x" in pwscf_cmd and shutil.which("pw.x") is None:
            logger.warning("pw.x not found on PATH; skipping execution")
            return {"return_code": 127, "out_file": None}

        # Run the command and return metadata so callers can parse outputs.
        return_code = subprocess.call(pwscf_cmd, shell=True)  # noqa: S602
        logger.info("%s finished with return code: %s", pwscf_cmd, return_code)

        out_path = None
        p = Path("pw.out")
        if p.exists():
            out_path = str(p)

        result = {"return_code": return_code, "out_file": out_path}

        # If no validators provided, accept result immediately
        if not validators:
            return result

        # run validators: a validator is expected to accept `result` and
        # return True when the result is acceptable
        all_ok = True
        for v in validators:
            try:
                ok = v(result)
            except Exception:
                ok = False
            if not ok:
                all_ok = False
                break

        if all_ok:
            return result

        # failed validation: run handlers (side-effects) and potentially retry
        for h in handlers:
            try:
                # handler signature may accept (result,) or (result, attempt, pwscf_cmd)
                try:
                    h(result, attempts + 1, pwscf_cmd)
                except TypeError:
                    h(result)
            except Exception:
                logger.exception("Handler raised an exception")

        attempts += 1
        # check both legacy max_errors and custodian max_retries
        limit = max_errors if max_errors is not None else max_retries
        if limit is not None and attempts > int(limit):
            logger.warning("Maximum handler retries reached (%s)", limit)
            return result

        # backoff between retries (defaults to 0 to avoid slowing tests)
        if backoff and backoff > 0:
            sleep_for = backoff * (2 ** (attempts - 1))
            logger.info("Sleeping %.3fs before retrying pwscf", sleep_for)
            time.sleep(sleep_for)
        # otherwise loop and retry
