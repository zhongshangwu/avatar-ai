
from typing import Generator


class LLM:

    def __init__(self, model: str, credentials: dict):
        self.model = model
        self.credentials = credentials

    def invoke(self, messages: str) -> str:
        pass

    def stream(self, prompt: str) -> Generator[str, None, None]:
        pass
