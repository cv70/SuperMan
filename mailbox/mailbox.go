package mailbox

import (
	"superman/types"
	"sync"
)

// MailboxConfig Mailbox配置
type MailboxConfig struct {
	MailboxBus       *MailboxBus     // 所属的MailboxBus
	Receiver         types.AgentRole // 接收者角色
	InboxBufferSize  int             // 收件箱channel缓冲区大小
}

// DefaultMailboxConfig 返回默认配置
func DefaultMailboxConfig(receiver types.AgentRole) *MailboxConfig {
	return &MailboxConfig{
		Receiver:         receiver,
		InboxBufferSize:  1000,
	}
}

// MessageHandler 消息处理函数类型
type MessageHandler func(msg *types.Message) error

// Mailbox Agent信箱
type Mailbox struct {
	bus      *MailboxBus
	receiver types.AgentRole
	inbox    chan *types.Message // 收件箱
	archive  []*types.Message    // 消息归档
	mu       sync.RWMutex
}

// NewMailbox 创建新的Mailbox
func NewMailbox(config *MailboxConfig) *Mailbox {
	mb := &Mailbox{
		bus:      config.MailboxBus,
		receiver: config.Receiver,
		inbox:    make(chan *types.Message, config.InboxBufferSize),
		archive:  make([]*types.Message, 0),
	}

	return mb
}

// Send 发送消息到Mailbox（外部调用）
func (mb *Mailbox) Send(msg *types.Message) {
	// 投递到inbox
	mb.inbox <- msg
}

// PushInbox 向收件箱推送消息（内部使用）
func (mb *Mailbox) PushInbox(msg *types.Message) bool {
	select {
	case mb.inbox <- msg:
		return true
	default:
		return false // 信箱已满
	}
}

// PopInbox 从收件箱取出消息
func (mb *Mailbox) PopInbox() *types.Message {
	return <-mb.inbox
}

// PushOutbox 向发件箱推送消息
func (mb *Mailbox) PushOutbox(msg *types.Message) error {
	return mb.bus.Send(msg)
}

// ArchiveMessage 归档消息
func (mb *Mailbox) ArchiveMessage(msg *types.Message) {
	mb.mu.Lock()
	defer mb.mu.Unlock()
	mb.archive = append(mb.archive, msg)

	// 限制归档大小，保留最新的1000条消息
	if len(mb.archive) > 1000 {
		mb.archive = mb.archive[1:]
	}
}

// GetInboxCount 获取收件箱消息数量
func (mb *Mailbox) GetInboxCount() int {
	return len(mb.inbox)
}

// GetArchiveCount 获取归档消息数量
func (mb *Mailbox) GetArchiveCount() int {
	mb.mu.Lock()
	defer mb.mu.Unlock()
	return len(mb.archive)
}

// GetMailboxStats 获取信箱统计信息
func (mb *Mailbox) GetMailboxStats() map[string]interface{} {
	mb.mu.Lock()
	defer mb.mu.Unlock()

	return map[string]interface{}{
		"inbox_count":   len(mb.inbox),
		"archive_count": len(mb.archive),
		"receiver":      mb.receiver.String(),
		"buffer_size":   cap(mb.inbox),
	}
}
