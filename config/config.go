package config

import (
	"os"

	"gopkg.in/yaml.v3"
)

type Config struct {
	LLM       []LLMConfig      `yaml:"llm"`
	DB        *DBConfig        `yaml:"db"`
	Agents    []AgentConfig    `yaml:"agents"`
	Scheduler *SchedulerConfig `yaml:"scheduler"`
	Timer     *TimerConfig     `yaml:"timer"`
}

type LLMConfig struct {
	Model   string `yaml:"model"`
	BaseURL string `yaml:"base_url"`
	APIKey  string `yaml:"api_key"`
}

type DBConfig struct {
	Name string `yaml:"name"`
}

type AgentConfig struct {
	Name            string  `yaml:"name"`
	Desc            string  `yaml:"desc"`
	Model           string  `yaml:"model"`
	Temperature     float64 `yaml:"temperature"`
	Hierarchy       int     `yaml:"hierarchy"`
	SkillDir        string  `yaml:"skill_dir"`
	TaskGenInterval string  `yaml:"task_gen_interval"` // 任务生成间隔，如 "30m"，默认 "30m"
	MaxTasks        int     `yaml:"max_tasks"`         // 最大并发任务数，默认 3
}

// SchedulerConfig 调度器配置
type SchedulerConfig struct {
	TickInterval string `yaml:"tick_interval"` // 调度轮询间隔，如 "5s"，默认 "5s"
}

// TimerConfig 定时器配置
type TimerConfig struct {
	Enabled bool       `yaml:"enabled"`
	Jobs    []TimerJob `yaml:"jobs"`
}

// TimerJob 定时任务配置
type TimerJob struct {
	Name        string          `yaml:"name"`
	Interval    string          `yaml:"interval"` // 间隔，如 "30m", "1h", "24h"
	TargetAgent string          `yaml:"target_agent"`
	Task        TimerTaskConfig `yaml:"task"`
}

// TimerTaskConfig 定时任务模板
type TimerTaskConfig struct {
	Title       string `yaml:"title"`
	Description string `yaml:"description"`
	Priority    string `yaml:"priority"` // Critical, High, Medium, Low
}

var AppConfig Config

func InitConfig() error {
	data, err := os.ReadFile("config.yaml")
	if err != nil {
		return err
	}
	err = yaml.Unmarshal(data, &AppConfig)
	return err
}
