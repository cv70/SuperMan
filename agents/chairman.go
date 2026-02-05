package agents

import (
	"context"
	"fmt"
	"math/rand"

	"superman/types"
)

type ChairmanAgent struct {
	*BaseAgentImpl
}

func NewChairmanAgent(ctx context.Context) (*ChairmanAgent, error) {
	baseAgent, err := NewBaseAgent(
		ctx,
		types.AgentRoleChairman,
		0, // Chairman has the highest hierarchy level (0 = highest)
	)
	if err != nil {
		return nil, err
	}
	return &ChairmanAgent{
		BaseAgentImpl: baseAgent,
	}, nil
}

func (a *ChairmanAgent) ProcessMessage(msg *types.Message) error {
	switch msg.MessageType {
	case types.MessageTypeStatusReport:
		return a.handleStatusReport(msg)
	case types.MessageTypeTaskAssignment:
		return a.handleTaskAssignment(msg)
	case types.MessageTypeApprovalRequest:
		return a.handleApprovalRequest(msg)
	case types.MessageTypeAlert:
		return a.handleAlert(msg)
	case types.MessageTypeCollaboration:
		return a.handleCollaboration(msg)
	default:
		// For unknown message types, log but don't process
		fmt.Printf("[Chairman] Received unknown message type: %s from %s\n", msg.MessageType.String(), msg.Sender)
		return nil
	}
}

func (a *ChairmanAgent) handleStatusReport(msg *types.Message) error {
	content := msg.Content

	// Check who sent the report
	sender := msg.Sender
	fmt.Printf("[Chairman] Received status report from %s\n", sender)

	if reportType, ok := content["report_type"].(string); ok {
		fmt.Printf("[Chairman] Report type: %s\n", reportType)

		// Strategic oversight based on report type
		switch reportType {
		case "financial":
			a.overseeFinancialReport(content)
		case "market":
			a.overseeMarketReport(content)
		case "product":
			a.overseeProductReport(content)
		case "operational":
			a.overseeOperationalReport(content)
		case "technical":
			a.overseeTechnicalReport(content)
		default:
			a.generalOversee(content)
		}
	}

	// Archive report to private outbox
	a.mailbox.PushOutbox(msg)

	return nil
}

func (a *ChairmanAgent) handleTaskAssignment(msg *types.Message) error {
	content := msg.Content
	if taskData, ok := content["task"].(map[string]any); ok {
		fmt.Printf("[Chairman] Strategic task assignment: %s\n", taskData["title"])

		// Evaluate strategic alignment
		alignment := a.evaluateStrategicAlignment(taskData)
		fmt.Printf("[Chairman] Strategic alignment: %s\n", alignment)

		// Resource approval
		a.approveResources(taskData, alignment)
	}
	return nil
}

func (a *ChairmanAgent) handleApprovalRequest(msg *types.Message) error {
	content := msg.Content

	if requestType, ok := content["request_type"].(string); ok {
		fmt.Printf("[Chairman] Approval request for: %s\n", requestType)

		// Evaluate and approve/reject
		approved := a.evaluateApprovalRequest(content, requestType)
		a.provideApprovalDecision(content, approved)
	}
	return nil
}

func (a *ChairmanAgent) handleAlert(msg *types.Message) error {
	content := msg.Content

	if severity, ok := content["severity"].(string); ok {
		fmt.Printf("[Chairman] CRITICAL ALERT (severity: %s): %s\n", severity, content["description"])

		// High-level crisis management directives
		a.issueCrisisDirective(content, severity)
	}
	return nil
}

func (a *ChairmanAgent) handleCollaboration(msg *types.Message) error {
	content := msg.Content

	if collaborationType, ok := content["collaboration_type"].(string); ok {
		fmt.Printf("[Chairman] Collaboration request: %s\n", collaborationType)

		// Facilitate cross-departmental collaboration
		a.facilitateCollaboration(content, collaborationType)
	}
	return nil
}

func (a *ChairmanAgent) GetRoleHierarchy() int {
	return 0 // Chairman has the highest authority
}

// Strategic oversight methods

func (a *ChairmanAgent) overseeFinancialReport(content map[string]any) {
	if revenue, ok := content["revenue"].(float64); ok {
		if revenue > 10000000 {
			fmt.Printf("[Chairman] Excellent financial performance: $%.2f - Maintain growth trajectory\n", revenue)
		} else {
			fmt.Printf("[Chairman] Financial performance review: $%.2f - Review strategic initiatives\n", revenue)
		}
	}

	if profitMargin, ok := content["profit_margin"].(float64); ok {
		if profitMargin > 0.2 {
			fmt.Printf("[Chairman] Strong profit margin: %.1f%% - Consider expansion opportunities\n", profitMargin*100)
		} else {
			fmt.Printf("[Chairman] Profit margin improvement needed: %.1f%% - Review cost structure\n", profitMargin*100)
		}
	}
}

