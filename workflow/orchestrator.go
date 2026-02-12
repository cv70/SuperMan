package workflow

import (
	"fmt"
	"time"

	"superman/agents"
	"superman/ds"
	"superman/mailbox"
)

type Orchestrator interface {
	RegisterAgent(agent agents.Agent)
	GetAgent(name string) agents.Agent
	GetAllAgents() []agents.Agent
	RunTask(task *ds.Task) error
	SendMessage(msg *ds.Message) error
	SendMessageTo(sender, receiver string, content map[string]interface{}) error
	GetMailboxBus() *mailbox.MailboxBus
}

type orchestratorImpl struct {
	agents     map[string]agents.Agent
	MailboxBus *mailbox.MailboxBus
}

func NewOrchestrator(MailboxBus *mailbox.MailboxBus) Orchestrator {
	return &orchestratorImpl{
		agents:     make(map[string]agents.Agent),
		MailboxBus: MailboxBus,
	}
}

func (o *orchestratorImpl) RegisterAgent(agent agents.Agent) {
	o.agents[agent.GetName()] = agent
}

func (o *orchestratorImpl) GetAgent(name string) agents.Agent {
	return o.agents[name]
}

func (o *orchestratorImpl) GetAllAgents() []agents.Agent {
	result := make([]agents.Agent, 0, len(o.agents))
	for _, agent := range o.agents {
		result = append(result, agent)
	}
	return result
}

func (o *orchestratorImpl) RunTask(task *ds.Task) error {
	receiver := task.AssignedTo
	if _, exists := o.agents[receiver]; exists {
		// 创建任务创建消息
		body := &ds.TaskCreateBody{
			TaskID:       task.ID,
			Title:        task.Title,
			Description:  task.Description,
			AssignedTo:   task.AssignedTo,
			AssignedBy:   task.AssignedBy,
			Dependencies: task.Dependencies,
			Deliverables: task.Deliverables,
			Metadata:     task.Metadata,
		}

		// 设置截止日期
		if task.Deadline != nil {
			deadlineStr := task.Deadline.Format(time.RFC3339)
			body.Deadline = &deadlineStr
		}

		msg, err := ds.NewTaskCreateMessage(
			task.ID,
			task.Title,
			task.Description,
			task.AssignedTo,
			task.AssignedBy,
			task.Dependencies,
			task.Deliverables,
			nil, // deadline 通过 body 传递
			task.Metadata,
		)
		if err != nil {
			return fmt.Errorf("failed to create task message: %w", err)
		}

		if err := o.MailboxBus.Send(msg); err != nil {
			return fmt.Errorf("failed to send task via mailbox: %w", err)
		}
		return nil
	}
	return fmt.Errorf("agent %s not found", receiver)
}

// SendMessage 通过mailbox发送消息
func (o *orchestratorImpl) SendMessage(msg *ds.Message) error {
	// 根据消息类型创建新消息
	switch msg.Type {
	case ds.MessageTypeRequest:
		body, _ := msg.GetRequestBody()
		newMsg, err := ds.NewRequestMessage(
			msg.Sender,
			msg.Receiver,
			body.Type,
			body.Content,
			body.Metadata,
		)
		if err != nil {
			return err
		}
		return o.MailboxBus.Send(newMsg)
	case ds.MessageTypeNotification:
		body, _ := msg.GetNotificationBody()
		newMsg, err := ds.NewNotificationMessage(
			msg.Sender,
			msg.Receiver,
			body.Title,
			body.Content,
			body.Priority,
		)
		if err != nil {
			return err
		}
		return o.MailboxBus.Send(newMsg)
	default:
		// 默认作为一般请求消息处理
		newMsg, err := ds.NewRequestMessage(
			msg.Sender,
			msg.Receiver,
			"message",
			msg.Body,
			nil,
		)
		if err != nil {
			return err
		}
		return o.MailboxBus.Send(newMsg)
	}
}

// SendMessageTo 发送消息到指定角色
func (o *orchestratorImpl) SendMessageTo(sender, receiver string, content map[string]interface{}) error {
	return o.MailboxBus.SendTo(
		sender,
		receiver,
		content,
	)
}

// GetMailboxBus 获取mailbox管理器
func (o *orchestratorImpl) GetMailboxBus() *mailbox.MailboxBus {
	return o.MailboxBus
}
