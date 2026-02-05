package mailbox

import (
	"sync"
	"time"

	"superman/agents"
)

// Metrics 监控指标收集器
type Metrics struct {
	mu sync.RWMutex

	// 消息计数
	messagesSentTotal      map[string]int64 // key: sender_receiver_type
	messagesReceivedTotal  map[string]int64 // key: receiver_type
	messagesProcessedTotal map[string]int64 // key: receiver_status

	// 延迟统计（单位：毫秒）
	messageLatency []int64 // 最近1000条消息的延迟

	// 队列深度
	mailboxQueueDepth map[string]int64 // key: receiver_priority

	// 处理时间
	mailboxProcessingDuration []int64 // 最近1000条消息的处理时间

	// 重试计数
	mailboxRetryTotal map[string]int64 // key: receiver

	// WAL指标
	walWriteLatency []int64
	walSizeBytes    int64

	// DLQ指标
	dlqDepthTotal int64

	// 启动时间
	startTime time.Time
}

// NewMetrics 创建新的指标收集器
func NewMetrics() *Metrics {
	return &Metrics{
		messagesSentTotal:         make(map[string]int64),
		messagesReceivedTotal:     make(map[string]int64),
		messagesProcessedTotal:    make(map[string]int64),
		messageLatency:            make([]int64, 0, 1000),
		mailboxQueueDepth:         make(map[string]int64),
		mailboxProcessingDuration: make([]int64, 0, 1000),
		mailboxRetryTotal:         make(map[string]int64),
		walWriteLatency:           make([]int64, 0, 100),
		startTime:                 time.Now(),
	}
}

// RecordMessageSent 记录消息发送
func (m *Metrics) RecordMessageSent(sender, receiver agents.AgentRole, msgType agents.MessageType) {
	m.mu.Lock()
	defer m.mu.Unlock()

	key := formatKey(string(sender), string(receiver), msgType.String())
	m.messagesSentTotal[key]++
}

// RecordMessageReceived 记录消息接收
func (m *Metrics) RecordMessageReceived(receiver agents.AgentRole, msgType agents.MessageType) {
	m.mu.Lock()
	defer m.mu.Unlock()

	key := formatKey(string(receiver), msgType.String())
	m.messagesReceivedTotal[key]++
}

// RecordMessageProcessed 记录消息处理完成
func (m *Metrics) RecordMessageProcessed(receiver agents.AgentRole, status string) {
	m.mu.Lock()
	defer m.mu.Unlock()

	key := formatKey(string(receiver), status)
	m.messagesProcessedTotal[key]++
}

// RecordMessageLatency 记录消息延迟
func (m *Metrics) RecordMessageLatency(latency time.Duration) {
	m.mu.Lock()
	defer m.mu.Unlock()

	m.messageLatency = append(m.messageLatency, latency.Milliseconds())
	if len(m.messageLatency) > 1000 {
		m.messageLatency = m.messageLatency[len(m.messageLatency)-1000:]
	}
}

// RecordQueueDepth 记录队列深度
func (m *Metrics) RecordQueueDepth(receiver agents.AgentRole, priority agents.Priority, depth int64) {
	m.mu.Lock()
	defer m.mu.Unlock()

	key := formatKey(string(receiver), priority.String())
	m.mailboxQueueDepth[key] = depth
}

// RecordProcessingDuration 记录处理时间
func (m *Metrics) RecordProcessingDuration(duration time.Duration) {
	m.mu.Lock()
	defer m.mu.Unlock()

	m.mailboxProcessingDuration = append(m.mailboxProcessingDuration, duration.Milliseconds())
	if len(m.mailboxProcessingDuration) > 1000 {
		m.mailboxProcessingDuration = m.mailboxProcessingDuration[len(m.mailboxProcessingDuration)-1000:]
	}
}

// RecordRetry 记录重试
func (m *Metrics) RecordRetry(receiver agents.AgentRole) {
	m.mu.Lock()
	defer m.mu.Unlock()

	m.mailboxRetryTotal[string(receiver)]++
}

