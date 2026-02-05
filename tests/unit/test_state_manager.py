"""测试State Manager核心功能"""

import pytest
from datetime import datetime

from src.workflow.state_manager import (
    AgentState,
    AgentMetrics,
    AgentPreferences,
    CompanyState,
)
from src.agents.base import AgentRole, Priority, Task


class TestAgentMetrics:
    """测试AgentMetrics数据类"""

    def test_agent_metrics_defaults(self):
        """测试AgentMetrics具有正确的默认值"""
        metrics = AgentMetrics(
            total_tasks_completed=10,
            total_tasks_failed=2,
            avg_response_time_ms=50.0,
            avg_task_completion_time_ms=100.0,
            success_rate=0.8,
            collaboration_score=0.9,
            workload_balance_score=0.85,
        )
        assert metrics.total_tasks_completed == 10
        assert metrics.success_rate == 0.8
        assert metrics.collaboration_score == 0.9

    def test_agent_metrics_all_fields(self):
        """测试AgentMetrics所有字段"""
        metrics = AgentMetrics(
            total_tasks_completed=100,
            total_tasks_failed=5,
            avg_response_time_ms=25.5,
            avg_task_completion_time_ms=200.0,
            success_rate=0.95,
            collaboration_score=0.88,
            workload_balance_score=0.92,
        )
        assert metrics.total_tasks_failed == 5
        assert metrics.avg_response_time_ms == 25.5
        assert metrics.avg_task_completion_time_ms == 200.0
        assert metrics.collaboration_score == 0.88
        assert metrics.workload_balance_score == 0.92


class TestAgentPreferences:
    """测试AgentPreferences数据类"""

    def test_agent_preferences(self):
        """测试AgentPreferences具有正确的字段"""
        prefs = AgentPreferences(
            max_concurrent_tasks=3,
            preferred_channels=["http", "grpc"],
            auto_accept_collaborations=True,
            escalation_threshold=0.8,
        )
        assert prefs.max_concurrent_tasks == 3
        assert len(prefs.preferred_channels) == 2
        assert prefs.auto_accept_collaborations is True
        assert prefs.escalation_threshold == 0.8

    def test_agent_preferences_default_values(self):
        """测试AgentPreferences默认值"""
        prefs = AgentPreferences(
            max_concurrent_tasks=5,
            preferred_channels=["http"],
            auto_accept_collaborations=False,
            escalation_threshold=0.9,
        )
        assert prefs.max_concurrent_tasks == 5
        assert prefs.preferred_channels == ["http"]
        assert prefs.auto_accept_collaborations is False
        assert prefs.escalation_threshold == 0.9


class TestAgentState:
    """测试AgentState数据类"""

    def test_agent_state(self):
        """测试AgentState具有正确的结构"""
        metrics = AgentMetrics(
            total_tasks_completed=5,
            total_tasks_failed=0,
            avg_response_time_ms=30.0,
            avg_task_completion_time_ms=80.0,
            success_rate=1.0,
            collaboration_score=0.95,
            workload_balance_score=0.9,
        )

        state = AgentState(
            role=AgentRole.CTO,
            current_tasks={},
            task_history=[],
            workload=0.5,
            capacity=1.0,
            last_update=datetime.now(),
            metrics=metrics,
            context={},
            preferences=AgentPreferences(
                max_concurrent_tasks=2,
                preferred_channels=["http"],
                auto_accept_collaborations=False,
                escalation_threshold=0.85,
            ),
        )
        assert state.role == AgentRole.CTO
        assert state.workload == 0.5
        assert state.capacity == 1.0
        assert state.current_tasks == {}
        assert state.task_history == []

    def test_agent_state_with_tasks(self):
        """测试带任务的AgentState"""
        task1 = Task(
            task_id="task_1",
            title="Test Task 1",
            description="Test description 1",
            assigned_to=AgentRole.RD,
            assigned_by=AgentRole.CTO,
            priority=Priority.HIGH,
        )

        task2 = Task(
            task_id="task_2",
            title="Test Task 2",
            description="Test description 2",
            assigned_to=AgentRole.RD,
            assigned_by=AgentRole.CTO,
            priority=Priority.MEDIUM,
        )

        metrics = AgentMetrics(
            total_tasks_completed=1,
            total_tasks_failed=0,
            avg_response_time_ms=20.0,
            avg_task_completion_time_ms=50.0,
            success_rate=1.0,
            collaboration_score=0.9,
            workload_balance_score=0.85,
        )

        state = AgentState(
            role=AgentRole.RD,
            current_tasks={"task_1": task1, "task_2": task2},
            task_history=[task1],
            workload=0.7,
            capacity=1.0,
            last_update=datetime.now(),
            metrics=metrics,
            context={"session_id": "123"},
            preferences=AgentPreferences(
                max_concurrent_tasks=3,
                preferred_channels=["grpc", "http"],
                auto_accept_collaborations=True,
                escalation_threshold=0.75,
            ),
        )

        assert len(state.current_tasks) == 2
        assert len(state.task_history) == 1
        assert state.context == {"session_id": "123"}
        assert state.preferences.max_concurrent_tasks == 3


