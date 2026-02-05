package mailbox

import (
	"fmt"
	"sync"
	"time"

	"superman/agents"
)

// MailboxManager Mailbox管理器
type MailboxManager struct {
	mu        sync.RWMutex
	mailboxes map[agents.AgentRole]*Mailbox
	dlq       *DeadLetterQueue
	idChecker *IdempotencyChecker
	metrics   *Metrics
	config    *MailboxManagerConfig
	started   bool
}

// MailboxManagerConfig 管理器配置
type MailboxManagerConfig struct {
	DLQConfig            *DLQConfig
	IdempotencyMaxSize   int
	IdempotencyWindow    int // 小时
	EnableMetrics        bool
	EnableDLQ            bool // 是否启用死信队列（需要SQLite）
	DefaultMailboxConfig *MailboxConfig
}

// DefaultMailboxManagerConfig 返回默认配置
func DefaultMailboxManagerConfig() *MailboxManagerConfig {
	return &MailboxManagerConfig{
		DLQConfig:          DefaultDLQConfig(),
		IdempotencyMaxSize: 100000,
		IdempotencyWindow:  24, // 24小时
		EnableMetrics:      true,
		EnableDLQ:          true,
	}
}

// NewMailboxManager 创建新的Mailbox管理器
func NewMailboxManager(config *MailboxManagerConfig) (*MailboxManager, error) {
	if config == nil {
		config = DefaultMailboxManagerConfig()
	}

	// 创建死信队列（可选）
	var dlq *DeadLetterQueue
	var err error
	if config.EnableDLQ {
		dlq, err = NewDeadLetterQueue(config.DLQConfig)
		if err != nil {
			return nil, fmt.Errorf("failed to create DLQ: %w", err)
		}
	}

	// 创建幂等性检查器
	idChecker := NewIdempotencyChecker(
		config.IdempotencyMaxSize,
		time.Duration(config.IdempotencyWindow)*time.Hour,
	)

	// 创建指标收集器
	var metrics *Metrics
	if config.EnableMetrics {
		metrics = NewMetrics()
	}

	mm := &MailboxManager{
		mailboxes: make(map[agents.AgentRole]*Mailbox),
		dlq:       dlq,
		idChecker: idChecker,
		metrics:   metrics,
		config:    config,
	}

	return mm, nil
}

// RegisterMailbox 注册Mailbox
func (mm *MailboxManager) RegisterMailbox(role agents.AgentRole, handler MessageHandler) error {
	mm.mu.Lock()
	defer mm.mu.Unlock()

	if _, exists := mm.mailboxes[role]; exists {
		return fmt.Errorf("mailbox for role %s already exists", role)
	}

	// 创建Mailbox配置
	config := DefaultMailboxConfig(role)
	if mm.config.DefaultMailboxConfig != nil {
		config = mm.config.DefaultMailboxConfig
		config.Receiver = role
	}

	// 创建Mailbox
	mb, err := NewMailbox(config, mm.idChecker, mm.dlq, mm.metrics)
	if err != nil {
		return err
	}

	// 设置处理器
	mb.SetHandler(handler)

	mm.mailboxes[role] = mb

	return nil
}

// GetMailbox 获取Mailbox
func (mm *MailboxManager) GetMailbox(role agents.AgentRole) (*Mailbox, error) {
	mm.mu.RLock()
	defer mm.mu.RUnlock()

	mb, exists := mm.mailboxes[role]
	if !exists {
		return nil, fmt.Errorf("mailbox for role %s not found", role)
	}

	return mb, nil
}

// Start 启动所有Mailbox
func (mm *MailboxManager) Start() error {
	mm.mu.Lock()
	defer mm.mu.Unlock()

	if mm.started {
		return fmt.Errorf("mailbox manager already started")
	}

	// 启动所有Mailbox
	for role, mb := range mm.mailboxes {
		if err := mb.Start(); err != nil {
			return fmt.Errorf("failed to start mailbox for %s: %w", role, err)
		}
	}

	mm.started = true
	return nil
}

// Stop 停止所有Mailbox
func (mm *MailboxManager) Stop() error {
	mm.mu.Lock()
	defer mm.mu.Unlock()

	if !mm.started {
		return nil
	}

	var errs []error

	// 停止所有Mailbox
	for role, mb := range mm.mailboxes {
		if err := mb.Stop(); err != nil {
			errs = append(errs, fmt.Errorf("failed to stop mailbox for %s: %w", role, err))
		}
	}

	// 关闭DLQ
	if mm.dlq != nil {
		if err := mm.dlq.Close(); err != nil {
			errs = append(errs, fmt.Errorf("failed to close DLQ: %w", err))
		}
	}

	mm.started = false

	if len(errs) > 0 {
		return fmt.Errorf("errors during stop: %v", errs)
	}

	return nil
}

// Send 发送消息到指定Mailbox
func (mm *MailboxManager) Send(msg *Message) error {
	if msg == nil {
		return fmt.Errorf("message is nil")
	}

	mb, err := mm.GetMailbox(msg.Receiver)
	if err != nil {
		return err
	}

	return mb.Send(msg)
}

// SendTo 发送消息到指定角色
func (mm *MailboxManager) SendTo(sender, receiver agents.AgentRole, msgType agents.MessageType, content map[string]interface{}, priority agents.Priority) error {
	msg := NewMessage(sender, receiver, msgType, content)
	msg.WithPriority(priority)
	return mm.Send(msg)
}

// GetAllStats 获取所有统计信息
func (mm *MailboxManager) GetAllStats() map[string]interface{} {
	mm.mu.RLock()
	defer mm.mu.RUnlock()

	stats := make(map[string]interface{})

	// Mailbox统计
	mailboxStats := make(map[string]interface{})
	for role, mb := range mm.mailboxes {
		mailboxStats[string(role)] = mb.GetStats()
	}
	stats["mailboxes"] = mailboxStats

	// DLQ统计
	if mm.dlq != nil {
		dlqStats, _ := mm.dlq.GetStats()
		stats["dlq"] = dlqStats
	}

	// 指标
	if mm.metrics != nil {
		stats["metrics"] = mm.metrics.GetSnapshot()
	}

	return stats
}

// GetMetrics 获取指标收集器
func (mm *MailboxManager) GetMetrics() *Metrics {
	return mm.metrics
}

// GetDLQ 获取死信队列
func (mm *MailboxManager) GetDLQ() *DeadLetterQueue {
	return mm.dlq
}

// IsStarted 检查是否已启动
func (mm *MailboxManager) IsStarted() bool {
	mm.mu.RLock()
	defer mm.mu.RUnlock()
	return mm.started
}
