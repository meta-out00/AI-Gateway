from abc import ABC, abstractmethod


class AIHandler(ABC):

    @abstractmethod
    async def generate(self, request: dict) -> dict:
        pass