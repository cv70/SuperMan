package ds

import (
	"encoding/json"
	"superman/utils"
)

// MessageType 消息类型
type MessageType string

const (
	MessageTypeTaskCreate     MessageType = "task_create"     // 任务创建
	MessageTypeTaskUpdate     MessageType = "task_update"     // 任务更新
	MessageTypeTaskComplete   MessageType = "task_complete"   // 任务完成
	MessageTypeTaskAssign     MessageType = "task_assign"     // 任务分配
	MessageTypeTaskQuery      MessageType = "task_query"      // 任务查询
	MessageTypeTaskDependency MessageType = "task_dependency" // 任务依赖
	MessageTypeRequest        MessageType = "request"         // 一般请求
	MessageTypeResponse       MessageType = "response"        // 响应
	MessageTypeNotification   MessageType = "notification"    // 通知
	MessageTypeSystem         MessageType = "system"          // 系统消息
)

// MessageBody 消息体接口
type MessageBody interface{}

// TaskCreateBody 任务创建消息体
type TaskCreateBody struct {
	TaskID       string         `json:"task_id"`
	Title        string         `json:"title"`
	Description  string         `json:"description"`
	AssignedTo   string         `json:"assigned_to"`
	AssignedBy   string         `json:"assigned_by"`
	Dependencies []string       `json:"dependencies"`
	Deliverables []string       `json:"deliverables"`
	Deadline     *string        `json:"deadline,omitempty"`
	Metadata     map[string]any `json:"metadata,omitempty"`
}

// TaskUpdateBody 任务更新消息体
type TaskUpdateBody struct {
	TaskID   string         `json:"task_id"`
	Field    string         `json:"field"`
	OldValue any            `json:"old_value"`
	NewValue any            `json:"new_value"`
	Metadata map[string]any `json:"metadata,omitempty"`
}

// TaskCompleteBody 任务完成消息体
type TaskCompleteBody struct {
	TaskID       string         `json:"task_id"`
	Success      bool           `json:"success"`
	ErrorMessage string         `json:"error_message,omitempty"`
	Metadata     map[string]any `json:"metadata,omitempty"`
}

// TaskAssignBody 任务分配消息体
type TaskAssignBody struct {
	TaskID      string `json:"task_id"`
	NewAssignee string `json:"new_assignee"`
	Reason      string `json:"reason,omitempty"`
}

// RequestBody 一般请求消息体
type RequestBody struct {
	Type     string         `json:"type"`
	Content  any            `json:"content"`
	Metadata map[string]any `json:"metadata,omitempty"`
}

// ResponseBody 响应消息体
type ResponseBody struct {
	RequestID    string `json:"request_id"`
	Success      bool   `json:"success"`
	Content      any    `json:"content,omitempty"`
	ErrorMessage string `json:"error_message,omitempty"`
}

// NotificationBody 通知消息体
type NotificationBody struct {
	Title    string `json:"title"`
	Content  string `json:"content"`
	Priority string `json:"priority,omitempty"`
}

// Message 代表agent之间的消息
type Message struct {
	ID       string      `json:"id"`
	Sender   string      `json:"sender"`
	Receiver string      `json:"receiver"`
	Type     MessageType `json:"type"`
	Body     any         `json:"body"`
}

// NewMessage 创建新的消息（通用）
func NewMessage(sender, receiver string, msgType MessageType, body any) (*Message, error) {
	id, err := utils.NewUUID()
	if err != nil {
		return nil, err
	}
	return &Message{
		ID:       id,
		Sender:   sender,
		Receiver: receiver,
		Type:     msgType,
		Body:     body,
	}, nil
}

// NewTaskCreateMessage 创建任务创建消息
func NewTaskCreateMessage(taskID, title, description, assignedTo, assignedBy string, dependencies, deliverables []string, deadline *string, metadata map[string]any) (*Message, error) {
	body := &TaskCreateBody{
		TaskID:       taskID,
		Title:        title,
		Description:  description,
		AssignedTo:   assignedTo,
		AssignedBy:   assignedBy,
		Dependencies: dependencies,
		Deliverables: deliverables,
		Deadline:     deadline,
		Metadata:     metadata,
	}
	return NewMessage("scheduler", assignedTo, MessageTypeTaskCreate, body)
}

