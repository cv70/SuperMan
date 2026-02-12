package agents

import (
	"context"
	"fmt"
	"sync"
	"time"

	"superman/config"
	"superman/mailbox"
	"superman/state"
	"superman/tools"
	"superman/types"
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
	UpdateState(updater func(*state.AgentState))
	ProcessMessage(ctx context.Context, msg *types.Message) error
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
	ReceiveMessage(msg *types.Message) error
	Start() error
	Stop() error
	IsRunning() bool
	GetExecutionStats() map[string]interface{}
	GetLLMModel() model.ToolCallingChatModel
}

// BaseAgentImpl 是所有 Agent 的基础实现
type BaseAgentImpl struct {
	mu   sync.RWMutex
	name string
	desc string

	agent adk.ResumableAgent

	currentTasks       []*types.Task
	completedTasks     []*types.Task
	messages           []*types.Message
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
		currentTasks:       make([]*types.Task, 0),
		completedTasks:     make([]*types.Task, 0),
		messages:           make([]*types.Message, 0),
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

// UpdateState 更新状态
func (a *BaseAgentImpl) UpdateState(updater func(*state.AgentState)) {
	a.mu.Lock()
	defer a.mu.Unlock()
	updater(&state.AgentState{
		Name:               a.name,
		CurrentTasks:       a.currentTasks,
		CompletedTasks:     a.completedTasks,
		Messages:           a.messages,
		PerformanceMetrics: a.performanceMetrics,
		Workload:           a.workload,
		LastActive:         a.lastActive,
	})
}

// ProcessMessage 处理消息
func (a *BaseAgentImpl) ProcessMessage(ctx context.Context, msg *types.Message) error {
	a.processingMu.Lock()
	running := a.running
	a.processingMu.Unlock()

	if !running {
		return fmt.Errorf("agent is not running")
	}

	// 构建消息流
	messages := []*schema.Message{
		schema.UserMessage(msg.Body),
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

		// AgentEvent 处理完成，事件包含 Action 结果
		// event.Output
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
func (a *BaseAgentImpl) ReceiveMessage(msg *types.Message) error {
	if msg == nil {
		return fmt.Errorf("message is nil")
	}
	msg.Receiver = a.name
	success := a.mailbox.PushInbox(msg)
	if !success {
		return fmt.Errorf("mailbox is full")
	}
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
func (a *BaseAgentImpl) processMessageAsync(msg *types.Message) {
	startTime := time.Now()
	history, err := a.CreateExecutionHistory(
		"", msg.ID, "process_message",
		map[string]any{
			"sender":   msg.Sender,
			"receiver": msg.Receiver,
		},
		map[string]any{},
	)
	if err != nil {
		return
	}
	history.Status = "processing"
	a.AddExecutionHistory(history)

	err = a.ProcessMessage(context.Background(), msg)
	duration := time.Since(startTime)

	if err != nil {
		history.Status = "failed"
		history.ErrorMessage = err.Error()
	} else {
		history.Status = "success"
		history.Output = map[string]any{
			"processed_at": time.Now(),
			"duration_ms":  duration.Milliseconds(),
		}
	}
	history.Duration = duration
	a.updateExecutionHistory(history)
	a.mailbox.ArchiveMessage(msg)
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