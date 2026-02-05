"""测试 BaseAgent 核心功能"""

import pytest
from datetime import datetime, timedelta

from src.agents.base import (
    AgentRole,
    MessageType,
    Priority,
    Message,
    Task,
    AgentState,
    CompanyState,
    BaseAgent,
    CommunicationProtocol,
    RetryStrategy,
    MessageMetadata,
    create_task_id,
    format_timestamp,
    calculate_kpi_completion,
    validate_message,
)


class MockAgent(BaseAgent):
    """用于测试的模拟智能体"""

    def __init__(self, role: AgentRole):
        super().__init__(role, ["test_capability"])

    async def process_message(self, message: Message, company_state: CompanyState):
        return None

    async def execute_task(self, task: Task, company_state: CompanyState):
        return {"status": "completed"}

    async def generate_report(self, company_state: CompanyState):
        return {"data": "test_report"}


class TestAgentRole:
    """测试 AgentRole 枚举"""

    def test_all_roles_exist(self):
        """测试所有角色都存在"""
        assert AgentRole.CEO.value == "ceo"
        assert AgentRole.CTO.value == "cto"
        assert AgentRole.CPO.value == "cpo"
        assert AgentRole.CMO.value == "cmo"
        assert AgentRole.CFO.value == "cfo"
        assert AgentRole.HR.value == "hr"
        assert AgentRole.RD.value == "rd"
        assert AgentRole.DATA_ANALYST.value == "data_analyst"
        assert AgentRole.CUSTOMER_SUPPORT.value == "customer_support"
        assert AgentRole.OPERATIONS.value == "operations"


class TestMessageType:
    """测试 MessageType 枚举"""

    def test_all_message_types_exist(self):
        """测试所有消息类型都存在"""
        assert MessageType.TASK_ASSIGNMENT.value == "task_assignment"
        assert MessageType.STATUS_REPORT.value == "status_report"
        assert MessageType.DATA_REQUEST.value == "data_request"
        assert MessageType.DATA_RESPONSE.value == "data_response"
        assert MessageType.APPROVAL_REQUEST.value == "approval_request"
        assert MessageType.APPROVAL_RESPONSE.value == "approval_response"
        assert MessageType.ALERT.value == "alert"
        assert MessageType.COLLABORATION.value == "collaboration"


class TestPriority:
    """测试 Priority 枚举"""

    def test_all_priorities_exist(self):
        """测试所有优先级都存在"""
        assert Priority.LOW.value == "low"
        assert Priority.MEDIUM.value == "medium"
        assert Priority.HIGH.value == "high"
        assert Priority.CRITICAL.value == "critical"


class TestMessage:
    """测试 Message 数据类"""

    def test_default_priority(self):
        """测试默认优先级"""
        msg = Message(
            sender=AgentRole.CEO,
            recipient=AgentRole.CTO,
            message_type=MessageType.STATUS_REPORT,
            content={"test": "data"},
        )
        assert msg.priority == Priority.MEDIUM

    def test_custom_priority(self):
        """测试自定义优先级"""
        msg = Message(
            sender=AgentRole.CEO,
            recipient=AgentRole.CTO,
            message_type=MessageType.ALERT,
            content={"alert": "test"},
            priority=Priority.CRITICAL,
        )
        assert msg.priority == Priority.CRITICAL


class TestTask:
    """测试 Task 数据类"""

    def test_default_status(self):
        """测试默认任务状态"""
        task = Task(
            task_id="test_task_123",
            title="Test Task",
            description="Test description",
            assigned_to=AgentRole.RD,
            assigned_by=AgentRole.CTO,
            priority=Priority.MEDIUM,
        )
        assert task.status == "pending"

    def test_task_has_dependencies(self):
        """测试任务依赖"""
        task = Task(
            task_id="test_task_123",
            title="Test Task",
            description="Test description",
            assigned_to=AgentRole.RD,
            assigned_by=AgentRole.CTO,
            priority=Priority.MEDIUM,
            dependencies=["task_1", "task_2"],
        )
        assert len(task.dependencies) == 2

    def test_task_has_deadline(self):
        """测试任务截止日期"""
        deadline = datetime.now() + timedelta(days=7)
        task = Task(
            task_id="test_task_123",
            title="Test Task",
            description="Test description",
            assigned_to=AgentRole.RD,
            assigned_by=AgentRole.CTO,
            priority=Priority.MEDIUM,
            deadline=deadline,
        )
        assert task.deadline == deadline


class TestAgentState:
    """测试 AgentState 数据类"""

    def test_default_workload(self):
        """测试默认工作负载"""
        state = AgentState(role=AgentRole.RD)
        assert state.workload == 0.0

    def test_capabilities_default(self):
        """测试默认能力列表"""
        state = AgentState(role=AgentRole.CTO, capabilities=["test"])
        assert len(state.capabilities) == 1


