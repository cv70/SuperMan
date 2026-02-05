package agents

import (
	"context"
	"fmt"
	"math/rand"
	"time"

	"superman/types"
)

type CPOAgent struct {
	*BaseAgentImpl
}

func NewCPOAgent(ctx context.Context) (*CPOAgent, error) {
	baseAgent, err := NewBaseAgent(
		ctx,
		types.AgentRoleCPO,
		2,
	)
	if err != nil {
		return nil, err
	}
	return &CPOAgent{
		BaseAgentImpl: baseAgent,
	}, nil
}

func (a *CPOAgent) ProcessMessage(msg *types.Message) error {
	a.mu.Lock()
	defer a.mu.Unlock()

	a.messages = append(a.messages, msg)
	a.lastActive = time.Now()

	switch msg.MessageType {
	case types.MessageTypeStatusReport:
		return a.handleStatusReport(msg)
	case types.MessageTypeTaskAssignment:
		return a.handleTaskAssignment(msg)
	case types.MessageTypeDataRequest:
		return a.handleDataRequest(msg)
	case types.MessageTypeAlert:
		return a.handleAlert(msg)
	default:
		return nil
	}
}

func (a *CPOAgent) handleStatusReport(msg *types.Message) error {
	content := msg.Content
	if report, ok := content["report_type"].(string); ok {
		fmt.Printf("[CPO] Received %s status report from %s\n", report, msg.Sender)

		// Product analysis and user experience evaluation
		switch report {
		case "user_feedback":
			a.analyzeUserFeedback(content)
		case "product_metrics":
			a.analyzeProductMetrics(content)
		case "market_research":
			a.analyzeMarketResearch(content)
		case "usability":
			a.analyzeUsabilityReport(content)
		}
	}
	return nil
}

func (a *CPOAgent) handleTaskAssignment(msg *types.Message) error {
	content := msg.Content
	if taskData, ok := content["task"].(map[string]any); ok {
		fmt.Printf("[CPO] Assigning product task: %s\n", taskData["title"])

		// Product planning and feature prioritization
		productStrategy := a.defineProductStrategy(taskData)
		a.prioritizeFeatures(taskData, productStrategy)
	}
	return nil
}

func (a *CPOAgent) handleDataRequest(msg *types.Message) error {
	content := msg.Content
	if dataType, ok := content["data_type"].(string); ok {
		fmt.Printf("[CPO] Requesting product data: %s\n", dataType)

		// User research and data analysis
		a.conductUserResearch(content, dataType)
		a.generateProductInsights(content, dataType)
	}
	return nil
}

func (a *CPOAgent) handleAlert(msg *types.Message) error {
	content := msg.Content
	if severity, ok := content["severity"].(string); ok {
		fmt.Printf("[CPO] Product alert (severity: %s): %s\n", severity, content["description"])
	}
	return nil
}

func (a *CPOAgent) GetRoleHierarchy() int {
	return 2
}

// Product planning and user research methods
func (a *CPOAgent) analyzeUserFeedback(content map[string]any) {
	if satisfaction, ok := content["satisfaction_score"].(float64); ok {
		if satisfaction > 4.5 {
			fmt.Printf("[CPO] Excellent user satisfaction: %.1f/5 - Scale successful features\n", satisfaction)
		} else if satisfaction > 3.5 {
			fmt.Printf("[CPO] Good user satisfaction: %.1f/5 - Incremental improvements needed\n", satisfaction)
		} else {
			fmt.Printf("[CPO] User satisfaction concerns: %.1f/5 - Major UX overhaul required\n", satisfaction)
		}
	}

	if feedbackCount, ok := content["feedback_count"].(int); ok {
		fmt.Printf("[CPO] User engagement: %d feedback responses - Analyze trends\n", feedbackCount)
	}
}

func (a *CPOAgent) analyzeProductMetrics(content map[string]any) {
	if adoption, ok := content["adoption_rate"].(float64); ok {
		if adoption > 0.7 {
			fmt.Printf("[CPO] Strong product adoption: %.1f%% - Focus on retention\n", adoption*100)
		} else {
			fmt.Printf("[CPO] Product adoption opportunity: %.1f%% - Enhance onboarding\n", adoption*100)
		}
	}

	if retention, ok := content["retention_rate"].(float64); ok {
		if retention > 0.8 {
			fmt.Printf("[CPO] Excellent retention: %.1f%% - Maintain quality\n", retention*100)
		} else {
			fmt.Printf("[CPO] Retention improvement needed: %.1f%% - Add value features\n", retention*100)
		}
	}
}

func (a *CPOAgent) analyzeMarketResearch(content map[string]any) {
	if marketSize, ok := content["market_size"].(float64); ok {
		fmt.Printf("[CPO] Market opportunity: $%.2fM - Validate product-market fit\n", marketSize)
	}

	if competitorCount, ok := content["competitor_count"].(int); ok {
		if competitorCount > 5 {
			fmt.Printf("[CPO] Competitive market: %d competitors - Differentiate strongly\n", competitorCount)
		} else {
			fmt.Printf("[CPO] Market opportunity: %d competitors - First-mover advantage\n", competitorCount)
		}
	}
}

func (a *CPOAgent) analyzeUsabilityReport(content map[string]any) {
	if taskCompletion, ok := content["task_completion_rate"].(float64); ok {
		if taskCompletion > 0.9 {
			fmt.Printf("[CPO] Excellent usability: %.1f%% completion - Intuitive design\n", taskCompletion*100)
		} else {
			fmt.Printf("[CPO] Usability improvements needed: %.1f%% completion - Simplify workflows\n", taskCompletion*100)
		}
	}
}

func (a *CPOAgent) defineProductStrategy(taskData map[string]any) string {
	// Product strategy framework
	if market, ok := taskData["market_position"].(string); ok {
		switch market {
		case "emerging":
			return "innovation_first"
		case "mature":
			return "optimization_focused"
		default:
			return "balanced_growth"
		}
	}
	return "balanced_growth"
}

func (a *CPOAgent) prioritizeFeatures(taskData map[string]any, strategy string) {
	features := []string{"Core functionality", "User experience", "Performance", "Security"}
	priority := rand.Perm(len(features))

	fmt.Printf("[CPO] Feature prioritization - Strategy: %s, Priority order: %v\n",
		strategy, priority)
}

func (a *CPOAgent) conductUserResearch(content map[string]any, dataType string) {
	methods := []string{"User interviews", "Surveys", "Usability testing", "A/B testing"}
	sampleSize := rand.Intn(500) + 100

	fmt.Printf("[CPO] User research - Method: %s, Sample size: %d users\n",
		methods[rand.Intn(len(methods))], sampleSize)
}

func (a *CPOAgent) generateProductInsights(content map[string]any, dataType string) {
	insights := []string{
		"Users prefer simplified workflows",
		"Mobile experience needs improvement",
		"Integration requests increasing",
		"Price sensitivity detected",
	}

	selectedInsights := insights[rand.Intn(len(insights))+1:]
	fmt.Printf("[CPO] Product insights: %v\n", selectedInsights)
}
