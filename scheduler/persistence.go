package scheduler

import (
	"encoding/json"

	"gorm.io/gorm"
)

type TaskRecord struct {
	TaskID       string `json:"task_id" gorm:"primaryKey"`
	Title        string `json:"title"`
	Description  string `json:"description"`
	AssignedTo   string `json:"assigned_to"`
	AssignedBy   string `json:"assigned_by"`
	Status       string `json:"status"`
	Priority     string `json:"priority"`
	CreatedAt    string `json:"created_at"`
	Source       string `json:"source"`
	GeneratedBy  string `json:"generated_by"`
	Metadata     string `json:"metadata"`
}

type ExecutionRecord struct {
	ExecutionID   string `json:"execution_id" gorm:"primaryKey"`
	TaskID        string `json:"task_id"`
	AgentName     string `json:"agent_name"`
	Action        string `json:"action"`
	Input         string `json:"input"`
	Output        string `json:"output"`
	Status        string `json:"status"`
	DurationMS    int64  `json:"duration_ms"`
	ErrorMessage  string `json:"error_message"`
	Timestamp     string `json:"timestamp"`
}

type CronJob struct {
	JobID        string `json:"job_id" gorm:"primaryKey"`
	Name         string `json:"name"`
	CronExpr     string `json:"cron_expr"`
	TargetAgent  string `json:"target_agent"`
	TaskTemplate string `json:"task_template"`
}

type AgentConfig struct {
	AgentName   string `json:"agent_name" gorm:"primaryKey"`
	Description string `json:"description"`
	Model       string `json:"model"`
	Hierarchy   int    `json:"hierarchy"`
	SkillDir    string `json:"skill_dir"`
}

type Persistence struct {
	db *gorm.DB
}

func NewPersistence(db *gorm.DB) *Persistence {
	return &Persistence{db: db}
}

func (p *Persistence) Migrate() error {
	return p.db.AutoMigrate(&TaskRecord{}, &ExecutionRecord{}, &CronJob{}, &AgentConfig{})
}

func (p *Persistence) SaveTask(task *TaskRecord) error {
	return p.db.Create(task).Error
}

func (p *Persistence) GetTask(taskID string) (*TaskRecord, error) {
	var record TaskRecord
	err := p.db.Where("task_id = ?", taskID).First(&record).Error
	if err != nil {
		return nil, err
	}
	return &record, nil
}

func (p *Persistence) SaveExecution(execution *ExecutionRecord) error {
	return p.db.Create(execution).Error
}

func (p *Persistence) SaveCronJob(job *CronJob) error {
	return p.db.Create(job).Error
}

func (p *Persistence) GetCronJobs() ([]*CronJob, error) {
	var jobs []*CronJob
	err := p.db.Find(&jobs).Error
	return jobs, err
}

func (p *Persistence) SaveAgentConfig(agent *AgentConfig) error {
	return p.db.Create(agent).Error
}

func ToJSON(v interface{}) string {
	b, _ := json.Marshal(v)
	return string(b)
}
