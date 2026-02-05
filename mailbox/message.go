package mailbox

import (
	"time"

	"superman/agents"
)

// MessageContext 消息追踪上下文
type MessageContext struct {
	TraceID   string    `json:"trace_id"`
	SpanID    string    `json:"span_id"`
	ParentID  string    `json:"parent_id,omitempty"`
	StartTime time.Time `json:"start_time"`
}

// Message 信箱消息结构
type Message struct {
	MessageID      string                 `json:"message_id"`
	Sender         agents.AgentRole       `json:"sender"`
	Receiver       agents.AgentRole       `json:"receiver"`
	MessageType    agents.MessageType     `json:"message_type"`
	Content        map[string]interface{} `json:"content"`
	Priority       agents.Priority        `json:"priority"`
	Timestamp      time.Time              `json:"timestamp"`
	Context        *MessageContext        `json:"context,omitempty"`
	IdempotencyKey string                 `json:"idempotency_key,omitempty"`
}

// NewMessage 创建新消息
func NewMessage(sender, receiver agents.AgentRole, msgType agents.MessageType, content map[string]interface{}) *Message {
	return &Message{
		MessageID:   generateMessageID(),
		Sender:      sender,
		Receiver:    receiver,
		MessageType: msgType,
		Content:     content,
		Priority:    agents.PriorityMedium,
		Timestamp:   time.Now(),
	}
}

// generateMessageID 生成消息ID (使用UUIDv7或类似的时间有序ID)
func generateMessageID() string {
	// 这里简化实现，使用时间戳+随机数
	// 生产环境应该使用真正的UUIDv7
	return time.Now().Format("20060102150405.000000000") + randomString(8)
}

// randomString 生成随机字符串
func randomString(length int) string {
	const charset = "abcdefghijklmnopqrstuvwxyz0123456789"
	result := make([]byte, length)
	for i := range result {
		result[i] = charset[time.Now().UnixNano()%int64(len(charset))]
	}
	return string(result)
}

// WithPriority 设置优先级
func (m *Message) WithPriority(priority agents.Priority) *Message {
	m.Priority = priority
	return m
}

// WithContext 设置追踪上下文
func (m *Message) WithContext(ctx *MessageContext) *Message {
	m.Context = ctx
	return m
}

// WithIdempotencyKey 设置幂等键
func (m *Message) WithIdempotencyKey(key string) *Message {
	m.IdempotencyKey = key
	return m
}
