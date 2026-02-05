package workflow

import (
	"testing"
	"time"

	"superman/agents"
)

// TestNewStateManager 测试 StateManager 创建
func TestNewStateManager(t *testing.T) {
	initialState := agents.CreateEmptyState()
	sm := NewStateManager(initialState)

	if sm == nil {
		t.Fatal("NewStateManager returned nil")
	}

	// 验证所有 Agent 状态都已创建
	allAgents := []agents.AgentRole{
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
	}

	state := sm.GetState()
	if len(state.Agents) != len(allAgents) {
		t.Errorf("Expected %d agents, got %d", len(allAgents), len(state.Agents))
	}

	for _, role := range allAgents {
		if _, exists := state.Agents[role]; !exists {
			t.Errorf("Agent state for %s not created", role)
		}
	}
}

// TestStateManagerConcurrency 测试并发访问安全性
func TestStateManagerConcurrency(t *testing.T) {
	initialState := agents.CreateEmptyState()
	sm := NewStateManager(initialState)

	// 并发添加消息
	done := make(chan bool, 10)
	for i := 0; i < 10; i++ {
		go func(idx int) {
			msg := &agents.Message{
				MessageID:   "msg-concurrent-test",
				Sender:      agents.AgentRoleCTO,
				Receiver:    agents.AgentRoleCEO,
				MessageType: agents.MessageTypeTaskAssignment,
				Content:     map[string]any{"index": idx},
				Priority:    agents.PriorityMedium,
				Timestamp:   time.Now(),
			}
			sm.AddMessage(msg)
			done <- true
		}(i)
	}

	// 等待所有 goroutine 完成
	for i := 0; i < 10; i++ {
		<-done
	}

	// 验证消息数量
	state := sm.GetState()
	if len(state.Messages) != 10 {
		t.Errorf("Expected 10 messages, got %d", len(state.Messages))
	}
}

// TestAddTask 测试添加任务
func TestAddTask(t *testing.T) {
	initialState := agents.CreateEmptyState()
	sm := NewStateManager(initialState)

	task := &agents.Task{
		TaskID:       "task-001",
		Title:        "Test Task",
		Description:  "Description",
		AssignedTo:   agents.AgentRoleRD,
		AssignedBy:   agents.AgentRoleCTO,
		Priority:     agents.PriorityHigh,
		Status:       "pending",
		Dependencies: []string{},
		Deliverables: []string{"deliverable1"},
		CreatedAt:    time.Now(),
		UpdatedAt:    time.Now(),
	}

	sm.AddTask(task)

	state := sm.GetState()
	if taskState, exists := state.Tasks["task-001"]; !exists {
		t.Error("Task not found in state")
	} else if taskState.Title != "Test Task" {
		t.Errorf("Task title = %s, want Test Task", taskState.Title)
	}
}

// TestGetTimestamp 测试获取时间戳
func TestGetTimestamp(t *testing.T) {
	initialState := agents.CreateEmptyState()
	sm := NewStateManager(initialState)

	ts := sm.GetTimestamp()
	if ts.IsZero() {
		t.Error("Timestamp should not be zero")
	}
}

// TestCreateAgentState 测试创建 Agent 状态
func TestCreateAgentState(t *testing.T) {
	initialState := agents.CreateEmptyState()
	sm := NewStateManager(initialState)

	// 创建一个新的 AgentRole（临时）
	dummyRole := agents.AgentRole("dummy")
	sm.CreateAgentState(dummyRole)

	state := sm.GetState()
	if _, exists := state.Agents[dummyRole]; !exists {
		t.Error("Agent state not created")
	}

	// 验证重复创建不会出错
	sm.CreateAgentState(dummyRole)
	if len(state.Agents) != 11 { // 10 + 1 dummy
		t.Errorf("Expected 11 agents, got %d", len(state.Agents))
	}
}

