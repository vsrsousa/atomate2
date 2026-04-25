"""Powerups for Quantum ESPRESSO workflows.

Powerups modify makers/flows to adjust input generators or settings.
This module mirrors the pattern used by `vasp.powerups`.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, TypeVar

from jobflow.core.maker import Maker

JobType = TypeVar("JobType")


def update_qe_input_generators(flow: JobType, updates: dict[str, Any]) -> JobType:
    """Apply dictionary updates to QE input generators within a flow/maker.

    This is a shallow scaffold that demonstrates the API surface; implementations
    should follow patterns in `atomate2.vasp.powerups`.
    """
    new = deepcopy(flow)
    if isinstance(new, Maker):
        new = new.update_kwargs(update={"_set": updates})
    else:
        new.update_maker_kwargs(update={"_set": updates})
    return new
