package agents

import (
	"context"
	"fmt"
	"log/slog"
	"sync"
	"time"

	"superman/mailbox"
	"superman/state"
	"superman/types"
	"superman/utils"

	"github.com/cloudwego/eino/adk"
	"github.com/cloudwego/eino/adk/middlewares/skill"
)

type Agent interface {
	GetRole() types.AgentRole
	GetName() string
	SetName(name string)
	GetState() *state.AgentState
	UpdateState(updater func(*state.AgentState))
	ProcessMessage(msg *types.Message) error
	GetRoleHierarchy() int
	GetWorkload() float64
	GetMailbox() *mailbox.Mailbox

	// 新增接口方法
	GetExecutionHistory() []*state.AgentExecutionHistory
	AddExecutionHistory(history *state.AgentExecutionHistory)
	GetExecutionHistoryByTaskID(taskID string) []*state.AgentExecutionHistory
	GetExecutionHistoryByTimeRange(start, end time.Time) []*state.AgentExecutionHistory
	GetRecentExecutions(count int) []*state.AgentExecutionHistory

	// 全局状态管理
	SetGlobalState(gs *state.GlobalState)
	GetGlobalState() *state.GlobalState

	// 异步处理接口
	ReceiveMessage(msg *types.Message) error   // 主要消息接收入口
	Start() error                              // 启动异步处理
	Stop() error                               // 停止异步处理
	IsRunning() bool                           // 检查是否正在运行
	GetExecutionStats() map[string]interface{} // 获取执行统计信息
}

type BaseAgentImpl struct {
	mu                 sync.RWMutex
	role               types.AgentRole
	name               string
	currentTasks       []*types.Task
	completedTasks     []*types.Task
	messages           []*types.Message
	performanceMetrics map[string]float64
	workload           float64
	lastActive         time.Time
	taskCount          int
	roleHierarchy      int

	skills             adk.AgentMiddleware

	mailbox          *mailbox.Mailbox               // 信箱
	executionHistory []*state.AgentExecutionHistory // 执行历史
	historyMaxSize   int                            // 历史记录最大容量

	globalState *state.GlobalState // 全局状态

	// 异步处理控制
	stopCh       chan struct{}
	wg           sync.WaitGroup
	running      bool
	processingMu sync.RWMutex
}

var _ Agent = (*BaseAgentImpl)(nil)

func NewBaseAgent(ctx context.Context, role types.AgentRole, hierarchy int) (*BaseAgentImpl, error) {
	// 为agent创建私有信箱
	mailboxConfig := mailbox.DefaultMailboxConfig(role)
	mailbox := mailbox.NewMailbox(mailboxConfig)

	localSkillBackend, err := skill.NewLocalBackend(&skill.LocalBackendConfig{
		BaseDir: "./skills",
	})
	if err != nil {
		return nil, err
	}
	skillMiddleware, err := skill.New(ctx, &skill.Config{
		Backend: localSkillBackend,
		UseChinese: true,
	})

	return &BaseAgentImpl{
		role:               role,
		name:               role.String(),
		currentTasks:       make([]*types.Task, 0),
		completedTasks:     make([]*types.Task, 0),
		messages:           make([]*types.Message, 0),
		performanceMetrics: make(map[string]float64),
		skills:             skillMiddleware,
		lastActive:         time.Now(),
		roleHierarchy:      hierarchy,

		// 初始化新增字段
		mailbox:          mailbox, // 私有信箱容量1000
		executionHistory: make([]*state.AgentExecutionHistory, 0),
		historyMaxSize:   10000, // 历史记录最大10000条

		// 初始化异步处理控制
		stopCh:  make(chan struct{}),
		running: false,

		globalState: nil,
	}, nil
}

func (a *BaseAgentImpl) GetRole() types.AgentRole {
	a.mu.RLock()
	defer a.mu.RUnlock()
	return a.role
}

func (a *BaseAgentImpl) GetName() string {
	a.mu.RLock()
	defer a.mu.RUnlock()
	return a.name
}