// NewTaskUpdateMessage 创建任务更新消息
func NewTaskUpdateMessage(taskID, field string, oldValue, newValue any, metadata map[string]any) (*Message, error) {
	body := &TaskUpdateBody{
		TaskID:   taskID,
		Field:    field,
		OldValue: oldValue,
		NewValue: newValue,
		Metadata: metadata,
	}
	return NewMessage("scheduler", "", MessageTypeTaskUpdate, body)
}

// NewTaskCompleteMessage 创建任务完成消息
func NewTaskCompleteMessage(taskID string, success bool, errorMessage string, metadata map[string]any) (*Message, error) {
	body := &TaskCompleteBody{
		TaskID:       taskID,
		Success:      success,
		ErrorMessage: errorMessage,
		Metadata:     metadata,
	}
	return NewMessage("agent", "", MessageTypeTaskComplete, body)
}

// NewTaskAssignMessage 创建任务重新分配消息
func NewTaskAssignMessage(taskID, newAssignee, reason string) (*Message, error) {
	body := &TaskAssignBody{
		TaskID:      taskID,
		NewAssignee: newAssignee,
		Reason:      reason,
	}
	return NewMessage("scheduler", "", MessageTypeTaskAssign, body)
}

// NewRequestMessage 创建一般请求消息
func NewRequestMessage(sender, receiver, msgType string, content any, metadata map[string]any) (*Message, error) {
	body := &RequestBody{
		Type:     msgType,
		Content:  content,
		Metadata: metadata,
	}
	return NewMessage(sender, receiver, MessageTypeRequest, body)
}

// NewResponseMessage 创建响应消息
func NewResponseMessage(requestID string, success bool, content any, errorMessage string) (*Message, error) {
	body := &ResponseBody{
		RequestID:    requestID,
		Success:      success,
		Content:      content,
		ErrorMessage: errorMessage,
	}
	return NewMessage("", "", MessageTypeResponse, body)
}

// NewNotificationMessage 创建通知消息
func NewNotificationMessage(sender, receiver, title, content, priority string) (*Message, error) {
	body := &NotificationBody{
		Title:    title,
		Content:  content,
		Priority: priority,
	}
	return NewMessage(sender, receiver, MessageTypeNotification, body)
}

// UnmarshalBody 反序列化消息体到指定类型
func (m *Message) UnmarshalBody(v any) error {
	return json.Unmarshal(m.Body.(json.RawMessage), v)
}

// GetTaskCreateBody 获取任务创建消息体
func (m *Message) GetTaskCreateBody() (*TaskCreateBody, bool) {
	if body, ok := m.Body.(*TaskCreateBody); ok {
		return body, true
	}
	if rawBody, ok := m.Body.(json.RawMessage); ok {
		var body TaskCreateBody
		if err := json.Unmarshal(rawBody, &body); err == nil {
			return &body, true
		}
	}
	return nil, false
}

// GetTaskUpdateBody 获取任务更新消息体
func (m *Message) GetTaskUpdateBody() (*TaskUpdateBody, bool) {
	if body, ok := m.Body.(*TaskUpdateBody); ok {
		return body, true
	}
	return nil, false
}

// GetTaskCompleteBody 获取任务完成消息体
func (m *Message) GetTaskCompleteBody() (*TaskCompleteBody, bool) {
	if body, ok := m.Body.(*TaskCompleteBody); ok {
		return body, true
	}
	return nil, false
}

// GetTaskAssignBody 获取任务分配消息体
func (m *Message) GetTaskAssignBody() (*TaskAssignBody, bool) {
	if body, ok := m.Body.(*TaskAssignBody); ok {
		return body, true
	}
	return nil, false
}

// GetRequestBody 获取请求消息体
func (m *Message) GetRequestBody() (*RequestBody, bool) {
	if body, ok := m.Body.(*RequestBody); ok {
		return body, true
	}
	return nil, false
}

// GetResponseBody 获取响应消息体
func (m *Message) GetResponseBody() (*ResponseBody, bool) {
	if body, ok := m.Body.(*ResponseBody); ok {
		return body, true
	}
	return nil, false
}

// GetNotificationBody 获取通知消息体
func (m *Message) GetNotificationBody() (*NotificationBody, bool) {
	if body, ok := m.Body.(*NotificationBody); ok {
		return body, true
	}
	return nil, false
}
