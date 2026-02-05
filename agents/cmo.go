package agents

import (
	"context"
	"fmt"
	"math/rand"
	"time"

	"superman/types"
)

type CMOAgent struct {
	*BaseAgentImpl
}

func NewCMOAgent(ctx context.Context) (*CMOAgent, error) {
	baseAgent, err := NewBaseAgent(
		ctx,
		types.AgentRoleCMO,
		2,
	)
	if err != nil {
		return nil, err
	}
	return &CMOAgent{
		BaseAgentImpl: baseAgent,
	}, nil
}

func (a *CMOAgent) ProcessMessage(msg *types.Message) error {
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
	default:
		return nil
	}
}

func (a *CMOAgent) handleStatusReport(msg *types.Message) error {
	content := msg.Content
	if report, ok := content["report_type"].(string); ok {
		fmt.Printf("[CMO] Received %s status report from %s\n", report, msg.Sender)

		// Marketing analysis and campaign evaluation
		switch report {
		case "campaign_performance":
			a.analyzeCampaignPerformance(content)
		case "brand_metrics":
			a.analyzeBrandMetrics(content)
		case "customer_acquisition":
			a.analyzeCustomerAcquisition(content)
		case "market_position":
			a.analyzeMarketPosition(content)
		}
	}
	return nil
}

func (a *CMOAgent) handleTaskAssignment(msg *types.Message) error {
	content := msg.Content
	if taskData, ok := content["task"].(map[string]any); ok {
		fmt.Printf("[CMO] Assigning marketing task: %s\n", taskData["title"])

		// Marketing strategy and campaign planning
		strategy := a.developMarketingStrategy(taskData)
		a.planCampaignExecution(taskData, strategy)
	}
	return nil
}

func (a *CMOAgent) handleDataRequest(msg *types.Message) error {
	content := msg.Content
	if dataType, ok := content["data_type"].(string); ok {
		fmt.Printf("[CMO] Requesting marketing data: %s\n", dataType)

		// Market research and competitive analysis
		a.conductMarketAnalysis(content, dataType)
		a.performCompetitiveIntelligence(content, dataType)
	}
	return nil
}

func (a *CMOAgent) GetRoleHierarchy() int {
	return 2
}

// Marketing strategy and campaign management methods
func (a *CMOAgent) analyzeCampaignPerformance(content map[string]any) {
	if roi, ok := content["roi"].(float64); ok {
		if roi > 3.0 {
			fmt.Printf("[CMO] Excellent campaign ROI: %.2fx - Scale successful campaigns\n", roi)
		} else if roi > 1.5 {
			fmt.Printf("[CMO] Good campaign ROI: %.2fx - Optimize and expand\n", roi)
		} else {
			fmt.Printf("[CMO] Campaign ROI improvement needed: %.2fx - Reassess strategy\n", roi)
		}
	}

	if conversion, ok := content["conversion_rate"].(float64); ok {
		fmt.Printf("[CMO] Campaign conversion rate: %.2f%% - A/B test for improvement\n", conversion*100)
	}
}

func (a *CMOAgent) analyzeBrandMetrics(content map[string]any) {
	if awareness, ok := content["brand_awareness"].(float64); ok {
		if awareness > 0.7 {
			fmt.Printf("[CMO] Strong brand awareness: %.1f%% - Maintain brand consistency\n", awareness*100)
		} else {
			fmt.Printf("[CMO] Brand awareness opportunity: %.1f%% - Increase brand visibility\n", awareness*100)
		}
	}

	if sentiment, ok := content["brand_sentiment"].(float64); ok {
		if sentiment > 0.8 {
			fmt.Printf("[CMO] Positive brand sentiment: %.1f%% - Leverage advocacy\n", sentiment*100)
		} else {
			fmt.Printf("[CMO] Brand sentiment improvement: %.1f%% - Address negative perceptions\n", sentiment*100)
		}
	}
}

func (a *CMOAgent) analyzeCustomerAcquisition(content map[string]any) {
	if cac, ok := content["customer_acquisition_cost"].(float64); ok {
		if cac < 100 {
			fmt.Printf("[CMO] Efficient CAC: $%.2f - Scale acquisition channels\n", cac)
		} else {
			fmt.Printf("[CMO] CAC optimization needed: $%.2f - Improve funnel efficiency\n", cac)
		}
	}

	if ltv, ok := content["lifetime_value"].(float64); ok {
		fmt.Printf("[CMO] Customer LTV: $%.2f - Focus on retention strategies\n", ltv)
	}
}

func (a *CMOAgent) analyzeMarketPosition(content map[string]any) {
	if marketShare, ok := content["market_share"].(float64); ok {
		if marketShare > 0.3 {
			fmt.Printf("[CMO] Market leadership: %.1f%% - Defend market position\n", marketShare*100)
		} else {
			fmt.Printf("[CMO] Market share growth: %.1f%% - Aggressive acquisition strategy\n", marketShare*100)
		}
	}
}

func (a *CMOAgent) developMarketingStrategy(taskData map[string]any) string {
	// Marketing strategy framework
	if target, ok := taskData["target_audience"].(string); ok {
		switch target {
		case "enterprise":
			return "account_based_marketing"
		case "consumer":
			return "digital_first_marketing"
		default:
			return "integrated_marketing"
		}
	}
	return "integrated_marketing"
}

func (a *CMOAgent) planCampaignExecution(taskData map[string]any, strategy string) {
	channels := []string{"Social media", "Email marketing", "Content marketing", "PPC advertising"}
	_ = channels // 避免未使用变量警告
	budget := rand.Float64()*100000 + 10000
	duration := rand.Intn(90) + 30

	fmt.Printf("[CMO] Campaign plan - Strategy: %s, Budget: $%.2f, Duration: %d days\n",
		strategy, budget, duration)
}

func (a *CMOAgent) conductMarketAnalysis(content map[string]any, dataType string) {
	methods := []string{"Surveys", "Focus groups", "Market research reports", "Social listening"}
	sampleSize := rand.Intn(1000) + 200

	fmt.Printf("[CMO] Market analysis - Method: %s, Sample: %d respondents\n",
		methods[rand.Intn(len(methods))], sampleSize)
}

func (a *CMOAgent) performCompetitiveIntelligence(content map[string]any, dataType string) {
	competitors := []string{"Competitor A", "Competitor B", "Competitor C"}
	analysis := []string{"Pricing analysis", "Feature comparison", "Marketing tactics", "Market positioning"}

	fmt.Printf("[CMO] Competitive intelligence - Tracking %d competitors, Analysis: %v\n",
		len(competitors), analysis[rand.Intn(len(analysis))+1])
}
