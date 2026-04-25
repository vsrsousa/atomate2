from pathlib import Path

import pytest

from atomate2.pwscf.schemas import TaskDocument


def test_task_document_from_directory(monkeypatch, tmp_path):
    # create dummy pw.out
    p = tmp_path / "pw.out"
    p.write_text("dummy")

    # monkeypatch parse_pwscf_output to return known dict
    def fake_parse(path):
        return {"final_energy": -5.0, "converged": True}

    # patch the parser where TaskDocument.from_directory imports it
    monkeypatch.setattr("atomate2.pwscf.schemas.task.parse_pwscf_output", fake_parse)

    doc = TaskDocument.from_directory(tmp_path)
    assert doc.output.final_energy == -5.0
    assert doc.output.converged is True
    assert tmp_path.name in doc.dir_name
