package agents

import (
	"context"
	"fmt"
	"math/rand"
	"time"

	"superman/types"
)

type HRAgent struct {
	*BaseAgentImpl
}

func NewHRAgent(ctx context.Context) (*HRAgent, error) {
	baseAgent, err := NewBaseAgent(
		ctx,
		types.AgentRoleHR,
		2,
	)
	if err != nil {
		return nil, err
	}
	return &HRAgent{
		BaseAgentImpl: baseAgent,
	}, nil
}

func (a *HRAgent) ProcessMessage(msg *types.Message) error {
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

func (a *HRAgent) handleStatusReport(msg *types.Message) error {
	content := msg.Content
	if report, ok := content["report_type"].(string); ok {
		fmt.Printf("[HR] Received %s status report from %s\n", report, msg.Sender)

		// HR analytics and organizational insights
		switch report {
		case "employee_satisfaction":
			a.analyzeEmployeeSatisfaction(content)
		case "turnover":
			a.analyzeTurnoverMetrics(content)
		case "performance":
			a.analyzePerformanceData(content)
		case "productivity":
			a.analyzeProductivityMetrics(content)
		}
	}
	return nil
}

func (a *HRAgent) handleTaskAssignment(msg *types.Message) error {
	content := msg.Content
	if taskData, ok := content["task"].(map[string]any); ok {
		fmt.Printf("[HR] Assigning HR task: %s\n", taskData["title"])

		// Talent management and organizational planning
		strategy := a.developTalentStrategy(taskData)
		a.implementOrganizationalDevelopment(taskData, strategy)
	}
	return nil
}

func (a *HRAgent) handleCollaboration(msg *types.Message) error {
	content := msg.Content
	if collabType, ok := content["collaboration_type"].(string); ok {
		fmt.Printf("[HR] Collaboration request: %s\n", collabType)

		// Cross-functional team coordination
		a.coordinateTeamDynamics(content, collabType)
		a.facilitateOrganizationalAlignment(content, collabType)
	}
	return nil
}

func (a *HRAgent) GetRoleHierarchy() int {
	return 2
}

// Talent management and organizational development methods
func (a *HRAgent) analyzeEmployeeSatisfaction(content map[string]any) {
	if satisfaction, ok := content["satisfaction_score"].(float64); ok {
		if satisfaction > 4.5 {
			fmt.Printf("[HR] Excellent employee satisfaction: %.1f/5 - Maintain positive culture\n", satisfaction)
		} else if satisfaction > 3.5 {
			fmt.Printf("[HR] Good employee satisfaction: %.1f/5 - Focus on engagement initiatives\n", satisfaction)
		} else {
			fmt.Printf("[HR] Employee satisfaction concerns: %.1f/5 - Immediate culture intervention needed\n", satisfaction)
		}
	}

	if engagement, ok := content["engagement_rate"].(float64); ok {
		fmt.Printf("[HR] Employee engagement: %.1f%% - Implement recognition programs\n", engagement*100)
	}
}

func (a *HRAgent) analyzeTurnoverMetrics(content map[string]any) {
	if turnover, ok := content["turnover_rate"].(float64); ok {
		if turnover < 0.1 {
			fmt.Printf("[HR] Low turnover rate: %.1f%% - Strong retention strategy\n", turnover*100)
		} else if turnover < 0.2 {
			fmt.Printf("[HR] Moderate turnover: %.1f%% - Enhance employee experience\n", turnover*100)
		} else {
			fmt.Printf("[HR] High turnover rate: %.1f%% - Urgent retention measures required\n", turnover*100)
		}
	}
}

func (a *HRAgent) analyzePerformanceData(content map[string]any) {
	if performance, ok := content["performance_score"].(float64); ok {
		if performance > 4.0 {
			fmt.Printf("[HR] Strong performance: %.1f/5 - Scale high-performer programs\n", performance)
		} else {
			fmt.Printf("[HR] Performance improvement needed: %.1f/5 - Enhance training programs\n", performance)
		}
	}
}

func (a *HRAgent) analyzeProductivityMetrics(content map[string]any) {
	if productivity, ok := content["productivity_index"].(float64); ok {
		if productivity > 0.85 {
			fmt.Printf("[HR] High productivity: %.1f%% - Optimize workflow efficiency\n", productivity*100)
		} else {
			fmt.Printf("[HR] Productivity improvement: %.1f%% - Process optimization required\n", productivity*100)
		}
	}
}

func (a *HRAgent) developTalentStrategy(taskData map[string]any) string {
	// Talent strategy framework
	if focus, ok := taskData["strategic_focus"].(string); ok {
		switch focus {
		case "growth":
			return "aggressive_hiring"
		case "retention":
			return "employee_development"
		case "optimization":
			return "performance_management"
		default:
			return "balanced_talent_strategy"
		}
	}
	return "balanced_talent_strategy"
}

func (a *HRAgent) implementOrganizationalDevelopment(taskData map[string]any, strategy string) {
	initiatives := []string{
		"Leadership development program",
		"Skills training workshops",
		"Career path planning",
		"Succession planning",
		"Team building activities",
	}

	selected := initiatives[rand.Intn(len(initiatives))]
	fmt.Printf("[HR] Organizational development - Strategy: %s, Initiative: %s\n", strategy, selected)
}

func (a *HRAgent) coordinateTeamDynamics(content map[string]any, collabType string) {
	// Team coordination strategies
	approaches := []string{
		"Cross-functional project teams",
		"Agile team structures",
		"Matrix organization",
		"Self-managed teams",
	}

	fmt.Printf("[HR] Team coordination - Type: %s, Approach: %s\n",
		collabType, approaches[rand.Intn(len(approaches))])
}

func (a *HRAgent) facilitateOrganizationalAlignment(content map[string]any, collabType string) {
	// Organizational alignment mechanisms
	mechanisms := []string{
		"Regular team syncs",
		"Shared goal setting",
		"Interdepartmental workshops",
		"Communication protocols",
	}

	fmt.Printf("[HR] Organizational alignment - Collaboration: %s, Mechanisms: %v\n",
		collabType, mechanisms[rand.Intn(len(mechanisms))+1])
}
