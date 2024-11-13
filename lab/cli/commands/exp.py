import typer


def attach(app: typer.Typer, *, name: str):
    exp_cmd = typer.Typer()
    #
    # # Create sub-apps for each registered experiment
    # for name, exp in Experiment.get_registered_experiments().items():
    #     exp_app = typer.Typer()
    #     exp_cmd.add_typer(exp_app, name=name)
    #
    #     @exp_app.command("run")
    #     def run_experiment(
    #         exp=exp,  # Capture experiment class in closure
    #         spec: str = typer.Argument(..., help="Specification file name"),
    #         vary: Optional[str] = typer.Option(None, help="Variation parameter"),
    #         k: int = typer.Option(1, "--K", "-K", help="Number of iterations"),
    #     ):
    #         """Run an experiment with the given specification"""
    #         vary_ = Vary.parse_str(vary) if vary else None
    #         spec_class = exp.spec()
    #         if not spec_class or not issubclass(spec_class, Spec):
    #             raise typer.BadParameter(
    #                 f"Experiment {exp} does not have a valid Spec class"
    #             )
    #
    #         settings = Settings()
    #         namespaces = {Callable: func}
    #
    #         specfile = (
    #             settings.spec_root
    #             / "experiment"
    #             / exp.__name__.lower()
    #             / f"{spec}.yaml"
    #         )
    #         experiment_spec = spec_class.parse_with_namespaces(
    #             yaml.safe_load(specfile.read_text()), namespaces
    #         )
    #         experiment = experiment_spec.build()
    #         data = experiment(K=k, vary=vary_)
    #         data.plot()

    app.add_typer(exp_cmd, name=name)
