"""Base Q E job maker and helper decorator.

Provides a `qe_job` decorator (thin wrapper of `jobflow.job`) and a base maker
`BaseQEMaker` to follow project conventions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from jobflow import Maker, job
from typing import Any


def qe_job(method):
    """Decorator for QE maker `make` methods. Wraps `jobflow.job`.

    This is a small alias to keep API consistent with `vasp.vasp_job`.
    """
    return job(method)


@dataclass
class BaseQEMaker(Maker):
    """Base QE job maker scaffold.

    Subclasses should implement `make(self, structure, prev_dir=None)` decorated
    with `@qe_job`.
    """

    name: str = "base qe job"
    input_set_generator: Any = field(default_factory=lambda: None)
    write_input_set_kwargs: dict = field(default_factory=dict)
    run_qe_kwargs: dict = field(default_factory=dict)
