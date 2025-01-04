import asyncio
import inspect
from collections.abc import Callable, Coroutine
from functools import wraps
from typing import Any, Final, ParamSpec, TypeVar, cast

from click import get_current_context
from dishka import Container
from dishka.integrations.base import is_dishka_injected, wrap_injection
from typer import Context, Typer
from typer.core import TyperCommand, TyperGroup
from typer.models import CommandFunctionType

P = ParamSpec("P")
R = TypeVar("R")


class AsyncTyper(Typer):
    """Async support for Typer commands

    @source: https://github.com/fastapi/typer/issues/950#issuecomment-2338225913
    """

    @staticmethod
    def maybe_run_async(
        decorator: Callable[[CommandFunctionType], CommandFunctionType],
        f: CommandFunctionType,
    ) -> CommandFunctionType:
        if inspect.iscoroutinefunction(f):

            @wraps(f)
            def runner(*args: Any, **kwargs: Any) -> Any:
                return asyncio.run(
                    cast(Callable[..., Coroutine[Any, Any, Any]], f)(*args, **kwargs)
                )

            return decorator(cast(CommandFunctionType, runner))
        return decorator(f)

    # noinspection PyShadowingBuiltins
    def callback(
        self,
        # name: str | None = None,
        *,
        cls: type[TyperGroup] | None = None,
        invoke_without_command: bool = False,
        no_args_is_help: bool = False,
        subcommand_metavar: str | None = None,
        chain: bool = False,
        result_callback: Callable[..., Any] | None = None,
        context_settings: dict[Any, Any] | None = None,
        help: str | None = None,  # noqa: A002
        epilog: str | None = None,
        short_help: str | None = None,
        options_metavar: str = "[OPTIONS]",
        add_help_option: bool = True,
        hidden: bool = False,
        deprecated: bool = False,
        rich_help_panel: str | None = None,
    ) -> Callable[[CommandFunctionType], CommandFunctionType]:
        decorator = super().callback(
            cls=cls,
            # name=name,
            invoke_without_command=invoke_without_command,
            no_args_is_help=no_args_is_help,
            subcommand_metavar=subcommand_metavar,
            chain=chain,
            result_callback=result_callback,
            context_settings=context_settings,
            help=help,
            epilog=epilog,
            short_help=short_help,
            options_metavar=options_metavar,
            add_help_option=add_help_option,
            hidden=hidden,
            deprecated=deprecated,
            rich_help_panel=rich_help_panel,
        )
        return lambda f: self.maybe_run_async(decorator, f)

    # noinspection PyShadowingBuiltins
    def command(
        self,
        name: str | None = None,
        *,
        cls: type[TyperCommand] | None = None,
        context_settings: dict[Any, Any] | None = None,
        help: str | None = None,  # noqa: A002
        epilog: str | None = None,
        short_help: str | None = None,
        options_metavar: str = "[OPTIONS]",
        add_help_option: bool = True,
        no_args_is_help: bool = False,
        hidden: bool = False,
        deprecated: bool = False,
        rich_help_panel: str | None = None,
    ) -> Callable[[CommandFunctionType], CommandFunctionType]:
        decorator = super().command(
            name=name,
            cls=cls,
            context_settings=context_settings,
            help=help,
            epilog=epilog,
            short_help=short_help,
            options_metavar=options_metavar,
            add_help_option=add_help_option,
            no_args_is_help=no_args_is_help,
            hidden=hidden,
            deprecated=deprecated,
            rich_help_panel=rich_help_panel,
        )
        return lambda f: self.maybe_run_async(decorator, f)


T = TypeVar("T")
CONTAINER_NAME: Final = "dishka_container"


def inject(func: Callable[..., T]) -> Callable[..., T]:
    return wrap_injection(
        func=func,
        container_getter=lambda _, __: get_current_context().meta[CONTAINER_NAME],
        remove_depends=True,
        is_async=False,
    )


def _inject_commands(context: Context, app: Typer) -> None:
    for command in app.registered_commands:
        if command.callback is None:
            continue
        if not is_dishka_injected(command.callback):
            command.callback = inject(command.callback)

    for group in app.registered_groups:
        if group.typer_instance is None:
            continue
        _inject_commands(context, group.typer_instance)


def setup_dishka(
    container: Container,
    context: Context,
    app: Typer,
    *,
    finalize_container: bool = True,
    auto_inject: bool = False,
) -> None:
    context.meta[CONTAINER_NAME] = container

    if finalize_container:
        context.call_on_close(container.close)

    if auto_inject:
        _inject_commands(context, app)
