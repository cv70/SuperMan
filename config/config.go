package config

import (
	"os"

	"gopkg.in/yaml.v3"
)

type Config struct {
	LLM      []LLMConfig            `yaml:"llm"`
	DB       *DBConfig              `yaml:"db"`
	Agents   []AgentConfig          `yaml:"agents"`
}

type LLMConfig struct {
	Model   string `yaml:"model"`
	BaseURL string `yaml:"base_url"`
	APIKey  string `yaml:"api_key"`
}

type DBConfig struct {
	Name string `json:"name"`
}

type AgentConfig struct {
	Name        string   `yaml:"name"`
	Desc        string   `yaml:"desc"`
	Model       string   `yaml:"model"`
	Temperature float64  `yaml:"temperature"`
	Hierarchy   int      `yaml:"hierarchy"`
	SkillDir    string   `yaml:"skill_dir"`
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
