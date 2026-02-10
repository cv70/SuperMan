package types

import "time"

type Task struct {
	TaskID       string
	Title        string
	Description  string
	AssignedTo   string
	AssignedBy   string
	Status       string
	Dependencies []string
	Deliverables []string
	Deadline     *time.Time
	CreatedAt    time.Time
	UpdatedAt    time.Time
	Metadata     map[string]any
}
