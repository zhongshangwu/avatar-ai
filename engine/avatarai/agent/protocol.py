
from abc import ABC, abstractmethod

from nostr_sdk import Event


class AgentProtocol(ABC):

    @abstractmethod
    async def nostr(self, event: Event) -> None:
        """
        和人类进行交互
        """
        pass

    @abstractmethod
    async def randomwalk(self) -> None:
        """
        随机游走， 探索世界
        """
        pass

    @abstractmethod
    async def selfimprove(self) -> None:
        """
        自我提升
        """
        pass