func (a *ChairmanAgent) overseeMarketReport(content map[string]any) {
	if marketShare, ok := content["market_share"].(float64); ok {
		if marketShare > 0.3 {
			fmt.Printf("[Chairman] Market leadership position: %.1f%% - Defend and expand\n", marketShare*100)
		} else {
			fmt.Printf("[Chairman] Market opportunity: %.1f%% - Develop aggressive growth strategy\n", marketShare*100)
		}
	}

	if growthRate, ok := content["growth_rate"].(float64); ok {
		if growthRate > 0.15 {
			fmt.Printf("[Chairman] Strong market growth: %.1f%% - Capitalize on momentum\n", growthRate*100)
		} else {
			fmt.Printf("[Chairman] Market growth slowing: %.1f%% - Consider new initiatives\n", growthRate*100)
		}
	}
}

func (a *ChairmanAgent) overseeProductReport(content map[string]any) {
	if satisfaction, ok := content["satisfaction_score"].(float64); ok {
		if satisfaction > 4.5 {
			fmt.Printf("[Chairman] Outstanding product satisfaction: %.1f/5 - Scale successful features\n", satisfaction)
		} else {
			fmt.Printf("[Chairman] Product satisfaction review: %.1f/5 - Prioritize customer feedback\n", satisfaction)
		}
	}

	if adoptionRate, ok := content["adoption_rate"].(float64); ok {
		if adoptionRate > 0.5 {
			fmt.Printf("[Chairman] Strong product adoption: %.1f%% - Focus on retention\n", adoptionRate*100)
		} else {
			fmt.Printf("[Chairman] Adoption challenges: %.1f%% - Review go-to-market strategy\n", adoptionRate*100)
		}
	}
}

func (a *ChairmanAgent) overseeOperationalReport(content map[string]any) {
	if efficiency, ok := content["efficiency"].(float64); ok {
		if efficiency > 0.9 {
			fmt.Printf("[Chairman] Operational excellence: %.1f%% - Optimize for scalability\n", efficiency*100)
		} else {
			fmt.Printf("[Chairman] Operational review: %.1f%% - Identify bottlenecks\n", efficiency*100)
		}
	}

	if costControl, ok := content["cost_control"].(float64); ok {
		if costControl > 0.8 {
			fmt.Printf("[Chairman] Good cost control: %.1f%% - Monitor for waste\n", costControl*100)
		} else {
			fmt.Printf("[Chairman] Cost management needed: %.1f%% - Review operations\n", costControl*100)
		}
	}
}

func (a *ChairmanAgent) overseeTechnicalReport(content map[string]any) {
	if systemUptime, ok := content["uptime"].(float64); ok {
		if systemUptime > 0.99 {
			fmt.Printf("[Chairman] Exceptional system reliability: %.2f%% - Excellent engineering\n", systemUptime*100)
		} else {
			fmt.Printf("[Chairman] System reliability review: %.2f%% - Review infrastructure strategy\n", systemUptime*100)
		}
	}

	if innovationRate, ok := content["innovation_rate"].(float64); ok {
		if innovationRate > 0.3 {
			fmt.Printf("[Chairman] Strong innovation pipeline: %.1f%% - Maintain R&D investment\n", innovationRate*100)
		} else {
			fmt.Printf("[Chairman] Innovation concerns: %.1f%% - Review technology strategy\n", innovationRate*100)
		}
	}
}

func (a *ChairmanAgent) generalOversee(content map[string]any) {
	// Generic oversight for unclassified reports
	fmt.Printf("[Chairman] General oversight: Report received for review\n")

	// Add strategic recommendations
	if recommendations, ok := content["recommendations"].([]any); ok {
		fmt.Printf("[Chairman] Strategic recommendations to review: %d items\n", len(recommendations))
	}
}

// Strategic evaluation methods

func (a *ChairmanAgent) evaluateStrategicAlignment(taskData map[string]any) string {
	// Evaluate how well task aligns with company strategy
	if strategicImpact, ok := taskData["strategic_impact"].(string); ok {
		switch strategicImpact {
		case "high":
			return "full_support"
		case "medium":
			return "conditional_support"
		case "low":
			return "review_needed"
		default:
			return "standard_review"
		}
	}
	return "standard_review"
}

