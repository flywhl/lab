from typing import Sequence, Set, Dict, List
from collections import defaultdict
from uuid import UUID
from lab.model.pipeline import Pipeline
from lab.model.project import Experiment, Project
from lab.service.experiment import ExperimentService


class PipelineService:
    """Service for managing and executing pipelines of experiments."""

    def __init__(self, experiment_service: ExperimentService) -> None:
        self._experiment_service = experiment_service

    ### PUBLIC ##############

    def create_pipeline(self, labfile: Project) -> Pipeline:
        """Create a Pipeline from a Labfile, with experimentes ordered by dependencies.

        Args:
            labfile: The input Labfile containing experimentes, providers, and datasets

        Returns:
            A Pipeline with ordered experiments ready for execution

        Raises:
            ValueError: If circular dependencies are detected between experimentes
        """
        ordered_experiments = self._order_experiments(labfile.experiments)

        # Create experiments from ordered experimentes
        return Pipeline(
            experiments=ordered_experiments,
        )

    def run(self, pipeline: Pipeline) -> None:
        """Execute all experiments in the pipeline in dependency order.

        Args:
            pipeline: The pipeline to execute
        """
        for exp in pipeline.experiments:
            self._experiment_service.run(exp)

    ### PRIVATE #############

    def _validate_no_cycles(
        self,
        experiment: Experiment,
        visited: Set[UUID],
        path: Set[UUID],
        graph: Dict[UUID, Set[Experiment]],
        experiments: Sequence[Experiment],
    ) -> None:
        """Detect cycles in the experiment dependency graph using DFS.

        Raises ValueError if a cycle is found.
        """
        path.add(experiment.id)
        visited.add(experiment.id)

        for dependency in graph[experiment.id]:
            if dependency.id in path:
                cycle = " -> ".join(
                    next(exp.name for exp in experiments if exp.id == exp_id)
                    for exp_id in path
                )
                raise ValueError(
                    f"Circular dependency detected: {cycle} -> {dependency.name}"
                )
            if dependency.id not in visited:
                self._validate_no_cycles(dependency, visited, path, graph, experiments)

        path.remove(experiment.id)

    def _order_experiments(
        self, experimentes: Sequence[Experiment]
    ) -> List[Experiment]:
        """Order experimentes based on their dependencies using topological sort.

        Raises ValueError if circular dependencies are detected.
        """
        # Build dependency graph
        graph: Dict[UUID, Set[Experiment]] = defaultdict(set)
        for experiment in experimentes:
            graph[experiment.id].update(experiment.dependencies)

        # Validate no cycles exist
        visited: Set[UUID] = set()
        for experiment in experimentes:
            if experiment.id not in visited:
                self._validate_no_cycles(
                    experiment, visited, set(), graph, experimentes
                )

        # Perform topological sort
        ordered: List[Experiment] = []
        visited = set()

        def visit(experiment: Experiment) -> None:
            if experiment.id in visited:
                return
            visited.add(experiment.id)

            for dependency in graph[experiment.id]:
                visit(dependency)

            ordered.append(experiment)

        for experiment in experimentes:
            visit(experiment)

        return ordered
