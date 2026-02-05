package agents

import (
	"fmt"
	"math/rand"
	"time"

	"github.com/google/uuid"
)

type CEOAgent struct {
	*BaseAgentImpl
}

func NewCEOAgent() *CEOAgent {
	return &CEOAgent{
		BaseAgentImpl: NewBaseAgent(
			AgentRoleCEO,
			[]string{"战略规划", "资源分配", "风险评估", "高层决策", "跨部门协调"},
			1,
		),
	}
}

func (a *CEOAgent) ProcessMessage(msg *Message) error {
	a.mu.Lock()
	defer a.mu.Unlock()

	a.messages = append(a.messages, msg)
	a.lastActive = time.Now()

	switch msg.MessageType {
	case MessageTypeStatusReport:
		return a.handleStatusReport(msg)
	case MessageTypeTaskAssignment:
		return a.handleTaskAssignment(msg)
	case MessageTypeAlert:
		return a.handleAlert(msg)
	default:
		return nil
	}
}

func (a *CEOAgent) handleStatusReport(msg *Message) error {
	content := msg.Content
	if report, ok := content["report_type"].(string); ok {
		fmt.Printf("[CEO] Received %s status report from %s\n", report, msg.Sender)

		// Analyze report and make strategic decisions
		switch report {
		case "financial":
			a.analyzeFinancialReport(content)
		case "market":
			a.analyzeMarketReport(content)
		case "product":
			a.analyzeProductReport(content)
		case "operational":
			a.analyzeOperationalReport(content)
		}
	}
	return nil
}

func (a *CEOAgent) handleTaskAssignment(msg *Message) error {
	content := msg.Content
	if taskData, ok := content["task"].(map[string]any); ok {
		fmt.Printf("[CEO] Assigning strategic task: %s\n", taskData["title"])

		// Evaluate strategic importance and allocate resources
		strategy := a.evaluateStrategicImportance(taskData)
		a.allocateResources(taskData, strategy)
	}
	return nil
}

func (a *CEOAgent) handleAlert(msg *Message) error {
	content := msg.Content
	if severity, ok := content["severity"].(string); ok {
		fmt.Printf("[CEO] Critical alert (severity: %s): %s\n", severity, content["description"])

		// Risk assessment and crisis management
		riskLevel := a.assessRisk(content)
		a.initiateCrisisManagement(content, riskLevel)
	}
	return nil
}

func (a *CEOAgent) GenerateResponse(task *Task) (*Message, error) {
	a.mu.Lock()
	defer a.mu.Unlock()

	response := &Message{
		Sender:      a.role,
		Receiver:    task.AssignedBy,
		MessageType: MessageTypeStatusReport,
		Content: map[string]any{
			"task_id":           task.TaskID,
			"status":            "completed",
			"updated_at":        time.Now(),
			"executive_summary": fmt.Sprintf("Task '%s' completed by CEO", task.Title),
			"results":           "Strategic execution complete",
		},
		Priority:  task.Priority,
		Timestamp: time.Now(),
		MessageID: uuid.New().String(),
	}
	a.messages = append(a.messages, response)
	return response, nil
}

func (a *CEOAgent) GetRoleHierarchy() int {
	return 1
}

// Strategic decision making methods
func (a *CEOAgent) analyzeFinancialReport(content map[string]any) {
	if revenue, ok := content["revenue"].(float64); ok {
		if revenue > 1000000 {
			fmt.Printf("[CEO] Strong revenue performance: $%.2f - Consider expansion\n", revenue)
		} else {
			fmt.Printf("[CEO] Revenue needs improvement: $%.2f - Focus on growth strategies\n", revenue)
		}
	}
}

func (a *CEOAgent) analyzeMarketReport(content map[string]any) {
	if marketShare, ok := content["market_share"].(float64); ok {
		if marketShare > 0.25 {
			fmt.Printf("[CEO] Market leader position: %.1f%% - Maintain competitive advantage\n", marketShare*100)
		} else {
			fmt.Printf("[CEO] Market share opportunity: %.1f%% - Aggressive growth needed\n", marketShare*100)
		}
	}
}

func (a *CEOAgent) analyzeProductReport(content map[string]any) {
	if userSatisfaction, ok := content["user_satisfaction"].(float64); ok {
		if userSatisfaction > 4.5 {
			fmt.Printf("[CEO] Excellent product satisfaction: %.1f/5 - Scale success\n", userSatisfaction)
		} else {
			fmt.Printf("[CEO] Product improvement needed: %.1f/5 - Prioritize UX enhancements\n", userSatisfaction)
		}
	}
}

func (a *CEOAgent) analyzeOperationalReport(content map[string]any) {
	if efficiency, ok := content["efficiency"].(float64); ok {
		if efficiency > 0.85 {
			fmt.Printf("[CEO] High operational efficiency: %.1f%% - Optimize further\n", efficiency*100)
		} else {
			fmt.Printf("[CEO] Operational improvements needed: %.1f%% - Process optimization required\n", efficiency*100)
		}
	}
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
