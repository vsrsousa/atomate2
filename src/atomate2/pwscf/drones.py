"""Drones for parsing PWSCF (pw.x) outputs into TaskDocument objects."""

from __future__ import annotations

import logging
from pathlib import Path

from pymatgen.apps.borg.hive import AbstractDrone

from atomate2.pwscf.schemas import TaskDocument

logger = logging.getLogger(__name__)


class PwscfDrone(AbstractDrone):
    """A drone to parse PWSCF `pw.out` directories into a `TaskDocument`.

    Parameters
    ----------
    **task_document_kwargs
        Keyword args passed to :obj:`TaskDocument.from_directory`.
    """

    def __init__(self, **task_document_kwargs) -> None:
        self.task_document_kwargs = task_document_kwargs

    def assimilate(self, path: str | Path | None = None) -> TaskDocument:
        path = path or Path.cwd()
        try:
            doc = TaskDocument.from_directory(path, **self.task_document_kwargs)
        except Exception:
            import traceback

            logger.exception(
                f"Error in {Path(path).absolute()}\n{traceback.format_exc()}"
            )
            raise
        return doc

    def get_valid_paths(self, path: tuple[str, list[str], list[str]]) -> list[str]:
        parent, subdirs, files = path
        # Accept directories that contain a pw.out file
        if any(f.startswith("pw.out") for f in files):
            return [parent]
        return []
