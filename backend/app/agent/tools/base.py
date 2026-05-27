from abc import ABC, abstractmethod
from typing import Any


class BaseTool(ABC):
    """工具基类"""

    @abstractmethod
    def name(self) -> str:
        """工具名称"""

    @abstractmethod
    def description(self) -> str:
        """工具描述，用于意图识别"""

    @abstractmethod
    async def execute(self, user_input: str, **kwargs) -> dict[str, Any]:
        """执行工具，返回结果字典"""
