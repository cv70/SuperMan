package config

import (
	"os"

	"gopkg.in/yaml.v3"
)

type Config struct {
	LLM      []LLMConfig            `yaml:"llm"`
	Database *DatabaseConfig        `yaml:"database"`
	Agents   []AgentConfig          `yaml:"agents"`
}

type LLMConfig struct {
	Model   string `yaml:"model"`
	BaseURL string `yaml:"base_url"`
	APIKey  string `yaml:"api_key"`
}

type DatabaseConfig struct {
	DBName string `json:"db_name"`
}

type AgentConfig struct {
	Name        string   `yaml:"name"`
	Desc        string   `yaml:"desc"`
	Model       string   `yaml:"model"`
	Temperature float64  `yaml:"temperature"`
	Hierarchy   int      `yaml:"hierarchy"`
	SkillDir    string   `yaml:"skill_dir"`
	SendTo      []string `yaml:"send_to"`
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