func (a *BaseAgentImpl) SetName(name string) {
	a.mu.Lock()
	defer a.mu.Unlock()
	a.name = name
}

func (a *BaseAgentImpl) GetState() *state.AgentState {
	a.mu.RLock()
	defer a.mu.RUnlock()
	return &state.AgentState{
		Role:               a.role,
		CurrentTasks:       a.currentTasks,
		CompletedTasks:     a.completedTasks,
		Messages:           a.messages,
		PerformanceMetrics: a.performanceMetrics,
		Workload:           a.workload,
		LastActive:         a.lastActive,
	}
}

func (a *BaseAgentImpl) UpdateState(updater func(*state.AgentState)) {
	a.mu.Lock()
	defer a.mu.Unlock()
	updater(&state.AgentState{
		Role:               a.role,
		CurrentTasks:       a.currentTasks,
		CompletedTasks:     a.completedTasks,
		Messages:           a.messages,
		PerformanceMetrics: a.performanceMetrics,
		Workload:           a.workload,
		LastActive:         a.lastActive,
	})
}

func (a *BaseAgentImpl) ProcessMessage(msg *types.Message) error {
	startTime := time.Now()

	// 1. 将消息转换为mailbox.Message并添加到私有收件箱
	success := a.mailbox.PushInbox(msg)
	if !success {
		return fmt.Errorf("mailbox is full")
	}

	// 2. 记录到全局消息历史
	a.mu.Lock()
	a.messages = append(a.messages, msg)
	a.lastActive = time.Now()
	a.mu.Unlock()

	// 3. 记录执行开始
	history, err := a.CreateExecutionHistory(
		"", // 暂时没有任务ID
		msg.ID,
		"process_message",
		map[string]any{
			"message_type": msg.MessageType.String(),
			"sender":       msg.Sender.String(),
			"receiver":     msg.Receiver.String(),
		},
		map[string]any{},
	)
	if err != nil {
		return fmt.Errorf("failed to create execution history: %w", err)
	}
	history.Status = "processing"
	a.AddExecutionHistory(history)

	// 4. 执行实际的消息处理逻辑
	err = a.processMessageInternal(msg)
	duration := time.Since(startTime)

	// 5. 更新执行历史
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
	// 更新历史记录(替换processing状态的记录)
	a.updateExecutionHistory(history)

	return err
}

// processMessageInternal 内部消息处理逻辑(由具体agent实现)
func (a *BaseAgentImpl) processMessageInternal(msg *types.Message) error {
	// 默认实现：根据消息类型进行基本处理
	switch msg.MessageType {
	case types.MessageTypeTaskAssignment:
		return a.handleTaskAssignment(msg)
	case types.MessageTypeStatusReport:
		return a.handleStatusReport(msg)
	case types.MessageTypeDataRequest:
		return a.handleDataRequest(msg)
	case types.MessageTypeDataResponse:
		return a.handleDataResponse(msg)
	case types.MessageTypeAlert:
		return a.handleAlert(msg)
	case types.MessageTypeCollaboration:
		return a.handleCollaboration(msg)
	default:
		// 其他消息类型的默认处理
		return nil
	}
}

// handleStatusReport 处理状态报告
func (a *BaseAgentImpl) handleStatusReport(msg *types.Message) error {
	// 默认实现：记录状态报告
	return nil
}

// handleDataRequest 处理数据请求
func (a *BaseAgentImpl) handleDataRequest(msg *types.Message) error {
	// 默认实现：记录数据请求
	return nil
}

// handleDataResponse 处理数据响应
func (a *BaseAgentImpl) handleDataResponse(msg *types.Message) error {
	// 默认实现：记录数据响应
	return nil
}

// handleAlert 处理警报
func (a *BaseAgentImpl) handleAlert(msg *types.Message) error {
	// 默认实现：记录警报
	return nil
}

