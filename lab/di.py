from typing import Iterable
from dishka import Container, Provider, Scope, make_container, provide
from sqlalchemy import Engine, StaticPool, create_engine

from lab.core.messaging.bus import InMemoryMessageBus, MessageBus
from lab.core.ui import UserInterface
from lab.project.service.labfile import LabfileService
from lab.project.service.plan import PlanService
from lab.runtime.persistence.memory import (
    InMemoryExperimentRunRepository,
    InMemoryProjectRunRepository,
)
from lab.runtime.persistence.run import ExperimentRunRepository, ProjectRunRepository
from lab.runtime.runtime import Runtime
from lab.runtime.service.run import RunService


class EngineProvider(Provider):
    @provide(scope=Scope.APP)
    def new_connection(self) -> Iterable[Engine]:
        database_url = "@todo"
        in_memory = database_url is None
        if in_memory:
            database_url = "sqlite:///:memory:"

        connect_args = (
            {"check_same_thread": False} if database_url.startswith("sqlite") else {}
        )

        engine = create_engine(
            database_url,
            poolclass=StaticPool if in_memory else None,
            connect_args=connect_args,
            echo=False,
        )
        yield engine


class DI:
    def __init__(self) -> None:
        self._container = make_container(
            self.core(), self.repositories(), self.services(), EngineProvider()
        )

    @property
    def container(self) -> Container:
        return self._container

    def core(self) -> Provider:
        provider = Provider(scope=Scope.APP)
        provider.provide(UserInterface)
        provider.provide(InMemoryMessageBus, provides=MessageBus)

        return provider

    def repositories(self) -> Provider:
        provider = Provider(scope=Scope.APP)
        provider.provide(
            InMemoryExperimentRunRepository, provides=ExperimentRunRepository
        )
        provider.provide(InMemoryProjectRunRepository, provides=ProjectRunRepository)

        return provider

    def services(self) -> Provider:
        provider = Provider(scope=Scope.APP)
        provider.provide(RunService)
        provider.provide(PlanService)
        provider.provide(LabfileService)
        provider.provide(Runtime)

        return provider
