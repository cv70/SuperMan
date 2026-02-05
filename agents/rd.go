package agents

import (
	"context"
	"fmt"
	"math/rand"
	"time"

	"superman/types"
)

type RDAgent struct {
	*BaseAgentImpl
}

func NewRDAgent(ctx context.Context) (*RDAgent, error) {
	baseAgent, err := NewBaseAgent(
		ctx,
		types.AgentRoleRD,
		3,
	)
	if err != nil {
		return nil, err
	}
	return &RDAgent{
		BaseAgentImpl: baseAgent,
	}, nil
}

func (a *RDAgent) ProcessMessage(msg *types.Message) error {
	a.mu.Lock()
	defer a.mu.Unlock()

	a.messages = append(a.messages, msg)
	a.lastActive = time.Now()

	switch msg.MessageType {
	case types.MessageTypeStatusReport:
		return a.handleStatusReport(msg)
	case types.MessageTypeTaskAssignment:
		return a.handleTaskAssignment(msg)
	case types.MessageTypeApprovalRequest:
		return a.handleApprovalRequest(msg)
	default:
		return nil
	}
}

func (a *RDAgent) handleStatusReport(msg *types.Message) error {
	content := msg.Content
	if report, ok := content["report_type"].(string); ok {
		fmt.Printf("[RD] Received %s status report from %s\n", report, msg.Sender)

		// Development metrics and quality analysis
		switch report {
		case "development":
			a.analyzeDevelopmentMetrics(content)
		case "testing":
			a.analyzeTestingResults(content)
		case "code_quality":
			a.analyzeCodeQuality(content)
		case "deployment":
			a.analyzeDeploymentStatus(content)
		}
	}
	return nil
}

func (a *RDAgent) handleTaskAssignment(msg *types.Message) error {
	content := msg.Content
	if taskData, ok := content["task"].(map[string]any); ok {
		fmt.Printf("[RD] Assigning development task: %s\n", taskData["title"])

		// Development planning and technical implementation
		approach := a.planDevelopmentApproach(taskData)
		a.implementFeatureDevelopment(taskData, approach)
	}
	return nil
}

func (a *RDAgent) handleApprovalRequest(msg *types.Message) error {
	content := msg.Content
	if requestType, ok := content["request_type"].(string); ok {
		fmt.Printf("[RD] Approval request for: %s\n", requestType)

		// Technical review and code approval
		approval := a.conductTechnicalReview(content, requestType)
		a.performCodeReview(content, approval)
	}
	return nil
}

func (a *RDAgent) GetRoleHierarchy() int {
	return 3
}

// Development and testing capabilities methods
func (a *RDAgent) analyzeDevelopmentMetrics(content map[string]any) {
	if velocity, ok := content["team_velocity"].(float64); ok {
		if velocity > 50 {
			fmt.Printf("[RD] High development velocity: %.1f story points - Maintain sprint rhythm\n", velocity)
		} else {
			fmt.Printf("[RD] Development velocity improvement: %.1f story points - Remove impediments\n", velocity)
		}
	}

	if cycleTime, ok := content["cycle_time"].(float64); ok {
		if cycleTime < 7 {
			fmt.Printf("[RD] Fast cycle time: %.1f days - Efficient delivery pipeline\n", cycleTime)
		} else {
			fmt.Printf("[RD] Cycle time optimization: %.1f days - Streamline development process\n", cycleTime)
		}
	}
}

func (a *RDAgent) analyzeTestingResults(content map[string]any) {
	if coverage, ok := content["test_coverage"].(float64); ok {
		if coverage > 0.8 {
			fmt.Printf("[RD] Excellent test coverage: %.1f%% - Quality assurance effective\n", coverage*100)
		} else {
			fmt.Printf("[RD] Test coverage improvement: %.1f%% - Expand test suite\n", coverage*100)
		}
	}

	if passRate, ok := content["test_pass_rate"].(float64); ok {
		if passRate > 0.95 {
			fmt.Printf("[RD] High test pass rate: %.1f%% - Stable codebase\n", passRate*100)
		} else {
			fmt.Printf("[RD] Test stability concerns: %.1f%% - Address failing tests\n", passRate*100)
		}
	}
}

func (a *RDAgent) analyzeCodeQuality(content map[string]any) {
	if technicalDebt, ok := content["technical_debt"].(float64); ok {
		if technicalDebt < 0.1 {
			fmt.Printf("[RD] Low technical debt: %.1f%% - Clean codebase maintained\n", technicalDebt*100)
		} else {
			fmt.Printf("[RD] Technical debt reduction: %.1f%% - Schedule refactoring\n", technicalDebt*100)
		}
	}

	if bugs, ok := content["bug_count"].(int); ok {
		if bugs < 5 {
			fmt.Printf("[RD] Low bug count: %d - Quality engineering effective\n", bugs)
		} else {
			fmt.Printf("[RD] Bug count improvement: %d - Enhance testing practices\n", bugs)
		}
	}
}

func (a *RDAgent) analyzeDeploymentStatus(content map[string]any) {
	if success, ok := content["deployment_success"].(float64); ok {
		if success > 0.95 {
			fmt.Printf("[RD] High deployment success: %.1f%% - Reliable release process\n", success*100)
		} else {
			fmt.Printf("[RD] Deployment reliability: %.1f%% - Improve CI/CD pipeline\n", success*100)
		}
	}
}

func (a *RDAgent) planDevelopmentApproach(taskData map[string]any) string {
	// Development methodology selection
	if complexity, ok := taskData["complexity"].(string); ok {
		switch complexity {
		case "high":
			return "iterative_development"
		case "medium":
			return "agile_sprints"
		default:
			return "kanban_flow"
		}
	}
	return "kanban_flow"
}

func (a *RDAgent) implementFeatureDevelopment(taskData map[string]any, approach string) {
	// Development implementation plan
	technologies := []string{"Go", "React", "PostgreSQL", "Docker", "Kubernetes"}
	estimatedDays := rand.Intn(14) + 3

	fmt.Printf("[RD] Feature development - Approach: %s, Tech: %v, Duration: %d days\n",
		approach, technologies, estimatedDays)
}

func (a *RDAgent) conductTechnicalReview(content map[string]any, requestType string) bool {
	// Technical review criteria
	if complexity, ok := content["complexity"].(float64); ok {
		return complexity < 0.8 // Approve if complexity is manageable
	}
	return true
}

func (a *RDAgent) performCodeReview(content map[string]any, approved bool) {
	if approved {
		fmt.Printf("[RD] Code review approved - Merge to main branch\n")
	} else {
		fmt.Printf("[RD] Code review requires changes - Address feedback\n")
	}

	// Code quality metrics
	linesOfCode := rand.Intn(1000) + 100
	complexityScore := rand.Float64()*10 + 5
	fmt.Printf("[RD] Code metrics - LOC: %d, Complexity: %.1f\n", linesOfCode, complexityScore)
}
