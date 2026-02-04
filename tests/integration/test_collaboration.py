"""测试集成协作流程"""

import pytest
from datetime import datetime

from src.agents.base import (
    AgentRole,
    MessageType,
    Priority,
    Message,
    Task,
    CompanyState,
    CommunicationProtocol,
)


class TestAgentCollaboration:
    """测试智能体协作流程"""

    def test_ceo_to_cto_task_delegation(self):
        """测试 CEO 到 CTO 的任务委派"""
        CEO = AgentRole.CEO
        CTO = AgentRole.CTO

        # 创建任务分配消息
        task = Task(
            task_id="task_123",
            title="System Architecture Review",
            description="Review current system architecture",
            assigned_to=CTO,
            assigned_by=CEO,
            priority=Priority.HIGH,
        )

        msg = CommunicationProtocol.create_task_assignment(
            assigner=CEO, assignee=CTO, task=task
        )

        assert msg.message_type == MessageType.TASK_ASSIGNMENT
        assert msg.sender == CEO
        assert msg.recipient == CTO

    def test_cto_to_rd_task_flow(self):
        """测试 CTO 到 R&D 的任务流"""
        CTO = AgentRole.CTO
        RD = AgentRole.RD

        # CTO 创建任务分配消息
        task = Task(
            task_id="rd_task_1",
            title="Implement Feature X",
            description="Implement new feature",
            assigned_to=RD,
            assigned_by=CTO,
            priority=Priority.MEDIUM,
        )

        msg = CommunicationProtocol.create_task_assignment(
            assigner=CTO, assignee=RD, task=task
        )

        assert msg.recipient == RD
        assert "task" in msg.content

    def test_customer_support_feedback_flow(self):
        """测试客户支持反馈流程"""
        CS = AgentRole.CUSTOMER_SUPPORT
        CPO = AgentRole.CPO

        # 客户支持创建状态报告消息
        report_msg = CommunicationProtocol.create_status_report(
            agent=CS,
            report_data={
                "feedback_count": 10,
                "common_issues": ["bug_1", "bug_2"],
                "satisfaction_score": 4.5,
            },
        )

        assert report_msg.recipient == AgentRole.CEO  # 默认发送给 CEO

    def test_data_analyst_report_flow(self):
        """测试数据分析师报告流程"""
        CEO = AgentRole.CEO
        DATA_ANALYST = AgentRole.DATA_ANALYST

        # 数据分析师创建状态报告消息
        report_msg = CommunicationProtocol.create_status_report(
            agent=DATA_ANALYST,
            report_data={
                "kpi_revenue": 1000000,
                "kpi_user_growth": 5000,
                "kpi_maintenance": 0.95,
            },
        )

        assert report_msg.message_type == MessageType.STATUS_REPORT

    def test_alert_flow_to_operations(self):
        """测试警报流向运营专员"""
        OPERATIONS = AgentRole.OPERATIONS
        RD = AgentRole.RD

        # 系统错误触发警报
        alert_msg = CommunicationProtocol.create_alert(
            sender=RD,
            alert_type="system_failure",
            message="Critical system failure detected",
            severity=Priority.CRITICAL,
        )

        assert alert_msg.message_type == MessageType.ALERT
        assert alert_msg.priority == Priority.CRITICAL

    def test_approval_request_flow(self):
        """测试审批请求流程"""
        CTO = AgentRole.CTO
        CFO = AgentRole.CFO

        # CTO 发起预算审批请求
        approval_msg = Message(
            sender=CTO,
            recipient=CFO,
            message_type=MessageType.APPROVAL_REQUEST,
            content={
                "request_type": "budget",
                "amount": 50000,
                "description": "Server upgrade budget",
            },
            priority=Priority.HIGH,
        )

        assert approval_msg.message_type == MessageType.APPROVAL_REQUEST
        assert approval_msg.content["request_type"] == "budget"


class TestCompanyStateFlow:
    """测试公司状态流转"""

    def test_initial_state_structure(self):
        """测试初始状态结构"""
        state: CompanyState = {
            "agents": {},
            "tasks": {},
            "messages": [],
            "current_time": datetime.now(),
            "strategic_goals": {},
            "kpis": {},
            "market_data": {},
            "user_feedback": [],
            "system_health": {},
            "budget_allocation": {},
            "financial_metrics": {},
            "campaign_metrics": {},
            "product_backlog": [],
            "technical_debt": [],
            "campaign_data": {},
            "brand_data": {},
            "industry_reports": {},
            "historical_cashflow": {},
            "competitor_data": {},
            "customer_data": {},
            "product_data": {},
            "business_metrics": {},
            "historical_financials": {},
        }

        assert "agents" in state
        assert "tasks" in state
        assert "messages" in state

    def test_task_progression(self):
        """测试任务进度流转"""
        # 创建初始任务
        task = Task(
            task_id="task_1",
            title="Implement Feature",
            description="Implement new feature",
            assigned_to=AgentRole.RD,
            assigned_by=AgentRole.CTO,
            priority=Priority.MEDIUM,
        )

        assert task.status == "pending"

        # 模拟任务进行中
        task.status = "in_progress"
        assert task.status == "in_progress"

        # 模拟任务完成
        task.status = "completed"
        assert task.status == "completed"

    def test_message_chain(self):
        """测试消息链"""
        messages = []

        # CEO 发送战略规划任务给 CPO
        msg1 = Message(
            sender=AgentRole.CEO,
            recipient=AgentRole.CPO,
            message_type=MessageType.TASK_ASSIGNMENT,
            content={"task": {"title": "Product Strategy"}},
            priority=Priority.HIGH,
        )
        messages.append(msg1)

        # CPO 处理后返回状态报告给 CEO
        msg2 = Message(
            sender=AgentRole.CPO,
            recipient=AgentRole.CEO,
            message_type=MessageType.STATUS_REPORT,
            content={"status": "completed"},
            priority=Priority.MEDIUM,
        )
        messages.append(msg2)

        assert len(messages) == 2
        assert messages[0].sender == AgentRole.CEO
        assert messages[1].recipient == AgentRole.CEO
