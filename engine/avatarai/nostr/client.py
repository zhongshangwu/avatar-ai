import asyncio
import inspect
from typing import List, Callable, Optional, Union, Any
from nostr_sdk import (
    Keys,
    NostrSigner,
    Client,
    Filter,
    HandleNotification,
    RelayMessage,
    Event,
    PublicKey,
    EventBuilder
)
from avatarai.logger import init_logger

logger = init_logger("avatarai.nostr.client")

class Nostr:
    def __init__(self, private_key: str, relays: List[str],
                 auto_reconnect: bool = True,
                 reconnect_interval: int = 5) -> None:
        """
        初始化Nostr客户端

        Args:
            private_key: 私钥字符串
            relays: 中继服务器URL列表
            auto_reconnect: 是否自动重连
            reconnect_interval: 重连间隔（秒）
        """
        self.private_key = private_key
        self.keys = Keys.parse(private_key)
        self.public_key = self.keys.public_key()
        self.signer = NostrSigner.keys(self.keys)
        self.client = Client(self.signer)
        self.relays = relays
        self.auto_reconnect = auto_reconnect
        self.reconnect_interval = reconnect_interval
        self.connected = False
        self._reconnect_task = None
        self._current_subscriptions = []

    async def connect(self) -> bool:
        """连接到所有中继服务器"""
        try:
            for relay_url in self.relays:
                await self.client.add_relay(relay_url)
                logger.info(f"添加中继服务器: {relay_url}")

            await self.client.connect()
            logger.info("成功连接到所有中继服务器")
            self.connected = True

            # 如果启用自动重连且重连任务不存在，创建重连监控任务
            if self.auto_reconnect and not self._reconnect_task:
                self._reconnect_task = asyncio.create_task(self._reconnect_monitor())

            return True
        except Exception as e:
            logger.error(f"连接失败: {str(e)}")
            return False

    async def _reconnect_monitor(self):
        """监控连接状态并在断开时自动重连"""
        while self.auto_reconnect:
            if not self.connected:
                logger.info("检测到连接已断开，尝试重新连接...")
                success = await self.connect()
                if success and self._current_subscriptions:
                    # 重新建立之前的订阅
                    logger.info("重新建立之前的订阅...")
                    for subscription_info in self._current_subscriptions:
                        filter_obj, callback = subscription_info
                        await self.subscribe(filter_obj, callback)

            await asyncio.sleep(self.reconnect_interval)

    async def disconnect(self):
        """断开连接并清理资源"""
        self.auto_reconnect = False
        if self._reconnect_task:
            self._reconnect_task.cancel()
            try:
                await self._reconnect_task
            except asyncio.CancelledError:
                pass
            self._reconnect_task = None

        self._current_subscriptions.clear()
        self.connected = False
        # 假设client.disconnect()是nostr_sdk提供的方法
        # 如果没有，则需要根据SDK的API调整
        try:
            await self.client.disconnect()
            logger.info("成功断开连接")
        except Exception as e:
            logger.error(f"断开连接时发生错误: {str(e)}")

    async def subscribe(self, filter_obj: Optional[Filter] = None,
                       callback: Optional[Callable[[Event], Any]] = None):
        """
        订阅事件并开始监听

        Args:
            filter_obj: 过滤器对象，如果为None则创建默认过滤器
            callback: 收到事件时的回调函数

        Returns:
            订阅ID
        """
        if not self.connected:
            logger.warning("尝试订阅但未连接，正在自动连接")
            success = await self.connect()
            if not success:
                raise ConnectionError("无法连接到中继服务器")

        # 使用默认过滤器或创建新的
        filter_to_use = filter_obj if filter_obj else Filter()

        # 保存订阅信息以便重连时恢复
        if callback:
            self._current_subscriptions.append((filter_to_use, callback))

        # 创建统一的消息处理器
        class NostrNotificationHandler(HandleNotification):
            def __init__(self, parent: "Nostr"):
                self.parent = parent

            async def handle_msg(self, relay_url: str, msg: RelayMessage):
                """处理各种中继消息"""
                logger.debug(f"从 {relay_url} 收到消息: {msg}")

                if msg.as_enum().is_closed():
                    logger.info(f"订阅连接已关闭: {msg.as_json()}")
                    self.parent.connected = False

            async def handle(self, relay_url: str, subscription_id: str, event: Event):
                """处理事件"""
                if not callback:
                    return

                try:
                    # 根据回调类型（异步或同步）调用回调
                    if inspect.iscoroutinefunction(callback):
                        await callback(event)
                    else:
                        callback(event)
                except Exception as e:
                    logger.error(f"回调处理事件时出错: {str(e)}")

        # 创建订阅并设置处理器
        try:
            subscription = await self.client.subscribe(filter_to_use)
            handler = NostrNotificationHandler(self)

            # 启动监听任务
            asyncio.create_task(self._listen_with_handler(handler))

            logger.info(f"成功创建订阅，ID: {subscription}")
            return subscription
        except Exception as e:
            logger.error(f"创建订阅时出错: {str(e)}")
            self.connected = False
            raise

    async def _listen_with_handler(self, handler):
        """使用给定的处理器监听事件"""
        try:
            await self.client.handle_notifications(handler)
        except Exception as e:
            logger.error(f"监听过程中发生错误: {str(e)}")
            self.connected = False

    async def send_private_msg(self, pubkey: str, message: str):
        """发送私信"""
        public_key = PublicKey.parse(pubkey)
        output = await self.client.send_private_msg(public_key, message)

        logger.info(f"发送私信成功: {output}")

        event = EventBuilder.private_msg_rumor(
            public_key,
            message
        ).build(self.public_key)
        output = await self.client.gift_wrap(self.public_key, event, [])
        logger.info(f"(selfsend)发送私信成功: {output}")
        return
