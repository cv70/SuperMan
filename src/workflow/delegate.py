"""任务委派系统 - 基于能力匹配和负载均衡的智能委派算法"""

from typing import Dict, List, Optional, Any
from enum import Enum

from ..agents.base import AgentRole, Task, AgentState, CompanyState, Priority


PRIORITY_WEIGHTS = {
    "critical": 1.5,
    "high": 1.2,
    "medium": 1.0,
    "low": 0.8,
}

ACCEPTANCE_THRESHOLD = 0.9


def _calculate_capability_match(task: Task, agent: AgentState) -> float:
    """计算能力匹配分数 (0-1)

    Args:
        task: 待委派任务
        agent: 智能体状态

    Returns:
        能力匹配分数, 越高越好
    """
    required = set(task.required_capabilities or [])
    has = set(agent.capabilities or [])

    if not required:
        return 1.0

    match_count = len(required & has)
    return match_count / len(required)


def _calculate_workload_balance(
    agent_role: AgentRole,
    task: Task,
    company_state: CompanyState
) -> float:
    """计算负载均衡分数 (越高越好)

    Args:
        agent_role: 智能体角色
        task: 任务
        company_state: 公司状态

    Returns:
        负载均衡分数, 越高越好 (1.0 - load_score)
    """
    agent_state = company_state["agents"][agent_role]

    current_load = agent_state.workload
    task_load = task.estimated_workload or 0.1
    priority_weight = PRIORITY_WEIGHTS.get(task.priority.value, 1.0)

    load_score = current_load + (task_load * priority_weight)

    return max(0, 1.0 - load_score)


def _distribute_workload(scored_agents: List[tuple]) -> List[AgentRole]:
    """在多个智能体之间分配负载

    Args:
        scored_agents: 排序后的智能体列表 (role, score)

    Returns:
        用于负载均衡的前2个智能体角色列表
    """
    return [role for role, _ in scored_agents[:2]]


async def delegate_task(
    task: Task,
    company_state: CompanyState
) -> AgentRole:
    """基于多因素的智能委派算法

    Args:
        task: 待委派任务
        company_state: 全局状态

    Returns:
        被委派的智能体角色
    """
    agents = company_state.get("agents", {})
    
    if not agents:
        raise ValueError("No agents available for delegation")

    capability_scores = {}
    for agent_role, agent_state in agents.items():
        score = _calculate_capability_match(
            task=task,
            agent=agent_state
        )
        capability_scores[agent_role] = score

    workload_scores = {}
    for agent_role in capability_scores:
        score = _calculate_workload_balance(
            agent_role=agent_role,
            task=task,
            company_state=company_state
        )
        workload_scores[agent_role] = score

    history_scores = {
        role: 1.0 for role in capability_scores
    }

    final_scores = {}
    for agent_role in capability_scores:
        final_score = (
            0.5 * capability_scores[agent_role] +
            0.3 * workload_scores[agent_role] +
            0.2 * history_scores[agent_role]
        )
        final_scores[agent_role] = final_score

    best_agent = max(final_scores, key=final_scores.get)

    return best_agent
