"""测试消息协议和路由功能"""

import pytest
from datetime import datetime

from src.agents.base import (
    AgentRole,
    MessageType,
    Priority,
    Message,
    Task,
    CompanyState,
)
from src.agents.router import MessageRouter, create_router


class TestMessageRouter:
    """测试 MessageRouter 消息路由"""

    @pytest.fixture
    def router(self):
        """创建路由器实例"""
        return create_router()

    def test_route_task_assignment(self, router):
        """测试任务分配消息路由"""
        msg = Message(
            sender=AgentRole.CTO,
            recipient=AgentRole.RD,
            message_type=MessageType.TASK_ASSIGNMENT,
            content={"task": {"assigned_to": AgentRole.RD}},
        )
        result = router.route(msg)
        assert result == AgentRole.RD

    def test_route_status_report(self, router):
        """测试状态报告消息路由"""
        msg = Message(
            sender=AgentRole.CTO,
            recipient=AgentRole.CEO,
            message_type=MessageType.STATUS_REPORT,
            content={"status": "ok"},
        )
        result = router.route(msg)
        assert result == AgentRole.CEO

    def test_route_data_request(self, router):
        """测试数据请求消息路由"""
        msg = Message(
            sender=AgentRole.CFO,
            recipient=AgentRole.DATA_ANALYST,
            message_type=MessageType.DATA_REQUEST,
            content={"request_type": "financial", "data_category": "financial"},
        )
        result = router.route(msg)
        assert result == AgentRole.CFO

    def test_route_alert(self, router):
        """测试警报消息路由"""
        msg = Message(
            sender=AgentRole.OPERATIONS,
            recipient=AgentRole.OPERATIONS,
            message_type=MessageType.ALERT,
            content={"alert_type": "error"},
        )
        result = router.route(msg)
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
