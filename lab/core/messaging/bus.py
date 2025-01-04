from abc import ABC, abstractmethod
import logging
from typing import Callable, Type

from lab.core.messaging.message import Message, TMessage


class MessageBus(ABC):
    """Interface for message bus implementations"""

    @abstractmethod
    async def publish(self, message: Message) -> None:
        """Publish a message to all registered handlers"""
        pass

    @abstractmethod
    def register_handler(
        self, message_type: Type[TMessage], handler: Callable[[TMessage], None]
    ) -> None:
        """Register a handler for a specific message type"""
        pass

    @abstractmethod
    def subscribe(
        self, message_type: Type[TMessage], subscriber: Callable[[TMessage], None]
    ) -> None:
        """Subscribe to notifications for a specific message type"""
        pass


# In-memory implementation
class InMemoryMessageBus(MessageBus):
    """Simple in-memory implementation of the message bus"""

    def __init__(self):
        self._handlers: dict[Type[Message], list[Callable]] = {}
        self._subscribers: dict[Type[Message], list[Callable]] = {}
        self._logger = logging.getLogger(__name__)

    def register_handler(
        self, message_type: Type[TMessage], handler: Callable[[TMessage], None]
    ) -> None:
        if message_type not in self._handlers:
            self._handlers[message_type] = []
        self._handlers[message_type].append(handler)
        self._logger.debug(
            f"Registered handler {handler.__name__} for {message_type.__name__}"
        )

    def subscribe(
        self, message_type: Type[TMessage], subscriber: Callable[[TMessage], None]
    ) -> None:
        if message_type not in self._subscribers:
            self._subscribers[message_type] = []
        self._subscribers[message_type].append(subscriber)
        self._logger.debug(
            f"Added subscriber {subscriber.__name__} for {message_type.__name__}"
        )

    async def publish(self, message: Message) -> None:
        message_type = type(message)

        # Call handlers
        handlers = self._handlers.get(message_type, [])
        for handler in handlers:
            try:
                await handler(message)
            except Exception as e:
                self._logger.error(f"Error in handler {handler.__name__}: {str(e)}")

        # Notify subscribers
        subscribers = self._subscribers.get(message_type, [])
        for subscriber in subscribers:
            try:
                await subscriber(message)
            except Exception as e:
                self._logger.error(
                    f"Error in subscriber {subscriber.__name__}: {str(e)}"
                )

        self._logger.debug(
            f"Published {message_type.__name__} to "
            f"{len(handlers)} handlers and {len(subscribers)} subscribers"
        )
