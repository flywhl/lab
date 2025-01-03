from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from typing import Optional, Sequence

from lab.core.model import Event
from lab.runtime.model.run import ExperimentRunEvent


class UserInterface:
    """Handles all user interaction and feedback"""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.console = Console()
        self.error_console = Console(stderr=True)

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

    def render_experiment_started(self, event: Event) -> None:
        """Display when an experiment starts"""
        if not isinstance(event, ExperimentRunEvent):
            # @todo: raise exception?
            return
        self.console.print(
            f"[bold blue]►[/] Started experiment: {event.run.experiment.name}"
        )

    def render_experiment_completed(self, event: Event) -> None:
        """Display when an experiment completes"""
        if not isinstance(event, ExperimentRunEvent):
            # @todo: raise exception?
            return
        self.console.print(
            f"[bold green]✓[/] Completed experiment: {event.run.experiment.name}"
        )

    def render_experiment_failed(self, event: Event) -> None:
        """Display when an experiment fails"""
        if not isinstance(event, ExperimentRunEvent):
            # @todo: raise exception?
            return
        self.console.print(
            f"[bold red]✗[/] Failed experiment: {event.run.experiment.name}"
        )
        if event.data and "error" in event.data:
            self.console.print(f"  Error: {event.data['error']}", style="red")

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
