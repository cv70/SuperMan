package scheduler

import (
	"sync"

	"superman/ds"
	"superman/state"
)

type AutoScheduler struct {
	mu          sync.RWMutex
	taskQueues  map[string]*TaskQueue
	agentStates map[string]*state.AgentState
}

func NewAutoScheduler() *AutoScheduler {
	return &AutoScheduler{
		taskQueues: map[string]*TaskQueue{
			PriorityCritical: NewTaskQueue(),
			PriorityHigh:     NewTaskQueue(),
			PriorityMedium:   NewTaskQueue(),
			PriorityLow:      NewTaskQueue(),
		},
		agentStates: make(map[string]*state.AgentState),
	}
}

func (s *AutoScheduler) AddTask(task *ds.Task, priority string) {
	queue := s.taskQueues[priority]
	if queue == nil {
		queue = NewTaskQueue()
		s.taskQueues[priority] = queue
	}

	// 直接使用 ds.Task，不需要转换
	queue.Enqueue(task)
}

func (s *AutoScheduler) GetTask() *ds.Task {
	priorities := []string{PriorityCritical, PriorityHigh, PriorityMedium, PriorityLow}
	for _, priority := range priorities {
		queue := s.taskQueues[priority]
		if queue != nil && !queue.IsEmpty() {
			task := queue.Dequeue()
			if task != nil {
				return task
			}
		}
	}
	return nil
}

func (s *AutoScheduler) AddAgent(agentName string, maxTasks int) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.agentStates[agentName] = state.NewAgentState(agentName)
	s.agentStates[agentName].SetMaxTasks(maxTasks)
}

func (s *AutoScheduler) UpdateAgentTaskCount(agentName string, count int) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if agentState, exists := s.agentStates[agentName]; exists {
		for len(agentState.GetCurrentTasks()) > count {
			// 移除多余的任務
			tasks := agentState.GetCurrentTasks()
			if len(tasks) > 0 {
				agentState.CompleteTask(tasks[0])
			}
		}
	}
}

func (s *AutoScheduler) GetAgentTaskCount(agentName string) int {
	s.mu.RLock()
	defer s.mu.RUnlock()
	if agentState, exists := s.agentStates[agentName]; exists {
		return len(agentState.GetCurrentTasks())
	}
	return 0
}

func (s *AutoScheduler) GetAgentMaxTasks(agentName string) int {
	s.mu.RLock()
	defer s.mu.RUnlock()
	if agentState, exists := s.agentStates[agentName]; exists {
		return agentState.GetMaxTasks()
	}
	return 3
}

func (s *AutoScheduler) GetQueueLength() int {
	total := 0
	for _, queue := range s.taskQueues {
		total += queue.Len()
	}
	return total
}

func (s *AutoScheduler) GetQueueLengthByPriority(priority string) int {
	queue := s.taskQueues[priority]
	if queue != nil {
		return queue.Len()
	}
	return 0
}
