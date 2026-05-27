"""子Agent2: 图生文 + 文生图"""

import asyncio

import dashscope
from dashscope import MultiModalConversation

from app.agent.tools.base import BaseTool
from app.config import settings
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

dashscope.base_http_api_url = 'https://dashscope.aliyuncs.com/api/v1'


class ImageToTextTool:
    """图生文工具 — 调用千问 qwen3.5-omni-plus 多模态模型"""

    @staticmethod
    async def describe(image_url: str) -> dict:
        llm = ChatOpenAI(
            model=settings.QWEN_OMNI_MODEL,
            api_key=settings.QWEN_API_KEY,
            base_url=settings.QWEN_BASE_URL,
            temperature=0.7,
        )
        response = await llm.ainvoke([
            HumanMessage(content=[
                {"type": "image_url", "image_url": {"url": image_url}},
                {"type": "text", "text": "请详细描述这张图片的内容，包括场景、物体、颜色、氛围等。"},
            ])
        ])
        return {"image_url": image_url, "description": response.content}


class TextToImageTool:
    """文生图工具 — 调用 DashScope qwen-image-2.0 真实生成图片"""

    @staticmethod
    async def generate(prompt: str, style: str = "写实") -> dict:
        full_prompt = f"{style}风格：{prompt}"
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: MultiModalConversation.call(
                api_key=settings.QWEN_API_KEY,
                model="qwen-image-2.0",
                messages=[{
                    "role": "user",
                    "content": [{"text": full_prompt}],
                }],
                result_format="message",
                n=1,
                watermark=True,
                negative_prompt="",
            ),
        )

        output = response.get("output", {})
        choices = output.get("choices", [])
        image_url = ""
        if choices:
            message = choices[0].get("message", {})
            content_list = message.get("content", [])
            for item in content_list:
                if "image" in item:
                    image_url = item["image"]

        return {
            "prompt": prompt,
            "style": style,
            "image_url": image_url,
            "model": "qwen-image-2.0",
        }


class ImageProcessTool(BaseTool):
    """子Agent2: 整合图生文和文生图"""

    def __init__(self):
        self._img2text = ImageToTextTool()
        self._text2img = TextToImageTool()

    @property
    def name(self) -> str:
        return "image_process"

    @property
    def description(self) -> str:
        return "根据图片生成文字描述（图生文），或根据文字描述生成图片（文生图）"

    async def execute(self, user_input: str, **kwargs) -> dict:
        image_url = kwargs.get("image_url", "")
        prompt = kwargs.get("prompt", "")
        style = kwargs.get("style", "写实")

        result = {}
        if image_url:
            result["image_to_text"] = await self._img2text.describe(image_url)
        if prompt:
            result["text_to_image"] = await self._text2img.generate(prompt, style)

        if not result:
            if any(w in user_input for w in ["图片", "照片", "这张图", "图像", "图里", "图中"]):
                result["image_to_text"] = await self._img2text.describe(image_url or user_input)
            else:
                result["text_to_image"] = await self._text2img.generate(
                    prompt=user_input, style=style
                )
        return result
