package agents

import (
	"context"
	"fmt"
	"math/rand"

	"superman/types"
)

type CEOAgent struct {
	*BaseAgentImpl
}

func NewCEOAgent(ctx context.Context) (*CEOAgent, error) {
	baseAgent, err := NewBaseAgent(
		ctx,
		types.AgentRoleCEO,
		1,
	)
	if err != nil {
		return nil, err
	}
	return &CEOAgent{
		BaseAgentImpl: baseAgent,
	}, nil
}

func (a *CEOAgent) ProcessMessage(msg *types.Message) error {
	switch msg.MessageType {
	case types.MessageTypeStatusReport:
		return a.handleStatusReport(msg)
	case types.MessageTypeTaskAssignment:
		return a.handleTaskAssignment(msg)
	case types.MessageTypeAlert:
		return a.handleAlert(msg)
	case types.MessageTypeCollaboration:
		return a.handleCollaboration(msg)
	default:
		// 对于CEO不认识的消息类型，记录但不做处理
		fmt.Printf("[CEO] Received unknown message type: %s from %s\n", msg.MessageType.String(), msg.Sender)
		return nil
	}
}

func (a *CEOAgent) handleStatusReport(msg *types.Message) error {
	content := msg.Content
	var analysisResult map[string]any

	if report, ok := content["report_type"].(string); ok {
		fmt.Printf("[CEO] Received %s status report from %s\n", report, msg.Sender)

		// Analyze report and make strategic decisions
		switch report {
		case "financial":
			analysisResult = a.analyzeFinancialReport(content)
		case "market":
			analysisResult = a.analyzeMarketReport(content)
		case "product":
			analysisResult = a.analyzeProductReport(content)
		case "operational":
			analysisResult = a.analyzeOperationalReport(content)
		default:
			analysisResult = map[string]any{
				"analysis": "unknown report type",
				"action":   "logged for review",
			}
		}
	}

	// 存储分析结果到消息内容中（可选）
	if analysisResult != nil {
		msg.Content["analysis_result"] = analysisResult
	}

	// 将状态报告归档到私有发件箱
	a.mailbox.PushOutbox(msg)

	return nil
}

func (a *CEOAgent) handleTaskAssignment(msg *types.Message) error {
	content := msg.Content
	if taskData, ok := content["task"].(map[string]any); ok {
		fmt.Printf("[CEO] Assigning strategic task: %s\n", taskData["title"])

		// Evaluate strategic importance and allocate resources
		strategy := a.evaluateStrategicImportance(taskData)
		a.allocateResources(taskData, strategy)
	}
	return nil
}

func (a *CEOAgent) handleAlert(msg *types.Message) error {
	content := msg.Content
	if severity, ok := content["severity"].(string); ok {
		fmt.Printf("[CEO] Critical alert (severity: %s): %s\n", severity, content["description"])

		// Risk assessment and crisis management
		riskLevel := a.assessRisk(content)
		a.initiateCrisisManagement(content, riskLevel)
	}
	return nil
}

func (a *CEOAgent) GetRoleHierarchy() int {
	return 1
}

// Strategic decision making methods
func (a *CEOAgent) analyzeFinancialReport(content map[string]any) map[string]any {
	result := map[string]any{
		"report_type": "financial",
		"analysis":    "completed",
		"actions":     []string{},
		"priority":    "medium",
	}

	if revenue, ok := content["revenue"].(float64); ok {
		result["revenue"] = revenue
		if revenue > 1000000 {
			fmt.Printf("[CEO] Strong revenue performance: $%.2f - Consider expansion\n", revenue)
			result["analysis"] = "strong_performance"
			result["actions"] = append(result["actions"].([]string), "consider_expansion")
			result["priority"] = "high"
		} else {
			fmt.Printf("[CEO] Revenue needs improvement: $%.2f - Focus on growth strategies\n", revenue)
			result["analysis"] = "needs_improvement"
			result["actions"] = append(result["actions"].([]string), "focus_growth_strategies")
			result["priority"] = "high"
		}
	}

	return result
}

func (a *CEOAgent) analyzeMarketReport(content map[string]any) map[string]any {
	result := map[string]any{
		"report_type": "market",
		"analysis":    "completed",
		"actions":     []string{},
		"priority":    "medium",
	}

	if marketShare, ok := content["market_share"].(float64); ok {
		result["market_share"] = marketShare
		if marketShare > 0.25 {
			fmt.Printf("[CEO] Market leader position: %.1f%% - Maintain competitive advantage\n", marketShare*100)
			result["analysis"] = "market_leader"
			result["actions"] = append(result["actions"].([]string), "maintain_competitive_advantage")
			result["priority"] = "medium"
		} else {
			fmt.Printf("[CEO] Market share opportunity: %.1f%% - Aggressive growth needed\n", marketShare*100)
			result["analysis"] = "growth_opportunity"
			result["actions"] = append(result["actions"].([]string), "aggressive_growth")
			result["priority"] = "high"
		}
	}

	return result
}

