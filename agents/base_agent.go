package agents

import (
	"context"
	"encoding/json"
	"fmt"
	"log/slog"
	"strings"
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

// TaskSubmitFunc 任务提交回调（提交到调度器）
type TaskSubmitFunc func(task *ds.Task, priority string)

// OnTaskCompleteFunc 任务完成回调（通知调度器减少负载）
type OnTaskCompleteFunc func(taskID, agentName string, success bool)

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
	SetTaskSubmitter(fn TaskSubmitFunc)
	SetOnTaskComplete(fn OnTaskCompleteFunc)
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

	mailbox    *mailbox.Mailbox
	mailboxBus *mailbox.MailboxBus

	executionHistory []*state.AgentExecutionHistory
	historyMaxSize   int

	globalState *state.GlobalState

	llmModel model.ToolCallingChatModel // LLM 模型

	// 生命周期
	stopCh       chan struct{}
	wg           sync.WaitGroup
	running      bool
	processingMu sync.RWMutex

	// 回调
	taskSubmitter  TaskSubmitFunc
	onTaskComplete OnTaskCompleteFunc

	// 任务生成配置
	taskGenInterval time.Duration
}

var _ Agent = (*BaseAgentImpl)(nil)

// NewBaseAgent 创建基础 Agent 实例
func NewBaseAgent(ctx context.Context, llm model.ToolCallingChatModel, bus *mailbox.MailboxBus, agentConfig config.AgentConfig, allAgentConfig ...config.AgentConfig) (*BaseAgentImpl, error) {
	mailboxConfig := mailbox.DefaultMailboxConfig(agentConfig.Name)
	mb := mailbox.NewMailbox(mailboxConfig)

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
		MailboxBus: bus, // 使用传入的 MailboxBus，而非未初始化的 mailbox.bus
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

	// 解析任务生成间隔
	taskGenInterval := 30 * time.Minute
	if agentConfig.TaskGenInterval != "" {
		if d, err := time.ParseDuration(agentConfig.TaskGenInterval); err == nil {
			taskGenInterval = d
		}
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
		mailbox:            mb,
		mailboxBus:         bus,
		executionHistory:   make([]*state.AgentExecutionHistory, 0),
		historyMaxSize:     10000,
		stopCh:             make(chan struct{}),
		running:            false,
		globalState:        nil,
		llmModel:           llm,
		taskGenInterval:    taskGenInterval,
	}, nil
}

// SetTaskSubmitter 设置任务提交回调
func (a *BaseAgentImpl) SetTaskSubmitter(fn TaskSubmitFunc) {
	a.mu.Lock()
	defer a.mu.Unlock()
	a.taskSubmitter = fn
}

// SetOnTaskComplete 设置任务完成回调
func (a *BaseAgentImpl) SetOnTaskComplete(fn OnTaskCompleteFunc) {
	a.mu.Lock()
	defer a.mu.Unlock()
	a.onTaskComplete = fn
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
			return a.handleRequestMessage(ctx, body)
		}
	case ds.MessageTypeNotification:
		body, ok := msg.GetNotificationBody()
		if ok {
			return a.handleNotificationMessage(ctx, body)
		}
	case ds.MessageTypeResponse:
		body, ok := msg.GetResponseBody()
		if ok {
			return a.handleResponseMessage(ctx, body)
		}
	default:
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

	for {
		event, ok := iter.Next()
		if !ok {
			break
		}
		if event == nil {
			continue
		}
		slog.Info("agent response",
			slog.String("agent", a.name),
			slog.String("output", fmt.Sprintf("%v", event.Output.MessageOutput)),
		)
	}

	return nil
}

// handleRequestMessage 处理请求消息
func (a *BaseAgentImpl) handleRequestMessage(ctx context.Context, body *ds.RequestBody) error {
	switch body.Type {
	case "task_query":
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

		respBody := map[string]any{
			"tasks": tasks,
		}
		resp, err := ds.NewRequestMessage(
			a.name,
			"unknown",
			"task_query_response",
			respBody,
			nil,
		)
		if err != nil {
			return err
		}
		_ = a.mailbox.PushInbox(resp)
	default:
		slog.Debug("processing request", slog.String("agent", a.name), slog.String("type", body.Type))
	}

	return nil
}

