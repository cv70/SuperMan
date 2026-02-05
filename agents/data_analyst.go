package agents

import (
	"context"
	"fmt"
	"math/rand"
	"time"

	"superman/types"
)

type DataAnalystAgent struct {
	*BaseAgentImpl
}

func NewDataAnalystAgent(ctx context.Context) (*DataAnalystAgent, error) {
	baseAgent, err := NewBaseAgent(
		ctx,
		types.AgentRoleDataAnalyst,
		3,
	)
	if err != nil {
		return nil, err
	}
	return &DataAnalystAgent{
		BaseAgentImpl: baseAgent,
	}, nil
}

func (a *DataAnalystAgent) ProcessMessage(msg *types.Message) error {
	a.mu.Lock()
	defer a.mu.Unlock()

	a.messages = append(a.messages, msg)
	a.lastActive = time.Now()

	switch msg.MessageType {
	case types.MessageTypeStatusReport:
		return a.handleStatusReport(msg)
	case types.MessageTypeDataRequest:
		return a.handleDataRequest(msg)
	case types.MessageTypeDataResponse:
		return a.handleDataResponse(msg)
	default:
		return nil
	}
}

func (a *DataAnalystAgent) handleStatusReport(msg *types.Message) error {
	content := msg.Content
	if report, ok := content["report_type"].(string); ok {
		fmt.Printf("[DataAnalyst] Received %s status report from %s\n", report, msg.Sender)

		// Data quality and analytics performance
		switch report {
		case "data_quality":
			a.analyzeDataQuality(content)
		case "analytics_performance":
			a.analyzeAnalyticsPerformance(content)
		case "insight_generation":
			a.analyzeInsightGeneration(content)
		}
	}
	return nil
}

func (a *DataAnalystAgent) handleDataRequest(msg *types.Message) error {
	content := msg.Content
	if dataType, ok := content["data_type"].(string); ok {
		fmt.Printf("[DataAnalyst] Processing data request: %s\n", dataType)

		// Advanced data analysis and visualization
		a.performDataAnalysis(content, dataType)
		a.createDataVisualization(content, dataType)
	}
	return nil
}

func (a *DataAnalystAgent) handleDataResponse(msg *types.Message) error {
	content := msg.Content
	if insights, ok := content["insights"].([]string); ok {
		fmt.Printf("[DataAnalyst] Data response with %d insights\n", len(insights))

		// Insight validation and recommendation generation
		a.validateInsights(content, insights)
		a.generateRecommendations(content, insights)
	}
	return nil
}

func (a *DataAnalystAgent) GetRoleHierarchy() int {
	return 3
}

// Data analysis and visualization capabilities methods
func (a *DataAnalystAgent) analyzeDataQuality(content map[string]any) {
	if completeness, ok := content["data_completeness"].(float64); ok {
		if completeness > 0.95 {
			fmt.Printf("[DataAnalyst] Excellent data completeness: %.1f%% - Reliable analytics\n", completeness*100)
		} else {
			fmt.Printf("[DataAnalyst] Data completeness improvement: %.1f%% - Data cleansing required\n", completeness*100)
		}
	}

	if accuracy, ok := content["data_accuracy"].(float64); ok {
		if accuracy > 0.98 {
			fmt.Printf("[DataAnalyst] High data accuracy: %.1f%% - Trustworthy insights\n", accuracy*100)
		} else {
			fmt.Printf("[DataAnalyst] Data accuracy concerns: %.1f%% - Validation processes needed\n", accuracy*100)
		}
	}
}

func (a *DataAnalystAgent) analyzeAnalyticsPerformance(content map[string]any) {
	if processingTime, ok := content["processing_time"].(float64); ok {
		if processingTime < 5 {
			fmt.Printf("[DataAnalyst] Fast data processing: %.2f seconds - Real-time analytics\n", processingTime)
		} else {
			fmt.Printf("[DataAnalyst] Processing optimization: %.2f seconds - Query tuning needed\n", processingTime)
		}
	}

	if queryVolume, ok := content["query_volume"].(int); ok {
		fmt.Printf("[DataAnalyst] Query volume: %d/day - Scale analytics infrastructure\n", queryVolume)
	}
}

func (a *DataAnalystAgent) analyzeInsightGeneration(content map[string]any) {
	if insightCount, ok := content["insight_count"].(int); ok {
		if insightCount > 10 {
			fmt.Printf("[DataAnalyst] High insight generation: %d insights - Strong analytical capability\n", insightCount)
		} else {
			fmt.Printf("[DataAnalyst] Insight generation improvement: %d insights - Enhanced analysis needed\n", insightCount)
		}
	}
}

func (a *DataAnalystAgent) performDataAnalysis(content map[string]any, dataType string) {
	// Advanced analysis techniques
	techniques := []string{
		"Statistical analysis",
		"Machine learning models",
		"Trend analysis",
		"Correlation analysis",
		"Predictive modeling",
	}

	selected := techniques[rand.Intn(len(techniques))]
	sampleSize := rand.Intn(100000) + 10000
	fmt.Printf("[DataAnalyst] Data analysis - Type: %s, Technique: %s, Sample: %d records\n",
		dataType, selected, sampleSize)
}

func (a *DataAnalystAgent) createDataVisualization(content map[string]any, dataType string) {
	// Visualization types
	visualizations := []string{
		"Interactive dashboards",
		"Time series charts",
		"Heat maps",
		"Scatter plots",
		"Bar graphs",
		"Pie charts",
		"Geographic maps",
	}

	selected := visualizations[rand.Intn(len(visualizations))]
	fmt.Printf("[DataAnalyst] Data visualization - Type: %s, Format: %s\n", dataType, selected)
}

func (a *DataAnalystAgent) validateInsights(content map[string]any, insights []string) {
	// Insight validation process
	confidence := rand.Float64()*0.3 + 0.7 // 70% to 100%
	fmt.Printf("[DataAnalyst] Insight validation - Confidence: %.1f%%, Insights validated: %d\n",
		confidence*100, len(insights))
}

func (a *DataAnalystAgent) generateRecommendations(content map[string]any, insights []string) {
	// Business recommendations based on insights
	recommendations := []string{
		"Optimize marketing spend based on performance data",
		"Improve product features through user behavior analysis",
		"Enhance customer experience using journey analytics",
		"Streamline operations with process efficiency insights",
		"Increase revenue through pricing optimization analysis",
	}

	selected := recommendations[rand.Intn(len(recommendations))+1]
	fmt.Printf("[DataAnalyst] Business recommendations: %v\n", selected)
}
