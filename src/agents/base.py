from typing import Dict, List, Optional, Any, TypedDict
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
import json
from abc import ABC, abstractmethod


class AgentRole(Enum):
    """智能体角色枚举"""

    CEO = "ceo"  # 首席执行官
    CTO = "cto"  # 首席技术官
    CPO = "cpo"  # 首席产品官
    CMO = "cmo"  # 首席市场官
    CFO = "cfo"  # 首席财务官
    HR = "hr"  # 人力资源
    RD = "rd"  # 研发工程师
    DATA_ANALYST = "data_analyst"  # 数据分析师
    CUSTOMER_SUPPORT = "customer_support"  # 客户支持
    OPERATIONS = "operations"  # 运营专员


class MessageType(Enum):
    """消息类型枚举"""

    TASK_ASSIGNMENT = "task_assignment"  # 任务分配
    STATUS_REPORT = "status_report"  # 状态报告
    DATA_REQUEST = "data_request"  # 数据请求
    DATA_RESPONSE = "data_response"  # 数据响应
    APPROVAL_REQUEST = "approval_request"  # 审批请求
    APPROVAL_RESPONSE = "approval_response"  # 审批响应
    ALERT = "alert"  # 警报
    COLLABORATION = "collaboration"  # 协作请求


class Priority(Enum):
    """优先级枚举"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RetryStrategy(Enum):
    """重试策略枚举"""

    NO_RETRY = "no_retry"
    FIXED_DELAY = "fixed_delay"
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    JITTERED_BACKOFF = "jittered_backoff"
    CIRCUIT_BREAKER = "circuit_breaker"


class FallbackStrategy(Enum):
    """降级策略"""

    CACHE = "cache"
    DEFAULT = "default"
    GRACEFUL_DEGRADATION = "graceful"
    MANUAL_OVERRIDE = "manual"
    QUEUE_FOR_LATER = "queue"


@dataclass
class MessageMetadata:
    message_id: str
    correlation_id: Optional[str]
    trace_id: str
    sender: AgentRole
    recipients: List[AgentRole]
    message_type: MessageType
    priority: Priority
    timestamp: datetime
    expires_at: Optional[datetime]
    response_required: bool
    max_retries: int
    retry_strategy: RetryStrategy
    metadata: Dict[str, Any]


@dataclass
class Message:
    """消息数据类 - 用于智能体间通信"""

    sender: AgentRole  # 发送者角色
    recipient: AgentRole  # 接收者角色
    message_type: MessageType  # 消息类型
    content: Dict[str, Any]  # 消息内容
    priority: Priority = Priority.MEDIUM  # 优先级，默认中等
    timestamp: datetime = field(default_factory=datetime.now)  # 时间戳
    message_id: str = field(
        default_factory=lambda: f"msg_{datetime.now().timestamp()}"
    )  # 消息唯一ID


@dataclass
class Task:
    """任务数据类 - 用于任务分配和跟踪"""

    task_id: str  # 任务唯一ID
    title: str  # 任务标题
    description: str  # 任务描述
    assigned_to: AgentRole  # 分配给的角色
    assigned_by: AgentRole  # 分配者角色
    priority: Priority  # 优先级
    status: str = "pending"  # 任务状态：pending-待处理, in_progress-进行中, completed-已完成, failed-已失败
    dependencies: List[str] = field(default_factory=list)  # 依赖的任务ID列表
    deliverables: List[str] = field(default_factory=list)  # 交付成果列表
    deadline: Optional[datetime] = None  # 截止日期
    created_at: datetime = field(default_factory=datetime.now)  # 创建时间
    updated_at: datetime = field(default_factory=datetime.now)  # 更新时间
    metadata: Dict[str, Any] = field(default_factory=dict)  # 元数据


@dataclass
class AgentState:
    """智能体状态数据类"""

    role: AgentRole  # 智能体角色
    current_tasks: List[Task] = field(default_factory=list)  # 当前任务列表
    completed_tasks: List[Task] = field(default_factory=list)  # 已完成任务列表
    messages: List[Message] = field(default_factory=list)  # 消息列表
    performance_metrics: Dict[str, float] = field(default_factory=dict)  # 性能指标
    capabilities: List[str] = field(default_factory=list)  # 能力列表
    workload: float = 0.0  # 工作负载 (0.0-1.0)
    last_active: datetime = field(default_factory=datetime.now)  # 最后活跃时间


class CompanyState(TypedDict):
    """公司状态类型定义 - 全局共享状态"""

    agents: Dict[AgentRole, AgentState]  # 所有智能体的状态
    tasks: Dict[str, Task]  # 所有任务
    messages: List[Message]  # 所有消息
    current_time: datetime  # 当前时间
    strategic_goals: Dict[str, Any]  # 战略目标
    kpis: Dict[str, float]  # 关键绩效指标
    market_data: Dict[str, Any]  # 市场数据
    user_feedback: List[Dict[str, Any]]  # 用户反馈
    system_health: Dict[str, Any]  # 系统健康状态


class BaseAgent(ABC):
    """智能体基类 - 所有智能体的抽象基类"""

    def __init__(self, role: AgentRole, capabilities: List[str]):
        """初始化智能体
        Args:
            role: 智能体角色
            capabilities: 能力列表
        """
        self.role = role  # 智能体角色
        self.capabilities = capabilities  # 能力列表
        self.state = AgentState(role=role, capabilities=capabilities)  # 智能体状态

    @abstractmethod
    async def process_message(
        self, message: Message, company_state: CompanyState
    ) -> Optional[Message]:
        """处理传入消息，可选返回响应
        Args:
            message: 传入的消息
            company_state: 公司状态
        Returns:
            可选的响应消息
        """
        pass

    @abstractmethod
    async def execute_task(
        self, task: Task, company_state: CompanyState
    ) -> Dict[str, Any]:
        """执行分配的任务并返回结果
        Args:
            task: 要执行的任务
            company_state: 公司状态
        Returns:
            任务执行结果
        """
        pass

    @abstractmethod
    async def generate_report(self, company_state: CompanyState) -> Dict[str, Any]:
        """生成周期性性能/活动报告
        Args:
            company_state: 公司状态
        Returns:
            报告数据
        """
        pass

    def can_handle_task(self, task: Task) -> bool:
        """检查智能体是否能处理任务（基于能力）
        Args:
            task: 要检查的任务
        Returns:
            如果可以处理返回True
        """
        return self.state.workload < 0.8 and task.assigned_to == self.role

    def has_capabilities(self, required_capabilities: List[str]) -> bool:
        """检查智能体是否具备所需能力
        Args:
            required_capabilities: 所需能力列表
        Returns:
            如果具备所有所需能力返回True
        """
        agent_capabilities = set(self.capabilities)
        required_set = set(required_capabilities)
        return (
            len(required_set) == 0 or agent_capabilities & required_set == required_set
        )

    def update_workload(self, delta: float):
        """更新智能体工作负载 (0.0 到 1.0)
        Args:
            delta: 工作负载变化量
        """
        self.state.workload = max(0.0, min(1.0, self.state.workload + delta))
        self.state.last_active = datetime.now()

    def add_task(self, task: Task):
        """将任务添加到当前任务列表
        Args:
            task: 要添加的任务
        """
        self.state.current_tasks.append(task)
        self.update_workload(0.1)  # 增加工作负载

    def complete_task(self, task_id: str) -> Optional[Task]:
        """标记任务为已完成
        Args:
            task_id: 要完成的任务ID
        Returns:
            完成的任务，如果未找到则返回None
        """
        for i, task in enumerate(self.state.current_tasks):
            if task.task_id == task_id:
                task.status = "completed"
                task.updated_at = datetime.now()
                completed_task = self.state.current_tasks.pop(i)
                self.state.completed_tasks.append(completed_task)
                self.update_workload(-0.1)  # 减少工作负载
                return completed_task
        return None

    def get_role_hierarchy(self) -> int:
        """获取决策层级级别，用于公司内部权限和优先级比较

        Returns:
            层级值，值越大优先级越高，用于决策冲突解决和消息路由
        """
        hierarchy = {
            AgentRole.CEO: 10,  # 首席执行官 - 最高优先级
            AgentRole.CTO: 9,  # 首席技术官
            AgentRole.CPO: 9,  # 首席产品官
            AgentRole.CMO: 9,  # 首席市场官
            AgentRole.CFO: 9,  # 首席财务官
            AgentRole.HR: 8,  # 人力资源
            AgentRole.OPERATIONS: 7,  # 运营专员
            AgentRole.DATA_ANALYST: 6,  # 数据分析师
            AgentRole.RD: 5,  # 研发工程师
            AgentRole.CUSTOMER_SUPPORT: 4,  # 客户支持
        }
        return hierarchy.get(self.role, 0)  # 默认层级为0


class CommunicationProtocol:
    """通信协议类 - 提供创建标准化消息的静态方法"""

    @staticmethod
    def create_message(
        sender: AgentRole,
        recipient: AgentRole,
        message_type: MessageType,
        content: Dict[str, Any],
        priority: Priority = Priority.MEDIUM,
    ) -> Message:
        """创建标准化消息
        Args:
            sender: 发送者角色
            recipient: 接收者角色
            message_type: 消息类型
            content: 消息内容
            priority: 优先级，默认中等
        Returns:
            Message对象
        """
        return Message(
            sender=sender,
            recipient=recipient,
            message_type=message_type,
            content=content,
            priority=priority,
        )

    @staticmethod
    def create_task_assignment(
        assigner: AgentRole, assignee: AgentRole, task: Task
    ) -> Message:
        """创建任务分配消息
        Args:
            assigner: 分配者角色
            assignee: 接收者角色
            task: 任务对象
        Returns:
            任务分配消息
        """
        return CommunicationProtocol.create_message(
            sender=assigner,
            recipient=assignee,
            message_type=MessageType.TASK_ASSIGNMENT,
            content={"task": task.__dict__},
            priority=task.priority,
        )

    @staticmethod
    def create_status_report(
        agent: AgentRole,
        report_data: Dict[str, Any],
        recipient: Optional[AgentRole] = None,
    ) -> Message:
        """创建状态报告消息
        Args:
            agent: 报告发送者角色
            report_data: 报告数据
            recipient: 接收者角色，默认CEO
        Returns:
            状态报告消息
        """
        return CommunicationProtocol.create_message(
            sender=agent,
            recipient=recipient or AgentRole.CEO,  # 默认发送给CEO
            message_type=MessageType.STATUS_REPORT,
            content=report_data,
        )

    @staticmethod
    def create_alert(
        sender: AgentRole,
        alert_type: str,
        message: str,
        severity: Priority = Priority.HIGH,
        recipient: Optional[AgentRole] = None,
    ) -> Message:
        """创建警报消息
        Args:
            sender: 发送者角色
            alert_type: 警报类型
            message: 警报消息
            severity: 严重程度，默认高优先级
            recipient: 接收者角色，默认运营专员
        Returns:
            警报消息
        """
        return CommunicationProtocol.create_message(
            sender=sender,
            recipient=recipient or AgentRole.OPERATIONS,
            message_type=MessageType.ALERT,
            content={
                "alert_type": alert_type,  # 警报类型
                "message": message,  # 警报消息
                "severity": severity.value,  # 严重程度
            },
            priority=severity,
        )


# 工具函数 - 用于状态管理
def create_task_id() -> str:
    """生成唯一任务ID"""
    return f"task_{datetime.now().timestamp()}"


def format_timestamp(dt: datetime) -> str:
    """格式化时间为一致显示格式"""
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def calculate_kpi_completion(current: float, target: float) -> float:
    """计算KPI完成百分比
    Args:
        current: 当前值
        target: 目标值
    Returns:
        完成百分比 (0-100)
    """
    if target == 0:
        return 100.0
    return min(100.0, (current / target) * 100.0)


def validate_message(message: Message) -> bool:
    """验证消息结构
    Args:
        message: 要验证的消息
    Returns:
        结构有效返回True
    """
    required_fields = ["sender", "recipient", "message_type", "content"]
    return all(hasattr(message, field) for field in required_fields)
