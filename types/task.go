package types

import "time"

type Task struct {
	TaskID       string
	Title        string
	Description  string
	AssignedTo   AgentRole
	AssignedBy   AgentRole
	Status       string
	Dependencies []string
	Deliverables []string
	Deadline     *time.Time
	CreatedAt    time.Time
	UpdatedAt    time.Time
	Metadata     map[string]any
}
