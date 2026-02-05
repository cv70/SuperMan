package mailbox

import (
	"context"
	"fmt"
	"sync"
	"time"

	"superman/agents"
)

// MailboxConfig Mailbox配置
type MailboxConfig struct {
	Receiver          agents.AgentRole                  // 接收者角色
	InboxBufferSize   int                               // 收件箱channel缓冲区大小
	MaxRetries        int                               // 最大重试次数
	BaseDelay         time.Duration                     // 基础退避延迟
	MaxDelay          time.Duration                     // 最大退避延迟
	ProcessingTimeout map[agents.Priority]time.Duration // 各优先级超时
	MaxQueueDepth     int                               // 最大队列深度
	EnableDLQ         bool                              // 是否启用死信队列
}

// DefaultMailboxConfig 返回默认配置
func DefaultMailboxConfig(receiver agents.AgentRole) *MailboxConfig {
	return &MailboxConfig{
		Receiver:        receiver,
		InboxBufferSize: 1000,
		MaxRetries:      3,
		BaseDelay:       1 * time.Second,
		MaxDelay:        5 * time.Minute,
		ProcessingTimeout: map[agents.Priority]time.Duration{
			agents.PriorityCritical: 5 * time.Second,
			agents.PriorityHigh:     10 * time.Second,
			agents.PriorityMedium:   30 * time.Second,
			agents.PriorityLow:      60 * time.Second,
		},
		MaxQueueDepth: 10000,
		EnableDLQ:     true,
	}
}

// MessageHandler 消息处理函数类型
type MessageHandler func(msg *Message) error

// Mailbox Agent信箱
type Mailbox struct {
	config             *MailboxConfig
	receiver           agents.AgentRole
	queue              *PriorityQueue
	inbox              chan *Message
	processing         map[string]*Message
	idempotencyChecker *IdempotencyChecker
	dlq                *DeadLetterQueue
	metrics            *Metrics
	handler            MessageHandler
	stopCh             chan struct{}
	wg                 sync.WaitGroup
	mu                 sync.RWMutex
	started            bool
}

// NewMailbox 创建新的Mailbox
func NewMailbox(config *MailboxConfig, idempotencyChecker *IdempotencyChecker, dlq *DeadLetterQueue, metrics *Metrics) (*Mailbox, error) {
	if config == nil {
		return nil, fmt.Errorf("config is required")
	}

	mb := &Mailbox{
		config:             config,
		receiver:           config.Receiver,
		queue:              NewPriorityQueue(),
		inbox:              make(chan *Message, config.InboxBufferSize),
		processing:         make(map[string]*Message),
		idempotencyChecker: idempotencyChecker,
		dlq:                dlq,
		metrics:            metrics,
		stopCh:             make(chan struct{}),
	}

	return mb, nil
}

// SetHandler 设置消息处理器
func (mb *Mailbox) SetHandler(handler MessageHandler) {
	mb.mu.Lock()
	defer mb.mu.Unlock()
	mb.handler = handler
}

// Start 启动Mailbox
func (mb *Mailbox) Start() error {
	mb.mu.Lock()
	defer mb.mu.Unlock()

	if mb.started {
		return fmt.Errorf("mailbox already started")
	}

	if mb.handler == nil {
		return fmt.Errorf("message handler not set")
	}

	mb.started = true

	// 启动收件处理goroutine
	mb.wg.Add(1)
	go mb.receiveLoop()

	// 启动队列处理goroutine
	mb.wg.Add(1)
	go mb.processLoop()

	return nil
}

// Stop 停止Mailbox
func (mb *Mailbox) Stop() error {
	mb.mu.Lock()
	if !mb.started {
		mb.mu.Unlock()
		return nil
	}
	mb.started = false
	mb.mu.Unlock()

	close(mb.stopCh)
	mb.wg.Wait()

	return nil
}

// Send 发送消息到Mailbox（外部调用）
func (mb *Mailbox) Send(msg *Message) error {
	if msg == nil {
		return fmt.Errorf("message is nil")
	}

	// 检查队列深度
	if mb.queue.Len() >= mb.config.MaxQueueDepth {
		return fmt.Errorf("mailbox queue is full (depth: %d)", mb.queue.Len())
	}

	// 投递到inbox（非阻塞）
	select {
	case mb.inbox <- msg:
		// 记录指标
		if mb.metrics != nil {
			mb.metrics.RecordMessageSent(msg.Sender, mb.receiver, msg.MessageType)
		}
		return nil
	default:
		return fmt.Errorf("mailbox inbox is full")
	}
}

// receiveLoop 接收循环（从inbox到queue）
func (mb *Mailbox) receiveLoop() {
	defer mb.wg.Done()

	for {
		select {
		case msg := <-mb.inbox:
			// 按优先级入队
			mb.queue.Enqueue(msg)

			// 记录队列深度指标
			if mb.metrics != nil {
				mb.metrics.RecordQueueDepth(mb.receiver, msg.Priority, int64(mb.queue.Len()))
			}

		case <-mb.stopCh:
			return
		}
	}
}

