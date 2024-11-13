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
        definitions = [
            ExperimentDefinition(name=exp.name, path=exp.path)
            for exp in tree.experiments
        ]
        
        # Build symbol table
        symbols = SymbolTable(table={d.name: d for d in definitions})
        
        # Convert to domain objects
        experiments = [d.to_domain(symbols) for d in definitions]
        
        return Project(experiments=experiments)