class TestCommunicationProtocol:
    """测试 CommunicationProtocol 工具类"""

    def test_create_message(self):
        """测试创建消息"""
        msg = CommunicationProtocol.create_message(
            sender=AgentRole.CEO,
            recipient=AgentRole.CTO,
            message_type=MessageType.STATUS_REPORT,
            content={"report": "data"},
        )
        assert msg.sender == AgentRole.CEO
        assert msg.recipient == AgentRole.CTO
        assert msg.message_type == MessageType.STATUS_REPORT

    def test_create_task_assignment(self):
        """测试创建任务分配消息"""
        task = Task(
            task_id="test_task",
            title="Test Task",
            description="Test",
            assigned_to=AgentRole.RD,
            assigned_by=AgentRole.CTO,
            priority=Priority.HIGH,
        )
        msg = CommunicationProtocol.create_task_assignment(
            assigner=AgentRole.CTO, assignee=AgentRole.RD, task=task
        )
        assert msg.message_type == MessageType.TASK_ASSIGNMENT
        assert "task" in msg.content

    def test_create_alert(self):
        """测试创建警报消息"""
        msg = CommunicationProtocol.create_alert(
            sender=AgentRole.OPERATIONS,
            alert_type="system_error",
            message="Test error",
            severity=Priority.HIGH,
        )
        assert msg.message_type == MessageType.ALERT
        assert msg.content["alert_type"] == "system_error"
        assert msg.priority == Priority.HIGH


class TestTaskId:
    """测试任务ID生成"""

    def test_task_id_format(self):
        """测试任务ID格式"""
        task_id = create_task_id()
        assert task_id.startswith("task_")


class TestFormatTimestamp:
    """测试时间戳格式化"""

    def test_format_timestamp(self):
        """测试时间戳格式"""
        dt = datetime(2026, 1, 1, 12, 0, 0)
        result = format_timestamp(dt)
        assert result == "2026-01-01 12:00:00"


class TestCalculateKPICompletion:
    """测试KPI完成度计算"""

    def test_kpi_below_target(self):
        """测试KPI未达标"""
        result = calculate_kpi_completion(50, 100)
        assert result == 50.0

    def test_kpi_above_target(self):
        """测试KPI超过目标"""
        result = calculate_kpi_completion(150, 100)
        assert result == 100.0

    def test_kpi_with_zero_target(self):
        """测试目标为零"""
        result = calculate_kpi_completion(0, 0)
        assert result == 100.0


class TestValidateMessage:
    """测试消息验证"""

    def test_valid_message(self):
        """测试有效消息"""
        msg = Message(
            sender=AgentRole.CEO,
            recipient=AgentRole.CTO,
            message_type=MessageType.STATUS_REPORT,
            content={"test": "data"},
        )
        assert validate_message(msg) is True

    def test_invalid_message_missing_fields(self):
        """测试缺少字段的消息"""
        msg = Message(
            sender=AgentRole.CEO,
            recipient=AgentRole.CTO,
            message_type=MessageType.STATUS_REPORT,
            content={"test": "data"},
        )
        delattr(msg, "sender")
        assert validate_message(msg) is False


class TestRetryStrategy:
    def test_all_retry_strategies_exist(self):
        assert RetryStrategy.FIXED.value == "fixed"
        assert RetryStrategy.EXPONENTIAL_BACKOFF.value == "exponential_backoff"
        assert RetryStrategy.LINEAR_BACKOFF.value == "linear_backoff"


class TestMessageMetadata:
    def test_message_metadata_fields(self):
        metadata = MessageMetadata(
            message_id="msg_001",
            correlation_id=None,
            trace_id="trace_001",
            sender=AgentRole.CEO,
            recipients=[AgentRole.CTO],
            message_type=MessageType.TASK_ASSIGNMENT,
            priority=Priority.HIGH,
            timestamp=datetime.now(),
            expires_at=None,
            response_required=True,
            max_retries=3,
            retry_strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            metadata={"key": "value"},
        )
        assert metadata.message_id == "msg_001"
        assert metadata.trace_id == "trace_001"
        assert metadata.sender == AgentRole.CEO
        assert len(metadata.recipients) == 1
        assert metadata.response_required is True

    def test_message_metadata_defaults(self):
        metadata = MessageMetadata(
            message_id="msg_002",
            correlation_id=None,
            trace_id="trace_002",
            sender=AgentRole.RD,
            recipients=[AgentRole.CTO],
            message_type=MessageType.STATUS_REPORT,
            priority=Priority.MEDIUM,
            timestamp=datetime.now(),
            expires_at=None,
            response_required=False,
            max_retries=3,
            retry_strategy=RetryStrategy.FIXED,
            metadata={},
        )
        assert metadata.correlation_id is None
        assert metadata.expires_at is None
        assert metadata.metadata == {}


class TestMockAgent:
    """测试模拟智能体"""

    def test_agent_init(self):
        """测试智能体初始化"""
        agent = MockAgent(AgentRole.CEO)
        assert agent.role == AgentRole.CEO
        assert "test_capability" in agent.capabilities

    def test_agent_state_initialized(self):
        """测试状态初始化"""
        agent = MockAgent(AgentRole.RD)
        assert agent.state.role == AgentRole.RD
        assert agent.state.current_tasks == []
        assert agent.state.completed_tasks == []
