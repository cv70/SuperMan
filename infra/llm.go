package infra

import (
	"context"
	"superman/config"

	"github.com/cloudwego/eino-ext/components/model/qwen"
	"github.com/cloudwego/eino/components/model"
)

func NewLLM(ctx context.Context, c *config.LLMConfig) (model.ToolCallingChatModel, error) {
	model, err := qwen.NewChatModel(ctx, &qwen.ChatModelConfig{
		Model:   c.Model,
		BaseURL: c.BaseURL,
		APIKey:  c.APIKey,
	})
	return model, err
}
