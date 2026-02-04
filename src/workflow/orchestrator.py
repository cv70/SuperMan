"""
SuperMan AI 多智能体公司编排器

使用LangGraph编排所有10个AI智能体之间的交互。
"""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from langgraph.graph import StateGraph, END

from .state_graph import CompanyState, AgentState, AgentRole
from ..agents import (
    CEO,
    CTO,
    CPO,
    CMO,
    CFO,
    HR,
    RD,
    CustomerSupport,
    DataAnalyst,
    Operations,
)
from ..agents.router import MessageRouter, create_router


class CompanyOrchestrator:
    """SuperMan AI公司主编排器。"""

    def __init__(self):
        """初始化公司编排器。"""
        self.agents = {
            AgentRole.CEO: CEO(),
            AgentRole.CTO: CTO(),
            AgentRole.CPO: CPO(),
            AgentRole.CMO: CMO(),
            AgentRole.CFO: CFO(),
            AgentRole.HR: HR(),
            AgentRole.RD: RD(),
            AgentRole.DATA_ANALYST: DataAnalyst(),
            AgentRole.CUSTOMER_SUPPORT: CustomerSupport(),
            AgentRole.OPERATIONS: Operations(),
        }

        self.state: CompanyState = self._create_initial_state()
        self.workflow = self._build_workflow()
        self.compiled_workflow = self.workflow.compile()

    def _create_initial_state(self) -> CompanyState:
        """创建初始公司状态。"""
        return CompanyState(
            agents={role: agent.state for role, agent in self.agents.items()},
            tasks={},
            messages=[],
            current_time=datetime.now(),
            strategic_goals={},
            kpis={
                "revenue_growth": 0.0,  # 收入增长
                "user_growth": 0,  # 用户增长
                "market_share": 0.0,  # 市场份额
                "operational_efficiency": 0.0,  # 运营效率
            },
            market_data={},
            user_feedback=[],
            system_health={},
            budget_allocation={},
            financial_metrics={},
            campaign_metrics={},
            product_backlog=[],
            technical_debt=[],
            campaign_data={},
            brand_data={},
            industry_reports={},
            historical_cashflow={},
            competitor_data={},
            customer_data={},
            product_data={},
            business_metrics={},
            historical_financials={},
        )

    def _build_workflow(self) -> StateGraph:
        """构建LangGraph工作流。"""
        workflow = StateGraph(CompanyState)

        # 添加智能体节点
        for role, agent in self.agents.items():
            workflow.add_node(role.value, self._create_agent_node(role))

        # 添加边 - 基本协作流程
        workflow.add_edge(AgentRole.CEO.value, AgentRole.CTO.value)
        workflow.add_edge(AgentRole.CEO.value, AgentRole.CPO.value)
        workflow.add_edge(AgentRole.CEO.value, AgentRole.CMO.value)
        workflow.add_edge(AgentRole.CEO.value, AgentRole.CFO.value)

        # C级到支持智能体
        workflow.add_edge(AgentRole.CPO.value, AgentRole.CUSTOMER_SUPPORT.value)
        workflow.add_edge(AgentRole.CTO.value, AgentRole.RD.value)
        workflow.add_edge(AgentRole.OPERATIONS.value, END)

        # 入口点
        workflow.set_entry_point(AgentRole.OPERATIONS.value)

        return workflow

    def _create_agent_node(self, role: AgentRole):
        """为LangGraph创建智能体节点。"""

        async def agent_node(state: CompanyState) -> CompanyState:
            agent = self.agents.get(role)
            if not agent:
                return state

            # 处理挂起消息
            messages = state.get("messages", [])
            for message in messages:
                if message.recipient == role:
                    response = await agent.process_message(message, state)
                    if response:
                        state["messages"].append(response)

            return state

        return agent_node

    async def run_simulation(self, steps: int = 5) -> CompanyState:
        """运行公司操作模拟。"""
        state = self._create_initial_state()

        for step in range(steps):
            # 模拟一些活动
            if step == 0:
                # CEO开始战略规划
                from ..agents.base import Message, MessageType, Priority, create_task_id

                cpo_strategic = Message(
                    sender=AgentRole.CEO,
                    recipient=AgentRole.CPO,
                    message_type=MessageType.TASK_ASSIGNMENT,
                    content={
                        "task": {
                            "task_id": create_task_id(),
                            "title": "产品战略规划",
                            "description": "为下一个季度创建产品战略",
                            "assigned_to": AgentRole.CPO.value,
                            "assigned_by": AgentRole.CEO.value,
                            "priority": "high",
                        }
                    },
                    priority=Priority.HIGH,
                )
                state["messages"].append(cpo_strategic)

            # 处理每个智能体的消息
            for role, agent in self.agents.items():
                pending = [m for m in state["messages"] if m.recipient == role]
                for msg in pending:
                    response = await agent.process_message(msg, state)
                    if response:
                        state["messages"].append(response)
                    state["current_time"] = datetime.now()

        return state

    async def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """通过公司工作流执行任务。"""
        from ..agents.base import Task, Priority, create_task_id

        task = Task(
            task_id=task_data.get("task_id", create_task_id()),
            title=task_data.get("title", "未知任务"),
            description=task_data.get("description", ""),
            assigned_to=task_data.get("assigned_to", AgentRole.RD),
            assigned_by=task_data.get("assigned_by", AgentRole.CTO),
            priority=Priority(task_data.get("priority", "medium")),
        )

        # 添加到状态
        self.state["tasks"][task.task_id] = task

        # 路由到适当的智能体
        agent = self.agents.get(task.assigned_to)
        if agent:
            result = await agent.execute_task(task, self.state)
            return {
                "status": "success",
                "result": result,
                "task_id": task.task_id,
            }

        return {
            "status": "failed",
            "error": "未找到处理任务的智能体",
            "task_id": task.task_id,
        }

    async def get_status(self) -> Dict[str, Any]:
        """获取当前公司状态。"""
        return {
            "timestamp": datetime.now().isoformat(),
            "agents_active": len(
                [a for a in self.agents.values() if a.state.workload > 0]
            ),
            "pending_tasks": len(
                [t for t in self.state["tasks"].values() if t.status == "pending"]
            ),
            "in_progress_tasks": len(
                [t for t in self.state["tasks"].values() if t.status == "in_progress"]
            ),
            "completed_tasks": len(
                [t for t in self.state["tasks"].values() if t.status == "completed"]
            ),
        }

    async def generate_report(
        self, agent_role: Optional[AgentRole] = None
    ) -> Dict[str, Any]:
        """从智能体或所有智能体生成报告。"""
        if agent_role:
            agent = self.agents.get(agent_role)
            if agent:
                return await agent.generate_report(self.state)
            return {"error": f"未找到智能体 {agent_role}"}

        # 从所有智能体生成报告
        reports = {}
        for role, agent in self.agents.items():
            try:
                report = await agent.generate_report(self.state)
                reports[role.value] = report
            except Exception as e:
                reports[role.value] = {"error": str(e)}

        return {
            "timestamp": datetime.now().isoformat(),
            "reports": reports,
            "summary": {
                role: "OK" if "data" in report else "ERROR"
                for role, report in reports.items()
            },
        }


# 工厂函数
def create_orchestrator() -> CompanyOrchestrator:
    """创建新的公司编排器实例。"""
    return CompanyOrchestrator()


router = create_router()
