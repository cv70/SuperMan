import json
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path

from .base import (
    AgentRole,
    MessageType,
    Priority,
    Message,
    Task,
    AgentState,
    CompanyState,
)
from .utils import (
    format_timestamp,
    parse_datetime,
    safe_get,
    validate_dict_fields,
    convert_to_serializable,
)


DEFAULT_STATE_FILE = "data/company_state.json"


class StateManager:
    """Manages state persistence for the company's AI agents.

    Provides methods to load, save, and update agent states
    using JSON file persistence.
    """

    def __init__(self, state_file: Optional[str] = None):
        """Initialize the state manager.

        Args:
            state_file: Path to the state file. Defaults to data/company_state.json
        """
        self.state_file = Path(state_file or DEFAULT_STATE_FILE)
        self._state: CompanyState = self._get_default_state()
        self._lock = asyncio.Lock()

    def _get_default_state(self) -> CompanyState:
        """Create default company state.

        Returns:
            Default CompanyState with empty structures
        """
        return {
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

    def _ensure_directory(self) -> None:
        """确保状态文件的目录存在。"""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)

    async def load_state(self) -> CompanyState:
        """从文件加载公司状态。

        返回:
            加载的 CompanyState 对象

        异常:
            FileNotFoundError: 如果状态文件不存在
            json.JSONDecodeError: 如果文件包含无效的 JSON
        """
        async with self._lock:
            if not self.state_file.exists():
                raise FileNotFoundError(f"State file not found: {self.state_file}")

            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                self._state = self._deserialize_state(data)
                return self._state

            except FileNotFoundError:
                raise
            except json.JSONDecodeError as e:
                raise json.JSONDecodeError(
                    f"Invalid JSON in state file: {e.msg}", e.doc, e.pos
                )

    async def save_state(self, state: CompanyState) -> None:
        """Save company state to file.

        Args:
            state: CompanyState to save
        """
        async with self._lock:
            self._ensure_directory()

            serializable_state = self._serialize_state(state)

            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(serializable_state, f, indent=2, ensure_ascii=False)

    async def update_agent_state(
        self, agent_role: AgentRole, updates: Dict[str, Any]
    ) -> None:
        """Update state for a specific agent.

        Args:
            agent_role: Role of the agent to update
            updates: Dictionary of fields to update
        """
        async with self._lock:
            if not validate_dict_fields(updates, []):
                return

            if agent_role not in self._state["agents"]:
                self._state["agents"][agent_role] = {
                    "role": agent_role.value,
                    "current_tasks": [],
                    "completed_tasks": [],
                    "messages": [],
                    "performance_metrics": {},
                    "capabilities": [],
                    "workload": 0.0,
                    "last_active": format_timestamp(datetime.now()),
                }

            agent_state = self._state["agents"][agent_role]

            if "current_tasks" in updates:
                agent_state["current_tasks"] = [
                    t if isinstance(t, dict) else convert_to_serializable(t)
                    for t in updates["current_tasks"]
                ]

            if "completed_tasks" in updates:
                agent_state["completed_tasks"] = [
                    t if isinstance(t, dict) else convert_to_serializable(t)
                    for t in updates["completed_tasks"]
                ]

            if "performance_metrics" in updates:
                agent_state["performance_metrics"].update(
                    updates["performance_metrics"]
                )

            if "capabilities" in updates:
                agent_state["capabilities"] = updates["capabilities"]

            if "workload" in updates:
                agent_state["workload"] = float(updates["workload"])

            agent_state["last_active"] = format_timestamp(datetime.now())

    async def get_company_state(self) -> CompanyState:
        """Get current company state.

        Returns:
            Current CompanyState
        """
        async with self._lock:
            return self._state.copy()

    async def add_task(self, task: Task) -> None:
        """Add a task to the company state.

        Args:
            task: Task to add
        """
        async with self._lock:
            self._state["tasks"][task.task_id] = task

    async def add_message(self, message: Message) -> None:
        """Add a message to the company state.

        Args:
            message: Message to add
        """
        async with self._lock:
            self._state["messages"].append(message)

    async def add_user_feedback(self, feedback: Dict[str, Any]) -> None:
        """Add user feedback to the company state.

        Args:
            feedback: Feedback dictionary with user_id, content, sentiment, etc.
        """
        async with self._lock:
            feedback["timestamp"] = format_timestamp(datetime.now())
            feedback["feedback_id"] = f"fb_{datetime.now().timestamp()}"
            self._state["user_feedback"].append(feedback)

    async def update_kpis(self, kpis: Dict[str, float]) -> None:
        """Update company KPIs.

        Args:
            kpis: Dictionary of KPI names to values
        """
        async with self._lock:
            self._state["kpis"].update(kpis)

    async def update_system_health(self, health_data: Dict[str, Any]) -> None:
        """Update system health metrics.

        Args:
            health_data: Dictionary of health metrics
        """
        async with self._lock:
            self._state["system_health"].update(health_data)
            self._state["system_health"]["last_updated"] = format_timestamp(
                datetime.now()
            )

    def _serialize_state(self, state: CompanyState) -> Dict[str, Any]:
        """Convert CompanyState to JSON-serializable dict.

        Args:
            state: CompanyState to serialize

        Returns:
            JSON-serializable dictionary
        """
        serializable = {
            "agents": {},
            "tasks": {},
            "messages": [],
            "current_time": format_timestamp(state["current_time"]),
            "strategic_goals": state.get("strategic_goals", {}),
            "kpis": state.get("kpis", {}),
            "market_data": state.get("market_data", {}),
            "user_feedback": state.get("user_feedback", []),
            "system_health": state.get("system_health", {}),
        }

        for role, agent_state in state.get("agents", {}).items():
            serializable["agents"][role] = convert_to_serializable(agent_state)

        for task_id, task in state.get("tasks", {}).items():
            serializable["tasks"][task_id] = convert_to_serializable(task)

        for message in state.get("messages", []):
            serializable["messages"].append(convert_to_serializable(message))

        return serializable

    def _deserialize_state(self, data: Dict[str, Any]) -> CompanyState:
        """Convert deserialized dict to CompanyState.

        Args:
            data: Deserialized dictionary

        Returns:
            CompanyState object
        """
        state: CompanyState = {
            "agents": {},
            "tasks": {},
            "messages": [],
            "current_time": parse_datetime(
                data.get("current_time", format_timestamp(datetime.now()))
            ),
            "strategic_goals": data.get("strategic_goals", {}),
            "kpis": data.get("kpis", {}),
            "market_data": data.get("market_data", {}),
            "user_feedback": data.get("user_feedback", []),
            "system_health": data.get("system_health", {}),
        }

        agents_data = data.get("agents", {})
        for role_str, agent_dict in agents_data.items():
            try:
                role = AgentRole(role_str)
                state["agents"][role] = agent_dict
            except ValueError:
                continue

        tasks_data = data.get("tasks", {})
        for task_id, task_dict in tasks_data.items():
            state["tasks"][task_id] = task_dict

        messages_data = data.get("messages", [])
        for msg_dict in messages_data:
            try:
                sender = AgentRole(msg_dict.get("sender", ""))
                recipient = AgentRole(msg_dict.get("recipient", ""))
                msg_type = MessageType(msg_dict.get("message_type", ""))
                priority = Priority(msg_dict.get("priority", "medium"))

                timestamp_str = msg_dict.get(
                    "timestamp", format_timestamp(datetime.now())
                )
                timestamp = parse_datetime(timestamp_str)

                message = Message(
                    sender=sender,
                    recipient=recipient,
                    message_type=msg_type,
                    content=msg_dict.get("content", {}),
                    priority=priority,
                    timestamp=timestamp,
                    message_id=msg_dict.get("message_id", ""),
                )
                state["messages"].append(message)
            except (ValueError, KeyError):
                continue

        return state


_state_manager: Optional[StateManager] = None


async def get_state_manager(state_file: Optional[str] = None) -> StateManager:
    """Get or create the global state manager instance.

    Args:
        state_file: Path to state file (only used for first call)

    Returns:
        StateManager instance
    """
    global _state_manager

    if _state_manager is None:
        _state_manager = StateManager(state_file)

    return _state_manager


async def cleanup_state_manager() -> None:
    """清理状态管理器实例。"""
    global _state_manager

    if _state_manager is not None:
        _state_manager = None
