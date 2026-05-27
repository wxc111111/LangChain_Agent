"""子Agent1: 天气查询 + 出行穿衣推荐"""

from app.agent.tools.base import BaseTool
from app.agent.mock.weather_data import WEATHER_MOCK


class WeatherTool:
    """天气查询工具"""

    @staticmethod
    def get_weather(city: str) -> dict:
        data = WEATHER_MOCK.get(city)
        if data:
            return {"city": city, "found": True, **data}
        return {
            "city": city,
            "found": False,
            "temp": 22,
            "weather": "晴",
            "humidity": 55,
            "wind": "微风",
        }


class OutfitTool:
    """穿衣推荐工具"""

    @staticmethod
    def recommend(temp: int, weather: str, wind: str) -> str:
        if temp >= 30:
            outfit = "短袖、短裤、遮阳帽，注意防晒防暑"
        elif temp >= 25:
            outfit = "短袖、薄长裤，可备一件薄外套应对早晚温差"
        elif temp >= 18:
            outfit = "长袖T恤或衬衫、薄外套、长裤"
        elif temp >= 10:
            outfit = "毛衣或卫衣、夹克、长裤"
        elif temp >= 0:
            outfit = "厚毛衣、棉服或羽绒服、围巾"
        else:
            outfit = "厚羽绒服、保暖内衣、围巾、手套、帽子"

        parts = [outfit]
        if "雨" in weather:
            parts.append("记得带伞")
        if "雪" in weather:
            parts.append("穿防滑鞋，注意路面结冰")
        if "风" in wind and any(c.isdigit() and int(c) >= 4 for c in wind):
            parts.append("风力较大，建议穿防风外套")
        return "；".join(parts)


class WeatherOutfitTool(BaseTool):
    """子Agent1: 整合天气查询和穿衣推荐"""

    def __init__(self):
        self._weather = WeatherTool()
        self._outfit = OutfitTool()

    @property
    def name(self) -> str:
        return "weather_outfit"

    @property
    def description(self) -> str:
        return "获取指定城市的天气信息，并根据温度、天气状况给出出行穿衣建议"

    async def execute(self, user_input: str, **kwargs) -> dict:
        city = kwargs.get("city", "")
        if not city:
            city = self._extract_city(user_input)

        weather = self._weather.get_weather(city)
        outfit = self._outfit.recommend(
            temp=weather["temp"],
            weather=weather["weather"],
            wind=weather.get("wind", ""),
        )
        return {"weather": weather, "outfit": outfit}

    def _extract_city(self, text: str) -> str:
        """从用户输入中简单提取城市名"""
        for city in WEATHER_MOCK:
            if city in text:
                return city
        return "北京"
