package agents

import (
	"context"
	"fmt"
	"math/rand"
	"time"

	"superman/types"
)

type CustomerSupportAgent struct {
	*BaseAgentImpl
}

func NewCustomerSupportAgent(ctx context.Context) (*CustomerSupportAgent, error) {
	baseAgent, err := NewBaseAgent(
		ctx,
		types.AgentRoleCustomerSupport,
		3,
	)
	if err != nil {
		return nil, err
	}
	return &CustomerSupportAgent{
		BaseAgentImpl: baseAgent,
	}, nil
}

func (a *CustomerSupportAgent) ProcessMessage(msg *types.Message) error {
	a.mu.Lock()
	defer a.mu.Unlock()

	a.messages = append(a.messages, msg)
	a.lastActive = time.Now()

	switch msg.MessageType {
	case types.MessageTypeStatusReport:
		return a.handleStatusReport(msg)
	case types.MessageTypeTaskAssignment:
		return a.handleTaskAssignment(msg)
	case types.MessageTypeCollaboration:
		return a.handleCollaboration(msg)
	default:
		return nil
	}
}

func (a *CustomerSupportAgent) handleStatusReport(msg *types.Message) error {
	content := msg.Content
	if report, ok := content["report_type"].(string); ok {
		fmt.Printf("[CustomerSupport] Received %s status report from %s\n", report, msg.Sender)

		// Support metrics and customer satisfaction analysis
		switch report {
		case "support_metrics":
			a.analyzeSupportMetrics(content)
		case "customer_satisfaction":
			a.analyzeCustomerSatisfaction(content)
		case "ticket_resolution":
			a.analyzeTicketResolution(content)
		case "knowledge_base":
			a.analyzeKnowledgeBaseUsage(content)
		}
	}
	return nil
}

func (a *CustomerSupportAgent) handleTaskAssignment(msg *types.Message) error {
	content := msg.Content
	if taskData, ok := content["task"].(map[string]any); ok {
		fmt.Printf("[CustomerSupport] Assigning support task: %s\n", taskData["title"])

		// Customer interaction and support workflow
		strategy := a.developSupportStrategy(taskData)
		a.executeSupportWorkflow(taskData, strategy)
	}
	return nil
}

func (a *CustomerSupportAgent) handleCollaboration(msg *types.Message) error {
	content := msg.Content
	if collabType, ok := content["collaboration_type"].(string); ok {
		fmt.Printf("[CustomerSupport] Collaboration request: %s\n", collabType)

		// Cross-departmental customer issue resolution
		a.coordinateIssueEscalation(content, collabType)
		a.facilitateCustomerFeedbackLoop(content, collabType)
	}
	return nil
}

func (a *CustomerSupportAgent) GetRoleHierarchy() int {
	return 3
}

// User interaction and feedback collection capabilities methods
func (a *CustomerSupportAgent) analyzeSupportMetrics(content map[string]any) {
	if responseTime, ok := content["avg_response_time"].(float64); ok {
		if responseTime < 60 {
			fmt.Printf("[CustomerSupport] Fast response time: %.1f minutes - Excellent service\n", responseTime)
		} else {
			fmt.Printf("[CustomerSupport] Response time improvement: %.1f minutes - Optimize triage\n", responseTime)
		}
	}

	if ticketVolume, ok := content["ticket_volume"].(int); ok {
		fmt.Printf("[CustomerSupport] Daily ticket volume: %d - Staff accordingly\n", ticketVolume)
	}
}

func (a *CustomerSupportAgent) analyzeCustomerSatisfaction(content map[string]any) {
	if satisfaction, ok := content["satisfaction_score"].(float64); ok {
		if satisfaction > 4.5 {
			fmt.Printf("[CustomerSupport] Excellent customer satisfaction: %.1f/5 - Maintain service quality\n", satisfaction)
		} else if satisfaction > 3.5 {
			fmt.Printf("[CustomerSupport] Good customer satisfaction: %.1f/5 - Enhance support training\n", satisfaction)
		} else {
			fmt.Printf("[CustomerSupport] Customer satisfaction concerns: %.1f/5 - Service improvement needed\n", satisfaction)
		}
	}

	if nps, ok := content["net_promoter_score"].(float64); ok {
		if nps > 50 {
			fmt.Printf("[CustomerSupport] Strong NPS: %.1f - Leverage customer advocacy\n", nps)
		} else {
			fmt.Printf("[CustomerSupport] NPS improvement: %.1f - Address detractors\n", nps)
		}
	}
}

func (a *CustomerSupportAgent) analyzeTicketResolution(content map[string]any) {
	if resolutionTime, ok := content["avg_resolution_time"].(float64); ok {
		if resolutionTime < 240 {
			fmt.Printf("[CustomerSupport] Fast resolution: %.1f minutes - Efficient problem solving\n", resolutionTime)
		} else {
			fmt.Printf("[CustomerSupport] Resolution time optimization: %.1f minutes - Improve knowledge base\n", resolutionTime)
		}
	}

	if firstContact, ok := content["first_contact_resolution"].(float64); ok {
		fmt.Printf("[CustomerSupport] First contact resolution: %.1f%% - Enhance agent training\n", firstContact*100)
	}
}

func (a *CustomerSupportAgent) analyzeKnowledgeBaseUsage(content map[string]any) {
	if usage, ok := content["kb_usage_rate"].(float64); ok {
		if usage > 0.6 {
			fmt.Printf("[CustomerSupport] High knowledge base usage: %.1f%% - Self-service effective\n", usage*100)
		} else {
			fmt.Printf("[CustomerSupport] Knowledge base improvement: %.1f%% - Enhance content\n", usage*100)
		}
	}
}

func (a *CustomerSupportAgent) developSupportStrategy(taskData map[string]any) string {
	// Support strategy framework
	if priority, ok := taskData["priority"].(string); ok {
		switch priority {
		case "urgent":
			return "immediate_escalation"
		case "high":
			return "dedicated_support"
		default:
			return "standard_workflow"
		}
	}
	return "standard_workflow"
}

func (a *CustomerSupportAgent) executeSupportWorkflow(taskData map[string]any, strategy string) {
	// Support workflow execution
	channels := []string{"Email", "Phone", "Chat", "Social Media", "Self-service"}
	estimatedResolution := rand.Intn(120) + 15

	fmt.Printf("[CustomerSupport] Support workflow - Strategy: %s, Channels: %v, ETA: %d minutes\n",
		strategy, channels, estimatedResolution)
}

func (a *CustomerSupportAgent) coordinateIssueEscalation(content map[string]any, collabType string) {
	// Issue escalation coordination
	departments := []string{"Technical", "Billing", "Product", "Sales", "Legal"}
	urgency := rand.Float64()*0.4 + 0.6 // 60% to 100%

	fmt.Printf("[CustomerSupport] Issue escalation - Type: %s, Department: %s, Urgency: %.1f%%\n",
		collabType, departments[rand.Intn(len(departments))], urgency*100)
}

func (a *CustomerSupportAgent) facilitateCustomerFeedbackLoop(content map[string]any, collabType string) {
	// Customer feedback collection and analysis
	feedbackMethods := []string{
		"Post-interaction surveys",
		"NPS surveys",
		"Customer interviews",
		"Feedback forms",
		"Social media monitoring",
	}

	sampleSize := rand.Intn(500) + 50
	fmt.Printf("[CustomerSupport] Feedback collection - Method: %s, Sample: %d customers\n",
		feedbackMethods[rand.Intn(len(feedbackMethods))], sampleSize)
}
