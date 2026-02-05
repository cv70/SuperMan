package agents

import (
	"context"
	"fmt"
	"math/rand"
	"time"

	"superman/types"
)

type CFOAgent struct {
	*BaseAgentImpl
}

func NewCFOAgent(ctx context.Context) (*CFOAgent, error) {
	baseAgent, err := NewBaseAgent(
		ctx,
		types.AgentRoleCFO,
		2,
	)
	if err != nil {
		return nil, err
	}
	return &CFOAgent{
		BaseAgentImpl: baseAgent,
	}, nil
}

func (a *CFOAgent) ProcessMessage(msg *types.Message) error {
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

func (a *CFOAgent) handleStatusReport(msg *types.Message) error {
	content := msg.Content
	if report, ok := content["report_type"].(string); ok {
		fmt.Printf("[CFO] Received %s status report from %s\n", report, msg.Sender)

		// Financial analysis and planning
		switch report {
		case "revenue":
			a.analyzeRevenueReport(content)
		case "expenses":
			a.analyzeExpenseReport(content)
		case "cashflow":
			a.analyzeCashflowReport(content)
		case "profitability":
			a.analyzeProfitabilityReport(content)
		}
	}
	return nil
}

func (a *CFOAgent) handleTaskAssignment(msg *types.Message) error {
	content := msg.Content
	if taskData, ok := content["task"].(map[string]any); ok {
		fmt.Printf("[CFO] Assigning financial task: %s\n", taskData["title"])

		// Budget planning and financial allocation
		budget := a.createBudgetPlan(taskData)
		a.allocateFinancialResources(taskData, budget)
	}
	return nil
}

func (a *CFOAgent) handleDataRequest(msg *types.Message) error {
	content := msg.Content
	if dataType, ok := content["data_type"].(string); ok {
		fmt.Printf("[CFO] Requesting financial data: %s\n", dataType)

		// Financial forecasting and risk analysis
		a.performFinancialForecasting(content, dataType)
		a.conductRiskAssessment(content, dataType)
	}
	return nil
}

func (a *CFOAgent) GetRoleHierarchy() int {
	return 2
}

// Financial planning and budget management methods
func (a *CFOAgent) analyzeRevenueReport(content map[string]any) {
	if revenue, ok := content["total_revenue"].(float64); ok {
		if revenue > 10000000 {
			fmt.Printf("[CFO] Strong revenue performance: $%.2fM - Consider investment opportunities\n", revenue/1000000)
		} else if revenue > 5000000 {
			fmt.Printf("[CFO] Solid revenue growth: $%.2fM - Maintain current strategy\n", revenue/1000000)
		} else {
			fmt.Printf("[CFO] Revenue acceleration needed: $%.2fM - Implement growth initiatives\n", revenue/1000000)
		}
	}

	if growth, ok := content["growth_rate"].(float64); ok {
		if growth > 0.2 {
			fmt.Printf("[CFO] Excellent revenue growth: %.1f%% - Scale successful initiatives\n", growth*100)
		} else {
			fmt.Printf("[CFO] Revenue growth improvement: %.1f%% - Explore new markets\n", growth*100)
		}
	}
}

func (a *CFOAgent) analyzeExpenseReport(content map[string]any) {
	if expenses, ok := content["total_expenses"].(float64); ok {
		if revenue, ok := content["total_revenue"].(float64); ok {
			ratio := expenses / revenue
			if ratio < 0.7 {
				fmt.Printf("[CFO] Efficient expense management: %.1f%% of revenue - Optimize further\n", ratio*100)
			} else {
				fmt.Printf("[CFO] Expense reduction needed: %.1f%% of revenue - Implement cost controls\n", ratio*100)
			}
		}
	}
}

func (a *CFOAgent) analyzeCashflowReport(content map[string]any) {
	if cashflow, ok := content["net_cashflow"].(float64); ok {
		if cashflow > 1000000 {
			fmt.Printf("[CFO] Positive cash flow: $%.2fM - Investment opportunities available\n", cashflow/1000000)
		} else if cashflow > 0 {
			fmt.Printf("[CFO] Healthy cash flow: $%.2fM - Maintain operational stability\n", cashflow/1000000)
		} else {
			fmt.Printf("[CFO] Cash flow concerns: $%.2fM - Immediate liquidity management required\n", cashflow/1000000)
		}
	}
}

func (a *CFOAgent) analyzeProfitabilityReport(content map[string]any) {
	if margin, ok := content["profit_margin"].(float64); ok {
		if margin > 0.2 {
			fmt.Printf("[CFO] Strong profitability: %.1f%% margin - Sustainable growth model\n", margin*100)
		} else if margin > 0.1 {
			fmt.Printf("[CFO] Moderate profitability: %.1f%% margin - Optimization opportunities\n", margin*100)
		} else {
			fmt.Printf("[CFO] Profitability improvement needed: %.1f%% margin - Strategic review required\n", margin*100)
		}
	}
}

func (a *CFOAgent) createBudgetPlan(taskData map[string]any) map[string]float64 {
	// Budget allocation by department
	budget := map[string]float64{
		"engineering": rand.Float64()*1000000 + 500000,
		"marketing":   rand.Float64()*500000 + 200000,
		"sales":       rand.Float64()*400000 + 150000,
		"operations":  rand.Float64()*300000 + 100000,
		"admin":       rand.Float64()*200000 + 50000,
	}

	total := 0.0
	for _, amount := range budget {
		total += amount
	}
	fmt.Printf("[CFO] Budget plan created - Total: $%.2fM\n", total/1000000)
	return budget
}

func (a *CFOAgent) allocateFinancialResources(taskData map[string]any, budget map[string]float64) {
	// Resource allocation based on strategic priorities
	priority := rand.Perm(len(budget))
	departments := []string{"Engineering", "Marketing", "Sales", "Operations", "Admin"}

	fmt.Printf("[CFO] Resource allocation priority: %v\n", priority)
	for i, dept := range departments {
		fmt.Printf("[CFO] %s: Priority %d, Budget: $%.2f\n", dept, priority[i], budget[dept])
	}
}

func (a *CFOAgent) performFinancialForecasting(content map[string]any, dataType string) {
	// Financial forecasting models
	scenarios := []string{"Conservative", "Moderate", "Aggressive"}
	growthRates := []float64{0.05, 0.15, 0.25}

	selected := rand.Intn(len(scenarios))
	fmt.Printf("[CFO] Financial forecast - Scenario: %s, Growth: %.1f%%\n",
		scenarios[selected], growthRates[selected]*100)
}

func (a *CFOAgent) conductRiskAssessment(content map[string]any, dataType string) {
	// Financial risk analysis
	riskFactors := []string{
		"Market volatility",
		"Currency fluctuations",
		"Credit risk",
		"Liquidity risk",
		"Regulatory changes",
	}

	riskLevel := rand.Float64()*0.3 + 0.1 // 10% to 40%
	fmt.Printf("[CFO] Risk assessment - Overall risk: %.1f%%, Key factors: %v\n",
		riskLevel*100, riskFactors[rand.Intn(len(riskFactors))+1])
}
