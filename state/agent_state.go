package state

import (
	"superman/ds"
	"time"
)

// AgentExecutionHistory 代表单个智能体的执行历史记录
type AgentExecutionHistory struct {
	ExecutionID  string         `json:"execution_id"`
	Timestamp    time.Time      `json:"timestamp"`
	TaskID       string         `json:"task_id"`
	MessageID    string         `json:"message_id"`
	Action       string         `json:"action"`
	Input        map[string]any `json:"input"`
	Output       map[string]any `json:"output"`
	Status       string         `json:"status"`
	Duration     time.Duration  `json:"duration"`
	ErrorMessage string         `json:"error_message,omitempty"`
	Dependencies []string       `json:"dependencies,omitempty"`
	Metadata     map[string]any `json:"metadata,omitempty"`
}

// AgentState 代表单个智能体的状态
type AgentState struct {
	Name               string                   `json:"name"`
	CurrentTasks       []*ds.Task               `json:"current_tasks"`
	CompletedTasks     []*ds.Task               `json:"completed_tasks"`
	Messages           []*ds.Message            `json:"messages"`
	PerformanceMetrics map[string]float64       `json:"performance_metrics"`
	Workload           float64                  `json:"workload"`
	LastActive         time.Time                `json:"last_active"`
	ExecutionHistory   []*AgentExecutionHistory `json:"execution_history"`
	MaxTasks           int                      `json:"max_tasks"`
}

// NewAgentState 创建新的 AgentState 实例
func NewAgentState(name string) *AgentState {
	return &AgentState{
		Name:               name,
		CurrentTasks:       make([]*ds.Task, 0),
		CompletedTasks:     make([]*ds.Task, 0),
		Messages:           make([]*ds.Message, 0),
		PerformanceMetrics: make(map[string]float64),
		Workload:           0,
		LastActive:         time.Now(),
		ExecutionHistory:   make([]*AgentExecutionHistory, 0),
		MaxTasks:           3,
	}
}

// GetMaxTasks 获取最大任务数
func (s *AgentState) GetMaxTasks() int {
	return s.MaxTasks
}

// SetMaxTasks 设置最大任务数
func (s *AgentState) SetMaxTasks(maxTasks int) {
	s.MaxTasks = maxTasks
}

// ==================== Getters ====================

// GetName 获取智能体名称
func (s *AgentState) GetName() string {
	return s.Name
}

// GetCurrentTasks 获取当前任务列表
func (s *AgentState) GetCurrentTasks() []*ds.Task {
	return s.CurrentTasks
}

// GetCompletedTasks 获取已完成任务列表
func (s *AgentState) GetCompletedTasks() []*ds.Task {
	return s.CompletedTasks
}

// GetMessages 获取消息历史
func (s *AgentState) GetMessages() []*ds.Message {
	return s.Messages
}

// GetPerformanceMetrics 获取性能指标
func (s *AgentState) GetPerformanceMetrics() map[string]float64 {
	return s.PerformanceMetrics
}

// GetWorkload 获取工作负载
func (s *AgentState) GetWorkload() float64 {
	return s.Workload
}

// GetLastActive 获取最后活跃时间
func (s *AgentState) GetLastActive() time.Time {
	return s.LastActive
}

// GetExecutionHistory 获取执行历史
func (s *AgentState) GetExecutionHistory() []*AgentExecutionHistory {
	return s.ExecutionHistory
}

// AddExecutionHistory 添加执行历史
func (s *AgentState) AddExecutionHistory(history *AgentExecutionHistory) {
	s.ExecutionHistory = append(s.ExecutionHistory, history)
}

// GetExecutionHistoryByTaskID 根据任务ID获取执行历史
func (s *AgentState) GetExecutionHistoryByTaskID(taskID string) []*AgentExecutionHistory {
	var result []*AgentExecutionHistory
	for _, h := range s.ExecutionHistory {
		if h.TaskID == taskID {
			result = append(result, h)
		}
	}
	return result
}

