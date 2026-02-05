package agents

import (
	"sync"
	"time"
)

type Agent interface {
	GetRole() AgentRole
	GetName() string
	SetName(name string)
	GetState() *AgentState
	UpdateState(updater func(*AgentState))
	ProcessMessage(msg *Message) error
	GenerateResponse(task *Task) (*Message, error)
	GetCapabilities() []string
	GetRoleHierarchy() int
	GetWorkload() float64
}

type BaseAgentImpl struct {
	mu                 sync.RWMutex
	role               AgentRole
	name               string
	currentTasks       []*Task
	completedTasks     []*Task
	messages           []*Message
	performanceMetrics map[string]float64
	capabilities       []string
	workload           float64
	lastActive         time.Time
	taskCount          int
	roleHierarchy      int
}

func NewBaseAgent(role AgentRole, capabilities []string, hierarchy int) *BaseAgentImpl {
	return &BaseAgentImpl{
		role:               role,
		name:               role.String(),
		currentTasks:       make([]*Task, 0),
		completedTasks:     make([]*Task, 0),
		messages:           make([]*Message, 0),
		performanceMetrics: make(map[string]float64),
		capabilities:       capabilities,
		lastActive:         time.Now(),
		roleHierarchy:      hierarchy,
	}
}

func (a *BaseAgentImpl) GetRole() AgentRole {
	a.mu.RLock()
	defer a.mu.RUnlock()
	return a.role
}

func (a *BaseAgentImpl) GetName() string {
	return a.name
}

func (a *BaseAgentImpl) SetName(name string) {
	a.name = name
}

func (a *BaseAgentImpl) GetState() *AgentState {
	a.mu.RLock()
	defer a.mu.RUnlock()
	return &AgentState{
		Role:               a.role,
		CurrentTasks:       a.currentTasks,
		CompletedTasks:     a.completedTasks,
		Messages:           a.messages,
		PerformanceMetrics: a.performanceMetrics,
		Capabilities:       a.capabilities,
		Workload:           a.workload,
		LastActive:         a.lastActive,
	}
}

func (a *BaseAgentImpl) UpdateState(updater func(*AgentState)) {
	a.mu.Lock()
	defer a.mu.Unlock()
	updater(&AgentState{
		Role:               a.role,
		CurrentTasks:       a.currentTasks,
		CompletedTasks:     a.completedTasks,
		Messages:           a.messages,
		PerformanceMetrics: a.performanceMetrics,
		Capabilities:       a.capabilities,
		Workload:           a.workload,
		LastActive:         a.lastActive,
	})
}

func (a *BaseAgentImpl) ProcessMessage(msg *Message) error {
	a.mu.Lock()
	defer a.mu.Unlock()
	a.messages = append(a.messages, msg)
	a.lastActive = time.Now()
	return nil
}

func (a *BaseAgentImpl) GenerateResponse(task *Task) (*Message, error) {
	a.mu.Lock()
	defer a.mu.Unlock()
	response := &Message{
		Sender:      a.role,
		MessageType: MessageTypeStatusReport,
		Content: map[string]any{
			"task_id":    task.TaskID,
			"status":     "in_progress",
			"updated_at": time.Now(),
		},
		Priority:  PriorityMedium,
		Timestamp: time.Now(),
		MessageID: "",
	}
	a.messages = append(a.messages, response)
	return response, nil
}

func (a *BaseAgentImpl) GetCapabilities() []string {
	a.mu.RLock()
	defer a.mu.RUnlock()
	return a.capabilities
}

func (a *BaseAgentImpl) GetRoleHierarchy() int {
	a.mu.RLock()
	defer a.mu.RUnlock()
	return a.roleHierarchy
}

func (a *BaseAgentImpl) GetWorkload() float64 {
	a.mu.RLock()
	defer a.mu.RUnlock()
	return a.workload
}

func (a *BaseAgentImpl) CompleteTask(task *Task) {
	a.mu.Lock()
	defer a.mu.Unlock()
	a.completedTasks = append(a.completedTasks, task)
	for i, t := range a.currentTasks {
		if t.TaskID == task.TaskID {
			a.currentTasks = append(a.currentTasks[:i], a.currentTasks[i+1:]...)
			break
		}
	}
	a.workload = float64(len(a.currentTasks))
}
