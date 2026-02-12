package ds

import (
	"time"
)

// TaskStatus 任务状态
type TaskStatus string

const (
	TaskStatusPending    TaskStatus = "pending"    // 待处理
	TaskStatusAssigned   TaskStatus = "assigned"   // 已分配
	TaskStatusProcessing TaskStatus = "processing" // 处理中
	TaskStatusCompleted  TaskStatus = "completed"  // 已完成
	TaskStatusFailed     TaskStatus = "failed"     // 失败
	TaskStatusCancelled  TaskStatus = "cancelled"  // 已取消
)

// TaskPriority 任务优先级
type TaskPriority string

const (
	TaskPriorityCritical TaskPriority = "critical" // 紧急
	TaskPriorityHigh     TaskPriority = "high"     // 高
	TaskPriorityMedium   TaskPriority = "medium"   // 中
	TaskPriorityLow      TaskPriority = "low"      // 低
)

// Task 代表一个任务
type Task struct {
	ID           string         `json:"id" gorm:"primaryKey"`
	Title        string         `json:"title"`
	Description  string         `json:"description"`
	AssignedTo   string         `json:"assigned_to"`
	AssignedBy   string         `json:"assigned_by"`
	Status       TaskStatus     `json:"status"`
	Priority     TaskPriority   `json:"priority"`
	Dependencies []string       `json:"dependencies"`
	Deliverables []string       `json:"deliverables"`
	Deadline     *time.Time     `json:"deadline,omitempty"`
	CreatedAt    time.Time      `json:"created_at"`
	UpdatedAt    time.Time      `json:"updated_at"`
	Metadata     map[string]any `json:"metadata,omitempty"`
}

// NewTask 创建新任务
func NewTask(taskID, title, description, assignedTo, assignedBy string, status TaskStatus, priority TaskPriority) *Task {
	now := time.Now()
	return &Task{
		ID:       taskID,
		Title:        title,
		Description:  description,
		AssignedTo:   assignedTo,
		AssignedBy:   assignedBy,
		Status:       status,
		Priority:     priority,
		Dependencies: make([]string, 0),
		Deliverables: make([]string, 0),
		CreatedAt:    now,
		UpdatedAt:    now,
		Metadata:     make(map[string]any),
	}
}

// NewTaskWithDependencies 创建带依赖的任务
func NewTaskWithDependencies(taskID, title, description, assignedTo, assignedBy string, status TaskStatus, priority TaskPriority, dependencies []string) *Task {
	task := NewTask(taskID, title, description, assignedTo, assignedBy, status, priority)
	task.Dependencies = dependencies
	return task
}

// NewTaskWithDeliverables 创建带交付物的任务
func NewTaskWithDeliverables(taskID, title, description, assignedTo, assignedBy string, status TaskStatus, priority TaskPriority, deliverables []string) *Task {
	task := NewTask(taskID, title, description, assignedTo, assignedBy, status, priority)
	task.Deliverables = deliverables
	return task
}

// GenerateTaskID 生成任务ID
func GenerateTaskID() string {
	return "auto_" + time.Now().Format("20060102_150405")
}

// SetDependencies 设置依赖
func (t *Task) SetDependencies(dependencies []string) {
	t.Dependencies = dependencies
	t.UpdatedAt = time.Now()
}

// AddDependency 添加依赖
func (t *Task) AddDependency(dependency string) {
	for _, dep := range t.Dependencies {
		if dep == dependency {
			return
		}
	}
	t.Dependencies = append(t.Dependencies, dependency)
	t.UpdatedAt = time.Now()
}

// RemoveDependency 移除依赖
func (t *Task) RemoveDependency(dependency string) {
	for i, dep := range t.Dependencies {
		if dep == dependency {
			t.Dependencies = append(t.Dependencies[:i], t.Dependencies[i+1:]...)
			t.UpdatedAt = time.Now()
			return
		}
	}
}

// SetDeliverables 设置交付物
func (t *Task) SetDeliverables(deliverables []string) {
	t.Deliverables = deliverables
	t.UpdatedAt = time.Now()
}

// AddDeliverable 添加交付物
func (t *Task) AddDeliverable(deliverable string) {
	for _, d := range t.Deliverables {
		if d == deliverable {
			return
		}
	}
	t.Deliverables = append(t.Deliverables, deliverable)
	t.UpdatedAt = time.Now()
}

// SetDeadline 设置截止日期
func (t *Task) SetDeadline(deadline *time.Time) {
	t.Deadline = deadline
	t.UpdatedAt = time.Now()
}

// SetMetadata 设置元数据
func (t *Task) SetMetadata(metadata map[string]any) {
	t.Metadata = metadata
	t.UpdatedAt = time.Now()
}

// SetStatus 设置状态
func (t *Task) SetStatus(status TaskStatus) {
	t.Status = status
	t.UpdatedAt = time.Now()
}

// SetPriority 设置优先级
func (t *Task) SetPriority(priority TaskPriority) {
	t.Priority = priority
	t.UpdatedAt = time.Now()
}

// Copy 创建任务副本
func (t *Task) Copy() *Task {
	metadataCopy := make(map[string]any)
	for k, v := range t.Metadata {
		metadataCopy[k] = v
	}
	dependenciesCopy := make([]string, len(t.Dependencies))
	copy(dependenciesCopy, t.Dependencies)
	deliverablesCopy := make([]string, len(t.Deliverables))
	copy(deliverablesCopy, t.Deliverables)

	var deadlineCopy *time.Time
	if t.Deadline != nil {
		deadlineCopy = &time.Time{}
		*deadlineCopy = *t.Deadline
	}

	return &Task{
		ID:       t.ID,
		Title:        t.Title,
		Description:  t.Description,
		AssignedTo:   t.AssignedTo,
		AssignedBy:   t.AssignedBy,
		Status:       t.Status,
		Priority:     t.Priority,
		Dependencies: dependenciesCopy,
		Deliverables: deliverablesCopy,
		Deadline:     deadlineCopy,
		CreatedAt:    t.CreatedAt,
		UpdatedAt:    t.UpdatedAt,
		Metadata:     metadataCopy,
	}
}

// IsCompleted 检查任务是否完成
func (t *Task) IsCompleted() bool {
	return t.Status == TaskStatusCompleted || t.Status == TaskStatusFailed || t.Status == TaskStatusCancelled
}

// IsPending 检查任务是否待处理
func (t *Task) IsPending() bool {
	return t.Status == TaskStatusPending || t.Status == TaskStatusAssigned
}

// HasDependencies 检查是否有依赖
func (t *Task) HasDependencies() bool {
	return len(t.Dependencies) > 0
}

// HasDependencyOn 检查是否有特定依赖
func (t *Task) HasDependencyOn(taskID string) bool {
	for _, dep := range t.Dependencies {
		if dep == taskID {
			return true
		}
	}
	return false
}

// Clone 更新任务字段并返回新任务
func (t *Task) Clone(updater func(*Task)) *Task {
	newTask := t.Copy()
	updater(newTask)
	return newTask
}
