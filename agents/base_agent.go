package agents

import (
	"context"
	"fmt"
	"sync"
	"time"

	"superman/config"
	"superman/ds"
	"superman/mailbox"
	"superman/state"
	"superman/tools"
	"superman/utils"

	"github.com/cloudwego/eino/adk"
	"github.com/cloudwego/eino/adk/middlewares/skill"
	"github.com/cloudwego/eino/adk/prebuilt/deep"
	"github.com/cloudwego/eino/components/model"
	"github.com/cloudwego/eino/components/tool"
	"github.com/cloudwego/eino/compose"
	"github.com/cloudwego/eino/schema"
	"github.com/cv70/pkgo/gslice"
)

// Agent 定义 Agent 接口
type Agent interface {
	GetName() string
	GetDesc() string
	GetState() *state.AgentState
	ProcessMessage(ctx context.Context, msg *ds.Message) error
	ProcessTask(ctx context.Context, task *ds.Task) error
	GetRoleHierarchy() int
	GetWorkload() float64
	GetMailbox() *mailbox.Mailbox
	GetExecutionHistory() []*state.AgentExecutionHistory
	AddExecutionHistory(history *state.AgentExecutionHistory)
	GetExecutionHistoryByTaskID(taskID string) []*state.AgentExecutionHistory
	GetExecutionHistoryByTimeRange(start, end time.Time) []*state.AgentExecutionHistory
	GetRecentExecutions(count int) []*state.AgentExecutionHistory
	SetGlobalState(gs *state.GlobalState)
	GetGlobalState() *state.GlobalState
	ReceiveMessage(msg *ds.Message) error
	Start() error
	Stop() error
	IsRunning() bool
	GetExecutionStats() map[string]interface{}
	GetLLMModel() model.ToolCallingChatModel
	// GenerateTasks 生成该Agent需要执行的任务
	GenerateTasks(ctx context.Context) ([]*ds.Task, error)
}

// BaseAgentImpl 是所有 Agent 的基础实现
type BaseAgentImpl struct {
	mu   sync.RWMutex
	name string
	desc string

	agent adk.ResumableAgent

	currentTasks       []*ds.Task
	completedTasks     []*ds.Task
	messages           []*ds.Message
	performanceMetrics map[string]float64
	workload           float64
	lastActive         time.Time
	roleHierarchy      int

	mailbox          *mailbox.Mailbox
	executionHistory []*state.AgentExecutionHistory
	historyMaxSize   int

	globalState *state.GlobalState

	llmModel model.ToolCallingChatModel // LLM 模型

	stopCh       chan struct{}
	wg           sync.WaitGroup
	running      bool
	processingMu sync.RWMutex
}

var _ Agent = (*BaseAgentImpl)(nil)

// NewBaseAgent 创建基础 Agent 实例
func NewBaseAgent(ctx context.Context, llm model.ToolCallingChatModel, agentConfig config.AgentConfig, allAgentConfig ...config.AgentConfig) (*BaseAgentImpl, error) {
	mailboxConfig := mailbox.DefaultMailboxConfig(agentConfig.Name)
	mailbox := mailbox.NewMailbox(mailboxConfig)

	localSkillBackend, err := skill.NewLocalBackend(&skill.LocalBackendConfig{
		BaseDir: agentConfig.SkillDir,
	})
	if err != nil {
		return nil, err
	}
	skillBackend, err := skill.New(ctx, &skill.Config{
		Backend:    localSkillBackend,
		UseChinese: true,
	})
	if err != nil {
		return nil, err
	}
	allAgentNames := gslice.Map(allAgentConfig, func(c config.AgentConfig) string {
		return c.Name
	})
	sendMessage := tools.SendMessage{
		Sender:     agentConfig.Name,
		Receivers:  allAgentNames,
		MailboxBus: mailbox.GetMailboxBus(),
	}
	sendMessageTool, err := sendMessage.ToEinoTool()
	if err != nil {
		return nil, err
	}

	agent, err := deep.New(ctx, &deep.Config{
		Name:        agentConfig.Name,
		Description: agentConfig.Desc,
		ChatModel:   llm,
		Middlewares: []adk.AgentMiddleware{skillBackend},
		ToolsConfig: adk.ToolsConfig{
			ToolsNodeConfig: compose.ToolsNodeConfig{
				Tools: []tool.BaseTool{sendMessageTool},
			},
		},
	})
	if err != nil {
		return nil, err
	}

	return &BaseAgentImpl{
		name:               agentConfig.Name,
		desc:               agentConfig.Desc,
		agent:              agent,
		currentTasks:       make([]*ds.Task, 0),
		completedTasks:     make([]*ds.Task, 0),
		messages:           make([]*ds.Message, 0),
		performanceMetrics: make(map[string]float64),
		lastActive:         time.Now(),
		roleHierarchy:      agentConfig.Hierarchy,
		mailbox:            mailbox,
		executionHistory:   make([]*state.AgentExecutionHistory, 0),
		historyMaxSize:     10000,
		stopCh:             make(chan struct{}),
		running:            false,
		globalState:        nil,
		llmModel:           llm,
	}, nil
}

