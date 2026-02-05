package infra

import (
	"context"
	"superman/config"

	"github.com/cv70/pkgo/llm"
	"google.golang.org/adk/model"
)

func NewLLM(ctx context.Context, c *config.LLMConfig) (model.LLM, error) {
	model, err := llm.NewModel(ctx, c.Model, &llm.ClientConfig{
		BaseURL: c.BaseURL,
		APIKey:  c.APIKey,
	})
	return model, err
}