// processLoop 处理循环（从queue消费）
func (mb *Mailbox) processLoop() {
	defer mb.wg.Done()

	for {
		select {
		case <-mb.stopCh:
			return
		default:
		}

		// 从队列取消息
		msg := mb.queue.Dequeue()
		if msg == nil {
			// 队列为空，短暂休眠
			time.Sleep(10 * time.Millisecond)
			continue
		}

		// 处理消息
		mb.processMessage(msg)
	}
}

// processMessage 处理单条消息
func (mb *Mailbox) processMessage(msg *Message) {
	// 检查幂等性
	if mb.idempotencyChecker != nil && mb.idempotencyChecker.IsProcessed(msg.MessageID) {
		// 消息已处理，直接返回
		return
	}

	// 添加到processing表
	mb.mu.Lock()
	mb.processing[msg.MessageID] = msg
	mb.mu.Unlock()

	// 记录指标
	if mb.metrics != nil {
		mb.metrics.RecordMessageReceived(mb.receiver, msg.MessageType)
	}

	// 获取超时时间
	timeout := mb.config.ProcessingTimeout[agents.PriorityMedium]
	if t, ok := mb.config.ProcessingTimeout[msg.Priority]; ok {
		timeout = t
	}

	// 创建带超时的context
	ctx, cancel := context.WithTimeout(context.Background(), timeout)
	defer cancel()

	// 处理消息
	startTime := time.Now()
	var processErr error
	var panicRecover interface{}

	done := make(chan struct{})
	go func() {
		defer func() {
			if r := recover(); r != nil {
				panicRecover = r
			}
			close(done)
		}()
		processErr = mb.handler(msg)
	}()

	select {
	case <-done:
		// 处理完成
	case <-ctx.Done():
		// 超时
		processErr = fmt.Errorf("message processing timeout")
	}

	duration := time.Since(startTime)

	// 记录处理时间指标
	if mb.metrics != nil {
		mb.metrics.RecordProcessingDuration(duration)
	}

	// 从processing表移除
	mb.mu.Lock()
	delete(mb.processing, msg.MessageID)
	mb.mu.Unlock()

	// 处理结果
	if processErr != nil || panicRecover != nil {
		// 处理失败
		reason := processErr.Error()
		if panicRecover != nil {
			reason = fmt.Sprintf("panic: %v", panicRecover)
		}

		// 检查是否需要重试
		retryCount := 0
		// TODO: 实现重试计数

		if retryCount < mb.config.MaxRetries {
			// 延迟重试
			delay := mb.calculateBackoff(retryCount)
			time.AfterFunc(delay, func() {
				mb.Send(msg)
			})

			// 记录重试指标
			if mb.metrics != nil {
				mb.metrics.RecordRetry(mb.receiver)
			}
		} else {
			// 进入死信队列
			if mb.dlq != nil && mb.config.EnableDLQ {
				mb.dlq.Add(msg, retryCount, reason, "")
			}

			// 记录失败指标
			if mb.metrics != nil {
				mb.metrics.RecordMessageProcessed(mb.receiver, "failed")
			}
		}
	} else {
		// 处理成功

		// 标记幂等性
		if mb.idempotencyChecker != nil {
			mb.idempotencyChecker.MarkProcessed(msg.MessageID, nil)
		}

		// 记录成功指标
		if mb.metrics != nil {
			mb.metrics.RecordMessageProcessed(mb.receiver, "success")
		}
	}
}

// calculateBackoff 计算退避延迟
func (mb *Mailbox) calculateBackoff(retryCount int) time.Duration {
	delay := mb.config.BaseDelay * (1 << retryCount)
	if delay > mb.config.MaxDelay {
		delay = mb.config.MaxDelay
	}
	return delay
}

// GetQueueDepth 获取队列深度
func (mb *Mailbox) GetQueueDepth() int {
	return mb.queue.Len()
}

// GetProcessingCount 获取正在处理的消息数
func (mb *Mailbox) GetProcessingCount() int {
	mb.mu.RLock()
	defer mb.mu.RUnlock()
	return len(mb.processing)
}

// GetStats 获取统计信息
func (mb *Mailbox) GetStats() map[string]interface{} {
	return map[string]interface{}{
		"receiver":         mb.receiver,
		"queue_depth":      mb.GetQueueDepth(),
		"processing_count": mb.GetProcessingCount(),
		"started":          mb.started,
	}
}

// IsStarted 检查是否已启动
func (mb *Mailbox) IsStarted() bool {
	mb.mu.RLock()
	defer mb.mu.RUnlock()
	return mb.started
}
