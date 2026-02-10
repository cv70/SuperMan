package state

import (
	"fmt"
	"sync"
	"time"

	"superman/types"
)

// GlobalState 代表全局状态（公司级状态）
type GlobalState struct {
	mu                   sync.RWMutex
	Agents               map[string]*AgentState `json:"agents"`
	Tasks                map[string]*types.Task `json:"tasks"`
	Messages             []*types.Message       `json:"messages"`
	CurrentTime          time.Time              `json:"current_time"`
	StrategicGoals       map[string]any         `json:"strategic_goals"`
	KPIs                 map[string]float64     `json:"kpis"`
	MarketData           map[string]any         `json:"market_data"`
	UserFeedback         []map[string]any       `json:"user_feedback"`
	SystemHealth         map[string]any         `json:"system_health"`
	BudgetAllocation     map[string]any         `json:"budget_allocation"`
	FinancialMetrics     map[string]any         `json:"financial_metrics"`
	CampaignMetrics      map[string]any         `json:"campaign_metrics"`
	ProductBacklog       []map[string]any       `json:"product_backlog"`
	TechnicalDebt        []map[string]any       `json:"technical_debt"`
	CampaignData         map[string]any         `json:"campaign_data"`
	BrandData            map[string]any         `json:"brand_data"`
	IndustryReports      map[string]any         `json:"industry_reports"`
	HistoricalCashflow   map[string]any         `json:"historical_cashflow"`
	CompetitorData       map[string]any         `json:"competitor_data"`
	CustomerData         map[string]any         `json:"customer_data"`
	ProductData          map[string]any         `json:"product_data"`
	BusinessMetrics      map[string]any         `json:"business_metrics"`
	HistoricalFinancials map[string]any         `json:"historical_financials"`
	Announcements        []string               `json:"announcements"`
	CompanyExecHistory   []*ExecutionHistory    `json:"company_exec_history"`
	Version              int64                  `json:"version"`
}

// ExecutionHistory 执行历史记录
type ExecutionHistory struct {
	ExecutionID  string
	Timestamp    time.Time
	TaskID       string
	MessageID    string
	Action       string
	Input        map[string]any
	Output       map[string]any
	Status       string
	Duration     time.Duration
	ErrorMessage string
	Dependencies []string
	Metadata     map[string]any
}

// NewGlobalState 创建新的 GlobalState 实例
func NewGlobalState() *GlobalState {
	return &GlobalState{
		Agents:               make(map[string]*AgentState),
		Tasks:                make(map[string]*types.Task),
		Messages:             make([]*types.Message, 0),
		CurrentTime:          time.Now(),
		StrategicGoals:       make(map[string]any),
		KPIs:                 make(map[string]float64),
		MarketData:           make(map[string]any),
		UserFeedback:         make([]map[string]any, 0),
		SystemHealth:         make(map[string]any),
		BudgetAllocation:     make(map[string]any),
		FinancialMetrics:     make(map[string]any),
		CampaignMetrics:      make(map[string]any),
		ProductBacklog:       make([]map[string]any, 0),
		TechnicalDebt:        make([]map[string]any, 0),
		CampaignData:         make(map[string]any),
		BrandData:            make(map[string]any),
		IndustryReports:      make(map[string]any),
		HistoricalCashflow:   make(map[string]any),
		CompetitorData:       make(map[string]any),
		CustomerData:         make(map[string]any),
		ProductData:          make(map[string]any),
		BusinessMetrics:      make(map[string]any),
		HistoricalFinancials: make(map[string]any),
		Announcements:        make([]string, 0),
		CompanyExecHistory:   make([]*ExecutionHistory, 0),
	}
}

// ==================== Agent State Management ====================

// GetAgentState 获取智能体状态
func (gs *GlobalState) GetAgentState(name string) *AgentState {
	gs.mu.RLock()
	defer gs.mu.RUnlock()
	return gs.Agents[name]
}

// SetAgentState 设置智能体状态
func (gs *GlobalState) SetAgentState(name string, state *AgentState) {
	gs.mu.Lock()
	defer gs.mu.Unlock()
	gs.Agents[name] = state
	gs.Version++
}

// GetAllAgentStates 获取所有智能体状态
func (gs *GlobalState) GetAllAgentStates() map[string]*AgentState {
	gs.mu.RLock()
	defer gs.mu.RUnlock()

	result := make(map[string]*AgentState)
	for name, state := range gs.Agents {
		result[name] = state
	}
	return result
}

// UpdateAgentState 更新智能体状态
func (gs *GlobalState) UpdateAgentState(name string, updater func(*AgentState)) {
	gs.mu.Lock()
	defer gs.mu.Unlock()

	if agent, exists := gs.Agents[name]; exists {
		updater(agent)
		gs.Version++
	}
}

// DeleteAgentState 删除智能体状态
func (gs *GlobalState) DeleteAgentState(name string) {
	gs.mu.Lock()
	defer gs.mu.Unlock()
	delete(gs.Agents, name)
	gs.Version++
}

