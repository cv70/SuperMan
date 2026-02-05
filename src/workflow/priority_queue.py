from enum import Enum
from typing import List, Tuple, Optional
from dataclasses import dataclass
import heapq
import time


class Priority(Enum):
    """优先级枚举"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    @property
    def weight(self) -> float:
        """Priority weight multiplier"""
        weights = {
            Priority.LOW: 1.0,
            Priority.MEDIUM: 2.0,
            Priority.HIGH: 3.0,
            Priority.CRITICAL: 4.0,
        }
        return weights[self]

    @property
    def timeout(self) -> int:
        """Default timeout in seconds"""
        timeouts = {
            Priority.LOW: 300,
            Priority.MEDIUM: 60,
            Priority.HIGH: 30,
            Priority.CRITICAL: 5,
        }
        return timeouts[self]

    @property
    def max_concurrent(self) -> int:
        """Maximum concurrent tasks"""
        limits = {
            Priority.LOW: 8,
            Priority.MEDIUM: 4,
            Priority.HIGH: 2,
            Priority.CRITICAL: 1,
        }
        return limits[self]


@dataclass
class QueueItem:
    """Priority queue item"""

    priority: Priority
    task_id: str
    payload: dict
    created_at: float = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()

    def __lt__(self, other):
        if self.priority.weight != other.priority.weight:
            return self.priority.weight > other.priority.weight
        return self.created_at < other.created_at


class PriorityQueue:
    """Priority queue for task scheduling"""

    def __init__(self):
        self._heap: List[QueueItem] = []
        self._items: dict = {}

    def push(self, item: QueueItem) -> None:
        """Add item to queue"""
        heapq.heappush(self._heap, item)
        self._items[item.task_id] = item

    def pop(self) -> Optional[QueueItem]:
        """Remove and return highest priority item"""
        if not self._heap:
            return None
        item = heapq.heappop(self._heap)
        del self._items[item.task_id]
        return item

    def peek(self) -> Optional[QueueItem]:
        """Return highest priority item without removing"""
        if not self._heap:
            return None
        return self._heap[0]

    def remove(self, task_id: str) -> Optional[QueueItem]:
        """Remove specific item by task_id"""
        if task_id not in self._items:
            return None
        item = self._items.pop(task_id)
        self._heap = [i for i in self._heap if i.task_id != task_id]
        heapq.heapify(self._heap)
        return item

    def __len__(self) -> int:
        return len(self._heap)

    def is_empty(self) -> bool:
        return len(self._heap) == 0

    def get_by_priority(self, priority: Priority) -> List[QueueItem]:
        """Get all items with given priority"""
        return [item for item in self._heap if item.priority == priority]
