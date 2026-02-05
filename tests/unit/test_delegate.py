"""测试任务委派系统"""

import pytest
from src.workflow.delegate import (
    delegate_task,
    _calculate_capability_match,
    _calculate_workload_balance,
    PRIORITY_WEIGHTS
)
from src.agents.base import AgentRole, Priority, Task


def test_priority_weights():
    """测试优先级权重正确"""
    assert PRIORITY_WEIGHTS["critical"] == 1.5
    assert PRIORITY_WEIGHTS["high"] == 1.2
    assert PRIORITY_WEIGHTS["medium"] == 1.0
    assert PRIORITY_WEIGHTS["low"] == 0.8


def test_calculate_capability_match_no_requirements():
    """测试无要求时得分为1.0"""
    task = Task(
        task_id="t1",
        title="Test",
        description="",
        assigned_to=AgentRole.RD,
        assigned_by=AgentRole.CTO,
        priority=Priority.MEDIUM
    )
    agent = type('obj', (object,), {'capabilities': ['python', 'api']})()

    score = _calculate_capability_match(task, agent)
    assert score == 1.0


def test_calculate_capability_match_partial():
    """测试部分能力匹配"""
    task = Task(
        task_id="t1",
        title="Test",
        description="",
        assigned_to=AgentRole.RD,
        assigned_by=AgentRole.CTO,
        priority=Priority.MEDIUM,
        required_capabilities=['python', 'api', 'ml']
    )
    agent = type('obj', (object,), {'capabilities': ['python', 'api']})()

    score = _calculate_capability_match(task, agent)
    assert score == 2/3


def test_calculate_capability_match_full():
    """测试完整能力匹配"""
    task = Task(
        task_id="t1",
        title="Test",
        description="",
        assigned_to=AgentRole.RD,
        assigned_by=AgentRole.CTO,
        priority=Priority.MEDIUM,
        required_capabilities=['python', 'api']
    )
    agent = type('obj', (object,), {'capabilities': ['python', 'api', 'ml']})()

    score = _calculate_capability_match(task, agent)
    assert score == 1.0


def test_calculate_workload_balance():
    """测试负载平衡计算"""
    task = Task(
        task_id="t1",
        title="Test",
        description="",
        assigned_to=AgentRole.RD,
        assigned_by=AgentRole.CTO,
        priority=Priority.HIGH,
        estimated_workload=0.3
    )

    agent_state = type('obj', (object,), {
        'workload': 0.4,
        'capabilities': ['python']
    })()

    company_state = {
        "agents": {AgentRole.RD: agent_state}
    }

    score = _calculate_workload_balance(AgentRole.RD, task, company_state)
    expected_load = 0.4 + (0.3 * 1.2)
    expected_score = 1.0 - expected_load
    assert abs(score - expected_score) < 0.01


def test_calculate_workload_balance_critical():
    """测试高优先级负载计算"""
    task = Task(
        task_id="t1",
        title="Test",
        description="",
        assigned_to=AgentRole.RD,
        assigned_by=AgentRole.CTO,
        priority=Priority.CRITICAL,
        estimated_workload=0.2
    )

    agent_state = type('obj', (object,), {
        'workload': 0.3,
        'capabilities': ['python']
    })()

    company_state = {
        "agents": {AgentRole.RD: agent_state}
    }

    score = _calculate_workload_balance(AgentRole.RD, task, company_state)
    expected_load = 0.3 + (0.2 * 1.5)
    expected_score = 1.0 - expected_load
    assert abs(score - expected_score) < 0.01


def test_calculate_workload_balance_low():
    """测试低优先级负载计算"""
    task = Task(
        task_id="t1",
        title="Test",
        description="",
        assigned_to=AgentRole.RD,
        assigned_by=AgentRole.CTO,
        priority=Priority.LOW,
        estimated_workload=0.5
    )

    agent_state = type('obj', (object,), {
        'workload': 0.2,
        'capabilities': ['python']
    })()

    company_state = {
        "agents": {AgentRole.RD: agent_state}
    }

    score = _calculate_workload_balance(AgentRole.RD, task, company_state)
    expected_load = 0.2 + (0.5 * 0.8)
    expected_score = 1.0 - expected_load
    assert abs(score - expected_score) < 0.01


def test_calculate_workload_balance_zero_workload():
    """测试零负载情况"""
    task = Task(
        task_id="t1",
        title="Test",
        description="",
        assigned_to=AgentRole.RD,
        assigned_by=AgentRole.CTO,
        priority=Priority.MEDIUM,
        estimated_workload=0.1
    )

    agent_state = type('obj', (object,), {
        'workload': 0.0,
        'capabilities': ['python']
    })()

    company_state = {
        "agents": {AgentRole.RD: agent_state}
    }

    score = _calculate_workload_balance(AgentRole.RD, task, company_state)
    expected_load = 0.0 + (0.1 * 1.0)
    expected_score = 1.0 - expected_load
    assert abs(score - expected_score) < 0.01


async def test_delegate_task_selects_best_agent():
    """测试delegate_task选择最佳智能体"""
    rd_ml = type('obj', (object,), {
        'role': AgentRole.RD,
        'capabilities': ['python', 'ml', 'api'],
        'workload': 0.3
    })()

    task = Task(
        task_id="t1",
        title="ML Feature",
        description="",
        assigned_to=AgentRole.RD,
        assigned_by=AgentRole.CTO,
        priority=Priority.MEDIUM,
        required_capabilities=['python', 'ml']
    )

    company_state = {
        "agents": {
            AgentRole.RD: rd_ml
        },
        "tasks": {},
        "messages": [],
        "current_time": None,
        "strategic_goals": {},
        "kpis": {}
    }

    result = await delegate_task(task, company_state)
    assert result == AgentRole.RD


async def test_delegate_task_with_multiple_agents():
    """测试多个智能体委派"""
    rd_ml = type('obj', (object,), {
        'role': AgentRole.RD,
        'capabilities': ['python', 'ml', 'api'],
        'workload': 0.3
    })()

    task = Task(
        task_id="t1",
        title="ML Feature",
        description="",
        assigned_to=AgentRole.RD,
        assigned_by=AgentRole.CTO,
        priority=Priority.MEDIUM,
        required_capabilities=['python', 'ml']
    )

    company_state = {
        "agents": {
            AgentRole.RD: rd_ml
        },
        "tasks": {},
        "messages": [],
        "current_time": None,
        "strategic_goals": {},
        "kpis": {}
    }

    result = await delegate_task(task, company_state)
    assert result == AgentRole.RD


async def test_delegate_task_empty_agents():
    """测试空智能体列表"""
    task = Task(
        task_id="t1",
        title="Test",
        description="",
        assigned_to=AgentRole.RD,
        assigned_by=AgentRole.CTO,
        priority=Priority.MEDIUM
    )

    company_state = {
        "agents": {},
        "tasks": {},
        "messages": [],
        "current_time": None,
        "strategic_goals": {},
        "kpis": {}
    }

    with pytest.raises(ValueError, match="No agents available for delegation"):
        await delegate_task(task, company_state)