class TestCompanyState:
    """测试CompanyState TypedDict"""

    def test_company_state_structure(self):
        """测试CompanyState基本结构"""
        test_time = datetime.now()

        state: CompanyState = {
            "agents": {},
            "tasks": {},
            "messages": [],
            "current_time": test_time,
            "strategic_goals": {},
            "kpis": {},
            "market_data": {},
            "user_feedback": [],
            "system_health": {},
            "financial_data": {},
            "product_backlog": [],
            "technical_debt": [],
            "campaign_metrics": [],
            "hr_metrics": {},
            "rd_performance": {},
            "active_collaborations": {},
            "collaboration_history": [],
            "message_queue_stats": {},
            "agent_performance": {},
            "event_log": [],
            "approval_history": [],
            "permission_matrix": {},
            "audit_log": [],
        }

        assert state["current_time"] == test_time
        assert state["agents"] == {}
        assert state["tasks"] == {}
        assert state["messages"] == []

    def test_company_state_with_data(self):
        """测试带数据的CompanyState"""
        test_time = datetime.now()

        state: CompanyState = {
            "agents": {
                AgentRole.CEO: AgentState(
                    role=AgentRole.CEO,
                    current_tasks={},
                    task_history=[],
                    workload=0.5,
                    capacity=1.0,
                    last_update=test_time,
                    metrics=AgentMetrics(
                        total_tasks_completed=10,
                        total_tasks_failed=0,
                        avg_response_time_ms=100.0,
                        avg_task_completion_time_ms=200.0,
                        success_rate=1.0,
                        collaboration_score=0.95,
                        workload_balance_score=0.9,
                    ),
                    context={},
                    preferences=AgentPreferences(
                        max_concurrent_tasks=2,
                        preferred_channels=["http"],
                        auto_accept_collaborations=False,
                        escalation_threshold=0.85,
                    ),
                )
            },
            "tasks": {
                "task_1": Task(
                    task_id="task_1",
                    title="战略规划",
                    description="制定季度战略",
                    assigned_to=AgentRole.CEO,
                    assigned_by=AgentRole.CEO,
                    priority=Priority.HIGH,
                )
            },
            "messages": [],
            "current_time": test_time,
            "strategic_goals": {"q1_2026": "用户增长20%"},
            "kpis": {"user_growth": 0.15, "revenue": 1000000},
            "market_data": {"competitors": 5, "market_size": "1B"},
            "user_feedback": [{"user_id": "u1", "score": 4.5}],
            "system_health": {"cpu": 0.5, "memory": 0.6},
            "financial_data": {"revenue": 1000000, "expenses": 500000},
            "product_backlog": [{"feature": "new_feature", "priority": "high"}],
            "technical_debt": [{"issue": "legacy_code", "severity": "medium"}],
            "campaign_metrics": [{"name": "campaign_1", "ctr": 0.05}],
            "hr_metrics": {"employee_satisfaction": 4.0, "turnover": 0.05},
            "rd_performance": {"projects_completed": 5, "bugs_fixed": 20},
            "active_collaborations": {
                "collab_1": {
                    "name": "project_alpha",
                    "members": [AgentRole.CTO, AgentRole.RD],
                }
            },
            "collaboration_history": [{"collab_id": "collab_1", "result": "success"}],
            "message_queue_stats": {
                "pending": 10,
                "processed": 100,
                "failed": 2,
            },
            "agent_performance": {
                AgentRole.CTO: {
                    "total_tasks": 50,
                    "completed_tasks": 45,
                    "failed_tasks": 5,
                }
            },
            "event_log": [{"event": "system_start", "timestamp": test_time}],
            "approval_history": [{"request_id": "req_1", "decision": "approved"}],
            "permission_matrix": {"admin": {AgentRole.CEO, AgentRole.HR}},
            "audit_log": [{"action": "login", "agent": AgentRole.CEO}],
        }

        assert len(state["agents"]) == 1
        assert "task_1" in state["tasks"]
        assert "q1_2026" in state["strategic_goals"]
        assert state["kpis"]["user_growth"] == 0.15