// GetName 获取名称
func (a *BaseAgentImpl) GetName() string {
	a.mu.RLock()
	defer a.mu.RUnlock()
	return a.name
}

// GetDesc 获取描述
func (a *BaseAgentImpl) GetDesc() string {
	a.mu.RLock()
	defer a.mu.RUnlock()
	return a.desc
}

// GetState 获取状态
func (a *BaseAgentImpl) GetState() *state.AgentState {
	a.mu.RLock()
	defer a.mu.RUnlock()
	return &state.AgentState{
		Name:               a.name,
		CurrentTasks:       a.currentTasks,
		CompletedTasks:     a.completedTasks,
		Messages:           a.messages,
		PerformanceMetrics: a.performanceMetrics,
		Workload:           a.workload,
		LastActive:         a.lastActive,
	}
}

// ProcessMessage 处理一般消息（非任务消息）
func (a *BaseAgentImpl) ProcessMessage(ctx context.Context, msg *ds.Message) error {
	a.processingMu.Lock()
	running := a.running
	a.processingMu.Unlock()

	if !running {
		return fmt.Errorf("agent is not running")
	}

	// 根据消息类型进行不同处理
	switch msg.Type {
	case ds.MessageTypeRequest:
		body, ok := msg.GetRequestBody()
		if ok {
			// 处理请求消息
			return a.handleRequestMessage(ctx, body)
		}
	case ds.MessageTypeNotification:
		body, ok := msg.GetNotificationBody()
		if ok {
			// 处理通知消息
			return a.handleNotificationMessage(ctx, body)
		}
	case ds.MessageTypeResponse:
		body, ok := msg.GetResponseBody()
		if ok {
			// 处理响应消息
			return a.handleResponseMessage(ctx, body)
		}
	default:
		// 默认处理：将消息内容传递给agent
		break
	}

	// 构建消息流
	messages := []*schema.Message{
		schema.UserMessage(fmt.Sprintf("%v", msg.Body)),
	}

	// 运行 agent
	iter := a.agent.Run(ctx, &adk.AgentInput{
		Messages: messages,
	})

	// 处理异步迭代器返回的事件
	for {
		event, ok := iter.Next()
		if !ok {
			break
		}

		if event == nil {
			continue
		}

		fmt.Println(event.Output.MessageOutput)
	}

	return nil
}

// handleRequestMessage 处理请求消息
func (a *BaseAgentImpl) handleRequestMessage(ctx context.Context, body *ds.RequestBody) error {
	// 根据请求类型进行处理
	switch body.Type {
	case "task_query":
		// 返回当前任务状态
		a.mu.RLock()
		tasks := make([]map[string]any, 0, len(a.currentTasks))
		for _, t := range a.currentTasks {
			tasks = append(tasks, map[string]any{
				"task_id":  t.ID,
				"title":    t.Title,
				"status":   string(t.Status),
				"priority": string(t.Priority),
			})
		}
		a.mu.RUnlock()

		// 发送响应
		respBody := map[string]any{
			"tasks": tasks,
		}
		resp, err := ds.NewRequestMessage(
			a.name,
			"unknown", // 响应的接收者需要根据上下文确定
			"task_query_response",
			respBody,
			nil,
		)
		if err != nil {
			return err
		}
		a.MailboxSend(resp)
	default:
		// 默认处理：传递给agent
		fmt.Printf("Processing request: %s\n", body.Type)
	}

	return nil
}