// CreateAgentState 创建新的智能体状态
func (gs *GlobalState) CreateAgentState(name string) *AgentState {
	gs.mu.Lock()
	defer gs.mu.Unlock()

	state := NewAgentState(name)
	gs.Agents[name] = state
	gs.Version++
	return state
}

// ==================== Task Management ====================

// AddTask 添加任务
func (gs *GlobalState) AddTask(task *types.Task) {
	gs.mu.Lock()
	defer gs.mu.Unlock()
	gs.Tasks[task.TaskID] = task
	gs.Version++
}

// GetTask 获取任务
func (gs *GlobalState) GetTask(taskID string) *types.Task {
	gs.mu.RLock()
	defer gs.mu.RUnlock()
	return gs.Tasks[taskID]
}

// GetAllTasks 获取所有任务
func (gs *GlobalState) GetAllTasks() map[string]*types.Task {
	gs.mu.RLock()
	defer gs.mu.RUnlock()

	result := make(map[string]*types.Task)
	for k, v := range gs.Tasks {
		result[k] = v
	}
	return result
}

// UpdateTask 更新任务
func (gs *GlobalState) UpdateTask(taskID string, updater func(*types.Task)) {
	gs.mu.Lock()
	defer gs.mu.Unlock()

	if task, exists := gs.Tasks[taskID]; exists {
		updater(task)
		gs.Version++
	}
}

// DeleteTask 删除任务
func (gs *GlobalState) DeleteTask(taskID string) {
	gs.mu.Lock()
	defer gs.mu.Unlock()
	delete(gs.Tasks, taskID)
	gs.Version++
}

// ==================== Message Management ====================

// AddMessage 添加消息
func (gs *GlobalState) AddMessage(msg *types.Message) {
	gs.mu.Lock()
	defer gs.mu.Unlock()
	gs.Messages = append(gs.Messages, msg)
	gs.Version++
}

// GetMessages 获取消息
func (gs *GlobalState) GetMessages() []*types.Message {
	gs.mu.RLock()
	defer gs.mu.RUnlock()

	messages := make([]*types.Message, len(gs.Messages))
	copy(messages, gs.Messages)
	return messages
}

// GetMessagesByReceiver 根据接收者获取消息
func (gs *GlobalState) GetMessagesByReceiver(receiver string) []*types.Message {
	gs.mu.RLock()
	defer gs.mu.RUnlock()

	var messages []*types.Message
	for _, msg := range gs.Messages {
		if msg.Receiver == receiver {
			messages = append(messages, msg)
		}
	}
	return messages
}

// ==================== Metrics and Health ====================

// SetKPI 设置 KPI
func (gs *GlobalState) SetKPI(key string, value float64) {
	gs.mu.Lock()
	defer gs.mu.Unlock()
	gs.KPIs[key] = value
	gs.Version++
}

// GetKPI 获取 KPI
func (gs *GlobalState) GetKPI(key string) float64 {
	gs.mu.RLock()
	defer gs.mu.RUnlock()
	return gs.KPIs[key]
}

// GetKPIs 获取所有 KPI
func (gs *GlobalState) GetKPIs() map[string]float64 {
	gs.mu.RLock()
	defer gs.mu.RUnlock()

	result := make(map[string]float64)
	for k, v := range gs.KPIs {
		result[k] = v
	}
	return result
}

// SetSystemHealth 设置系统健康度
func (gs *GlobalState) SetSystemHealth(key string, value any) {
	gs.mu.Lock()
	defer gs.mu.Unlock()
	gs.SystemHealth[key] = value
	gs.Version++
}

// GetSystemHealth 获取系统健康度
func (gs *GlobalState) GetSystemHealth() map[string]any {
	gs.mu.RLock()
	defer gs.mu.RUnlock()

	result := make(map[string]any)
	for k, v := range gs.SystemHealth {
		result[k] = v
	}
	return result
}

// ==================== Execution History Management ====================

// AddExecutionHistory 添加执行历史
func (gs *GlobalState) AddExecutionHistory(history *ExecutionHistory) {
	gs.mu.Lock()
	defer gs.mu.Unlock()
	gs.CompanyExecHistory = append(gs.CompanyExecHistory, history)
}

// GetExecutionHistory 获取执行历史
func (gs *GlobalState) GetExecutionHistory() []*ExecutionHistory {
	gs.mu.RLock()
	defer gs.mu.RUnlock()

	history := make([]*ExecutionHistory, len(gs.CompanyExecHistory))
	copy(history, gs.CompanyExecHistory)
	return history
}

// GetExecutionHistoryByAgent 获取指定智能体的执行历史
func (gs *GlobalState) GetExecutionHistoryByAgent(name string) []*ExecutionHistory {
	gs.mu.RLock()
	defer gs.mu.RUnlock()

	var history []*ExecutionHistory
	for _, h := range gs.CompanyExecHistory {
		_ = name
		history = append(history, h)
	}
	return history
}

