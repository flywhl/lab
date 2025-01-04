from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from typing import Optional, Sequence

from lab.core.messaging.bus import MessageBus
from lab.runtime.messages import (
    ExperimentRunComplete,
    ExperimentRunFailed,
    ExperimentRunStarted,
)


class UserInterface:
    """Handles all user interaction and feedback"""

    def __init__(self, message_bus: MessageBus):
        self.verbose = False  # @todo: parameterise via injected config
        self.console = Console()
        self.error_console = Console(stderr=True)
        self._message_bus = message_bus

        self._message_bus.subscribe(
            ExperimentRunStarted, self.render_experiment_started
        )
        self._message_bus.subscribe(
            ExperimentRunComplete, self.render_experiment_complete
        )
        self._message_bus.subscribe(ExperimentRunFailed, self.render_experiment_failed)

    def create_progress(self) -> Progress:
        """Create a progress display for long-running operations"""
        return Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            console=self.console,
        )

    def print(self, msg: str):
        self.console.print(msg)

    def display_start(self, path: str) -> None:
        """Display initial startup message"""
        self.console.print(f"[bold]Running experiments from[/] {path}")

    def display_error(self, message: str, details: Optional[str] = None) -> None:
        """Display error message to user"""
        self.error_console.print(f"[red bold]Error:[/] {message}")
        if details and self.verbose:
            self.error_console.print(f"[dim]{details}[/]")

    def display_success(self) -> None:
        """Display success message"""
        self.console.print("[green]✓[/] All experiments completed successfully")

    def render_experiment_started(self, message: ExperimentRunStarted) -> None:
        """Display when an experiment starts"""
        self.console.print(
            f"[bold blue]►[/] Started experiment: {message.run.experiment.name}"
        )

    def render_experiment_complete(self, message: ExperimentRunComplete) -> None:
        """Display when an experiment completes"""
        self.console.print(
            f"[bold green]✓[/] Completed experiment: {message.run.experiment.name}"
        )

    def render_experiment_failed(self, message: ExperimentRunFailed) -> None:
        """Display when an experiment fails"""
        self.console.print(
            f"[bold red]✗[/] Failed experiment: {message.run.experiment.name}"
        )
        self.console.print(f"  Error: {message.reason}", style="red")

    def display_experiment_summary(self, results: Sequence[dict]) -> None:
        """Display summary table of experiment results"""
        table = Table(title="Experiment Results")
        table.add_column("Name")
        table.add_column("Status")
        table.add_column("Duration")

        for result in results:
            table.add_row(
                result["name"],
                f"[green]✓[/]" if result["status"] == "success" else "[red]✗[/]",
                f"{result['duration']:.2f}s",
            )

        self.console.print(table)
