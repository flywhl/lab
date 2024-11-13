from pathlib import Path

from labfile import parse
from labfile.model.tree import LabfileNode
from lab.model.project import Project
from lab.service.service import Service
from lab.service.ir import ExperimentDefinition, SymbolTable


class LabfileService(Service):
    def parse(self, path: Path) -> Project:
        ast = parse(path)
        project = self._labfile_from_tree(ast)

        return project

    def _labfile_from_tree(self, tree: LabfileNode) -> Project:
        # Create intermediate definitions
        processes = [ExperimentDefinition.from_tree(node) for node in tree.processes]

        # Build symbol table
        symbols = SymbolTable(table={d.name: d for d in processes})

        # Convert to domain objects
        processes = [d.to_domain(symbols) for d in processes]

        return Project(experiments=processes)
