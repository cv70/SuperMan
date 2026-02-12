package tools

import (
	"context"
	"errors"
	"fmt"
	"reflect"
	"superman/ds"
	"superman/mailbox"

	"github.com/cloudwego/eino/components/tool"
	"github.com/cloudwego/eino/components/tool/utils"
	"github.com/eino-contrib/jsonschema"
)

type SendMessage struct {
	Sender     string
	Receivers  []string
	MailboxBus *mailbox.MailboxBus
}

func (m *SendMessage) ToEinoTool() (tool.BaseTool, error) {
	return utils.InferTool("send message", "send message to other agent", m.Invoke, utils.WithSchemaModifier(m.schemaModifier()))
}

// schemaModifier 返回一个自定义的 schema modifier 函数
// 它会根据 SendMessage.Receivers 字段的值，为 SendMessageRequest.Receivers 字段设置枚举值
func (m *SendMessage) schemaModifier() utils.SchemaModifierFn {
	receivers := m.Receivers
	return func(jsonTagName string, t reflect.Type, tag reflect.StructTag, schema *jsonschema.Schema) {
		// 检查是否是 SendMessageRequest.Receivers 字段
		if jsonTagName == "receivers" && t.Kind() == reflect.Slice {
			// 设置枚举值为 SendMessage.Receivers
			enumValues := make([]any, len(receivers))
			for i, v := range receivers {
				enumValues[i] = v
			}
			schema.Enum = enumValues
		}
	}
}

func (m *SendMessage) Invoke(ctx context.Context, req SendMessageRequest) (SendMessageResponse, error) {
	var e error
	for _, receiver := range req.Receivers {
		msg, err := ds.NewRequestMessage(
			m.Sender,
			receiver,
			"message",
			req.Body,
			nil,
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