// handleNotificationMessage 处理通知消息
func (a *BaseAgentImpl) handleNotificationMessage(ctx context.Context, body *ds.NotificationBody) error {
	fmt.Printf("Received notification: %s - %s\n", body.Title, body.Content)
	return nil
}

// handleResponseMessage 处理响应消息
func (a *BaseAgentImpl) handleResponseMessage(ctx context.Context, body *ds.ResponseBody) error {
	fmt.Printf("Received response: request_id=%s, success=%v\n", body.RequestID, body.Success)
	return nil
}

// ProcessTask 处理任务（专门的任务处理逻辑）
func (a *BaseAgentImpl) ProcessTask(ctx context.Context, task *ds.Task) error {
	a.processingMu.Lock()
	running := a.running
	a.processingMu.Unlock()

	if !running {
		return fmt.Errorf("agent is not running")
	}

	// 更新任务状态
	taskClone := task.Copy()
	a.mu.Lock()
	a.currentTasks = append(a.currentTasks, taskClone)
	a.workload = float64(len(a.currentTasks))
	a.lastActive = time.Now()
	a.mu.Unlock()

	// 更新全局状态
	if a.globalState != nil {
		a.globalState.UpdateTask(task.ID, func(t *ds.Task) {
			t.Status = ds.TaskStatusAssigned
			t.AssignedTo = a.name
		})
	}

	// 创建执行历史
	startTime := time.Now()
	history, err := a.CreateExecutionHistory(
		task.ID, "", "process_task",
		map[string]any{
			"task_id":      task.ID,
			"title":        task.Title,
			"description":  task.Description,
			"dependencies": task.Dependencies,
		},
		map[string]any{},
	)
	if err != nil {
		return err
	}
	history.Status = "processing"
	a.AddExecutionHistory(history)

	// 调用agent处理任务
	err = a.executeTask(ctx, task)

	duration := time.Since(startTime)
	history.Duration = duration

	if err != nil {
		history.Status = "failed"
		history.ErrorMessage = err.Error()

		// 更新任务状态为失败
		a.mu.Lock()
		a.workload = float64(len(a.currentTasks))
		a.mu.Unlock()

		if a.globalState != nil {
			a.globalState.UpdateTask(task.ID, func(t *ds.Task) {
				t.Status = ds.TaskStatusFailed
			})
		}
	} else {
		history.Status = "success"
		history.Output = map[string]any{
			"processed_at": time.Now(),
			"duration_ms":  duration.Milliseconds(),
		}

		// 完成任务
		a.mu.Lock()
		a.completedTasks = append(a.completedTasks, task.Copy())
		// 从当前任务中移除
		for i, t := range a.currentTasks {
			if t.ID == task.ID {
				a.currentTasks = append(a.currentTasks[:i], a.currentTasks[i+1:]...)
				break
			}
		}
		a.workload = float64(len(a.currentTasks))
		a.mu.Unlock()

		if a.globalState != nil {
			a.globalState.UpdateTask(task.ID, func(t *ds.Task) {
				t.Status = ds.TaskStatusCompleted
			})
		}
	}

	a.updateExecutionHistory(history)
	return err
}

// executeTask 执行任务
func (a *BaseAgentImpl) executeTask(ctx context.Context, task *ds.Task) error {
	// 构建任务消息
	messages := []*schema.Message{
		schema.UserMessage(fmt.Sprintf("任务: %s\n描述: %s\n请完成此任务。", task.Title, task.Description)),
	}

	// 运行 agent
	iter := a.agent.Run(ctx, &adk.AgentInput{
		Messages: messages,
	})

	// 处理异步迭代器返回的事件
	for {
		event, ok := iter.Next()
		if !ok {
			break
		}

		if event == nil {
			continue
		}

		fmt.Println(event.Output.MessageOutput)
	}

	return nil
}

// GetRoleHierarchy 获取角色层级
func (a *BaseAgentImpl) GetRoleHierarchy() int {
	a.mu.RLock()
	defer a.mu.RUnlock()
	return a.roleHierarchy
}

// GetWorkload 获取工作负载
func (a *BaseAgentImpl) GetWorkload() float64 {
	a.mu.RLock()
	defer a.mu.RUnlock()
	return a.workload
}

