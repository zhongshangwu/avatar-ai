from typing import List

from avatarai.engine.protocol import EngineProtocol
from avatarai.engine.engine_args import EngineArgs
from avatarai.config import AvatarAIConfig
from avatarai.agent.simple import SimpleAgent


class AsyncAvatarEngine(EngineProtocol):

    _engine_class = None

    def __init__(self, engine_config: AvatarAIConfig):
        self.engine_config = engine_config
        self.agent = SimpleAgent(engine_config.avatar_config)

    @classmethod
    def from_engine_args(cls, engine_args: EngineArgs) -> "AsyncAvatarEngine":
        engine_config = engine_args.create_avatar_ai_config()

        return cls(engine_config=engine_config)

    async def serve(self) -> None:
        await self.agent.serve()

    async def stop(self) -> None:
        pass

    async def add_avatar_async(self, avatar_id: str, **kwargs) -> bool:
        pass

    async def remove_avatar_async(self, avatar_id: str, **kwargs) -> bool:
        pass

    async def get_avatar_async(self, avatar_id: str, **kwargs) -> any:
        pass

    async def get_all_avatars_async(self, **kwargs) -> List[any]:
        pass


