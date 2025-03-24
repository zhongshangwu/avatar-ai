import asyncio
from nostr_sdk import Keys, Client, EventBuilder, NostrSigner, SecretKey, Nip19, Event, Nip21, PublicKey
from nostr_sdk import Keys, EventBuilder, Kind, Tag, NostrSigner, Timestamp
from nostr_sdk import Filter, Nip19, HandleNotification, RelayMessage
from nostr_sdk import Client, HandleNotification, Event, RelayMessage, Metadata
import datetime
from datetime import timedelta
import time
from nostr_sdk import Relay, SubscribeAutoCloseOptions, SubscribeOptions, EventId
from nostr_sdk import Contact
from mnemonic import Mnemonic
import fire
import functools
import inspect

MY_RELAY = "ws://127.0.0.1:8008"
MY_RELAY = "ws://10.127.20.211:2233"

MY_PKEY = "nsec1h7mwm7rl3fhrn86z5ut2l750stc0adrv9sqvrnxmelp40hpqpkzsz0megu"
AVATAR_PKEY = "nsec14yuk5l2lhs3u757nmdpdh9w0jml2ncfyv90q3ewwmsa7vus8j8wsezjpsw"

# 装饰器：自动将异步函数转换为同步函数
def async_to_sync(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if inspect.iscoroutinefunction(func):
            return asyncio.run(func(*args, **kwargs))
        return func(*args, **kwargs)
    return wrapper

class NostrDemo:
    """Nostr 示例程序，提供各种 Nostr 相关功能的演示。"""

    @async_to_sync
    def event_json(self):
        """显示事件的 JSON 格式。"""
        json = '{"content":"uRuvYr585B80L6rSJiHocw==?iv=oh6LVqdsYYol3JfFnXTbPA==","created_at":1640839235,"id":"2be17aa3031bdcb006f0fce80c146dea9c1c0268b0af2398bb673365c6444d45","kind":4,"pubkey":"f86c44a2de95d9149b51c6a29afeabba264c18e2fa7c49de93424a0c56947785","sig":"a5d9290ef9659083c490b303eb7ee41356d8778ff19f2f91776c8dc4443388a64ffcf336e61af4c25c05ac3ae952d1ced889ed655b67790891222aaa15b99fdd","tags":[["p","13adc511de7e1cfcf1c6b7f6365fb5a03442d7bcacf565ea57fa7770912c023d"]]}'

        event = Event.from_json(json)
        json = event.as_json()
        print(json)
        return json

    @async_to_sync
    async def filter_event(self):
        """演示如何过滤 Nostr 事件。"""
        print("  Filter for specific Event ID:")
        json = '{"content":"uRuvYr585B80L6rSJiHocw==?iv=oh6LVqdsYYol3JfFnXTbPA==","created_at":1640839235,"id":"2be17aa3031bdcb006f0fce80c146dea9c1c0268b0af2398bb673365c6444d45","kind":4,"pubkey":"f86c44a2de95d9149b51c6a29afeabba264c18e2fa7c49de93424a0c56947785","sig":"a5d9290ef9659083c490b303eb7ee41356d8778ff19f2f91776c8dc4443388a64ffcf336e61af4c25c05ac3ae952d1ced889ed655b67790891222aaa15b99fdd","tags":[["p","13adc511de7e1cfcf1c6b7f6365fb5a03442d7bcacf565ea57fa7770912c023d"]]}'

        event = Event.from_json(json)
        f = Filter().id(event.id())
        print(f"     {f.as_json()}")

        print("  Filter for specific Author:")
        keys = Keys.parse("nsec1h7mwm7rl3fhrn86z5ut2l750stc0adrv9sqvrnxmelp40hpqpkzsz0megu")
        f = Filter().author(keys.public_key())
        print(f"     {f.as_json()}")

        print("  Filter with PK and Kinds:")
        f = Filter()\
            .pubkey(keys.public_key())\
            .kind(Kind(1))
        print(f"     {f.as_json()}")

        print("  Filter for specific search string:")
        f = Filter().search("Ask Nostr Anything")
        print(f"     {f.as_json()}")

        print("  Filter for events from specific public key within given timeframe:")
        # Create timestamps
        date = datetime.datetime(2009, 1, 3, 0, 0)
        timestamp = int(time.mktime(date.timetuple()))
        since_ts = Timestamp.from_secs(timestamp)
        until_ts = Timestamp.now()

        # Filter with timeframe
        f = Filter()\
            .pubkey(keys.public_key())\
            .since(since_ts)\
            .until(until_ts)
        print(f"     {f.as_json()}")

        print("  Filter for a Reference:")
        f = Filter().reference("This is my NIP-12 Reference")
        print(f"     {f.as_json()}")

        print("  Filter for a Identifier:")
        identifier = event.tags().identifier()
        if identifier is not None:
            f = Filter().identifier(identifier)
            print(f"     {f.as_json()}")

        f = Filter()\
            .pubkeys([keys.public_key(), keys.public_key()])\
            .ids([event.id(), event.id()])\
            .kinds([Kind(0), Kind(1)])\
            .author(keys.public_key())

        # Add an additional Kind to existing filter
        f = f.kinds([Kind(4)])

        # Print Results
        print("  Before:")
        print(f"     {f.as_json()}")
        print()

        # Remove PKs, Kinds and IDs from filter
        f = f.remove_pubkeys([keys.public_key()])
        print(" After (remove pubkeys):")
        print(f"     {f.as_json()}")

        f = f.remove_kinds([Kind(0), Kind(4)])
        print("  After (remove kinds):")
        print(f"     {f.as_json()}")

        f = f.remove_ids([event.id()])
        print("  After (remove IDs):")
        print(f"     {f.as_json()}")

        event2 = await self.event_builder()

        print("  Logical tests:")
        f = Filter().author(keys.public_key()).kind(Kind(33001))
        print(f"     Event match for filter: {f.match_event(event)}")
        print(f"     Event2 match for filter: {f.match_event(event2)}")

    async def sign_and_print(self, signer: NostrSigner, builder: EventBuilder):
        event = await builder.sign(signer)
        print(event.as_json())
        return event

    @async_to_sync
    async def event_builder(self):
        """演示如何构建 Nostr 事件。"""
        keys = Keys.parse("nsec1h7mwm7rl3fhrn86z5ut2l750stc0adrv9sqvrnxmelp40hpqpkzsz0megu")
        signer = NostrSigner.keys(keys)

        builder1 = EventBuilder.text_note("Hello")
        await self.sign_and_print(signer, builder1)

        tag = Tag.alt("POW text-note")
        custom_timestamp = Timestamp.from_secs(1737976769)
        builder2 = EventBuilder.text_note("Hello with POW").tags([tag]).pow(20).custom_created_at(custom_timestamp)
        await self.sign_and_print(signer, builder2)

        kind = Kind(33001)
        builder3 = EventBuilder(kind, "My custom event")
        return await self.sign_and_print(signer, builder3)

    @async_to_sync
    async def mnemonic_words(self):
        """生成并演示助记词的使用。"""
        # Generate random Seed Phrase (24 words e.g. 256 bits entropy)
        print("Keys from 24 word Seed Phrase:")
        words = Mnemonic("english").generate(strength=256)
        passphrase = ""

        # Use Seed Phrase to generate basic Nostr keys
        keys = Keys.from_mnemonic(words, passphrase)

        print(f" Seed Words (24)  : {words}")
        print(f" Public key bech32: {keys.public_key().to_bech32()}")
        print(f" Secret key bech32: {keys.secret_key().to_bech32()}")

        pk_uri = keys.public_key().to_nostr_uri()
        print(f" Public key (URI):    {pk_uri}")

        # bech32 npub
        pk_parse = Nip21.parse(pk_uri)
        if pk_parse.as_enum().is_pubkey():
            pk_bech32 = PublicKey.parse(pk_uri).to_bech32()
            print(f" Public key (bech32): {pk_bech32}")

    @async_to_sync
    async def stream_events(self, relay_url=MY_RELAY, timeout=30):
        """流式接收 Nostr 事件。

        Args:
            relay_url: 中继服务器 URL
            timeout: 超时时间（秒）
        """
        keys = Keys.parse(AVATAR_PKEY)
        signer = NostrSigner.keys(keys)
        client = Client(signer)

        filter = Filter()
        # 可选：添加更多条件
        # filter.limit(10)  # 只获取最近10条消息

        # 可选：设置自动关闭选项
        auto_close = SubscribeAutoCloseOptions()
        auto_close.timeout(timedelta(seconds=timeout))  # 使用参数化的超时

        # 创建订阅选项
        subscribe_opts = SubscribeOptions().close_on(auto_close)

        # 订阅事件
        await client.add_relay(relay_url)
        await client.connect()

        print("订阅事件")
        print("检查中继连接状态...")
        await asyncio.sleep(2)  # 给连接一些时间
        relays = await client.relays()
        for key, relay in relays.items():
            print(f"中继 {relay.url()}: {relay.is_connected()}")
        subscription = await client.subscribe(filter)

        print("订阅结果: ", subscription)

        class MyNotificationHandler(HandleNotification):
            async def handle_msg(self, relay_url: str, msg: RelayMessage):
                """处理所有类型的中继消息"""
                print(f"\n从 {relay_url} 收到消息: {msg}")

                # 根据消息类型执行不同操作
                if msg.as_enum().is_event_msg():
                    print("收到事件消息")
                elif msg.as_enum().is_notice():
                    print(f"通知: {msg.as_json()}")
                elif msg.as_enum().is_closed():
                    print(f"订阅 {msg.as_json()} 的存储事件已结束")
                # 还可以处理其他消息类型...

            async def handle(self, relay_url: str, subscription_id: str, event: Event):
                """特别处理事件通知"""
                # print(f"从 {relay_url} 的订阅 {subscription_id} 收到事件:")
                # print(f"  事件: {event.id()}")
                # print(f"  作者: {event.author().to_bech32()}")
                # print(f"  类型: {event.kind()}")
                # print(f"  内容: {event.content()}")
                # tags = event.tags().to_vec()
                # print(f"  标签: {[tag.as_vec() for tag in tags]}")
                print(f"Kind: {event.kind()}, std: {event.kind().as_std()}")
                # 根据事件类型执行特定操作
                if event.kind() == 1:  # 文本备注
                    print("收到文本备注")
                elif event.kind() == 4:  # 私信
                    print("收到私信")
                # 处理其他事件类型...

        handler = MyNotificationHandler()
        await client.handle_notifications(handler)

        # 添加主循环防止程序退出
        print("等待接收消息...")
        try:
            # 添加一个主循环使程序保持运行
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("程序被用户中断")

    @async_to_sync
    async def hello(self, relay_url=MY_RELAY):
        """发送一条简单的 Hello 消息。

        Args:
            relay_url: 中继服务器 URL
        """
        keys = Keys.parse("nsec1h7mwm7rl3fhrn86z5ut2l750stc0adrv9sqvrnxmelp40hpqpkzsz0megu")
        print(keys)

        signer = NostrSigner.keys(keys)
        client = Client(signer)

        await client.add_relay(relay_url)
        await client.connect()

        builder = EventBuilder.text_note("Hello, rust-nostr!")
        output = await client.send_event_builder(builder)

        print(f"Event ID: {output.id.to_bech32()}")
        print(f"Sent to: {output.success}")
        print(f"Not send to: {output.failed}")

    @async_to_sync
    async def profile(self, relay_url=MY_RELAY):
        """设置个人资料。

        Args:
            relay_url: 中继服务器 URL
        """
        keys = Keys.parse(AVATAR_PKEY)
        print(keys)

        signer = NostrSigner.keys(keys)
        client = Client(signer)
        await client.add_relay(relay_url)
        await client.connect()

        # 创建元数据对象
        current_metadata = Metadata()
        current_metadata = current_metadata.set_name("avatar-01")  # 设置显示名称
        current_metadata = current_metadata.set_display_name("Avatar")  # 设置显示名称
        current_metadata = current_metadata.set_about("I am a avatar")  # 设置个人简介
        current_metadata = current_metadata.set_website("https://avatarai.roviix.com")  # 设置个人网站

        print("current_metadata: ", current_metadata.as_json())
        # 发送元数据事件
        output = await client.set_metadata(current_metadata)
        print("output: ", output)

        print(f"个人资料已更新，公钥: {keys.public_key().to_bech32()}")

        # 保持程序运行一段时间以确保消息发送
        await asyncio.sleep(5)

    @async_to_sync
    async def get_event(self, event_id, relay_url=MY_RELAY):
        """查询指定 ID 的事件。

        Args:
            event_id: 事件 ID
            relay_url: 中继服务器 URL
        """
        """查询指定 ID 的事件"""
        # 创建客户端并连接到中继
        keys = Keys.parse("nsec14yuk5l2lhs3u757nmdpdh9w0jml2ncfyv90q3ewwmsa7vus8j8wsezjpsw")
        signer = NostrSigner.keys(keys)
        client = Client(signer)
        await client.add_relay(relay_url)
        await client.connect()

        # 等待连接建立
        await asyncio.sleep(2)

        # 检查中继连接状态
        print("检查中继连接状态:")
        relays = await client.relays()
        for key, relay in relays.items():
            print(f"中继 {relay.url()}: {relay.is_connected()}")

        # 解析事件 ID
        try:
            # 如果传入的是十六进制字符串，需要转换为 EventId 对象
            if len(event_id) == 64:  # 标准 Nostr 事件 ID 是 32 字节 (64 个十六进制字符)
                event_id = EventId.parse(event_id)
            else:
                # 如果已经是 bech32 格式 (以 note1 开头)
                event_id = Nip19.from_bech32(event_id).as_enum().event_id
                print("event_id: ", event_id)

            print(f"查询事件 ID: {event_id}")
        except Exception as e:
            print(f"无效的事件 ID 格式: {e}")
            return None

        # 创建过滤器，只查询指定 ID 的事件
        filter = Filter().ids([event_id])

        # 查询事件
        print("查询事件中...")
        events = await client.fetch_events(filter, timeout=timedelta(seconds=10))

        if not events.is_empty():
            events = events.to_vec()
            print(f"找到 {len(events)} 个事件")

            # 返回第一个匹配的事件
            event = events[0]
            print("event: ", event.as_json())
            print(f"事件 ID: {event.id()}")
            print(f"作者: {event.author()}")
            print(f"种类: {event.kind()}")
            print(f"创建时间: {event.created_at()}")
            print(f"内容: {event.content()}")

            gift_wrap = await client.unwrap_gift_wrap(event)
            print("gift_wrap: ", gift_wrap)

            tags = event.tags()
            tag_list = tags.to_vec()
            if tag_list:
                print("标签:")
                for tag in tag_list:
                    print(f"  {tag}")

            return event
        else:
            print("未找到此 ID 的事件")
            return None

    @async_to_sync
    async def send_message(self, message="Hello, Human!", relay_url=MY_RELAY):
        """发送加密消息。

        Args:
            message: 要发送的消息内容
            relay_url: 中继服务器 URL
        """
        keys = Keys.parse(MY_PKEY)
        avatar_keys = Keys.parse(AVATAR_PKEY)

        print("avatar_pubkey: ", avatar_keys.public_key())
        print("avatar_keys: ", avatar_keys.secret_key().to_bech32())
        print("pubkey: ", keys.public_key())
        print("keys: ", keys.public_key().to_bech32())
        print("secret_key: ", keys.secret_key().to_hex())

        signer = NostrSigner.keys(avatar_keys)
        client = Client(signer)
        await client.add_relay(relay_url)
        await client.connect()

        # 创建加密消息并使用参数
        encrypted_message = message

        # 发送加密消息
        output = await client.send_private_msg(keys.public_key(), encrypted_message)
        print("output: ", output)

        event = EventBuilder.private_msg_rumor(
            keys.public_key(),
            encrypted_message
        ).build(avatar_keys.public_key())
        print("event: ", event.as_json())
        output = await client.gift_wrap(avatar_keys.public_key(), event, [])
        print("gift_wrap: ", output)

    @async_to_sync
    async def follow_user(self, relay_url=MY_RELAY, alias="avatar-alias"):
        """关注用户。

        Args:
            relay_url: 中继服务器 URL
            alias:
            用户别名
        """
        keys = Keys.parse(MY_PKEY)
        signer = NostrSigner.keys(keys)
        client = Client(signer)
        await client.add_relay(relay_url)
        await client.connect()

        avatar_keys = Keys.parse(AVATAR_PKEY)

        follow_list = [Contact(
            public_key=avatar_keys.public_key(),
            relay_url=relay_url,
            alias=alias
        )]
        event = EventBuilder.contact_list(follow_list)
        output = await client.send_event_builder(event)
        print("output: ", output)

def main():
    fire.Fire(NostrDemo)

if __name__ == '__main__':
    main()