from pathlib import Path

from lab.project.service.labfile import LabfileService


def test_parse_should_generate_valid_tree():
    labfile = Path(__file__).parent.parent / "Labfile.test"
    labfile_service = LabfileService()
    project = labfile_service.parse(labfile)

    assert len(project.experiments) == 2
