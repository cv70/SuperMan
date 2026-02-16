package mailbox

import (
	"fmt"
	"log/slog"
	"time"

	"superman/ds"
	"sync"
)

// MailboxConfig Mailbox配置
type MailboxConfig struct {
	MailboxBus      *MailboxBus // 所属的MailboxBus
	Receiver        string      // 接收者角色
	InboxBufferSize int         // 收件箱channel缓冲区大小
}

// DefaultMailboxConfig 返回默认配置
func DefaultMailboxConfig(receiver string) *MailboxConfig {
	return &MailboxConfig{
		Receiver:        receiver,
		InboxBufferSize: 1000,
	}
}

// MessageHandler 消息处理函数类型
type MessageHandler func(msg *ds.Message) error

// Mailbox Agent信箱
type Mailbox struct {
	bus      *MailboxBus
	receiver string
	Inbox    chan *ds.Message // 收件箱（导出字段）
	archive  []*ds.Message    // 消息归档
	mu       sync.RWMutex
}

// NewMailbox 创建新的Mailbox
func NewMailbox(config *MailboxConfig) *Mailbox {
	mb := &Mailbox{
		bus:      config.MailboxBus,
		receiver: config.Receiver,
		Inbox:    make(chan *ds.Message, config.InboxBufferSize),
		archive:  make([]*ds.Message, 0),
	}

	return mb
}

// PushInbox 向收件箱推送消息（非阻塞，带超时）
func (mb *Mailbox) PushInbox(msg *ds.Message) error {
	select {
	case mb.Inbox <- msg:
		return nil
	case <-time.After(5 * time.Second):
		slog.Warn("mailbox full, message dropped",
			slog.String("receiver", mb.receiver),
			slog.String("msg_id", msg.ID),
			slog.String("sender", msg.Sender),
		)
		return fmt.Errorf("mailbox %s is full, message %s dropped", mb.receiver, msg.ID)
	}
}

// PopInbox 从收件箱取出消息
func (mb *Mailbox) PopInbox() *ds.Message {
	return <-mb.Inbox
}

// PushOutbox 向发件箱推送消息
func (mb *Mailbox) PushOutbox(msg *ds.Message) error {
	return mb.bus.Send(msg)
}

// ArchiveMessage 归档消息
func (mb *Mailbox) ArchiveMessage(msg *ds.Message) {
	mb.mu.Lock()
	defer mb.mu.Unlock()
	mb.archive = append(mb.archive, msg)

	// 限制归档大小，保留最新的1000条消息
	if len(mb.archive) > 1000 {
		mb.archive = mb.archive[1:]
	}
}

// GetMailboxBus 获取信箱总线
func (mb *Mailbox) GetMailboxBus() *MailboxBus {
	return mb.bus
}

// GetInboxCount 获取收件箱消息数量
func (mb *Mailbox) GetInboxCount() int {
	return len(mb.Inbox)
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
		"inbox_count":   len(mb.Inbox),
		"archive_count": len(mb.archive),
		"receiver":      mb.receiver,
		"buffer_size":   cap(mb.Inbox),
	}
}