// GetRecentExecutions 获取最近的执行记录
func (gs *GlobalState) GetRecentExecutions(count int) []*ExecutionHistory {
	gs.mu.RLock()
	defer gs.mu.RUnlock()

	if count <= 0 {
		return []*ExecutionHistory{}
	}

	total := len(gs.CompanyExecHistory)
	if total == 0 {
		return []*ExecutionHistory{}
	}

	start := total - count
	if start < 0 {
		start = 0
	}

	result := make([]*ExecutionHistory, total-start)
	copy(result, gs.CompanyExecHistory[start:])
	return result
}

// ==================== Time Management ====================

// GetCurrentTime 获取当前时间
func (gs *GlobalState) GetCurrentTime() time.Time {
	gs.mu.RLock()
	defer gs.mu.RUnlock()
	return gs.CurrentTime
}

// UpdateCurrentTime 更新当前时间
func (gs *GlobalState) UpdateCurrentTime(t time.Time) {
	gs.mu.Lock()
	defer gs.mu.Unlock()
	gs.CurrentTime = t
	gs.Version++
}

// ==================== Clear Methods ====================

// ClearTasks 清空所有任务
func (gs *GlobalState) ClearTasks() {
	gs.mu.Lock()
	defer gs.mu.Unlock()
	gs.Tasks = make(map[string]*types.Task)
	gs.Version++
}

// ClearMessages 清空所有消息
func (gs *GlobalState) ClearMessages() {
	gs.mu.Lock()
	defer gs.mu.Unlock()
	gs.Messages = make([]*types.Message, 0)
	gs.Version++
}

// ClearAll 清空所有数据
func (gs *GlobalState) ClearAll() {
	gs.mu.Lock()
	defer gs.mu.Unlock()

	gs.Agents = make(map[string]*AgentState)
	gs.Tasks = make(map[string]*types.Task)
	gs.Messages = make([]*types.Message, 0)
	gs.CurrentTime = time.Now()
	gs.StrategicGoals = make(map[string]any)
	gs.KPIs = make(map[string]float64)
	gs.MarketData = make(map[string]any)
	gs.UserFeedback = make([]map[string]any, 0)
	gs.SystemHealth = make(map[string]any)
	gs.BudgetAllocation = make(map[string]any)
	gs.FinancialMetrics = make(map[string]any)
	gs.CampaignMetrics = make(map[string]any)
	gs.ProductBacklog = make([]map[string]any, 0)
	gs.TechnicalDebt = make([]map[string]any, 0)
	gs.CampaignData = make(map[string]any)
	gs.BrandData = make(map[string]any)
	gs.IndustryReports = make(map[string]any)
	gs.HistoricalCashflow = make(map[string]any)
	gs.CompetitorData = make(map[string]any)
	gs.CustomerData = make(map[string]any)
	gs.ProductData = make(map[string]any)
	gs.BusinessMetrics = make(map[string]any)
	gs.HistoricalFinancials = make(map[string]any)
	gs.Announcements = make([]string, 0)
	gs.CompanyExecHistory = make([]*ExecutionHistory, 0)
	gs.Version++
}

// GlobalStateConfig 全局状态配置
type GlobalStateConfig struct {
	MaxTasks       int
	MaxMessages    int
	MaxExecHistory int
}

// DefaultGlobalStateConfig 返回默认配置
func DefaultGlobalStateConfig() *GlobalStateConfig {
	return &GlobalStateConfig{
		MaxTasks:       10000,
		MaxMessages:    10000,
		MaxExecHistory: 10000,
	}
}

// Set 设置全局状态的值
func (gs *GlobalState) Set(key string, value any) error {
	gs.mu.Lock()
	defer gs.mu.Unlock()
	gs.SystemHealth[key] = value
	gs.Version++
	return nil
}

// Get 获取全局状态的值
func (gs *GlobalState) Get(key string) (any, error) {
	gs.mu.RLock()
	defer gs.mu.RUnlock()
	value, exists := gs.SystemHealth[key]
	if !exists {
		return nil, fmt.Errorf("key %s not found", key)
	}
	return value, nil
}

// GetAll 获取所有全局状态
func (gs *GlobalState) GetAll() map[string]any {
	gs.mu.RLock()
	defer gs.mu.RUnlock()

	result := make(map[string]any)
	for k, v := range gs.SystemHealth {
		result[k] = v
	}
	return result
}

// GetVersion 获取全局状态版本号
func (gs *GlobalState) GetVersion() int64 {
	gs.mu.RLock()
	defer gs.mu.RUnlock()
	return gs.Version
}

func (gs *GlobalState) AddPublicAnnouncement(announcement string) {
	gs.mu.RLock()
	defer gs.mu.RUnlock()
	gs.Announcements = append(gs.Announcements, announcement)
}
