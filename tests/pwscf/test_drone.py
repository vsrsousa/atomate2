from pathlib import Path

from atomate2.pwscf.drones import PwscfDrone


def test_pwscf_drone_assimilate(monkeypatch, tmp_path):
    p = tmp_path / "pw.out"
    p.write_text("dummy")

    def fake_from_directory(path, **kwargs):
        class DummyDoc:
            def __init__(self):
                self.dir_name = str(path)

        return DummyDoc()

    monkeypatch.setattr("atomate2.pwscf.schemas.task.TaskDocument.from_directory", fake_from_directory)

    drone = PwscfDrone()
    doc = drone.assimilate(tmp_path)
    assert doc.dir_name == str(tmp_path)
