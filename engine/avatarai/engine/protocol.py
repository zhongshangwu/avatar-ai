from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class EngineProtocol(ABC):

    @abstractmethod
    async def serve(self) -> None:
        pass

    @abstractmethod
    async def stop(self) -> None:
        pass

    @abstractmethod
    async def add_avatar_async(self, avatar_id: str, **kwargs) -> bool:
        pass

    @abstractmethod
    async def remove_avatar_async(self, avatar_id: str) -> bool:
        pass

    @abstractmethod
    async def get_avatar_async(self, avatar_id: str) -> Optional[Any]:
        pass

    @abstractmethod
    async def get_all_avatars_async(self) -> List[str]:
        pass
