from datetime import datetime
from typing import Dict, List, Optional, Any
from .base import (
    AgentRole,
    MessageType,
    Priority,
    Message,
    CompanyState,
    CommunicationProtocol,
    BaseAgent,
    RetryStrategy,
    FallbackStrategy,
)


class MessageRouter:
    """根据消息类型和内容将消息路由到相应的智能体。"""

    def __init__(self):
        self._approval_paths: Dict[MessageType, List[AgentRole]] = {
            MessageType.APPROVAL_REQUEST: self._default_approval_path()
        }

    def _default_approval_path(self) -> List[AgentRole]:
        """预算相关审批的默认审批链。"""
        return [AgentRole.CFO, AgentRole.CEO]

    def route(self, message: Message) -> AgentRole:
        """根据消息类型将消息路由到适当的智能体。"""
        message_type = message.message_type

        if message_type == MessageType.TASK_ASSIGNMENT:
            return message.content.get("task", {}).get(
                "assigned_to", message.content.get("assignee", AgentRole.RD)
            )

        elif message_type == MessageType.STATUS_REPORT:
            return AgentRole.CEO

        elif message_type == MessageType.DATA_REQUEST:
            return self._route_data_request(message)

        elif message_type == MessageType.DATA_RESPONSE:
            return message.content.get("requester", message.sender)

        elif message_type == MessageType.APPROVAL_REQUEST:
            return self._get_approver(message)

        elif message_type == MessageType.ALERT:
            return AgentRole.OPERATIONS

        elif message_type == MessageType.COLLABORATION:
            return self._route_collaboration(message)

        return AgentRole.OPERATIONS

    def _route_data_request(self, message: Message) -> AgentRole:
        """将数据请求路由到适当的数据源。"""
        request_type = message.content.get("request_type", "")
        data_category = message.content.get("data_category", "")

        category_mapping = {
            "technology": AgentRole.CTO,
            "financial": AgentRole.CFO,
            "market": AgentRole.CMO,
            "product": AgentRole.CPO,
            "customer": AgentRole.CUSTOMER_SUPPORT,
            "general": AgentRole.DATA_ANALYST,
        }

        if data_category in category_mapping:
            return category_mapping[data_category]

        type_mapping = {
            "metrics": AgentRole.DATA_ANALYST,
            "kpi": AgentRole.DATA_ANALYST,
            "financial_report": AgentRole.CFO,
            "tech_stack": AgentRole.CTO,
            "security": AgentRole.CTO,
            "market_data": AgentRole.CMO,
        }

        if request_type in type_mapping:
            return type_mapping[request_type]

        return AgentRole.DATA_ANALYST

    def _get_approver(self, message: Message) -> AgentRole:
        """根据审批请求类型确定审批人。"""
        request_type = message.content.get("request_type", "")
        budget = message.content.get("budget", 0)

        type_approver_map = {
            "budget": AgentRole.CFO,
            "financial": AgentRole.CFO,
            "technology": AgentRole.CTO,
            "tech": AgentRole.CTO,
            "product": AgentRole.CPO,
            "hr": AgentRole.HR,
            "marketing": AgentRole.CMO,
        }

        for key, approver in type_approver_map.items():
            if key in request_type.lower():
                return approver

        if budget > 100000:
            return AgentRole.CEO

        return AgentRole.CFO

    def _route_collaboration(self, message: Message) -> AgentRole:
        """根据内容路由协作消息。"""
        content = message.content
        content_type = content.get("type", "")
        topic = content.get("topic", "")
        role_hint = content.get("requires_role")

        if role_hint:
            return role_hint

        topic_mapping = {
            "technical": AgentRole.CTO,
            "technology": AgentRole.CTO,
            "development": AgentRole.RD,
            "product": AgentRole.CPO,
            "marketing": AgentRole.CMO,
            "financial": AgentRole.CFO,
            "hr": AgentRole.HR,
            "strategy": AgentRole.CEO,
            "operations": AgentRole.OPERATIONS,
        }

        for key, role in topic_mapping.items():
            if key in topic.lower() or key in content_type.lower():
                return role

        return AgentRole.OPERATIONS

    def needs_approval(self, message: Message) -> bool:
        """检查消息是否需要审批流程。"""
        message_type = message.message_type
        content = message.content

        if message_type != MessageType.APPROVAL_REQUEST:
            return False

        approval_types = {
            "budget",
            "financial",
            "technology",
            "tech",
            "product",
            "architectural",
            "deployment",
            "security",
        }

        request_type = content.get("request_type", "")
        return any(
            approval_type in request_type.lower() for approval_type in approval_types
        )

    def should_alert(self, message: Message) -> bool:
        """检查消息是否应触发警报。"""
        message_type = message.message_type

        if message_type == MessageType.ALERT:
            return True

        if message_type != MessageType.STATUS_REPORT:
            return False

        content = message.content
        status = content.get("status", "")

        alert_keywords = {
            "critical",
            "error",
            "failed",
            "emergency",
            "urgent",
            "down",
            "broken",
            "severe",
            "high",
        }

        status_lower = status.lower() if isinstance(status, str) else ""
        return any(keyword in status_lower for keyword in alert_keywords)

    def get_approval_path(self, message_type: MessageType) -> List[AgentRole]:
        """获取给定消息类型的审批链。"""
        if message_type != MessageType.APPROVAL_REQUEST:
            return []

        return self._default_approval_path()


def create_router() -> MessageRouter:
    """创建配置好的 MessageRouter 的工厂函数。"""
    return MessageRouter()


async def _route_task_assignment(message: Message) -> List[AgentRole]:
    """基于能力匹配和负载均衡的动态路由"""
    task = message.content.get("task", {})
    required_capabilities = task.get("required_capabilities", [])
    workload_limit = task.get("workload_limit", 0.8)

    eligible_agents = []
    for agent in get_all_agents():
        if agent.has_capabilities(required_capabilities):
            eligible_agents.append(agent)

    available_agents = [
        agent for agent in eligible_agents if agent.current_workload < workload_limit
    ]

    scored_agents = []
    for agent in available_agents:
        score = calculate_agent_score(
            agent=agent, task=task, company_state=get_company_state()
        )
        scored_agents.append((agent, score))

    scored_agents.sort(key=lambda x: x[1], reverse=True)

    if len(scored_agents) == 0:
        return [AgentRole.HR]
    elif len(scored_agents) == 1:
        return [scored_agents[0][0].role]
    else:
        return _distribute_workload(scored_agents)


def calculate_agent_score(agent, task, company_state):
    """Calculate agent score based on capabilities and workload"""
    capability_score = len(
        set(agent.capabilities) & set(task.get("required_capabilities", []))
    )
    workload_penalty = agent.current_workload
    return capability_score - (workload_penalty * 0.5)


def _distribute_workload(scored_agents):
    """Distribute workload among multiple agents"""
    return [agent.role for agent, _ in scored_agents[:2]]


def get_all_agents() -> List[BaseAgent]:
    """Get all registered agents - simplified for routing"""
    return []


def get_company_state() -> CompanyState:
    """Get current company state - simplified for routing"""
    return CompanyState(
        agents={},
        tasks={},
        messages=[],
        current_time=datetime.now(),
        strategic_goals={},
        kpis={},
        market_data={},
        user_feedback=[],
        system_health={},
    )