// GetMailbox 获取信箱
func (a *BaseAgentImpl) GetMailbox() *mailbox.Mailbox {
	a.mu.RLock()
	defer a.mu.RUnlock()
	return a.mailbox
}

// MailboxSend 通过信箱发送消息
func (a *BaseAgentImpl) MailboxSend(msg *ds.Message) {
	a.mailbox.PushInbox(msg)
}

// GetExecutionHistory 获取执行历史
func (a *BaseAgentImpl) GetExecutionHistory() []*state.AgentExecutionHistory {
	a.mu.RLock()
	defer a.mu.RUnlock()
	history := make([]*state.AgentExecutionHistory, len(a.executionHistory))
	copy(history, a.executionHistory)
	return history
}

// AddExecutionHistory 添加执行历史
func (a *BaseAgentImpl) AddExecutionHistory(history *state.AgentExecutionHistory) {
	a.mu.Lock()
	defer a.mu.Unlock()
	if len(a.executionHistory) >= a.historyMaxSize {
		a.executionHistory = a.executionHistory[1:]
	}
	a.executionHistory = append(a.executionHistory, history)
}

// GetExecutionHistoryByTaskID 根据任务ID获取执行历史
func (a *BaseAgentImpl) GetExecutionHistoryByTaskID(taskID string) []*state.AgentExecutionHistory {
	a.mu.RLock()
	defer a.mu.RUnlock()
	var result []*state.AgentExecutionHistory
	for _, history := range a.executionHistory {
		if history.TaskID == taskID {
			result = append(result, history)
		}
	}
	return result
}

// GetExecutionHistoryByTimeRange 根据时间范围获取执行历史
func (a *BaseAgentImpl) GetExecutionHistoryByTimeRange(start, end time.Time) []*state.AgentExecutionHistory {
	a.mu.RLock()
	defer a.mu.RUnlock()
	var result []*state.AgentExecutionHistory
	for _, history := range a.executionHistory {
		if history.Timestamp.After(start) && history.Timestamp.Before(end) {
			result = append(result, history)
		}
	}
	return result
}

// GetRecentExecutions 获取最近的执行记录
func (a *BaseAgentImpl) GetRecentExecutions(count int) []*state.AgentExecutionHistory {
	a.mu.RLock()
	defer a.mu.RUnlock()
	if count <= 0 {
		return []*state.AgentExecutionHistory{}
	}
	total := len(a.executionHistory)
	if total == 0 {
		return []*state.AgentExecutionHistory{}
	}
	start := total - count
	if start < 0 {
		start = 0
	}
	result := make([]*state.AgentExecutionHistory, total-start)
	copy(result, a.executionHistory[start:])
	return result
}

// SetGlobalState 设置全局状态
func (a *BaseAgentImpl) SetGlobalState(gs *state.GlobalState) {
	a.mu.Lock()
	defer a.mu.Unlock()
	a.globalState = gs
}

// GetGlobalState 获取全局状态
func (a *BaseAgentImpl) GetGlobalState() *state.GlobalState {
	a.mu.RLock()
	defer a.mu.RUnlock()
	return a.globalState
}

// GetLLMModel 获取 LLM 模型
func (a *BaseAgentImpl) GetLLMModel() model.ToolCallingChatModel {
	a.mu.RLock()
	defer a.mu.RUnlock()
	return a.llmModel
}

// ReceiveMessage 接收消息
func (a *BaseAgentImpl) ReceiveMessage(msg *ds.Message) error {
	if msg == nil {
		return fmt.Errorf("message is nil")
	}
	msg.Receiver = a.name
	a.mailbox.PushInbox(msg)
	a.mu.Lock()
	a.messages = append(a.messages, msg)
	a.lastActive = time.Now()
	a.mu.Unlock()
	return nil
}

// Start 启动 Agent
func (a *BaseAgentImpl) Start() error {
	a.processingMu.Lock()
	defer a.processingMu.Unlock()
	if a.running {
		return fmt.Errorf("agent is already running")
	}
	a.running = true
	a.stopCh = make(chan struct{})
	a.wg.Add(1)
	go a.messageProcessingLoop()
	return nil
}

