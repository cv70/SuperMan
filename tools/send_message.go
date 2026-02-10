package tools

import (
	"context"
	"errors"
	"fmt"
	"superman/mailbox"
	"superman/types"

	"github.com/cloudwego/eino/components/tool"
	"github.com/cloudwego/eino/components/tool/utils"
)

type SendMessage struct {
	Sender     string
	Receivers  []string
	MailboxBus *mailbox.MailboxBus
}

func (m *SendMessage) ToEinoTool() (tool.BaseTool, error) {
	return utils.InferTool("send message", "send message to other agent", m.Invoke)
}

func (m *SendMessage) Invoke(ctx context.Context, req SendMessageRequest) (SendMessageResponse, error) {
	var e error
	for _, receiver := range req.Receivers {
		msg, err := types.NewMessage(
			m.Sender,
			receiver,
			req.Body,
		)
		if err != nil {
			e = errors.Join(e, fmt.Errorf("failed to create message, receiver: %v, err: %v", receiver, err))
			continue
		}
		err = m.MailboxBus.Send(msg)
		if err != nil {
			e = errors.Join(e, fmt.Errorf("failed to send message, receiver: %v, err: %v", receiver, err))
			continue
		}
	}
	return SendMessageResponse{}, e
}

type SendMessageRequest struct {
	Receivers []string `json:"receivers" jsonschema:"description=The list of agent names to receive the message"`
	Body      string   `json:"body" jsonschema:"description=The message body to send to other agents"`
}

type SendMessageResponse struct {
}
