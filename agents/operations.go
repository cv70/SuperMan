package agents

import (
	"fmt"
	"math/rand"
	"time"

	"github.com/google/uuid"
)

type OperationsAgent struct {
	*BaseAgentImpl
}

func NewOperationsAgent() *OperationsAgent {
	return &OperationsAgent{
		BaseAgentImpl: NewBaseAgent(
			AgentRoleOperations,
			[]string{"流程编排", "异常检测", "监控告警", "任务调度", "熔断降级"},
			2,
		),
	}
}

func (a *OperationsAgent) ProcessMessage(msg *Message) error {
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
	case MessageTypeCollaboration:
		return a.handleCollaboration(msg)
	default:
		return nil
	}
}

func (a *OperationsAgent) handleStatusReport(msg *Message) error {
	content := msg.Content
	if report, ok := content["report_type"].(string); ok {
		fmt.Printf("[Operations] Received %s status report from %s\n", report, msg.Sender)

		// Operations metrics and system health analysis
		switch report {
		case "system_health":
			a.analyzeSystemHealth(content)
		case "workflow_efficiency":
			a.analyzeWorkflowEfficiency(content)
		case "resource_utilization":
			a.analyzeResourceUtilization(content)
		case "service_availability":
			a.analyzeServiceAvailability(content)
		}
	}
	return nil
}

func (a *OperationsAgent) handleTaskAssignment(msg *Message) error {
	content := msg.Content
	if taskData, ok := content["task"].(map[string]any); ok {
		fmt.Printf("[Operations] Assigning operations task: %s\n", taskData["title"])

		// Workflow orchestration and process optimization
		workflow := a.designWorkflow(taskData)
		a.optimizeProcess(taskData, workflow)
	}
	return nil
}

func (a *OperationsAgent) handleAlert(msg *Message) error {
	content := msg.Content
	if severity, ok := content["severity"].(string); ok {
		fmt.Printf("[Operations] Alert (severity: %s): %s\n", severity, content["description"])

		// Incident response and system recovery
		incident := a.classifyIncident(content)
		a.initiateIncidentResponse(content, incident)
	}
	return nil
}

func (a *OperationsAgent) handleCollaboration(msg *Message) error {
	content := msg.Content
	if collabType, ok := content["collaboration_type"].(string); ok {
		fmt.Printf("[Operations] Collaboration request: %s\n", collabType)

		// Cross-functional process coordination
		a.coordinateProcessIntegration(content, collabType)
		a.facilitateSystemAlignment(content, collabType)
	}
	return nil
}

func (a *OperationsAgent) GenerateResponse(task *Task) (*Message, error) {
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
			"executive_summary": fmt.Sprintf("Operations task '%s' completed by Operations", task.Title),
			"system_health":     "All systems operational",
		},
		Priority:  task.Priority,
		Timestamp: time.Now(),
		MessageID: uuid.New().String(),
	}
	a.messages = append(a.messages, response)
	return response, nil
}

func (a *OperationsAgent) GetRoleHierarchy() int {
	return 2
}

// Workflow management and monitoring capabilities methods
func (a *OperationsAgent) analyzeSystemHealth(content map[string]any) {
	if uptime, ok := content["system_uptime"].(float64); ok {
		if uptime > 0.999 {
			fmt.Printf("[Operations] Excellent system uptime: %.3f%% - Five nines achieved\n", uptime*100)
		} else if uptime > 0.99 {
			fmt.Printf("[Operations] Good system uptime: %.3f%% - Industry standard\n", uptime*100)
		} else {
			fmt.Printf("[Operations] Uptime improvement needed: %.3f%% - Reliability measures required\n", uptime*100)
		}
	}

	if errorRate, ok := content["error_rate"].(float64); ok {
		if errorRate < 0.001 {
			fmt.Printf("[Operations] Low error rate: %.3f%% - Stable system performance\n", errorRate*100)
		} else {
			fmt.Printf("[Operations] Error rate concerns: %.3f%% - Debugging and optimization needed\n", errorRate*100)
		}
	}
}

func (a *OperationsAgent) analyzeWorkflowEfficiency(content map[string]any) {
	if throughput, ok := content["workflow_throughput"].(float64); ok {
		if throughput > 1000 {
			fmt.Printf("[Operations] High workflow throughput: %.1f tasks/hour - Efficient processes\n", throughput)
		} else {
			fmt.Printf("[Operations] Throughput optimization: %.1f tasks/hour - Process improvement needed\n", throughput)
		}
	}

	if cycleTime, ok := content["avg_cycle_time"].(float64); ok {
		if cycleTime < 30 {
			fmt.Printf("[Operations] Fast cycle time: %.1f minutes - Streamlined workflows\n", cycleTime)
		} else {
			fmt.Printf("[Operations] Cycle time reduction: %.1f minutes - Bottleneck elimination needed\n", cycleTime)
		}
	}
}