// GetExecutionHistoryByTimeRange 根据时间范围获取执行历史
func (s *AgentState) GetExecutionHistoryByTimeRange(start, end time.Time) []*AgentExecutionHistory {
	var result []*AgentExecutionHistory
	for _, h := range s.ExecutionHistory {
		if h.Timestamp.After(start) && h.Timestamp.Before(end) {
			result = append(result, h)
		}
	}
	return result
}

// GetRecentExecutions 获取最近的执行记录
func (s *AgentState) GetRecentExecutions(count int) []*AgentExecutionHistory {
	if count <= 0 {
		return []*AgentExecutionHistory{}
	}

	total := len(s.ExecutionHistory)
	if total == 0 {
		return []*AgentExecutionHistory{}
	}

	start := total - count
	if start < 0 {
		start = 0
	}

	result := make([]*AgentExecutionHistory, total-start)
	copy(result, s.ExecutionHistory[start:])
	return result
}

// ==================== Setters ====================
// SetLastActive 设置最后活跃时间
func (s *AgentState) SetLastActive(t time.Time) {
	s.LastActive = t
}

// ==================== State Update Methods ====================

// AddTask 添加任务到当前任务列表
func (s *AgentState) AddTask(task *ds.Task) {
	s.CurrentTasks = append(s.CurrentTasks, task)
	s.Workload = float64(len(s.CurrentTasks))
	s.LastActive = time.Now()
}

// CompleteTask 完成任务，从当前任务移动到完成列表
func (s *AgentState) CompleteTask(task *ds.Task) {
	for i, t := range s.CurrentTasks {
		if t.ID == task.ID {
			// 从当前任务移除
			s.CurrentTasks = append(s.CurrentTasks[:i], s.CurrentTasks[i+1:]...)
			// 添加到完成任务
			s.CompletedTasks = append(s.CompletedTasks, task)
			s.Workload = float64(len(s.CurrentTasks))
			s.LastActive = time.Now()
			break
		}
	}
}

// AddMessage 添加消息到消息历史
func (s *AgentState) AddMessage(msg *ds.Message) {
	s.Messages = append(s.Messages, msg)
	s.LastActive = time.Now()
}

// UpdateMetric 更新性能指标
func (s *AgentState) UpdateMetric(key string, value float64) {
	s.PerformanceMetrics[key] = value
	s.LastActive = time.Time{}
}

// ==================== State Query Methods ====================

// GetPendingTasks 获取待处理任务数量
func (s *AgentState) GetPendingTasks() int {
	return len(s.CurrentTasks)
}

// GetCompletedCount 获取已完成任务数量
func (s *AgentState) GetCompletedCount() int {
	return len(s.CompletedTasks)
}

// GetTotalTasks 获取总任务数量
func (s *AgentState) GetTotalTasks() int {
	return len(s.CurrentTasks) + len(s.CompletedTasks)
}

// GetPerformance 获取性能指标
func (s *AgentState) GetPerformance() map[string]float64 {
	return s.PerformanceMetrics
}

// GetTaskByID 根据 ID 获取任务
func (s *AgentState) GetTaskByID(taskID string) *ds.Task {
	// 先搜索当前任务
	for _, t := range s.CurrentTasks {
		if t.ID == taskID {
			return t
		}
	}
	// 再搜索完成任务
	for _, t := range s.CompletedTasks {
		if t.ID == taskID {
			return t
		}
	}
	return nil
}

// HasTask 检查是否包含特定任务
func (s *AgentState) HasTask(taskID string) bool {
	return s.GetTaskByID(taskID) != nil
}

// ClearCompleted 清空已完成任务列表
func (s *AgentState) ClearCompleted() {
	s.CompletedTasks = make([]*ds.Task, 0)
}

// ClearCurrent 清空当前任务列表
func (s *AgentState) ClearCurrent() {
	s.CurrentTasks = make([]*ds.Task, 0)
	s.Workload = 0
}

// ClearAll 清空所有任务
func (s *AgentState) ClearAll() {
	s.CurrentTasks = make([]*ds.Task, 0)
	s.CompletedTasks = make([]*ds.Task, 0)
	s.Workload = 0
}