func (a *CEOAgent) analyzeProductReport(content map[string]any) map[string]any {
	result := map[string]any{
		"report_type": "product",
		"analysis":    "completed",
		"actions":     []string{},
		"priority":    "medium",
	}

	if userSatisfaction, ok := content["user_satisfaction"].(float64); ok {
		result["user_satisfaction"] = userSatisfaction
		if userSatisfaction > 4.5 {
			fmt.Printf("[CEO] Excellent product satisfaction: %.1f/5 - Scale success\n", userSatisfaction)
			result["analysis"] = "excellent_satisfaction"
			result["actions"] = append(result["actions"].([]string), "scale_success")
			result["priority"] = "low"
		} else {
			fmt.Printf("[CEO] Product improvement needed: %.1f/5 - Prioritize UX enhancements\n", userSatisfaction)
			result["analysis"] = "improvement_needed"
			result["actions"] = append(result["actions"].([]string), "prioritize_ux_enhancements")
			result["priority"] = "high"
		}
	}

	return result
}

func (a *CEOAgent) analyzeOperationalReport(content map[string]any) map[string]any {
	result := map[string]any{
		"report_type": "operational",
		"analysis":    "completed",
		"actions":     []string{},
		"priority":    "medium",
	}

	if efficiency, ok := content["efficiency"].(float64); ok {
		result["efficiency"] = efficiency
		if efficiency > 0.85 {
			fmt.Printf("[CEO] High operational efficiency: %.1f%% - Optimize further\n", efficiency*100)
			result["analysis"] = "high_efficiency"
			result["actions"] = append(result["actions"].([]string), "optimize_further")
			result["priority"] = "low"
		} else {
			fmt.Printf("[CEO] Operational improvements needed: %.1f%% - Process optimization required\n", efficiency*100)
			result["analysis"] = "improvements_needed"
			result["actions"] = append(result["actions"].([]string), "process_optimization")
			result["priority"] = "high"
		}
	}

	return result
}

func (a *CEOAgent) evaluateStrategicImportance(taskData map[string]any) string {
	// Strategic decision matrix
	if priority, ok := taskData["priority"].(string); ok {
		switch priority {
		case "critical":
			return "immediate_execution"
		case "high":
			return "priority_allocation"
		case "medium":
			return "balanced_approach"
		default:
			return "standard_processing"
		}
	}
	return "standard_processing"
}

func (a *CEOAgent) allocateResources(taskData map[string]any, strategy string) {
	budget := rand.Float64() * 1000000 // Simulate budget allocation
	teamSize := rand.Intn(10) + 5      // Simulate team allocation

	fmt.Printf("[CEO] Resource allocation - Strategy: %s, Budget: $%.2f, Team: %d\n",
		strategy, budget, teamSize)
}

func (a *CEOAgent) assessRisk(content map[string]any) string {
	if severity, ok := content["severity"].(string); ok {
		switch severity {
		case "critical":
			return "high_risk"
		case "high":
			return "medium_risk"
		default:
			return "low_risk"
		}
	}
	return "low_risk"
}

func (a *CEOAgent) initiateCrisisManagement(content map[string]any, riskLevel string) {
	actions := map[string][]string{
		"high_risk": {
			"Emergency board meeting",
			"Stakeholder communication",
			"Business continuity plan",
			"Media response strategy",
		},
		"medium_risk": {
			"Department coordination",
			"Risk mitigation planning",
			"Progress monitoring",
		},
		"low_risk": {
			"Standard monitoring",
			"Preventive measures",
		},
	}

	if actionList, exists := actions[riskLevel]; exists {
		fmt.Printf("[CEO] Crisis management (%s): %v\n", riskLevel, actionList)
	}
}

// AnnounceToCompany 向公司发布公告
func (a *CEOAgent) AnnounceToCompany(title, content string) error {
	// 获取全局状态
	globalState := a.GetGlobalState()
	if globalState == nil {
		return fmt.Errorf("global state not initialized")
	}

	// 添加到公司公有信箱
	globalState.AddPublicAnnouncement(title + "\n" + content)

	fmt.Printf("[CEO] Company announcement published: %s\n", title)
	return nil
}

// GetName 获取Agent名称
func (a *CEOAgent) GetName() string {
	return "CEO Agent"
}