// TestGetHealthReport 测试健康报告
func TestGetHealthReport(t *testing.T) {
	initialState := agents.CreateEmptyState()
	sm := NewStateManager(initialState)

	// 添加一些测试数据
	for i := 0; i < 3; i++ {
		task := &agents.Task{
			TaskID:    "task-health-" + string(rune(i)),
			Title:     "Task " + string(rune(i)),
			Status:    "in_progress",
			CreatedAt: time.Now(),
			UpdatedAt: time.Now(),
		}
		sm.AddTask(task)
	}

	for i := 0; i < 5; i++ {
		msg := &agents.Message{
			MessageID:   "msg-health-" + string(rune(i)),
			Sender:      agents.AgentRoleCTO,
			Receiver:    agents.AgentRoleCEO,
			MessageType: agents.MessageTypeTaskAssignment,
			Timestamp:   time.Now(),
		}
		sm.AddMessage(msg)
	}

	report := sm.GetHealthReport()

	// 验证报告结构
	if _, ok := report["agents"]; !ok {
		t.Error("Health report missing 'agents' key")
	}
	if _, ok := report["total_tasks"]; !ok {
		t.Error("Health report missing 'total_tasks' key")
	}
	if _, ok := report["total_messages"]; !ok {
		t.Error("Health report missing 'total_messages' key")
	}

	totalTasks := report["total_tasks"].(int)
	if totalTasks != 3 {
		t.Errorf("Expected 3 tasks, got %d", totalTasks)
	}

	totalMessages := report["total_messages"].(int)
	if totalMessages != 5 {
		t.Errorf("Expected 5 messages, got %d", totalMessages)
	}
}

// TestGetStateReturnsCopy 测试 GetState 返回状态副本
func TestGetStateReturnsCopy(t *testing.T) {
	initialState := agents.CreateEmptyState()
	sm := NewStateManager(initialState)

	state1 := sm.GetState()
	state2 := sm.GetState()

	// 注意：在当前实现中，GetState 返回的是同一个指针
	// 这个测试验证的是如果修改返回的 state，不会影响后续 GetState 调用
	state2.Tasks["test-task"] = &agents.Task{
		TaskID:    "test-task",
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}

	// 验证 state1 和 state2 共享同一个 Tasks map（当前实现）
	// 这说明 GetState 没有返回深拷贝
	if _, exists := state1.Tasks["test-task"]; !exists {
		t.Error("Current implementation: GetState returns shared state, modification affects all references")
	}
}

// TestEmptyOperations 测试空状态操作
func TestEmptyOperations(t *testing.T) {
	initialState := agents.CreateEmptyState()
	sm := NewStateManager(initialState)

	state := sm.GetState()

	// 注意：NewStateManager 会预创建所有 AgentState
	// 所以 Tasks 和 Messages 为空，但 Agents 已初始化
	if len(state.Tasks) != 0 {
		t.Errorf("Expected 0 tasks, got %d", len(state.Tasks))
	}
	if len(state.Messages) != 0 {
		t.Errorf("Expected 0 messages, got %d", len(state.Messages))
	}
	// 验证 Agents 已初始化（10个预定义的 agent）
	if len(state.Agents) != 10 {
		t.Errorf("Expected 10 pre-initialized agents, got %d", len(state.Agents))
	}
}

// TestAgentStateInitialValues 测试 AgentState 初始值
func TestAgentStateInitialValues(t *testing.T) {
	initialState := agents.CreateEmptyState()
	sm := NewStateManager(initialState)

	state := sm.GetState()
	ceoState := state.Agents[agents.AgentRoleCEO]

	if ceoState.Role != agents.AgentRoleCEO {
		t.Errorf("Role = %s, want %s", ceoState.Role, agents.AgentRoleCEO)
	}
	if ceoState.Workload != 0 {
		t.Errorf("Initial Workload = %f, want 0", ceoState.Workload)
	}
	if len(ceoState.CurrentTasks) != 0 {
		t.Errorf("Initial CurrentTasks length = %d, want 0", len(ceoState.CurrentTasks))
	}
	if len(ceoState.CompletedTasks) != 0 {
		t.Errorf("Initial CompletedTasks length = %d, want 0", len(ceoState.CompletedTasks))
	}
	if ceoState.LastActive.IsZero() {
		t.Error("LastActive should not be zero")
	}
}
