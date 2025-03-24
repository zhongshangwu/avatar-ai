from dataclasses import dataclass, field
from typing import List, Optional
import os
import tomli

from avatarai.config import AvatarConfig, LLMConfig, ToolConfig, NostrConfig, AvatarAIConfig
from avatarai.logger import init_logger

logger = init_logger(__name__)


@dataclass
class EngineArgs:
    """Arguments for AvatarAI engine."""
    avatar_path: str = field(default=None,
                                   metadata={"description": "Avatar配置文件路径"})

    def __post_init__(self):
        """初始化后的处理"""
        if not self.avatar_path:
            raise ValueError("至少需要指定一个Avatar配置文件路径")

        if not os.path.exists(self.avatar_path):
            raise ValueError(f"Avatar配置文件路径不存在: {self.avatar_path}")

    def create_avatar_ai_config(self) -> AvatarAIConfig:
        """从Avatar路径创建AvatarAI配置"""
        avatar_config = None
        if self.avatar_path.endswith('.toml'):
            avatar_config = self._load_avatar_config(self.avatar_path)

        if not avatar_config:
            raise ValueError("未能从指定路径加载任何有效的Avatar配置")

        return AvatarAIConfig(avatar_config=avatar_config)

    def _load_avatar_config(self, file_path: str) -> Optional[AvatarConfig]:
        """从TOML文件加载Avatar配置"""
        try:
            with open(file_path, 'rb') as f:
                config_data = tomli.load(f)

            llm_config = LLMConfig(
                api_url=config_data.get('llm', {}).get('apiUrl', ''),
                model=config_data.get('llm', {}).get('model', ''),
                provider=config_data.get('llm', {}).get('provider', ''),
                api_key=config_data.get('llm', {}).get('apiKey', '')
            )

            tools_config = [
                ToolConfig(id=tool_id)
                for tool_id in config_data.get('tools', [])
            ]

            nostr_config = NostrConfig(
                private_key=config_data.get('nostr', {}).get('privateKey', ''),
                relays=config_data.get('nostr', {}).get('relays', [])
            )

            return AvatarConfig(
                name=config_data.get('name', ''),
                description=config_data.get('description', ''),
                memoId=config_data.get('memoId', ''),
                version=config_data.get('version', '1.0.0'),
                author=config_data.get('author', ''),
                tags=config_data.get('tags', []),
                llm_config=llm_config,
                tools_config=tools_config,
                nostr_config=nostr_config
            )
        except Exception as e:
            logger.error(f"加载Avatar配置文件失败 {file_path}: {str(e)}")
            return None

    @staticmethod
    def add_cli_args(parser):
        """添加命令行参数"""
        parser.add_argument('--avatar-path', type=str, default=None,
                           help='Avatar配置文件路径，xxxx.toml')
        return parser


    @classmethod
    def from_cli_args(cls, args):
        """从命令行参数创建EngineArgs实例"""
        return cls(
            avatar_path=args.avatar_path
        )
