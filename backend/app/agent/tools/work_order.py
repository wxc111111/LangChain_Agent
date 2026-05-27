"""子Agent3: 个人工单查询"""

from app.agent.tools.base import BaseTool
from app.agent.mock.work_order_data import WORK_ORDER_MOCK


class WorkOrderQueryTool:
    """工单查询工具"""

    @staticmethod
    def query(user: str = "", status: str = "", priority: str = "") -> list[dict]:
        result = WORK_ORDER_MOCK
        if user:
            result = [w for w in result if w["assignee"] == user]
        if status:
            result = [w for w in result if w["status"] == status]
        if priority:
            result = [w for w in result if w["priority"] == priority]
        return result

    @staticmethod
    def stats(orders: list[dict]) -> dict:
        """统计工单各状态的数目"""
        status_count = {}
        for o in orders:
            s = o["status"]
            status_count[s] = status_count.get(s, 0) + 1
        return {
            "total": len(orders),
            "by_status": status_count,
        }


class WorkOrderTool(BaseTool):
    """子Agent3: 工单查询"""

    def __init__(self):
        self._query = WorkOrderQueryTool()

    @property
    def name(self) -> str:
        return "work_order"

    @property
    def description(self) -> str:
        return "查询个人工单、任务、待办事项列表，支持按状态和优先级筛选"

    async def execute(self, user_input: str, **kwargs) -> dict:
        user = kwargs.get("user", "")
        status = kwargs.get("status", "")

        # 从 user_input 推断筛选条件
        if not status:
            if any(w in user_input for w in ["处理中", "进行中", "正在处理"]):
                status = "处理中"
            elif any(w in user_input for w in ["待处理", "未处理", "未开始"]):
                status = "待处理"
            elif any(w in user_input for w in ["已完成", "完成的", "完成"]):
                status = "已完成"

        orders = self._query.query(user=user, status=status)
        stats = self._query.stats(orders)

        return {"orders": orders, "stats": stats}
