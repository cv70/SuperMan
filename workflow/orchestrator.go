package workflow

import (
	"fmt"

	"superman/agents"
	"superman/mailbox"
	"superman/types"
)

type Orchestrator interface {
	RegisterAgent(agent agents.Agent)
	GetAgent(name string) agents.Agent
	GetAllAgents() []agents.Agent
	RunTask(task *types.Task) error
	SendMessage(msg *types.Message) error
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

func (o *orchestratorImpl) RunTask(task *types.Task) error {
	receiver := task.AssignedTo
	if _, exists := o.agents[receiver]; exists {
		// 通过mailbox系统发送任务消息
		content := map[string]interface{}{
			"task_id":      task.TaskID,
			"title":        task.Title,
			"description":  task.Description,
			"assigned_by":  task.AssignedBy,
			"status":       task.Status,
			"dependencies": task.Dependencies,
			"deliverables": task.Deliverables,
			"deadline":     task.Deadline,
			"created_at":   task.CreatedAt,
			"updated_at":   task.UpdatedAt,
			"metadata":     task.Metadata,
		}

		if err := o.MailboxBus.SendTo(
			task.AssignedBy,
			receiver,
			content,
		); err != nil {
			return fmt.Errorf("failed to send task via mailbox: %w", err)
		}
		return nil
	}
	return fmt.Errorf("agent %s not found", receiver)
}

// SendMessage 通过mailbox发送消息
func (o *orchestratorImpl) SendMessage(msg *types.Message) error {
	newMsg, err := types.NewMessage(msg.Sender, msg.Receiver, msg.Body)
	if err != nil {
		return err
	}

	return o.MailboxBus.Send(newMsg)
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
