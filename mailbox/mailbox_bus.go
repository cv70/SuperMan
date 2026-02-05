package mailbox

import (
	"fmt"
	"sync"

	"superman/state"
	"superman/types"
)

// MailboxBus 信箱总线
type MailboxBus struct {
	mu          sync.RWMutex
	mailboxes   map[types.AgentRole]*Mailbox
	globalState *state.GlobalState // 全局共享状态
}

// MailboxBusConfig MailboxBus配置
type MailboxBusConfig struct {
	MaxMailboxes int
}

// DefaultMailboxBusConfig 返回默认配置
func DefaultMailboxBusConfig() *MailboxBusConfig {
	return &MailboxBusConfig{
		MaxMailboxes: 100,
	}
}

// NewMailboxBus 创建新的Mailbox管理器
func NewMailboxBus() *MailboxBus {
	return NewMailboxBusWithConfig(nil)
}

// NewMailboxBusWithConfig 创建新的Mailbox管理器（带配置）
func NewMailboxBusWithConfig(config *MailboxBusConfig) *MailboxBus {
	if config == nil {
		config = DefaultMailboxBusConfig()
	}

	b := &MailboxBus{
		mailboxes:   make(map[types.AgentRole]*Mailbox),
		globalState: state.NewGlobalState(),
	}

	return b
}

// RegisterMailbox 注册Mailbox
func (b *MailboxBus) RegisterMailbox(role types.AgentRole, mailbox *Mailbox) error {
	b.mu.Lock()
	defer b.mu.Unlock()

	if _, exists := b.mailboxes[role]; exists {
		return fmt.Errorf("mailbox for role %s already exists", role)
	}

	b.mailboxes[role] = mailbox

	return nil
}

// GetMailbox 获取Mailbox
func (b *MailboxBus) GetMailbox(role types.AgentRole) (*Mailbox, error) {
	b.mu.RLock()
	defer b.mu.RUnlock()

	m, exists := b.mailboxes[role]
	if !exists {
		return nil, fmt.Errorf("mailbox for role %s not found", role)
	}

	return m, nil
}

// Send 发送消息到指定Mailbox
func (b *MailboxBus) Send(msg *types.Message) error {
	if msg == nil {
		return fmt.Errorf("message is nil")
	}

	m, err := b.GetMailbox(msg.Receiver)
	if err != nil {
		return err
	}

	m.Send(msg)
	return nil
}

// SendTo 发送消息到指定角色
func (b *MailboxBus) SendTo(sender, receiver types.AgentRole, msgType types.MessageType, content map[string]interface{}) error {
	msg, err := types.NewMessage(sender, receiver, msgType, content)
	if err != nil {
		return err
	}
	return b.Send(msg)
}

// GetGlobalState 获取全局共享状态
func (b *MailboxBus) GetGlobalState() *state.GlobalState {
	return b.globalState
}

// ShareState 发布状态到全局共享状态
func (b *MailboxBus) ShareState(key string, value any) error {
	return b.globalState.Set(key, value)
}

// GetSharedState 从全局共享状态获取数据
func (b *MailboxBus) GetSharedState(key string) (any, error) {
	return b.globalState.Get(key)
}

// GetAllSharedStates 获取所有共享状态
func (b *MailboxBus) GetAllSharedStates() map[string]any {
	return b.globalState.GetAll()
}

// GetSharedStateVersion 获取共享状态版本号
func (b *MailboxBus) GetSharedStateVersion() int64 {
	return b.globalState.GetVersion()
}