// handleCollaboration 处理协作
func (a *BaseAgentImpl) handleCollaboration(msg *types.Message) error {
	// 默认实现：记录协作请求
	return nil
}

// handleTaskAssignment 处理任务分配
func (a *BaseAgentImpl) handleTaskAssignment(msg *types.Message) error {
	// 从消息内容中提取任务信息
	taskID, ok := msg.Content["task_id"].(string)
	if !ok {
		return nil
	}

	// 创建任务对象
	task := &types.Task{
		TaskID:      taskID,
		Title:       getStringFromMap(msg.Content, "title"),
		Description: getStringFromMap(msg.Content, "description"),
		AssignedTo:  a.role,
		AssignedBy:  msg.Sender,
		Status:      "pending",
		CreatedAt:   time.Now(),
		UpdatedAt:   time.Now(),
	}

	// 添加到当前任务列表
	a.mu.Lock()
	a.currentTasks = append(a.currentTasks, task)
	a.workload = float64(len(a.currentTasks))
	a.mu.Unlock()

	// 将任务状态改为in_progress
	task.Status = "in_progress"

	return nil
}

// updateExecutionHistory 更新执行历史记录
func (a *BaseAgentImpl) updateExecutionHistory(newHistory *state.AgentExecutionHistory) {
	a.mu.Lock()
	defer a.mu.Unlock()

	// 查找并替换相同执行ID的记录
	for i, history := range a.executionHistory {
		if history.ExecutionID == newHistory.ExecutionID {
			a.executionHistory[i] = newHistory
			return
		}
	}

	// 如果没找到，添加新记录
	a.executionHistory = append(a.executionHistory, newHistory)
}

// getStringFromMap 从map中安全获取字符串值
func getStringFromMap(m map[string]any, key string) string {
	if val, ok := m[key]; ok {
		if str, ok := val.(string); ok {
			return str
		}
	}
	return ""
}

