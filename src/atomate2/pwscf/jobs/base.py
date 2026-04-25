"""Base PWSCF job maker and helper decorator.

Provides a `pwscf_job` decorator (thin wrapper of `jobflow.job`) and a base maker
`BasePwscfMaker` to follow project conventions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from jobflow import Maker, job
from typing import Any


def pwscf_job(method):
    """Decorator for PWSCF maker `make` methods. Wraps `jobflow.job`.
    Use this decorator as `@pwscf_job` in new code.
    """
    return job(method)


# No backwards-compatible aliases retained; use `pwscf_job`.


@dataclass
class BasePwscfMaker(Maker):
    """Base PWSCF maker scaffold.

    Subclasses should implement `make(self, structure, prev_dir=None)` decorated
    with `@pwscf_job`.
    """

    name: str = "base pwscf job"
    input_set_generator: Any = field(default_factory=lambda: None)
    write_input_set_kwargs: dict = field(default_factory=dict)
    # Primary preferred name for kwargs passed to the runner
    run_pwscf_kwargs: dict = field(default_factory=dict)
    # Note: legacy `qe` names were removed; use `run_pwscf_kwargs`.
