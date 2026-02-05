package agents

import (
	"testing"
	"time"
)

// TestAgentRoleString 测试 AgentRole 的 String 方法
func TestAgentRoleString(t *testing.T) {
	tests := []struct {
		role     AgentRole
		expected string
	}{
		{AgentRoleCEO, "ceo"},
		{AgentRoleCTO, "cto"},
		{AgentRoleCPO, "cpo"},
		{AgentRoleCMO, "cmo"},
		{AgentRoleCFO, "cfo"},
		{AgentRoleHR, "hr"},
		{AgentRoleRD, "rd"},
		{AgentRoleDataAnalyst, "data_analyst"},
		{AgentRoleCustomerSupport, "customer_support"},
		{AgentRoleOperations, "operations"},
	}

	for _, tt := range tests {
		t.Run(string(tt.role), func(t *testing.T) {
			result := tt.role.String()
			if result != tt.expected {
				t.Errorf("AgentRole.String() = %s, want %s", result, tt.expected)
			}
		})
	}
}

// TestPriorityString 测试 Priority 的 String 方法
func TestPriorityString(t *testing.T) {
	tests := []struct {
		priority Priority
		expected string
	}{
		{PriorityLow, "low"},
		{PriorityMedium, "medium"},
		{PriorityHigh, "high"},
		{PriorityCritical, "critical"},
	}

	for _, tt := range tests {
		t.Run(tt.expected, func(t *testing.T) {
			result := tt.priority.String()
			if result != tt.expected {
				t.Errorf("Priority.String() = %s, want %s", result, tt.expected)
			}
		})
	}
}

// TestPriorityUnknown 测试未知优先级的 String 方法
func TestPriorityUnknown(t *testing.T) {
	p := Priority(100)
	result := p.String()
	if result != "unknown" {
		t.Errorf("Unknown priority.String() = %s, want unknown", result)
	}
}

// TestMessageTypeString 测试 MessageType 的 String 方法
func TestMessageTypeString(t *testing.T) {
	tests := []struct {
		msgType  MessageType
		expected string
	}{
		{MessageTypeTaskAssignment, "task_assignment"},
		{MessageTypeStatusReport, "status_report"},
		{MessageTypeDataRequest, "data_request"},
		{MessageTypeDataResponse, "data_response"},
		{MessageTypeApprovalRequest, "approval_request"},
		{MessageTypeApprovalResponse, "approval_response"},
		{MessageTypeAlert, "alert"},
		{MessageTypeCollaboration, "collaboration"},
	}

	for _, tt := range tests {
		t.Run(tt.expected, func(t *testing.T) {
			result := tt.msgType.String()
			if result != tt.expected {
				t.Errorf("MessageType.String() = %s, want %s", result, tt.expected)
			}
		})
	}
}

// TestMessageTypeUnknown 测试未知消息类型的 String 方法
func TestMessageTypeUnknown(t *testing.T) {
	m := MessageType(100)
	result := m.String()
	if result != "unknown" {
		t.Errorf("Unknown MessageType.String() = %s, want unknown", result)
	}
}

// TestMessageCreation 测试消息创建
func TestMessageCreation(t *testing.T) {
	now := time.Now()
	msg := &Message{
		Sender:      AgentRoleCTO,
		Receiver:    AgentRoleCEO,
		MessageType: MessageTypeTaskAssignment,
		Content: map[string]any{
			"task": "test task",
			"id":   123,
		},
		Priority:  PriorityHigh,
		Timestamp: now,
		MessageID: "msg-001",
	}

	if msg.Sender != AgentRoleCTO {
		t.Errorf("Sender = %s, want %s", msg.Sender, AgentRoleCTO)
	}
	if msg.Receiver != AgentRoleCEO {
		t.Errorf("Receiver = %s, want %s", msg.Receiver, AgentRoleCEO)
	}
	if msg.MessageType != MessageTypeTaskAssignment {
		t.Errorf("MessageType = %v, want %v", msg.MessageType, MessageTypeTaskAssignment)
	}
	if msg.Priority != PriorityHigh {
		t.Errorf("Priority = %v, want %v", msg.Priority, PriorityHigh)
	}
	if msg.MessageID != "msg-001" {
		t.Errorf("MessageID = %s, want msg-001", msg.MessageID)
	}
}

