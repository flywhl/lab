from uuid import UUID, uuid4

from pydantic import Field
from lab.core.model import Model
from lab.project.model.project import Experiment, Project, ValueReference
from lab.runtime.model.execution import ScriptExecution


class ExecutionPlan(Model):
    id: UUID = Field(default_factory=uuid4)
    project: Project
    ordered_experiments: list[Experiment]

    def __str__(self) -> str:
        """Format the execution plan in a clear, visually appealing way."""
        # Header with plan ID
        lines = ["┌─ Execution Plan ─" + "─" * 50, f"│ ID: {self.id}", "│"]

        # Build dependency graph for visualization
        dep_graph: dict[str, set[str]] = {}
        for exp in self.ordered_experiments:
            dep_graph[exp.name] = {d.name for d in exp.dependencies}

        # Format experiments section
        lines.append("│ Experiments:")
        for i, exp in enumerate(self.ordered_experiments, 1):
            # Experiment header with number and name
            exp_header = f"│   {i}. {exp.name}"
            if exp.dependencies:
                deps = ", ".join(d.name for d in exp.dependencies)
                exp_header += f" (depends on: {deps})"
            lines.append(exp_header)

            # Execution method
            if isinstance(exp.execution_method, ScriptExecution):
                cmd = f"{exp.execution_method.command} {' '.join(exp.execution_method.args)}"
                lines.append(f"│      Run: {cmd}")

            # Parameters
            if exp.parameters:
                lines.append("│      Parameters:")
                for name, value in exp.parameters.items():
                    if isinstance(value, ValueReference):
                        val_str = f"@{value.owner.name}.{value.attribute}"
                    else:
                        val_str = str(value)
                    lines.append(f"│        • {name}: {val_str}")

        # ASCII dependency graph
        if len(self.ordered_experiments) > 1:
            lines.extend(["│", "│ Dependency Flow:", "│   " + "─" * 30])

            def build_graph_lines() -> list[str]:
                graph = []
                for i, exp in enumerate(self.ordered_experiments):
                    prefix = (
                        "└──► " if i == len(self.ordered_experiments) - 1 else "├──► "
                    )
                    graph.append(f"│   {prefix}{exp.name}")
                    if i < len(self.ordered_experiments) - 1:
                        graph.append("│   │")
                return graph

            lines.extend(build_graph_lines())

        # Footer
        lines.append("└" + "─" * 60)

        return "\n".join(lines)
