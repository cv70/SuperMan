"""
Tests for orchestrator module.
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch


def test_priority_queue_enqueue():
    """Test PriorityOrchestrator enqueue_message"""
    with (
        patch("src.agents.ceo.ChatOpenAI"),
        patch("src.agents.cto.ChatOpenAI"),
        patch("src.agents.cpo.ChatOpenAI"),
        patch("src.agents.cmo.ChatOpenAI"),
        patch("src.agents.cfo.ChatOpenAI"),
        patch("src.agents.hr.ChatOpenAI"),
        patch("src.agents.rd.ChatOpenAI"),
        patch("src.agents.data_analyst.ChatOpenAI"),
        patch("src.agents.customer_support.ChatOpenAI"),
        patch("src.agents.operations.ChatOpenAI"),
    ):
        from src.workflow.orchestrator import PriorityOrchestrator
        from src.agents.base import Message, MessageType, Priority
        from src.agents.base import AgentRole

        orch = PriorityOrchestrator()

        msg = Message(
            sender=AgentRole.CEO,
            recipient=AgentRole.CPO,
            message_type=MessageType.TASK_ASSIGNMENT,
            content={"task": {"task_id": "test", "title": "Test"}},
            priority=Priority.HIGH,
        )

        orch.enqueue_message(msg)

        stats = orch.get_queue_stats()
        assert stats["total_size"] == 1
        assert stats["by_priority"]["HIGH"] == 1


def test_priority_queue_ordering():
    """Test messages are processed in priority order"""
    with (
        patch("src.agents.ceo.ChatOpenAI"),
        patch("src.agents.cto.ChatOpenAI"),
        patch("src.agents.cpo.ChatOpenAI"),
        patch("src.agents.cmo.ChatOpenAI"),
        patch("src.agents.cfo.ChatOpenAI"),
        patch("src.agents.hr.ChatOpenAI"),
        patch("src.agents.rd.ChatOpenAI"),
        patch("src.agents.data_analyst.ChatOpenAI"),
        patch("src.agents.customer_support.ChatOpenAI"),
        patch("src.agents.operations.ChatOpenAI"),
    ):
        from src.workflow.orchestrator import PriorityOrchestrator
        from src.agents.base import Message, MessageType, Priority
        from src.agents.base import AgentRole

        orch = PriorityOrchestrator()

        low_msg = Message(
            sender=AgentRole.CEO,
            recipient=AgentRole.CPO,
            message_type=MessageType.TASK_ASSIGNMENT,
            content={"task": {"task_id": "low", "title": "Low priority"}},
            priority=Priority.LOW,
        )

        high_msg = Message(
            sender=AgentRole.CEO,
            recipient=AgentRole.CPO,
            message_type=MessageType.TASK_ASSIGNMENT,
            content={"task": {"task_id": "high", "title": "High priority"}},
            priority=Priority.HIGH,
        )

        critical_msg = Message(
            sender=AgentRole.CEO,
            recipient=AgentRole.CPO,
            message_type=MessageType.TASK_ASSIGNMENT,
            content={"task": {"task_id": "critical", "title": "Critical"}},
            priority=Priority.CRITICAL,
        )

        orch.enqueue_message(low_msg)
        orch.enqueue_message(high_msg)
        orch.enqueue_message(critical_msg)

        stats = orch.get_queue_stats()
        assert stats["total_size"] == 3
        assert stats["by_priority"]["CRITICAL"] == 1
        assert stats["by_priority"]["HIGH"] == 1
        assert stats["by_priority"]["LOW"] == 1


@pytest.mark.asyncio
async def test_process_next_message():
    """Test processing messages from priority queue"""
    with (
        patch("src.agents.ceo.ChatOpenAI"),
        patch("src.agents.cto.ChatOpenAI"),
        patch("src.agents.cpo.ChatOpenAI"),
        patch("src.agents.cmo.ChatOpenAI"),
        patch("src.agents.cfo.ChatOpenAI"),
        patch("src.agents.hr.ChatOpenAI"),
        patch("src.agents.rd.ChatOpenAI"),
        patch("src.agents.data_analyst.ChatOpenAI"),
        patch("src.agents.customer_support.ChatOpenAI"),
        patch("src.agents.operations.ChatOpenAI"),
    ):
        from src.workflow.orchestrator import PriorityOrchestrator
        from src.agents.base import Message, MessageType, Priority
        from src.agents.base import AgentRole

        orch = PriorityOrchestrator()

        msg = Message(
            sender=AgentRole.CEO,
            recipient=AgentRole.OPERATIONS,
            message_type=MessageType.STATUS_REPORT,
            content={"status": "test"},
            priority=Priority.HIGH,
        )

        orch.enqueue_message(msg)

        result = await orch.process_next_message()
        assert result is not None
