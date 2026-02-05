"""测试消息协议和路由功能"""

import pytest
import asyncio
from datetime import datetime

from src.agents.base import (
    AgentRole,
    MessageType,
    Priority,
    Message,
    Task,
    CompanyState,
    RetryStrategy,
    FallbackStrategy,
)
from src.agents.router import MessageRouter, create_router, _route_task_assignment


class TestMessageRouter:
    """测试 MessageRouter 消息路由"""

    @pytest.fixture
    def router(self):
        """创建路由器实例"""
        return create_router()

    async def test_route_task_assignment(self, router):
        """测试任务分配消息路由"""
        msg = Message(
            sender=AgentRole.CTO,
            recipient=AgentRole.RD,
            message_type=MessageType.TASK_ASSIGNMENT,
            content={"task": {"assigned_to": AgentRole.RD}},
        )
        result = await router.route(msg)
        assert result == AgentRole.RD

    async def test_route_status_report(self, router):
        """测试状态报告消息路由"""
        msg = Message(
            sender=AgentRole.CTO,
            recipient=AgentRole.CEO,
            message_type=MessageType.STATUS_REPORT,
            content={"status": "ok"},
        )
        result = await router.route(msg)
        assert result == AgentRole.CEO

    async def test_route_data_request(self, router):
        """测试数据请求消息路由"""
        msg = Message(
            sender=AgentRole.CFO,
            recipient=AgentRole.DATA_ANALYST,
            message_type=MessageType.DATA_REQUEST,
            content={"request_type": "financial", "data_category": "financial"},
        )
        result = await router.route(msg)
        assert result == AgentRole.CFO

    async def test_route_alert(self, router):
        """测试警报消息路由"""
        msg = Message(
            sender=AgentRole.OPERATIONS,
            recipient=AgentRole.OPERATIONS,
            message_type=MessageType.ALERT,
            content={"alert_type": "error"},
        )
        result = await router.route(msg)
        assert result == AgentRole.OPERATIONS

    def test_needs_approval(self, router):
        """测试需要审批的消息"""
        msg = Message(
            sender=AgentRole.RD,
            recipient=AgentRole.CTO,
            message_type=MessageType.APPROVAL_REQUEST,
            content={"request_type": "budget"},
        )
        assert router.needs_approval(msg) is True

    def test_should_alert(self, router):
        """测试需要警报的消息"""
        msg = Message(
            sender=AgentRole.OPERATIONS,
            recipient=AgentRole.CEO,
            message_type=MessageType.ALERT,
            content={"alert_type": "error", "severity": "high"},
        )
        assert router.should_alert(msg) is True


def test_retry_strategy_enum():
    """Test RetryStrategy has all required values"""
    assert RetryStrategy.NO_RETRY.value == "no_retry"
    assert RetryStrategy.EXPONENTIAL_BACKOFF.value == "exponential_backoff"


def test_fallback_strategy_enum():
    """Test FallbackStrategy has all required values"""
    assert FallbackStrategy.CACHE.value == "cache"
    assert FallbackStrategy.GRACEFUL_DEGRADATION.value == "graceful"


@pytest.mark.asyncio
async def test_dynamic_route_task_assignment():
    """Test dynamic routing based on task requirements"""
    msg = Message(
        sender=AgentRole.CTO,
        recipient=AgentRole.RD,
        message_type=MessageType.TASK_ASSIGNMENT,
        content={
            "task": {
                "required_capabilities": ["python", "ml"],
                "workload_limit": 0.8,
            }
        },
    )
    result = await _route_task_assignment(msg)
    assert isinstance(result, list)


def test_dynamic_route_engine():
    """Test DynamicRouteEngine routes tasks correctly"""
    from src.agents.router import DynamicRouteEngine
    from src.agents.base import Message, MessageType, Priority, create_task_id

    engine = DynamicRouteEngine()

    msg = Message(
        sender=AgentRole.CEO,
        recipient=AgentRole.CPO,
        message_type=MessageType.TASK_ASSIGNMENT,
        content={
            "task": {
                "task_id": create_task_id(),
                "title": "Test Task",
                "description": "Test",
                "priority": "high",
                "required_capabilities": ["python", "api"],
            }
        },
        priority=Priority.HIGH,
    )

    import asyncio

    result = asyncio.run(engine.route(msg))
    assert result is not None


def test_dynamic_collaboration_routing():
    """Test dynamic collaboration routing"""
    from src.agents.router import DynamicRouteEngine
    from src.agents.base import Message, MessageType

    engine = DynamicRouteEngine()

    msg = Message(
        sender=AgentRole.CPO,
        recipient=AgentRole.CTO,
        message_type=MessageType.COLLABORATION,
        content={
            "topic": "technical",
            "type": "feature_review",
            "requires_role": AgentRole.CTO,
        },
        priority=Priority.MEDIUM,
    )

    result = asyncio.run(engine.route(msg))
    assert result == AgentRole.CTO
