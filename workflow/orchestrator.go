package workflow

import (
	"fmt"

	"superman/agents"
	"superman/mailbox"
)

type Orchestrator interface {
	RegisterAgent(role agents.AgentRole, agent interface{})
	GetAgent(role agents.AgentRole) interface{}
	GetAllAgents() []interface{}
	RunTask(task *agents.Task) error
	SendMessage(msg *agents.Message) error
	SendMessageTo(sender, receiver agents.AgentRole, msgType agents.MessageType, content map[string]interface{}, priority agents.Priority) error
	GetMailboxManager() *mailbox.MailboxManager
	Start() error
	Stop() error
}

type orchestratorImpl struct {
	agents         map[agents.AgentRole]interface{}
	stateManager   StateManager
	messageRouter  MessageRouter
	mailboxManager *mailbox.MailboxManager
}

func NewOrchestrator(stateManager StateManager, messageRouter MessageRouter, mailboxManager *mailbox.MailboxManager) Orchestrator {
	return &orchestratorImpl{
		agents:         make(map[agents.AgentRole]interface{}),
		stateManager:   stateManager,
		messageRouter:  messageRouter,
		mailboxManager: mailboxManager,
	}
}

func (o *orchestratorImpl) RegisterAgent(role agents.AgentRole, agent interface{}) {
	o.agents[role] = agent
}

func (o *orchestratorImpl) GetAgent(role agents.AgentRole) interface{} {
	return o.agents[role]
}

func (o *orchestratorImpl) GetAllAgents() []interface{} {
	result := make([]interface{}, 0, len(o.agents))
	for _, agent := range o.agents {
		result = append(result, agent)
	}
	return result
}

func (o *orchestratorImpl) RunTask(task *agents.Task) error {
	Receiver := task.AssignedTo
	if _, exists := o.agents[Receiver]; exists {
		// 通过mailbox系统发送任务消息
		content := map[string]interface{}{
			"task_id":      task.TaskID,
			"title":        task.Title,
			"description":  task.Description,
			"assigned_by":  task.AssignedBy,
			"priority":     task.Priority,
			"status":       task.Status,
			"dependencies": task.Dependencies,
			"deliverables": task.Deliverables,
			"deadline":     task.Deadline,
			"created_at":   task.CreatedAt,
			"updated_at":   task.UpdatedAt,
			"metadata":     task.Metadata,
		}

		if err := o.mailboxManager.SendTo(
			task.AssignedBy,
			Receiver,
			agents.MessageTypeTaskAssignment,
			content,
			agents.Priority(task.Priority),
		); err != nil {
			return fmt.Errorf("failed to send task via mailbox: %w", err)
		}

		o.stateManager.AddTask(task)
		return nil
	}
	return fmt.Errorf("agent %s not found", Receiver)
}

// SendMessage 通过mailbox发送消息
func (o *orchestratorImpl) SendMessage(msg *agents.Message) error {
	mbMsg := mailbox.NewMessage(
		msg.Sender,
		msg.Receiver,
		msg.MessageType,
		convertContent(msg.Content),
	)
	mbMsg.WithPriority(msg.Priority)

	return o.mailboxManager.Send(mbMsg)
}

// SendMessageTo 发送消息到指定角色
func (o *orchestratorImpl) SendMessageTo(sender, receiver agents.AgentRole, msgType agents.MessageType, content map[string]interface{}, priority agents.Priority) error {
	return o.mailboxManager.SendTo(
		sender,
		receiver,
		msgType,
		content,
		priority,
	)
}

// GetMailboxManager 获取mailbox管理器
func (o *orchestratorImpl) GetMailboxManager() *mailbox.MailboxManager {
	return o.mailboxManager
}

// Start 启动orchestrator和mailbox系统
func (o *orchestratorImpl) Start() error {
	// 启动mailbox管理器
	if err := o.mailboxManager.Start(); err != nil {
		return fmt.Errorf("failed to start mailbox manager: %w", err)
	}
	return nil
}

// Stop 停止orchestrator和mailbox系统
func (o *orchestratorImpl) Stop() error {
	// 停止mailbox管理器
	if err := o.mailboxManager.Stop(); err != nil {
		return fmt.Errorf("failed to stop mailbox manager: %w", err)
	}
	return nil
}

// convertContent 转换agents.Message的content格式
func convertContent(content map[string]any) map[string]interface{} {
	result := make(map[string]interface{})
	for k, v := range content {
		result[k] = v
	}
	return result
}
