package agents

import (
	"fmt"
	"math/rand"
	"time"

	"github.com/google/uuid"
)

type CTOAgent struct {
	*BaseAgentImpl
}

func NewCTOAgent() *CTOAgent {
	return &CTOAgent{
		BaseAgentImpl: NewBaseAgent(
			AgentRoleCTO,
			[]string{"系统架构", "技术研发", "团队管理", "技术选型", "系统安全"},
			2,
		),
	}
}

func (a *CTOAgent) ProcessMessage(msg *Message) error {
	a.mu.Lock()
	defer a.mu.Unlock()

	a.messages = append(a.messages, msg)
	a.lastActive = time.Now()

	switch msg.MessageType {
	case MessageTypeStatusReport:
		return a.handleStatusReport(msg)
	case MessageTypeTaskAssignment:
		return a.handleTaskAssignment(msg)
	case MessageTypeApprovalRequest:
		return a.handleApprovalRequest(msg)
	case MessageTypeAlert:
		return a.handleAlert(msg)
	default:
		return nil
	}
}

func (a *CTOAgent) handleStatusReport(msg *Message) error {
	content := msg.Content
	if report, ok := content["report_type"].(string); ok {
		fmt.Printf("[CTO] Received %s status report from %s\n", report, msg.Sender)

		// Technical analysis and system optimization
		switch report {
		case "system_performance":
			a.analyzeSystemPerformance(content)
		case "development":
			a.analyzeDevelopmentMetrics(content)
		case "security":
			a.analyzeSecurityReport(content)
		case "infrastructure":
			a.analyzeInfrastructureReport(content)
		}
	}
	return nil
}

func (a *CTOAgent) handleTaskAssignment(msg *Message) error {
	content := msg.Content
	if taskData, ok := content["task"].(map[string]any); ok {
		fmt.Printf("[CTO] Assigning technical task: %s\n", taskData["title"])

		// Technical planning and architecture design
		architecture := a.designArchitecture(taskData)
		a.planTechnicalImplementation(taskData, architecture)
	}
	return nil
}

func (a *CTOAgent) handleApprovalRequest(msg *Message) error {
	content := msg.Content
	if requestType, ok := content["request_type"].(string); ok {
		fmt.Printf("[CTO] Approval request for: %s\n", requestType)

		// Technical review and approval process
		approval := a.reviewTechnicalProposal(content, requestType)
		a.provideTechnicalFeedback(content, approval)
	}
	return nil
}

func (a *CTOAgent) handleAlert(msg *Message) error {
	content := msg.Content
	if severity, ok := content["severity"].(string); ok {
		fmt.Printf("[CTO] Technical alert (severity: %s): %s\n", severity, content["description"])

		// Technical incident response
		incident := a.classifyIncident(content)
		a.initiateTechnicalResponse(content, incident)
	}
	return nil
}

func (a *CTOAgent) GenerateResponse(task *Task) (*Message, error) {
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
			"executive_summary": fmt.Sprintf("Technical task '%s' completed by CTO", task.Title),
			"technical_details": "Implementation and deployment complete",
		},
		Priority:  task.Priority,
		Timestamp: time.Now(),
		MessageID: uuid.New().String(),
	}
	a.messages = append(a.messages, response)
	return response, nil
}

func (a *CTOAgent) GetRoleHierarchy() int {
	return 2
}

// Technical architecture and system design methods
func (a *CTOAgent) analyzeSystemPerformance(content map[string]any) {
	if responseTime, ok := content["response_time"].(float64); ok {
		if responseTime < 100 {
			fmt.Printf("[CTO] Excellent system performance: %.2fms - Maintain optimization\n", responseTime)
		} else {
			fmt.Printf("[CTO] Performance optimization needed: %.2fms - Implement caching strategies\n", responseTime)
		}
	}

	if throughput, ok := content["throughput"].(float64); ok {
		fmt.Printf("[CTO] System throughput: %.2f req/s - Scale architecture if needed\n", throughput)
	}
}

