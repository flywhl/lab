from dataclasses import dataclass
import networkx as nx

from lab.project.model.project import Experiment, Project


@dataclass
class ExecutionPlan:
    ordered_experiments: list[Experiment]
    parallel_groups: list[set[Experiment]]


class Orchestrator:
    def resolve_execution_order(self, project: Project) -> list[Experiment]:
        """Determines the order experiments should be executed in based on dependencies"""
        # Build dependency graph
        graph = nx.DiGraph()

        for experiment in project.experiments:
            graph.add_node(experiment)
            for dep in experiment.dependencies:
                graph.add_edge(dep, experiment)

        # Check for cycles
        if not nx.is_directed_acyclic_graph(graph):
            raise ValueError("Experiment dependencies contain cycles")

        # Return topologically sorted order
        return list(nx.topological_sort(graph))

    def handle_failure(
        self, project: Project, failed_experiment: Experiment, error: Exception
    ) -> bool:
        """
        Determines how to proceed when an experiment fails.
        Returns True if execution should continue, False if it should stop.
        """
        # Get experiments that depend on the failed one
        dependent_experiments = {
            exp for exp in project.experiments if failed_experiment in exp.dependencies
        }

        if dependent_experiments:
            # If other experiments depend on this one, we should stop
            return False

        # If no dependencies, we can continue with other experiments
        return True

    def create_execution_plan(self, project: Project) -> ExecutionPlan:
        """Creates a plan for executing experiments, including parallel execution groups"""
        ordered = self.resolve_execution_order(project)

        # Group independent experiments that can run in parallel
        # This is a simple implementation - could be more sophisticated
        parallel_groups = []
        current_group = set()

        for exp in ordered:
            if not any(dep in current_group for dep in exp.dependencies):
                current_group.add(exp)
            else:
                if current_group:
                    parallel_groups.append(current_group)
                current_group = {exp}

        if current_group:
            parallel_groups.append(current_group)

        return ExecutionPlan(ordered, parallel_groups)
