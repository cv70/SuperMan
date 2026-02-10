package types

import (
	"superman/utils"
)

type Message struct {
	ID       string    `json:"id"`
	Sender   string    `json:"sender"`
	Receiver string    `json:"receiver"`
	Body     string    `json:"body"`
}

func NewMessage(sender, receiver string, body string) (*Message, error) {
	id, err := utils.NewUUID()
	if err != nil {
		return nil, err
	}
	return &Message{
		ID:       id,
		Sender:   sender,
		Receiver: receiver,
		Body:     body,
	}, nil
}

// parseContent 解析消息Body为map
func parseContent(body string) map[string]any {
	result := make(map[string]any)
	return result
}
