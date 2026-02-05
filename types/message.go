package types

import (
	"superman/utils"
)

type MessageType int

const (
	MessageTypeTaskAssignment   MessageType = iota // 任务分配
	MessageTypeStatusReport                        // 状态报告
	MessageTypeDataRequest                         // 数据请求
	MessageTypeDataResponse                        // 数据响应
	MessageTypeApprovalRequest                     // 审批请求
	MessageTypeApprovalResponse                    // 审批响应
	MessageTypeAlert                               // 警报
	MessageTypeCollaboration                       // 协作
)

func (m MessageType) String() string {
	switch m {
	case MessageTypeTaskAssignment:
		return "task_assignment"
	case MessageTypeStatusReport:
		return "status_report"
	case MessageTypeDataRequest:
		return "data_request"
	case MessageTypeDataResponse:
		return "data_response"
	case MessageTypeApprovalRequest:
		return "approval_request"
	case MessageTypeApprovalResponse:
		return "approval_response"
	case MessageTypeAlert:
		return "alert"
	case MessageTypeCollaboration:
		return "collaboration"
	default:
		return "unknown"
	}
}

type Message struct {
	ID          string         `json:"id"`
	Sender      AgentRole      `json:"sender"`
	Receiver    AgentRole      `json:"receiver"`
	MessageType MessageType    `json:"message_type"`
	Content     map[string]any `json:"content"`
}

func NewMessage(sender, receiver AgentRole, messageType MessageType, content map[string]any) (*Message, error) {
	id, err := utils.NewUUID()
	if err != nil {
		return nil, err
	}
	return &Message{
		ID:          id,
		Sender:      sender,
		Receiver:    receiver,
		MessageType: messageType,
		Content:     content,
	}, nil
}