// TestTaskCreation 测试任务创建
func TestTaskCreation(t *testing.T) {
	deadline := time.Now().Add(24 * time.Hour)
	task := &Task{
		TaskID:       "task-001",
		Title:        "Test Task",
		Description:  "This is a test task",
		AssignedTo:   AgentRoleRD,
		AssignedBy:   AgentRoleCTO,
		Priority:     PriorityHigh,
		Status:       "pending",
		Dependencies: []string{"task-000"},
		Deliverables: []string{"code", "tests"},
		Deadline:     &deadline,
		CreatedAt:    time.Now(),
		UpdatedAt:    time.Now(),
		Metadata:     map[string]any{"key": "value"},
	}

	if task.TaskID != "task-001" {
		t.Errorf("TaskID = %s, want task-001", task.TaskID)
	}
	if task.AssignedTo != AgentRoleRD {
		t.Errorf("AssignedTo = %s, want %s", task.AssignedTo, AgentRoleRD)
	}
	if len(task.Dependencies) != 1 || task.Dependencies[0] != "task-000" {
		t.Errorf("Dependencies = %v, want [task-000]", task.Dependencies)
	}
}

// TestAgentStateCreation 测试 AgentState 创建
func TestAgentStateCreation(t *testing.T) {
	state := &AgentState{
		Role:               AgentRoleCEO,
		CurrentTasks:       make([]*Task, 0),
		CompletedTasks:     make([]*Task, 0),
		Messages:           make([]*Message, 0),
		PerformanceMetrics: make(map[string]float64),
		Capabilities:       []string{"strategy", "leadership"},
		Workload:           0.5,
		LastActive:         time.Now(),
	}

	if state.Role != AgentRoleCEO {
		t.Errorf("Role = %s, want %s", state.Role, AgentRoleCEO)
	}
	if len(state.Capabilities) != 2 {
		t.Errorf("Capabilities length = %d, want 2", len(state.Capabilities))
	}
	if state.Workload != 0.5 {
		t.Errorf("Workload = %f, want 0.5", state.Workload)
	}
}

// TestCreateEmptyState 测试创建空状态
func TestCreateEmptyState(t *testing.T) {
	state := CreateEmptyState()

	if state.Agents == nil {
		t.Error("Agents should not be nil")
	}
	if state.Tasks == nil {
		t.Error("Tasks should not be nil")
	}
	if state.Messages == nil {
		t.Error("Messages should not be nil")
	}
	if state.StrategicGoals == nil {
		t.Error("StrategicGoals should not be nil")
	}
	if state.KPIs == nil {
		t.Error("KPIs should not be nil")
	}
	if state.MarketData == nil {
		t.Error("MarketData should not be nil")
	}
	if state.UserFeedback == nil {
		t.Error("UserFeedback should not be nil")
	}

	// 验证初始状态
	if len(state.Agents) != 0 {
		t.Errorf("Initial Agents count = %d, want 0", len(state.Agents))
	}
	if len(state.Tasks) != 0 {
		t.Errorf("Initial Tasks count = %d, want 0", len(state.Tasks))
	}
	if len(state.Messages) != 0 {
		t.Errorf("Initial Messages count = %d, want 0", len(state.Messages))
	}
}

// TestCompanyStateWithData 测试带数据的 CompanyState
func TestCompanyStateWithData(t *testing.T) {
	state := CreateEmptyState()

	// 添加任务
	task := &Task{
		TaskID:    "task-001",
		Title:     "Test",
		Status:    "completed",
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}
	state.Tasks[task.TaskID] = task

	if len(state.Tasks) != 1 {
		t.Errorf("Tasks count = %d, want 1", len(state.Tasks))
	}

	// 添加 KPI
	state.KPIs["revenue"] = 100000.0
	if state.KPIs["revenue"] != 100000.0 {
		t.Errorf("KPI revenue = %f, want 100000.0", state.KPIs["revenue"])
	}
}

// TestAgentRoleConstants 测试所有 AgentRole 常量值
func TestAgentRoleConstants(t *testing.T) {
	// 验证枚举值的一致性
	if AgentRoleCEO != "ceo" {
		t.Errorf("AgentRoleCEO = %s, want ceo", AgentRoleCEO)
	}
	if AgentRoleCTO != "cto" {
		t.Errorf("AgentRoleCTO = %s, want cto", AgentRoleCTO)
	}
}

// TestPriorityValues 测试 Priority 枚举值
func TestPriorityValues(t *testing.T) {
	// 验证 iota 值
	if PriorityLow != 0 {
		t.Errorf("PriorityLow = %d, want 0", PriorityLow)
	}
	if PriorityMedium != 1 {
		t.Errorf("PriorityMedium = %d, want 1", PriorityMedium)
	}
	if PriorityHigh != 2 {
		t.Errorf("PriorityHigh = %d, want 2", PriorityHigh)
	}
	if PriorityCritical != 3 {
		t.Errorf("PriorityCritical = %d, want 3", PriorityCritical)
	}
}
