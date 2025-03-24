
from avatarai.models.llm import LLM
from nostr_sdk import Event, KindStandard
from avatarai.nostr.client import Nostr
from avatarai.config import AvatarConfig

from avatarai.logger import init_logger

from .protocol import AgentProtocol

logger = init_logger("avatarai.agent.simple")


class SimpleAgent(AgentProtocol):

    def __init__(self, avatar_config: AvatarConfig):
        model_credentials = {
            "api_key": avatar_config.llm_config.api_key,
            "api_url": avatar_config.llm_config.api_url,
        }
        self.llm_model = LLM(
            model=avatar_config.llm_config.model,
            credentials=model_credentials
        )
        self.nostr_client = Nostr(
            private_key=avatar_config.nostr_config.private_key,
            relays=avatar_config.nostr_config.relays
        )

    async def serve(self):
        """
        启动并部署Agent，设置Nostr连接和事件监听
        """
        await self.nostr_client.connect()
        await self.nostr_client.subscribe(callback=self.nostr)
        logger.info("Agent已成功部署，Nostr连接和事件监听已启动")

    async def nostr(self, event: Event) -> None:
        logger.info(f"SimpleAgent 收到Nostr事件: {event}")

        if not event.verify():
            logger.warning(f"SimpleAgent 收到无效事件: {event}")
            return

        match event.kind().as_std():
            case KindStandard.TEXT_NOTE():
                logger.info(f"SimpleAgent 收到 TextNote 事件内容: {event.content()}")
            case KindStandard.GIFT_WRAP():
                # todo: 处理GiftWrap事件
                gift_wrap = await self.nostr_client.unwrap_gift_wrap(event)
                logger.info(f"SimpleAgent 收到 GiftWrap 事件内容: {gift_wrap}")
            case _:
                logger.warning(f"SimpleAgent 收到未知事件: {event}")

        # if event.author().to_bech32() != self.nostr_client.public_key.to_bech32():
        #     return


        # if not event.verify():
        #         logging.warning(
        #             "Ignoring event with invalid signature or id: %s", event.as_json()
        #         )
        #         return

        #     match event.kind().as_enum():
        #         case KindEnum.WALLET_CONNECT_REQUEST():
        #             await handle_nip47_event(event)
        #         case _:
        #             raise NotImplementedError()

        if event.kind() == 1:
            content = event.content()
            logger.info(f"SimpleAgent 收到 TextNote 事件内容: {content}")
        elif event.kind() == 4:
            content = event.content()
            logger.info(f"SimpleAgent 收到 DM 事件内容: {content}")
    async def randomwalk(self) -> None:
        pass

    async def selfimprove(self) -> None:
        pass