// Stop 停止 Agent
func (a *BaseAgentImpl) Stop() error {
	a.processingMu.Lock()
	defer a.processingMu.Unlock()
	if !a.running {
		return nil
	}
	a.running = false
	close(a.stopCh)
	a.wg.Wait()
	return nil
}

// IsRunning 检查是否正在运行
func (a *BaseAgentImpl) IsRunning() bool {
	a.processingMu.RLock()
	defer a.processingMu.RUnlock()
	return a.running
}

// GetExecutionStats 获取执行统计信息
func (a *BaseAgentImpl) GetExecutionStats() map[string]interface{} {
	a.mu.RLock()
	defer a.mu.RUnlock()
	stats := map[string]interface{}{
		"total_executions": len(a.executionHistory),
		"success_count":    0,
		"failed_count":     0,
	}
	var totalDuration time.Duration
	var lastExecutionTime time.Time
	for _, history := range a.executionHistory {
		switch history.Status {
		case "success":
			stats["success_count"] = stats["success_count"].(int) + 1
		case "failed":
			stats["failed_count"] = stats["failed_count"].(int) + 1
		}
		totalDuration += history.Duration
		if history.Timestamp.After(lastExecutionTime) {
			lastExecutionTime = history.Timestamp
		}
	}
	if len(a.executionHistory) > 0 {
		stats["avg_duration"] = totalDuration / time.Duration(len(a.executionHistory))
		stats["last_execution_time"] = lastExecutionTime
	}
	return stats
}

// messageProcessingLoop 消息处理循环
func (a *BaseAgentImpl) messageProcessingLoop() {
	defer a.wg.Done()
	for {
		select {
		case <-a.stopCh:
			return
		case msg := <-a.mailbox.Inbox:
			a.processMessageAsync(msg)
		}
	}
}

// processMessageAsync 异步处理消息
func (a *BaseAgentImpl) processMessageAsync(msg *ds.Message) {
	// 根据消息类型分发处理
	if taskBody, ok := msg.GetTaskCreateBody(); ok {
		// 这是任务创建消息
		task := &ds.Task{
			ID:       taskBody.TaskID,
			Title:        taskBody.Title,
			Description:  taskBody.Description,
			AssignedTo:   taskBody.AssignedTo,
			AssignedBy:   taskBody.AssignedBy,
			Dependencies: taskBody.Dependencies,
			Deliverables: taskBody.Deliverables,
			Metadata:     taskBody.Metadata,
		}
		if taskBody.Deadline != nil {
			if t, err := time.Parse(time.RFC3339, *taskBody.Deadline); err == nil {
				task.Deadline = &t
			}
		}
		a.ProcessTask(context.Background(), task)
	} else {
		// 一般消息
		a.ProcessMessage(context.Background(), msg)
	}
}

// CreateExecutionHistory 创建执行历史
func (a *BaseAgentImpl) CreateExecutionHistory(taskID, messageID, action string, input, output map[string]any) (*state.AgentExecutionHistory, error) {
	id, err := utils.NewUUID()
	if err != nil {
		return nil, err
	}
	return &state.AgentExecutionHistory{
		ExecutionID:  id,
		Timestamp:    time.Now(),
		TaskID:       taskID,
		MessageID:    messageID,
		Action:       action,
		Input:        input,
		Output:       output,
		Status:       "success",
		Duration:     0,
		ErrorMessage: "",
	}, nil
}

// updateExecutionHistory 更新执行历史
func (a *BaseAgentImpl) updateExecutionHistory(newHistory *state.AgentExecutionHistory) {
	a.mu.Lock()
	defer a.mu.Unlock()
	for i, history := range a.executionHistory {
		if history.ExecutionID == newHistory.ExecutionID {
			a.executionHistory[i] = newHistory
			return
		}
	}
	a.executionHistory = append(a.executionHistory, newHistory)
}

// GenerateTasks 生成该Agent需要执行的任务
// 默认实现：返回空任务列表，子类可以重写此方法来定义特定任务
func (a *BaseAgentImpl) GenerateTasks(ctx context.Context) ([]*ds.Task, error) {
	// 默认返回空任务列表
	// 子类可以重写此方法来定义特定任务
	return make([]*ds.Task, 0), nil
}