// RecordWALWriteLatency 记录WAL写入延迟
func (m *Metrics) RecordWALWriteLatency(latency time.Duration) {
	m.mu.Lock()
	defer m.mu.Unlock()

	m.walWriteLatency = append(m.walWriteLatency, latency.Milliseconds())
	if len(m.walWriteLatency) > 100 {
		m.walWriteLatency = m.walWriteLatency[len(m.walWriteLatency)-100:]
	}
}

// SetWALSize 设置WAL大小
func (m *Metrics) SetWALSize(size int64) {
	m.mu.Lock()
	defer m.mu.Unlock()

	m.walSizeBytes = size
}

// SetDLQDepth 设置DLQ深度
func (m *Metrics) SetDLQDepth(depth int64) {
	m.mu.Lock()
	defer m.mu.Unlock()

	m.dlqDepthTotal = depth
}

// GetSnapshot 获取指标快照
func (m *Metrics) GetSnapshot() map[string]interface{} {
	m.mu.RLock()
	defer m.mu.RUnlock()

	return map[string]interface{}{
		"messages_sent_total":      m.messagesSentTotal,
		"messages_received_total":  m.messagesReceivedTotal,
		"messages_processed_total": m.messagesProcessedTotal,
		"message_latency_p99":      m.calculateP99(m.messageLatency),
		"message_latency_avg":      m.calculateAvg(m.messageLatency),
		"mailbox_queue_depth":      m.mailboxQueueDepth,
		"processing_duration_p99":  m.calculateP99(m.mailboxProcessingDuration),
		"processing_duration_avg":  m.calculateAvg(m.mailboxProcessingDuration),
		"mailbox_retry_total":      m.mailboxRetryTotal,
		"wal_write_latency_p99":    m.calculateP99(m.walWriteLatency),
		"wal_write_latency_avg":    m.calculateAvg(m.walWriteLatency),
		"wal_size_bytes":           m.walSizeBytes,
		"dlq_depth_total":          m.dlqDepthTotal,
		"uptime_seconds":           time.Since(m.startTime).Seconds(),
	}
}

// calculateP99 计算P99分位数
func (m *Metrics) calculateP99(values []int64) int64 {
	if len(values) == 0 {
		return 0
	}

	// 复制切片以避免修改原始数据
	sorted := make([]int64, len(values))
	copy(sorted, values)

	// 简单选择排序（数据量小，不需要复杂算法）
	for i := 0; i < len(sorted); i++ {
		for j := i + 1; j < len(sorted); j++ {
			if sorted[i] > sorted[j] {
				sorted[i], sorted[j] = sorted[j], sorted[i]
			}
		}
	}

	// P99位置
	idx := int(float64(len(sorted)) * 0.99)
	if idx >= len(sorted) {
		idx = len(sorted) - 1
	}

	return sorted[idx]
}

// calculateAvg 计算平均值
func (m *Metrics) calculateAvg(values []int64) int64 {
	if len(values) == 0 {
		return 0
	}

	var sum int64
	for _, v := range values {
		sum += v
	}

	return sum / int64(len(values))
}

// formatKey 格式化key
func formatKey(parts ...string) string {
	key := ""
	for i, part := range parts {
		if i > 0 {
			key += "_"
		}
		key += part
	}
	return key
}

// Reset 重置所有指标
func (m *Metrics) Reset() {
	m.mu.Lock()
	defer m.mu.Unlock()

	m.messagesSentTotal = make(map[string]int64)
	m.messagesReceivedTotal = make(map[string]int64)
	m.messagesProcessedTotal = make(map[string]int64)
	m.messageLatency = make([]int64, 0, 1000)
	m.mailboxQueueDepth = make(map[string]int64)
	m.mailboxProcessingDuration = make([]int64, 0, 1000)
	m.mailboxRetryTotal = make(map[string]int64)
	m.walWriteLatency = make([]int64, 0, 100)
	m.walSizeBytes = 0
	m.dlqDepthTotal = 0
	m.startTime = time.Now()
}
