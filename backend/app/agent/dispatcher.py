"""工具调度器 — 根据意图识别结果，并行调用对应的子 Agent 工具"""

import asyncio
from typing import Any

from app.agent.tools.weather_outfit import WeatherOutfitTool
from app.agent.tools.image_process import ImageProcessTool
from app.agent.tools.work_order import WorkOrderTool

TOOL_REGISTRY: dict[str, Any] = {
    "weather_outfit": WeatherOutfitTool(),
    "image_process": ImageProcessTool(),
    "work_order": WorkOrderTool(),
}


async def dispatch_tools(tool_names: list[str], user_input: str, params: dict) -> dict:
    """并行执行多个工具，返回合并后的结果"""
    if not tool_names:
        return {}

    async def run_one(name: str):
        tool = TOOL_REGISTRY.get(name)
        if not tool:
            return name, {"error": f"未知工具: {name}"}
        try:
            result = await asyncio.wait_for(
                tool.execute(user_input, **params),
                timeout=10,
            )
            return name, result
        except asyncio.TimeoutError:
            return name, {"error": f"工具 {name} 执行超时"}
        except Exception as e:
            return name, {"error": str(e)}

    tasks = [run_one(name) for name in tool_names]
    results = await asyncio.gather(*tasks)
    return dict(results)
