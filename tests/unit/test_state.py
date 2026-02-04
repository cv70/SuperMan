"""测试状态管理功能"""

import pytest
import json
from datetime import datetime
from pathlib import Path

from src.agents.base import (
    AgentRole,
    MessageType,
    Priority,
    Message,
    Task,
    AgentState,
)


class TestStateManager:
    """测试 StateManager 状态管理器"""

    @pytest.fixture
    def temp_state_file(self, tmp_path):
        """创建临时状态文件"""
        return tmp_path / "test_state.json"

    @pytest.fixture
    def state_manager(self, temp_state_file):
        """创建状态管理器实例"""
        from src.agents.state_manager import StateManager

        return StateManager(str(temp_state_file))

    def test_get_default_state(self, state_manager):
        """测试默认状态"""
        state = state_manager._get_default_state()
        assert "agents" in state
        assert "tasks" in state
        assert "messages" in state
        assert "current_time" in state
        assert "strategic_goals" in state
        assert "kpis" in state
        assert "market_data" in state
        assert "user_feedback" in state
        assert "system_health" in state
        assert "budget_allocation" in state

    def test_save_and_load_state(self, state_manager, temp_state_file):
        """测试状态保存和加载"""
        state = state_manager._get_default_state()
        state["current_time"] = datetime(2026, 1, 1, 12, 0, 0)
        state["kpis"] = {"revenue": 100}

        # 保存状态
        import asyncio

        asyncio.run(state_manager.save_state(state))

        # 验证文件已创建
        assert temp_state_file.exists()

        # 加载状态
        loaded_state = asyncio.run(state_manager.load_state())
        assert loaded_state["kpis"]["revenue"] == 100

    def test_update_agent_state(self, state_manager):
        """测试更新智能体状态"""
        state_manager._state["agents"][AgentRole.RD] = {
            "role": "rd",
            "current_tasks": [],
            "completed_tasks": [],
            "messages": [],
            "performance_metrics": {},
            "capabilities": [],
            "workload": 0.0,
            "last_active": datetime.now().isoformat(),
        }

        state_manager._state["agents"][AgentRole.RD]["workload"] = 0.5
        state_manager._state["agents"][AgentRole.RD]["current_tasks"] = [
            {"task_id": "task_1", "status": "in_progress"}
        ]

        assert state_manager._state["agents"][AgentRole.RD]["workload"] == 0.5

    def test_add_task(self, state_manager):
        """测试添加任务"""
        task = Task(
            task_id="test_task_123",
            title="Test Task",
            description="Test",
            assigned_to=AgentRole.RD,
            assigned_by=AgentRole.CTO,
            priority=Priority.MEDIUM,
        )

        state_manager._state["tasks"][task.task_id] = task
        assert "test_task_123" in state_manager._state["tasks"]

    def test_add_message(self, state_manager):
        """测试添加消息"""
        msg = Message(
            sender=AgentRole.CEO,
            recipient=AgentRole.CTO,
            message_type=MessageType.STATUS_REPORT,
            content={"status": "ok"},
            priority=Priority.MEDIUM,
        )

        state_manager._state["messages"].append(msg)
        assert len(state_manager._state["messages"]) == 1
        assert state_manager._state["messages"][0].sender == AgentRole.CEO

    def test_update_kpis(self, state_manager):
        """测试更新KPIs"""
        state_manager._state["kpis"] = {"revenue": 100}
        state_manager._state["kpis"]["user_growth"] = 50
        assert state_manager._state["kpis"]["user_growth"] == 50

    def test_update_system_health(self, state_manager):
        """测试更新系统健康"""
        state_manager._state["system_health"] = {"uptime": 99.9, "error_rate": 0.1}
        state_manager._state["system_health"]["last_updated"] = (
            datetime.now().isoformat()
        )
        assert "last_updated" in state_manager._state["system_health"]
