package workflow

import (
	"sync"
	"time"

	"superman/agents"
)

type StateManager interface {
	CreateAgentState(role agents.AgentRole)
	GetTimestamp() time.Time
	GetHealthReport() map[string]any
	GetState() *agents.CompanyState
	AddMessage(msg *agents.Message)
	AddTask(task *agents.Task)
}

type stateManagerImpl struct {
	mu     sync.RWMutex
	state  *agents.CompanyState
	agents map[agents.AgentRole]*agents.AgentState
}

func NewStateManager(initialState *agents.CompanyState) StateManager {
	sm := &stateManagerImpl{
		state:  initialState,
		agents: make(map[agents.AgentRole]*agents.AgentState),
	}

	for _, role := range []agents.AgentRole{
		agents.AgentRoleCEO,
		agents.AgentRoleCTO,
		agents.AgentRoleCPO,
		agents.AgentRoleCMO,
		agents.AgentRoleCFO,
		agents.AgentRoleHR,
		agents.AgentRoleRD,
		agents.AgentRoleDataAnalyst,
		agents.AgentRoleCustomerSupport,
		agents.AgentRoleOperations,
	} {
		sm.CreateAgentState(role)
	}

	return sm
}

func (s *stateManagerImpl) CreateAgentState(role agents.AgentRole) {
	s.mu.Lock()
	defer s.mu.Unlock()

	if _, exists := s.agents[role]; !exists {
		s.agents[role] = &agents.AgentState{
			Role:               role,
			CurrentTasks:       make([]*agents.Task, 0),
			CompletedTasks:     make([]*agents.Task, 0),
			Messages:           make([]*agents.Message, 0),
			PerformanceMetrics: make(map[string]float64),
			Capabilities:       make([]string, 0),
			Workload:           0,
			LastActive:         time.Now(),
		}
		s.state.Agents[role] = s.agents[role]
	}
}

func (s *stateManagerImpl) GetTimestamp() time.Time {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return s.state.CurrentTime
}

func (s *stateManagerImpl) GetState() *agents.CompanyState {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return s.state
}

func (s *stateManagerImpl) AddMessage(msg *agents.Message) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.state.Messages = append(s.state.Messages, msg)
}

func (s *stateManagerImpl) AddTask(task *agents.Task) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.state.Tasks[task.TaskID] = task
}

func (s *stateManagerImpl) GetHealthReport() map[string]any {
	s.mu.RLock()
	defer s.mu.RUnlock()

	agentsMap := make(map[string]AgentStatus)
	for role, agentState := range s.state.Agents {
		agentsMap[string(role)] = AgentStatus{
			Role:           string(role),
			TaskCount:      len(agentState.CurrentTasks),
			CompletedCount: len(agentState.CompletedTasks),
			MessageCount:   len(agentState.Messages),
			Workload:       agentState.Workload,
		}
	}

	return map[string]any{
		"agents":         agentsMap,
		"total_tasks":    len(s.state.Tasks),
		"total_messages": len(s.state.Messages),
		"current_time":   s.state.CurrentTime,
	}
}

type AgentStatus struct {
	Role           string  `json:"role"`
	TaskCount      int     `json:"task_count"`
	CompletedCount int     `json:"completed_count"`
	MessageCount   int     `json:"message_count"`
	Workload       float64 `json:"workload"`
}
