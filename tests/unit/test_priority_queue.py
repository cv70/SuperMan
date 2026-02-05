import time
from src.workflow.priority_queue import Priority, QueueItem, PriorityQueue


def test_priority_enum_values():
    """Test Priority enum has correct values and weights"""
    assert Priority.LOW.value == "low"
    assert Priority.LOW.weight == 1.0
    assert Priority.LOW.timeout == 300
    assert Priority.LOW.max_concurrent == 8

    assert Priority.CRITICAL.value == "critical"
    assert Priority.CRITICAL.weight == 4.0
    assert Priority.CRITICAL.timeout == 5
    assert Priority.CRITICAL.max_concurrent == 1


def test_queue_item_comparison():
    """Test QueueItem sorts by priority"""
    item_low = QueueItem(priority=Priority.LOW, task_id="task1", payload={})
    item_high = QueueItem(priority=Priority.HIGH, task_id="task2", payload={})
    item_critical = QueueItem(priority=Priority.CRITICAL, task_id="task3", payload={})

    assert item_critical < item_high
    assert item_high < item_low


def test_priority_queue_operations():
    """Test basic queue operations"""
    pq = PriorityQueue()

    item1 = QueueItem(priority=Priority.LOW, task_id="task1", payload={"data": 1})
    item2 = QueueItem(priority=Priority.CRITICAL, task_id="task2", payload={"data": 2})
    item3 = QueueItem(priority=Priority.MEDIUM, task_id="task3", payload={"data": 3})

    pq.push(item1)
    pq.push(item2)
    pq.push(item3)

    assert len(pq) == 3
    assert pq.is_empty() is False

    # Should pop highest priority first
    first = pq.pop()
    assert first.priority == Priority.CRITICAL
    assert first.task_id == "task2"

    assert len(pq) == 2

    # Peek should not remove
    peeked = pq.peek()
    assert peeked.priority == Priority.MEDIUM
    assert len(pq) == 2

    # Pop remaining
    second = pq.pop()
    assert second.priority == Priority.MEDIUM
    third = pq.pop()
    assert third.priority == Priority.LOW

    assert pq.is_empty() is True
