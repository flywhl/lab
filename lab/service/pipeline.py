from typing import Sequence, Set, Dict, List
from collections import defaultdict
from lab.model.pipeline import Pipeline
from lab.model.project import Experiment, Project, ValueReference
from lab.service.experiment import ExperimentService


class PipelineService:
    """Service for managing and executing pipelines of experiments."""

    def __init__(self, experiment_service: ExperimentService) -> None:
        self._experiment_service = experiment_service

    def _find_experiment_dependencies(self, experiment: Experiment) -> Set[Experiment]:
        """Extract all experiment resources that this experiment depends on via ValueReferences."""
        dependencies = set()

        for value in experiment.parameters.values():
            if isinstance(value, ValueReference):
                if isinstance(value.owner, Experiment):
                    dependencies.add(value.owner)

        return dependencies

    def _validate_no_cycles(
        self,
        experiment: Experiment,
        visited: Set[Experiment],
        path: Set[Experiment],
        graph: Dict[Experiment, Set[Experiment]],
    ) -> None:
        """
        Detect cycles in the experiment dependency graph using DFS.
        Raises ValueError if a cycle is found.
        """
        path.add(experiment)
        visited.add(experiment)

        for dependency in graph[experiment]:
            if dependency in path:
                cycle = " -> ".join(p.name for p in path)
                raise ValueError(
                    f"Circular dependency detected: {cycle} -> {dependency.name}"
                )
            if dependency not in visited:
                self._validate_no_cycles(dependency, visited, path, graph)

        path.remove(experiment)

    def _order_experimentes(
        self, experimentes: Sequence[Experiment]
    ) -> List[Experiment]:
        """
        Order experimentes based on their dependencies using topological sort.
        Raises ValueError if circular dependencies are detected.
        """
        # Build dependency graph
        graph: Dict[Experiment, Set[Experiment]] = defaultdict(set)
        for experiment in experimentes:
            graph[experiment].update(self._find_experiment_dependencies(experiment))

        # Validate no cycles exist
        visited: Set[Experiment] = set()
        for experiment in experimentes:
            if experiment not in visited:
                self._validate_no_cycles(experiment, visited, set(), graph)

        # Perform topological sort
        ordered: List[Experiment] = []
        visited = set()

        def visit(experiment: Experiment) -> None:
            if experiment in visited:
                return
            visited.add(experiment)

            for dependency in graph[experiment]:
                visit(dependency)

            ordered.append(experiment)

        for experiment in experimentes:
            visit(experiment)

        return ordered

    def create_pipeline(self, labfile: Project) -> Pipeline:
        """
        Create a Pipeline from a Labfile, with experimentes ordered by dependencies.

        Args:
            labfile: The input Labfile containing experimentes, providers, and datasets

        Returns:
            A Pipeline with ordered experiments ready for execution

        Raises:
            ValueError: If circular dependencies are detected between experimentes
        """
        ordered_experiments = self._order_experimentes(labfile.experiments)

        # Create experiments from ordered experimentes
        # (assuming Pipeline model accepts a list of experimentes or experiments)
        return Pipeline(
            experiments=ordered_experiments,
            # providers=labfile.providers,
            # datasets=labfile.datasets,
        )

    def run(self, pipeline: Pipeline) -> None:
        """
        Execute all experiments in the pipeline in dependency order.

        Args:
            pipeline: The pipeline to execute
        """
        for exp in pipeline.experiments:
            self._experiment_service.run(exp)