func (a *BaseAgentImpl) GenerateResponse(task *types.Task) (*types.Message, error) {
	a.mu.Lock()
	defer a.mu.Unlock()
	response, err := types.NewMessage(a.role, "", types.MessageTypeStatusReport, map[string]any{
		"task_id":    task.TaskID,
		"status":     "in_progress",
		"updated_at": time.Now(),
	})
	if err != nil {
		return nil, err
	}
	a.messages = append(a.messages, response)
	return response, nil
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

func (a *BaseAgentImpl) GetMailbox() *mailbox.Mailbox {
	a.mu.RLock()
	defer a.mu.RUnlock()
	return a.mailbox
}

func (a *BaseAgentImpl) CompleteTask(task *types.Task) {
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

// Getmailbox 获取私有信箱
func (a *BaseAgentImpl) Getmailbox() *mailbox.Mailbox {
	a.mu.RLock()
	defer a.mu.RUnlock()
	return a.mailbox
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

// GetExecutionHistory 获取执行历史
func (a *BaseAgentImpl) GetExecutionHistory() []*state.AgentExecutionHistory {
	a.mu.RLock()
	defer a.mu.RUnlock()

	// 返回历史记录的副本
	history := make([]*state.AgentExecutionHistory, len(a.executionHistory))
	copy(history, a.executionHistory)
	return history
}

// ReceiveMessage 异步接收消息的主要入口点
func (a *BaseAgentImpl) ReceiveMessage(msg *types.Message) error {
	if msg == nil {
		return fmt.Errorf("message is nil")
	}

	// 设置接收者
	msg.Receiver = a.role

	// 添加到私有收件箱
	success := a.mailbox.PushInbox(msg)
	if !success {
		return fmt.Errorf("mailbox is full")
	}

	// 记录到全局消息历史
	a.mu.Lock()
	a.messages = append(a.messages, msg)
	a.lastActive = time.Now()
	a.mu.Unlock()

	return nil
}

// Start 启动Agent的异步消息处理
func (a *BaseAgentImpl) Start() error {
	a.processingMu.Lock()
	defer a.processingMu.Unlock()

	if a.running {
		return fmt.Errorf("agent is already running")
	}

	a.running = true
	a.stopCh = make(chan struct{})

	// 启动消息处理goroutine
	a.wg.Add(1)
	go a.messageProcessingLoop()

	return nil
}

// Stop 停止Agent的异步消息处理
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

// IsRunning 检查Agent是否正在运行
func (a *BaseAgentImpl) IsRunning() bool {
	a.processingMu.RLock()
	defer a.processingMu.RUnlock()
	return a.running
}

// messageProcessingLoop 异步消息处理循环
func (a *BaseAgentImpl) messageProcessingLoop() {
	defer a.wg.Done()

	for {
		select {
		case <-a.stopCh:
			return
		default:
			// 从私有收件箱获取消息
			msg := a.mailbox.PopInbox()
			if msg == nil {
				// 没有消息，短暂休眠
				time.Sleep(10 * time.Millisecond)
				continue
			}

			// 异步处理消息
			a.processMessageAsync(msg)
		}
	}
}

// processMessageAsync 异步处理单条消息
func (a *BaseAgentImpl) processMessageAsync(msg *types.Message) {
	defer func() {
		if r := recover(); r != nil {
			// 记录panic信息
			history, err := a.CreateExecutionHistory(
				"",
				msg.ID,
				"process_message_panic",
				map[string]any{
					"message_type": msg.MessageType.String(),
					"sender":       msg.Sender.String(),
					"receiver":     msg.Receiver.String(),
				},
				map[string]any{
					"panic": fmt.Sprintf("%v", r),
				},
			)
			if err != nil {
				slog.Error("panic error", slog.Any("e", err))
				return
			}
			history.Status = "failed"
			history.ErrorMessage = fmt.Sprintf("panic: %v", r)
			a.AddExecutionHistory(history)
		}
	}()

	startTime := time.Now()
	// 记录执行开始
	history, err := a.CreateExecutionHistory(
		"",
		msg.ID,
		"process_message",
		map[string]any{
			"message_type": msg.MessageType.String(),
			"sender":       msg.Sender.String(),
			"receiver":     msg.Receiver.String(),
		},
		map[string]any{},
	)
	if err != nil {
		slog.Error("create execution history error", slog.Any("e", err))
		return
	}
	history.Status = "processing"
	a.AddExecutionHistory(history)

	// 执行实际的消息处理逻辑
	err = a.processMessageInternal(msg)
	duration := time.Since(startTime)

	// 更新执行历史
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

	// 将已处理的消息归档
	a.mailbox.ArchiveMessage(msg)
}

// CreateExecutionHistory 创建执行历史记录
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
		Dependencies: []string{},
		Metadata:     make(map[string]any),
	}, nil
}

// AddExecutionHistory 添加执行历史记录
func (a *BaseAgentImpl) AddExecutionHistory(history *state.AgentExecutionHistory) {
	a.mu.Lock()
	defer a.mu.Unlock()

	// 检查历史记录大小限制
	if len(a.executionHistory) >= a.historyMaxSize {
		// 移除最旧的记录
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

	// 获取最近的count条记录
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

// GetExecutionStats 获取执行统计信息
func (a *BaseAgentImpl) GetExecutionStats() map[string]interface{} {
	a.mu.RLock()
	defer a.mu.RUnlock()

	stats := map[string]interface{}{
		"total_executions":    len(a.executionHistory),
		"success_count":       0,
		"failed_count":        0,
		"timeout_count":       0,
		"avg_duration":        time.Duration(0),
		"last_execution_time": time.Time{},
	}

	var totalDuration time.Duration
	var lastExecutionTime time.Time

	for _, history := range a.executionHistory {
		switch history.Status {
		case "success":
			stats["success_count"] = stats["success_count"].(int) + 1
		case "failed":
			stats["failed_count"] = stats["failed_count"].(int) + 1
		case "timeout":
			stats["timeout_count"] = stats["timeout_count"].(int) + 1
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