func (a *CTOAgent) analyzeDevelopmentMetrics(content map[string]any) {
	if deployFreq, ok := content["deploy_frequency"].(float64); ok {
		if deployFreq > 10 {
			fmt.Printf("[CTO] High deployment frequency: %.1f/week - Excellent CI/CD\n", deployFreq)
		} else {
			fmt.Printf("[CTO] Improve deployment pipeline: %.1f/week - Automate more\n", deployFreq)
		}
	}

	if bugRate, ok := content["bug_rate"].(float64); ok {
		if bugRate < 0.05 {
			fmt.Printf("[CTO] Low bug rate: %.2f%% - Quality engineering effective\n", bugRate*100)
		} else {
			fmt.Printf("[CTO] Bug rate improvement needed: %.2f%% - Enhance testing\n", bugRate*100)
		}
	}
}

func (a *CTOAgent) analyzeSecurityReport(content map[string]any) {
	if vulnerabilities, ok := content["vulnerabilities"].(int); ok {
		if vulnerabilities == 0 {
			fmt.Printf("[CTO] No security vulnerabilities - Excellent security posture\n")
		} else {
			fmt.Printf("[CTO] %d security vulnerabilities found - Immediate patching required\n", vulnerabilities)
		}
	}
}

func (a *CTOAgent) analyzeInfrastructureReport(content map[string]any) {
	if cpuUsage, ok := content["cpu_usage"].(float64); ok {
		if cpuUsage > 80 {
			fmt.Printf("[CTO] High CPU usage: %.1f%% - Scale horizontally\n", cpuUsage)
		} else {
			fmt.Printf("[CTO] CPU usage optimal: %.1f%% - Current capacity sufficient\n", cpuUsage)
		}
	}
}

func (a *CTOAgent) designArchitecture(taskData map[string]any) string {
	// Architecture decision matrix
	if complexity, ok := taskData["complexity"].(string); ok {
		switch complexity {
		case "high":
			return "microservices_architecture"
		case "medium":
			return "modular_monolith"
		default:
			return "simple_monolith"
		}
	}
	return "simple_monolith"
}

func (a *CTOAgent) planTechnicalImplementation(taskData map[string]any, architecture string) {
	techStack := []string{"Go", "PostgreSQL", "Redis", "Docker"}
	estimatedHours := rand.Intn(200) + 50

	fmt.Printf("[CTO] Technical plan - Architecture: %s, Stack: %v, Effort: %d hours\n",
		architecture, techStack, estimatedHours)
}

func (a *CTOAgent) reviewTechnicalProposal(content map[string]any, requestType string) bool {
	// Technical approval criteria
	if feasibility, ok := content["feasibility"].(float64); ok {
		return feasibility > 0.7
	}
	return true
}

func (a *CTOAgent) provideTechnicalFeedback(content map[string]any, approved bool) {
	if approved {
		fmt.Printf("[CTO] Technical proposal approved - Proceed with implementation\n")
	} else {
		fmt.Printf("[CTO] Technical proposal rejected - Requires architectural revision\n")
	}
}

func (a *CTOAgent) classifyIncident(content map[string]any) string {
	if severity, ok := content["severity"].(string); ok {
		switch severity {
		case "critical":
			return "system_outage"
		case "high":
			return "performance_degradation"
		default:
			return "minor_issue"
		}
	}
	return "minor_issue"
}

func (a *CTOAgent) initiateTechnicalResponse(content map[string]any, incident string) {
	responses := map[string][]string{
		"system_outage": {
			"Emergency deployment rollback",
			"Failover activation",
			"Stakeholder notification",
			"Root cause analysis",
		},
		"performance_degradation": {
			"Performance monitoring",
			"Resource scaling",
			"Load balancing adjustment",
		},
		"minor_issue": {
			"Log analysis",
			"Bug fix scheduling",
			"Documentation update",
		},
	}

	if responseList, exists := responses[incident]; exists {
		fmt.Printf("[CTO] Technical response (%s): %v\n", incident, responseList)
	}
}