func (a *ChairmanAgent) approveResources(taskData map[string]any, alignment string) {
	// Approve resources based on strategic alignment
	budgetAllocation := rand.Float64() * 5000000 // Simulate budget approval up to $5M
	teamSize := rand.Intn(20) + 5                // Simulate team allocation

	fmt.Printf("[Chairman] Resource approval - Alignment: %s, Budget: $%.2f, Team: %d\n",
		alignment, budgetAllocation, teamSize)
}

func (a *ChairmanAgent) evaluateApprovalRequest(content map[string]any, requestType string) bool {
	// Chairman-level approval criteria
	// Higher threshold for approval than other agents

	if recommendation, ok := content["recommendation"].(string); ok {
		switch recommendation {
		case "strongly_recommend":
			return true
		case "recommend":
			// Still requires chairman review
			return rand.Float64() > 0.3
		default:
			return false
		}
	}

	// Default approval for high-level requests
	if requestType == "executive_hire" || requestType == "acquisition" || requestType == "major_investment" {
		return true // Chairman typically approves these strategic moves
	}

	return true
}

func (a *ChairmanAgent) provideApprovalDecision(content map[string]any, approved bool) {
	if approved {
		fmt.Printf("[Chairman] Approval granted - Proceed with execution\n")
	} else {
		fmt.Printf("[Chairman] Approval denied - Review requirements and resubmit\n")
	}
}

// Crisis management methods

func (a *ChairmanAgent) issueCrisisDirective(content map[string]any, severity string) {
	directives := map[string][]string{
		"critical": {
			"Immediate executive meeting scheduled",
			"Board notification required",
			"Stakeholder communication plan activated",
			"Crisis management team assembled",
			"Business continuity evaluation",
		},
		"high": {
			"Executive leadership review",
			"Risk assessment team deployed",
			"Communication plan activated",
			"Resource allocation review",
		},
		"medium": {
			"Department head review",
			"Action plan required within 24 hours",
			"Progress monitoring activated",
		},
	}

	if directiveList, exists := directives[severity]; exists {
		fmt.Printf("[Chairman] Crisis directive (%s): %v\n", severity, directiveList)
	}
}

// Collaboration facilitation

func (a *ChairmanAgent) facilitateCollaboration(content map[string]any, collaborationType string) {
	facilitationMethods := map[string][]string{
		"cross_departmental": {
			"Schedule joint leadership meeting",
			"Establish cross-functional team",
			"Create shared KPIs",
			"Align incentive structures",
		},
		"resource_sharing": {
			"Review resource allocation",
			"Optimize shared services",
			"Eliminate redundancies",
		},
		"knowledge_transfer": {
			"Organize knowledge sharing sessions",
			"Implement best practices",
			"Create documentation standards",
		},
	}

	if methodList, exists := facilitationMethods[collaborationType]; exists {
		fmt.Printf("[Chairman] Collaboration facilitation (%s): %v\n", collaborationType, methodList)
	}
}

// Board and governance methods

// CallBoardMeeting 召集董事会会议
func (a *ChairmanAgent) CallBoardMeeting(title, agenda string) error {
	fmt.Printf("[Chairman] Calling board meeting: %s\n", title)
	fmt.Printf("[Chairman] Agenda: %s\n", agenda)

	// Create a summary for the board meeting
	fmt.Printf("[Chairman] Board meeting summary prepared\n")
	return nil
}

// ApproveBudget 预算审批
func (a *ChairmanAgent) ApproveBudget(budgetType string, amount float64, justification string) error {
	fmt.Printf("[Chairman] Budget approval review:\n")
	fmt.Printf("  Type: %s\n", budgetType)
	fmt.Printf("  Amount: $%.2f\n", amount)
	fmt.Printf("  Justification: %s\n", justification)

	// Chairman typically has final approval authority
	fmt.Printf("[Chairman] Budget approval: APPROVED\n")

	return nil
}

// EvaluateCEO 评估CEO绩效
func (a *ChairmanAgent) EvaluateCEO(achievement map[string]any) error {
	fmt.Printf("[Chairman] CEO Performance Evaluation:\n")

	if revenueGrowth, ok := achievement["revenue_growth"].(float64); ok {
		fmt.Printf("  Revenue Growth: %.1f%%\n", revenueGrowth*100)
	}

	if marketShare, ok := achievement["market_share"].(float64); ok {
		fmt.Printf("  Market Share: %.1f%%\n", marketShare*100)
	}

	if employeeSatisfaction, ok := achievement["employee_satisfaction"].(float64); ok {
		fmt.Printf("  Employee Satisfaction: %.1f/5\n", employeeSatisfaction)
	}

	fmt.Printf("[Chairman] Evaluation Result: PERFORMANCE_REVIEWED\n")
	return nil
}

// GetName 获取Agent名称
func (a *ChairmanAgent) GetName() string {
	return "Chairman Agent"
}
