package config

type Config struct {
	LLM []LLMConfig `yaml:"llm"`
	Database      *DatabaseConfig  `yaml:"database"`
	Agents map[string]AgentConfig `yaml:"agents"`
}

type LLMConfig struct {
	Model        string         `yaml:"model"`
	BaseURL      string         `yaml:"base_url"`
	APIKey       string         `yaml:"api_key"`
}

type DatabaseConfig struct {
	DBName   string `json:"db_name"`
}

type AgentConfig struct {
	Model       string  `yaml:"model"`
	Temperature float64 `yaml:"temperature"`
}

var AppConfig Config

func InitConfig() {
	AppConfig = Config{
		Agents: make(map[string]AgentConfig),
	}
}
