package mailbox

import (
	"container/heap"
	"sync"
	"time"

	"superman/agents"
)

// internalQueue 内部队列（无锁，仅供PriorityQueue内部使用）
type internalQueue struct {
	items []*PriorityQueueItem
}

func (iq *internalQueue) Len() int { return len(iq.items) }

func (iq *internalQueue) Less(i, j int) bool {
	// 首先比较Priority（数值越大优先级越高）
	if iq.items[i].Message.Priority != iq.items[j].Message.Priority {
		return iq.items[i].Message.Priority > iq.items[j].Message.Priority
	}
	// 优先级相同，按时间先后（先到的在前）
	return iq.items[i].EnqueuedAt.Before(iq.items[j].EnqueuedAt)
}

func (iq *internalQueue) Swap(i, j int) {
	iq.items[i], iq.items[j] = iq.items[j], iq.items[i]
	iq.items[i].Index = i
	iq.items[j].Index = j
}

func (iq *internalQueue) Push(x interface{}) {
	item := x.(*PriorityQueueItem)
	item.Index = len(iq.items)
	iq.items = append(iq.items, item)
}

func (iq *internalQueue) Pop() interface{} {
	old := iq.items
	n := len(old)
	item := old[n-1]
	old[n-1] = nil
	item.Index = -1
	iq.items = old[0 : n-1]
	return item
}

// PriorityQueueItem 优先级队列项
type PriorityQueueItem struct {
	Message    *Message
	Index      int
	EnqueuedAt time.Time
}

// PriorityQueue 优先级队列（最小堆）
type PriorityQueue struct {
	mu    sync.RWMutex
	items []*PriorityQueueItem
}

// NewPriorityQueue 创建新的优先级队列
func NewPriorityQueue() *PriorityQueue {
	return &PriorityQueue{
		items: make([]*PriorityQueueItem, 0),
	}
}

// Len 返回队列长度
func (pq *PriorityQueue) Len() int {
	pq.mu.RLock()
	defer pq.mu.RUnlock()
	return len(pq.items)
}

// Enqueue 入队
func (pq *PriorityQueue) Enqueue(msg *Message) {
	pq.mu.Lock()
	defer pq.mu.Unlock()

	// 使用内部队列进行堆操作
	iq := &internalQueue{items: pq.items}

	item := &PriorityQueueItem{
		Message:    msg,
		EnqueuedAt: time.Now(),
	}
	heap.Push(iq, item)

	pq.items = iq.items
}

// Dequeue 出队
func (pq *PriorityQueue) Dequeue() *Message {
	pq.mu.Lock()
	defer pq.mu.Unlock()

	if len(pq.items) == 0 {
		return nil
	}

	// 使用内部队列进行堆操作
	iq := &internalQueue{items: pq.items}

	item := heap.Pop(iq).(*PriorityQueueItem)

	pq.items = iq.items

	return item.Message
}

// Peek 查看最高优先级元素（不出队）
func (pq *PriorityQueue) Peek() *Message {
	pq.mu.RLock()
	defer pq.mu.RUnlock()

	if len(pq.items) == 0 {
		return nil
	}

	return pq.items[0].Message
}

// RemoveByMessageID 根据消息ID移除消息
func (pq *PriorityQueue) RemoveByMessageID(messageID string) bool {
	pq.mu.Lock()
	defer pq.mu.Unlock()

	for i, item := range pq.items {
		if item.Message.MessageID == messageID {
			iq := &internalQueue{items: pq.items}
			heap.Remove(iq, i)
			pq.items = iq.items
			return true
		}
	}
	return false
}

// GetByPriority 获取指定优先级的消息数量
func (pq *PriorityQueue) GetByPriority(priority agents.Priority) int {
	pq.mu.RLock()
	defer pq.mu.RUnlock()

	count := 0
	for _, item := range pq.items {
		if item.Message.Priority == priority {
			count++
		}
	}
	return count
}

// GetAll 获取所有消息（不改变队列）
func (pq *PriorityQueue) GetAll() []*Message {
	pq.mu.RLock()
	defer pq.mu.RUnlock()

	result := make([]*Message, len(pq.items))
	for i, item := range pq.items {
		result[i] = item.Message
	}
	return result
}

// Clear 清空队列
func (pq *PriorityQueue) Clear() {
	pq.mu.Lock()
	defer pq.mu.Unlock()

	pq.items = pq.items[:0]
}
