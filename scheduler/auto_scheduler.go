package scheduler

import (
	"sync"
	"time"

	"superman/types"
)

type AutoScheduler struct {
	mu          sync.RWMutex
	taskQueues  map[string]*TaskQueue
	agentStates map[string]*AgentState
}

type AgentState struct {
	Name         string
	CurrentTasks int
	MaxTasks     int
	LastActive   time.Time
}

func NewAutoScheduler() *AutoScheduler {
	return &AutoScheduler{
		taskQueues: map[string]*TaskQueue{
			PriorityCritical: NewTaskQueue(),
			PriorityHigh:     NewTaskQueue(),
			PriorityMedium:   NewTaskQueue(),
			PriorityLow:      NewTaskQueue(),
		},
		agentStates: make(map[string]*AgentState),
	}
}

func (s *AutoScheduler) AddTask(task *types.Task, priority string) {
	queue := s.taskQueues[priority]
	if queue == nil {
		queue = NewTaskQueue()
		s.taskQueues[priority] = queue
	}

	metaPriority := PriorityLow
	if task.Metadata != nil {
		if p, ok := task.Metadata["priority"]; ok {
			if str, ok := p.(string); ok {
				metaPriority = str
			}
		}
	}

	queue.Enqueue(&Task{
		ID:         task.TaskID,
		Title:      task.Title,
		AssignedTo: task.AssignedTo,
		Status:     task.Status,
		Priority:   metaPriority,
		CreatedAt:  task.CreatedAt,
		Metadata:   task.Metadata,
	})
}

func (s *AutoScheduler) GetTask() *types.Task {
	priorities := []string{PriorityCritical, PriorityHigh, PriorityMedium, PriorityLow}
	for _, priority := range priorities {
		queue := s.taskQueues[priority]
		if queue != nil && !queue.IsEmpty() {
			task := queue.Dequeue()
			if task != nil {
				return &types.Task{
					TaskID:      task.ID,
					Title:       task.Title,
					AssignedTo:  task.AssignedTo,
					Status:      task.Status,
					Metadata:    task.Metadata,
					CreatedAt:   task.CreatedAt,
				}
			}
		}
	}
	return nil
}

func (s *AutoScheduler) AddAgent(agentName string, maxTasks int) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.agentStates[agentName] = &AgentState{
		Name:       agentName,
		MaxTasks:   maxTasks,
		LastActive: time.Now(),
	}
}

func (s *AutoScheduler) UpdateAgentTaskCount(agentName string, count int) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if state, exists := s.agentStates[agentName]; exists {
		state.CurrentTasks = count
	}
}

func (s *AutoScheduler) GetAgentTaskCount(agentName string) int {
	s.mu.RLock()
	defer s.mu.RUnlock()
	if state, exists := s.agentStates[agentName]; exists {
		return state.CurrentTasks
	}
	return 0
}

func (s *AutoScheduler) GetAgentMaxTasks(agentName string) int {
	s.mu.RLock()
	defer s.mu.RUnlock()
	if state, exists := s.agentStates[agentName]; exists {
		return state.MaxTasks
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
