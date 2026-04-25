"""Task document schema for PWSCF (pw.x) calculations."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Union

from pydantic import BaseModel, Field
from pymatgen.core.structure import Structure

from atomate2.utils.datetime import datetime_str
from atomate2.utils.path import get_uri
from atomate2.pwscf.schemas import parse_pwscf_output


class PWOutputSummary(BaseModel):
    """Summary of parsed pw.x outputs."""

    final_energy: float | None = Field(None)
    total_energy: float | None = Field(None)
    converged: bool | None = Field(None)
    structure: Union[Structure, str] | None = Field(None)
    forces: Any = Field(None)
    ionic_steps: Any = Field(None)
    band_gap: float | None = Field(None)
    is_metal: bool | None = Field(None)
    magnetization: float | None = Field(None)
    stdout: str | None = Field(None)
    per_step_energies: list[float] | None = Field(None)
    per_step_forces: Any = Field(None)
    pressures: Any = Field(None)
    stress: Any = Field(None)
    scf_iterations: Any = Field(None)
    band_structure: Any = Field(None)
    dos: Any = Field(None)
    eigenvalues: Any = Field(None)
    occupations: Any = Field(None)
    timings: Any = Field(None)


class TaskDocument(BaseModel):
    """Minimal PWSCF TaskDocument capturing outputs and metadata."""

    dir_name: str | None = Field(None)
    last_updated: str = Field(default_factory=datetime_str)
    completed_at: str | None = Field(None)
    output: PWOutputSummary | None = Field(None)
    structure: Union[Structure, str] | None = Field(None, description="Final output structure from the task")
    additional: Dict[str, Any] | None = Field(None)
    schema_: str | None = Field(None, alias="schema")

    # Support both pydantic v1 and v2 without emitting deprecation warnings.
    try:
        import pydantic as _pydantic

        _pyd_major = int(getattr(_pydantic, "__version__", "0").split(".")[0])
    except Exception:
        _pyd_major = 0

    if _pyd_major >= 2:
        # pydantic v2 config
        model_config = {"populate_by_name": True}
    else:
        # pydantic v1 config
        class Config:  # type: ignore[misc]
            allow_population_by_field_name = True

    @classmethod
    def from_directory(cls, dir_name: Union[Path, str], **kwargs) -> "TaskDocument":
        dir_path = Path(dir_name)
        parsed = parse_pwscf_output(dir_path / "pw.out")

        out = PWOutputSummary(**{k: parsed.get(k) for k in parsed})

        return cls(dir_name=get_uri(dir_path), output=out, additional=kwargs)

    @classmethod
    def from_parsed(cls, parsed: dict, dir_name: Union[Path, str] | None = None, **kwargs) -> "TaskDocument":
        """Create a TaskDocument directly from a parsed pwscf output dict.

        Parameters
        ----------
        parsed
            Dictionary returned from :func:`parse_pwscf_output`.
        dir_name
            Optional directory name/uri for the task.
        **kwargs
            Additional fields to store in the `additional` attribute.
        """
        out = PWOutputSummary(**{k: parsed.get(k) for k in parsed})
        dir_uri = get_uri(Path(dir_name)) if dir_name is not None else None
        struct = parsed.get("structure")
        return cls(dir_name=dir_uri, output=out, structure=struct, additional=kwargs)
