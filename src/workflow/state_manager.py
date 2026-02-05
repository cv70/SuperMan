from typing import Dict, List, Any, TypedDict
from dataclasses import dataclass
from datetime import datetime

from src.agents.base import AgentRole, Task


@dataclass
class AgentMetrics:
    """智能体性能指标"""

    total_tasks_completed: int
    total_tasks_failed: int
    avg_response_time_ms: float
    avg_task_completion_time_ms: float
    success_rate: float
    collaboration_score: float
    workload_balance_score: float


@dataclass
class AgentPreferences:
    """智能体偏好配置"""

    max_concurrent_tasks: int
    preferred_channels: List[str]
    auto_accept_collaborations: bool
    escalation_threshold: float


@dataclass
class AgentState:
    """智能体本地状态"""

    role: AgentRole
    current_tasks: Dict[str, Task]
    task_history: List[Task]
    workload: float
    capacity: float
    last_update: datetime
    metrics: AgentMetrics
    context: Dict[str, Any]
    preferences: AgentPreferences


class CompanyState(TypedDict, total=False):
    """公司状态 TypedDict - 全局共享状态"""

    agents: Dict[AgentRole, AgentState]
    tasks: Dict[str, Task]
    messages: List[Any]
    current_time: datetime
    strategic_goals: Dict[str, Any]
    kpis: Dict[str, float]

    extended_market_data: Dict[str, Any]
    user_feedback: List[Dict[str, Any]]
    system_health: Dict[str, Any]
    financial_data: Dict[str, Any]
    product_backlog: List[Dict[str, Any]]
    technical_debt: List[Dict[str, Any]]
    campaign_metrics: List[Dict[str, Any]]
    hr_metrics: Dict[str, Any]
    rd_performance: Dict[str, Any]

    active_collaborations: Dict[str, Any]
    collaboration_history: List[Dict[str, Any]]

    message_queue_stats: Dict[str, Any]
    agent_performance: Dict[AgentRole, Any]

    event_log: List[Dict[str, Any]]
    approval_history: List[Dict[str, Any]]

    permission_matrix: Dict[str, Any]
    audit_log: List[Dict[str, Any]]