func (a *OperationsAgent) analyzeResourceUtilization(content map[string]any) {
	if cpuUsage, ok := content["cpu_utilization"].(float64); ok {
		if cpuUsage > 80 {
			fmt.Printf("[Operations] High CPU utilization: %.1f%% - Scale resources\n", cpuUsage)
		} else if cpuUsage > 60 {
			fmt.Printf("[Operations] Optimal CPU utilization: %.1f%% - Efficient resource use\n", cpuUsage)
		} else {
			fmt.Printf("[Operations] Low CPU utilization: %.1f%% - Consolidation opportunity\n", cpuUsage)
		}
	}

	if memoryUsage, ok := content["memory_utilization"].(float64); ok {
		fmt.Printf("[Operations] Memory utilization: %.1f%% - Monitor for optimization\n", memoryUsage)
	}
}

func (a *OperationsAgent) analyzeServiceAvailability(content map[string]any) {
	if availability, ok := content["service_availability"].(float64); ok {
		if availability > 0.995 {
			fmt.Printf("[Operations] High service availability: %.3f%% - SLA compliance\n", availability*100)
		} else {
			fmt.Printf("[Operations] Availability improvement: %.3f%% - Redundancy measures needed\n", availability*100)
		}
	}
}

func (a *OperationsAgent) designWorkflow(taskData map[string]any) string {
	// Workflow design patterns
	if complexity, ok := taskData["workflow_complexity"].(string); ok {
		switch complexity {
		case "high":
			return "parallel_processing"
		case "medium":
			return "sequential_pipeline"
		default:
			return "simple_linear"
		}
	}
	return "simple_linear"
}

func (a *OperationsAgent) optimizeProcess(taskData map[string]any, workflow string) {
	// Process optimization strategies
	optimizations := []string{
		"Automation implementation",
		"Bottleneck elimination",
		"Resource reallocation",
		"Process standardization",
		"Performance monitoring",
	}

	efficiencyGain := rand.Float64()*0.3 + 0.1 // 10% to 40%
	fmt.Printf("[Operations] Process optimization - Workflow: %s, Efficiency gain: %.1f%%\n",
		workflow, efficiencyGain*100)
}

func (a *OperationsAgent) classifyIncident(content map[string]any) string {
	if severity, ok := content["severity"].(string); ok {
		switch severity {
		case "critical":
			return "system_failure"
		case "high":
			return "service_degradation"
		case "medium":
			return "performance_issue"
		default:
			return "minor_incident"
		}
	}
	return "minor_incident"
}

func (a *OperationsAgent) initiateIncidentResponse(content map[string]any, incident string) {
	// Incident response procedures
	responses := map[string][]string{
		"system_failure": {
			"Emergency failover activation",
			"Disaster recovery procedures",
			"Stakeholder notification",
			"Root cause analysis team",
		},
		"service_degradation": {
			"Load balancing adjustment",
			"Resource scaling",
			"Performance monitoring",
			"Service restoration",
		},
		"performance_issue": {
			"Performance diagnostics",
			"Resource optimization",
			"Configuration tuning",
			"Monitoring enhancement",
		},
		"minor_incident": {
			"Log analysis",
			"Preventive measures",
			"Documentation update",
		},
	}

	if responseList, exists := responses[incident]; exists {
		fmt.Printf("[Operations] Incident response (%s): %v\n", incident, responseList)
	}
}

func (a *OperationsAgent) coordinateProcessIntegration(content map[string]any, collabType string) {
	// Process integration coordination
	integrationTypes := []string{
		"API integration",
		"Data pipeline integration",
		"Service mesh integration",
		"Workflow orchestration",
	}

	fmt.Printf("[Operations] Process integration - Type: %s, Method: %s\n",
		collabType, integrationTypes[rand.Intn(len(integrationTypes))])
}

func (a *OperationsAgent) facilitateSystemAlignment(content map[string]any, collabType string) {
	// System alignment mechanisms
	alignments := []string{
		"Service level agreements",
		"Operational procedures",
		"Monitoring standards",
		"Security protocols",
		"Compliance frameworks",
	}

	fmt.Printf("[Operations] System alignment - Collaboration: %s, Frameworks: %v\n",
		collabType, alignments[rand.Intn(len(alignments))+1])
}