// handleNotificationMessage 处理通知消息
func (a *BaseAgentImpl) handleNotificationMessage(ctx context.Context, body *ds.NotificationBody) error {
	slog.Info("received notification",
		slog.String("agent", a.name),
		slog.String("title", body.Title),
		slog.String("content", body.Content),
	)
	return nil
}

// handleResponseMessage 处理响应消息
func (a *BaseAgentImpl) handleResponseMessage(ctx context.Context, body *ds.ResponseBody) error {
	slog.Info("received response",
		slog.String("agent", a.name),
		slog.String("request_id", body.RequestID),
		slog.Bool("success", body.Success),
	)
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

	slog.Info("processing task",
		slog.String("agent", a.name),
		slog.String("task_id", task.ID),
		slog.String("title", task.Title),
	)

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

	success := true
	if err != nil {
		success = false
		history.Status = "failed"
		history.ErrorMessage = err.Error()

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

		a.mu.Lock()
		a.completedTasks = append(a.completedTasks, task.Copy())
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

	// 通知调度器任务完成
	a.mu.RLock()
	completeFn := a.onTaskComplete
	a.mu.RUnlock()
	if completeFn != nil {
		completeFn(task.ID, a.name, success)
	}

	return err
}

// executeTask 执行任务
func (a *BaseAgentImpl) executeTask(ctx context.Context, task *ds.Task) error {
	messages := []*schema.Message{
		schema.UserMessage(fmt.Sprintf("任务: %s\n描述: %s\n请完成此任务。", task.Title, task.Description)),
	}

	iter := a.agent.Run(ctx, &adk.AgentInput{
		Messages: messages,
	})

	for {
		event, ok := iter.Next()
		if !ok {
			break
		}
		if event == nil {
			continue
		}
		slog.Info("task execution output",
			slog.String("agent", a.name),
			slog.String("task_id", task.ID),
			slog.String("output", fmt.Sprintf("%v", event.Output.MessageOutput)),
		)
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
func (a *BaseAgentImpl) MailboxSend(msg *ds.Message) error {
	return a.mailbox.PushInbox(msg)
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
	if err := a.mailbox.PushInbox(msg); err != nil {
		return err
	}
	a.mu.Lock()
	a.messages = append(a.messages, msg)
	a.lastActive = time.Now()
	a.mu.Unlock()
	return nil
}

// Start 启动 Agent（消息处理循环 + 任务生成循环）
func (a *BaseAgentImpl) Start() error {
	a.processingMu.Lock()
	defer a.processingMu.Unlock()
	if a.running {
		return fmt.Errorf("agent is already running")
	}
	a.running = true
	a.stopCh = make(chan struct{})

	// 启动消息处理循环
	a.wg.Add(1)
	go a.messageProcessingLoop()

	// 启动任务生成循环
	a.wg.Add(1)
	go a.taskGenerationLoop()

	slog.Info("agent started", slog.String("name", a.name))
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
	slog.Info("agent stopped", slog.String("name", a.name))
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

// taskGenerationLoop 任务生成循环（Phase 2: 自驱任务生成）
func (a *BaseAgentImpl) taskGenerationLoop() {
	defer a.wg.Done()

	// 首次生成前先等待系统完成初始化
	select {
	case <-a.stopCh:
		return
	case <-time.After(10 * time.Second):
	}

	ticker := time.NewTicker(a.taskGenInterval)
	defer ticker.Stop()

	for {
		select {
		case <-a.stopCh:
			return
		case <-ticker.C:
			a.mu.RLock()
			submitter := a.taskSubmitter
			a.mu.RUnlock()

			if submitter == nil {
				continue
			}

			ctx, cancel := context.WithTimeout(context.Background(), 60*time.Second)
			tasks, err := a.GenerateTasks(ctx)
			cancel()

			if err != nil {
				slog.Error("task generation failed",
					slog.String("agent", a.name),
					slog.Any("error", err),
				)
				continue
			}

			for _, task := range tasks {
				priority := string(task.Priority)
				if priority == "" {
					priority = "Medium"
				}
				submitter(task, priority)
				slog.Info("auto-generated task submitted",
					slog.String("agent", a.name),
					slog.String("task_id", task.ID),
					slog.String("title", task.Title),
				)
			}
		}
	}
}

// processMessageAsync 异步处理消息
func (a *BaseAgentImpl) processMessageAsync(msg *ds.Message) {
	if taskBody, ok := msg.GetTaskCreateBody(); ok {
		task := &ds.Task{
			ID:           taskBody.TaskID,
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

// GenerateTasks 通过 LLM 生成该 Agent 需要执行的任务
func (a *BaseAgentImpl) GenerateTasks(ctx context.Context) ([]*ds.Task, error) {
	prompt := fmt.Sprintf(`你是 %s，职责描述：%s

请根据你的角色职责，生成 1-3 个你当前应该执行的工作任务。
每个任务应该是具体的、可执行的。

请严格按照以下 JSON 数组格式返回，不要包含任何其他文字：
[{"title": "任务标题", "description": "任务详细描述", "priority": "Medium"}]

priority 可选值: Critical, High, Medium, Low
`, a.name, a.desc)

	messages := []*schema.Message{
		schema.UserMessage(prompt),
	}

	resp, err := a.llmModel.Generate(ctx, messages)
	if err != nil {
		return nil, fmt.Errorf("LLM generate failed: %w", err)
	}

	content := resp.Content
	if content == "" {
		return make([]*ds.Task, 0), nil
	}

	// 解析 LLM 返回的 JSON
	tasks, err := a.parseLLMTasks(content)
	if err != nil {
		slog.Warn("failed to parse LLM task response",
			slog.String("agent", a.name),
			slog.String("content", content),
			slog.Any("error", err),
		)
		return make([]*ds.Task, 0), nil
	}

	return tasks, nil
}

// llmTaskResult LLM 返回的任务结构
type llmTaskResult struct {
	Title       string `json:"title"`
	Description string `json:"description"`
	Priority    string `json:"priority"`
}

// parseLLMTasks 从 LLM 响应中解析任务列表
func (a *BaseAgentImpl) parseLLMTasks(content string) ([]*ds.Task, error) {
	// 尝试从 Markdown code block 中提取 JSON
	jsonStr := extractJSON(content)

	var results []llmTaskResult
	if err := json.Unmarshal([]byte(jsonStr), &results); err != nil {
		return nil, fmt.Errorf("json unmarshal failed: %w", err)
	}

	tasks := make([]*ds.Task, 0, len(results))
	for _, r := range results {
		if r.Title == "" {
			continue
		}
		taskID := ds.GenerateTaskID()
		priority := ds.TaskPriority(r.Priority)
		if priority == "" {
			priority = ds.TaskPriorityMedium
		}
		task := ds.NewTask(
			taskID,
			r.Title,
			r.Description,
			a.name, // 分配给自己
			a.name, // 由自己生成
			ds.TaskStatusPending,
			priority,
		)
		task.Metadata["source"] = "llm_generated"
		task.Metadata["generated_by"] = a.name
		tasks = append(tasks, task)
	}

	return tasks, nil
}

// extractJSON 从文本中提取 JSON 数组
func extractJSON(content string) string {
	// 尝试从 markdown code block 中提取
	if idx := strings.Index(content, "```json"); idx != -1 {
		start := idx + 7
		end := strings.Index(content[start:], "```")
		if end != -1 {
			return strings.TrimSpace(content[start : start+end])
		}
	}
	if idx := strings.Index(content, "```"); idx != -1 {
		start := idx + 3
		// 跳过可能的语言标识行
		if nlIdx := strings.Index(content[start:], "\n"); nlIdx != -1 {
			start += nlIdx + 1
		}
		end := strings.Index(content[start:], "```")
		if end != -1 {
			return strings.TrimSpace(content[start : start+end])
		}
	}

	// 直接查找 JSON 数组边界
	start := strings.Index(content, "[")
	end := strings.LastIndex(content, "]")
	if start != -1 && end != -1 && end > start {
		return content[start : end+1]
	}

	return content
}
