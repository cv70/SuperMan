package scheduler

import (
	"superman/ds"
	"sync"
	"time"
)

const (
	PriorityCritical = "Critical"
	PriorityHigh     = "High"
	PriorityMedium   = "Medium"
	PriorityLow      = "Low"
)

var PriorityValue = map[string]int{
	PriorityCritical: 0,
	PriorityHigh:     1,
	PriorityMedium:   2,
	PriorityLow:      3,
}

type TaskQueue struct {
	mu       sync.Mutex
	queue    []*ds.Task
	lastTime map[string]time.Time
}

func NewTaskQueue() *TaskQueue {
	return &TaskQueue{
		queue:    make([]*ds.Task, 0),
		lastTime: make(map[string]time.Time),
	}
}

func (q *TaskQueue) Enqueue(task *ds.Task) {
	q.mu.Lock()
	defer q.mu.Unlock()

	q.queue = append(q.queue, task)
	q.lastTime[string(task.Priority)] = time.Now()
}

func (q *TaskQueue) Dequeue() *ds.Task {
	q.mu.Lock()
	defer q.mu.Unlock()

	if len(q.queue) == 0 {
		return nil
	}

	q.sortByPriority()
	task := q.queue[0]
	q.queue = q.queue[1:]

	return task
}

func (q *TaskQueue) Peek() *ds.Task {
	q.mu.Lock()
	defer q.mu.Unlock()

	if len(q.queue) == 0 {
		return nil
	}

	q.sortByPriority()
	return q.queue[0]
}

func (q *TaskQueue) Len() int {
	q.mu.Lock()
	defer q.mu.Unlock()
	return len(q.queue)
}

func (q *TaskQueue) IsEmpty() bool {
	q.mu.Lock()
	defer q.mu.Unlock()
	return len(q.queue) == 0
}

func (q *TaskQueue) GetByPriority(priority string) *ds.Task {
	q.mu.Lock()
	defer q.mu.Unlock()

	for i, task := range q.queue {
		if string(task.Priority) == priority {
			q.queue = append(q.queue[:i], q.queue[i+1:]...)
			q.lastTime[priority] = time.Now()
			return task
		}
	}

	return nil
}

func (q *TaskQueue) sortByPriority() {
	for i := 0; i < len(q.queue); i++ {
		for j := i + 1; j < len(q.queue); j++ {
			priI := PriorityValue[string(q.queue[i].Priority)]
			priJ := PriorityValue[string(q.queue[j].Priority)]
			if priI > priJ {
				q.queue[i], q.queue[j] = q.queue[j], q.queue[i]
			}
		}
	}
}
