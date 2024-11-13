from pathlib import Path

from labfile import parse
from labfile.model.tree import LabfileNode
from lab.model.project import Project
from lab.service.service import Service


class LabfileService(Service):
    def parse(self, path: Path) -> Project:
        ast = parse(path)
        project = self._labfile_from_tree(ast)

        return project

    def _labfile_from_tree(self, tree: LabfileNode) -> Project: ...
