package infra

import (
	"context"
	"superman/config"

	"github.com/cloudwego/eino/components/model"
	"gorm.io/gorm"
)

type Registry struct {
	DB  *gorm.DB
	LLM map[string]model.ToolCallingChatModel
}

func NewRegistry(ctx context.Context, c *config.Config) (*Registry, error) {
	r := &Registry{
		LLM: make(map[string]model.ToolCallingChatModel),
	}
	db, err := NewDB(ctx, c.DB)
	if err != nil {
		return nil, err
	}
	r.DB = db
	for _, llmConfig := range c.LLM {
		llm, err := NewLLM(ctx, &llmConfig)
		if err != nil {
			return nil, err
		}
		r.LLM[llmConfig.Model] = llm
	}
	return r, nil
}
