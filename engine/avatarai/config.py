from typing import List, Optional

from pydantic import BaseModel, Field


class LLMConfig(BaseModel):
    api_url: str = Field(description="The api url of the llm")
    model: str = Field(description="The model of the llm")
    provider: str = Field(description="The provider of the llm")
    api_key: str = Field(description="The api key of the llm")


class ToolConfig(BaseModel):
    id: str = Field(description="The id of the tool")


class NostrConfig(BaseModel):
    private_key: str = Field(description="The private key of the nostr")
    relays: List[str] = Field(description="The relays of the nostr")


class AvatarConfig(BaseModel):
    name: str = Field(description="The name of the avatar")
    description: str = Field(description="The description of the avatar")
    memoId: str = Field(description="The memoId of the avatar")
    version: str = Field(description="The version of the avatar")
    author: str = Field(description="The author of the avatar")
    tags: List[str] = Field(description="The tags of the avatar")
    llm_config: LLMConfig = Field(description="The llm config of the avatar")
    tools_config: List[ToolConfig] = Field(description="The tools config of the avatar")
    nostr_config: NostrConfig = Field(description="The nostr config of the avatar")


class AvatarAIConfig(BaseModel):
    avatar_config: Optional[AvatarConfig] = Field(default=None, description="The avatar configuration")
