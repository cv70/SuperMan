package agents

import "time"

type AgentRole string

const (
	AgentRoleCEO             AgentRole = "ceo"
	AgentRoleCTO             AgentRole = "cto"
	AgentRoleCPO             AgentRole = "cpo"
	AgentRoleCMO             AgentRole = "cmo"
	AgentRoleCFO             AgentRole = "cfo"
	AgentRoleHR              AgentRole = "hr"
	AgentRoleRD              AgentRole = "rd"
	AgentRoleDataAnalyst     AgentRole = "data_analyst"
	AgentRoleCustomerSupport AgentRole = "customer_support"
	AgentRoleOperations      AgentRole = "operations"
)

func (a AgentRole) String() string {
	return string(a)
}

type Priority int

const (
	PriorityLow Priority = iota
	PriorityMedium
	PriorityHigh
	PriorityCritical
)

func (p Priority) String() string {
	switch p {
	case PriorityLow:
		return "low"
	case PriorityMedium:
		return "medium"
	case PriorityHigh:
		return "high"
	case PriorityCritical:
		return "critical"
	default:
		return "unknown"
	}
}

type MessageType int

const (
	MessageTypeTaskAssignment MessageType = iota
	MessageTypeStatusReport
	MessageTypeDataRequest
	MessageTypeDataResponse
	MessageTypeApprovalRequest
	MessageTypeApprovalResponse
	MessageTypeAlert
	MessageTypeCollaboration
)

func (m MessageType) String() string {
	switch m {
	case MessageTypeTaskAssignment:
		return "task_assignment"
	case MessageTypeStatusReport:
		return "status_report"
	case MessageTypeDataRequest:
		return "data_request"
	case MessageTypeDataResponse:
		return "data_response"
	case MessageTypeApprovalRequest:
		return "approval_request"
	case MessageTypeApprovalResponse:
		return "approval_response"
	case MessageTypeAlert:
		return "alert"
	case MessageTypeCollaboration:
		return "collaboration"
	default:
		return "unknown"
	}
}

type Message struct {
	Sender      AgentRole
	Receiver    AgentRole
	MessageType MessageType
	Content     map[string]any
	Priority    Priority
	Timestamp   time.Time
	MessageID   string
}

type Task struct {
	TaskID       string
	Title        string
	Description  string
	AssignedTo   AgentRole
	AssignedBy   AgentRole
	Priority     Priority
	Status       string
	Dependencies []string
	Deliverables []string
	Deadline     *time.Time
	CreatedAt    time.Time
	UpdatedAt    time.Time
	Metadata     map[string]any
}

type AgentState struct {
	Role               AgentRole
	CurrentTasks       []*Task
	CompletedTasks     []*Task
	Messages           []*Message
	PerformanceMetrics map[string]float64
	Capabilities       []string
	Workload           float64
	LastActive         time.Time
}

type CompanyState struct {
	Agents               map[AgentRole]*AgentState
	Tasks                map[string]*Task
	Messages             []*Message
	CurrentTime          time.Time
	StrategicGoals       map[string]any
	KPIs                 map[string]float64
	MarketData           map[string]any
	UserFeedback         []map[string]any
	SystemHealth         map[string]any
	BudgetAllocation     map[string]any
	FinancialMetrics     map[string]any
	CampaignMetrics      map[string]any
	ProductBacklog       []map[string]any
	TechnicalDebt        []map[string]any
	CampaignData         map[string]any
	BrandData            map[string]any
	IndustryReports      map[string]any
	HistoricalCashflow   map[string]any
	CompetitorData       map[string]any
	CustomerData         map[string]any
	ProductData          map[string]any
	BusinessMetrics      map[string]any
	HistoricalFinancials map[string]any
}

func CreateEmptyState() *CompanyState {
	return &CompanyState{
		Agents:               make(map[AgentRole]*AgentState),
		Tasks:                make(map[string]*Task),
		Messages:             make([]*Message, 0),
		CurrentTime:          time.Now(),
		StrategicGoals:       make(map[string]any),
		KPIs:                 make(map[string]float64),
		MarketData:           make(map[string]any),
		UserFeedback:         make([]map[string]any, 0),
		SystemHealth:         make(map[string]any),
		BudgetAllocation:     make(map[string]any),
		FinancialMetrics:     make(map[string]any),
		CampaignMetrics:      make(map[string]any),
		ProductBacklog:       make([]map[string]any, 0),
		TechnicalDebt:        make([]map[string]any, 0),
		CampaignData:         make(map[string]any),
		BrandData:            make(map[string]any),
		IndustryReports:      make(map[string]any),
		HistoricalCashflow:   make(map[string]any),
		CompetitorData:       make(map[string]any),
		CustomerData:         make(map[string]any),
		ProductData:          make(map[string]any),
		BusinessMetrics:      make(map[string]any),
		HistoricalFinancials: make(map[string]any),
	}
}

func GetAgentName(agent interface{}) string {
	switch a := agent.(type) {
	case *CEOAgent:
		return a.GetName()
	case *CTOAgent:
		return a.GetName()
	case *CPOAgent:
		return a.GetName()
	case *CMOAgent:
		return a.GetName()
	case *CFOAgent:
		return a.GetName()
	case *HRAgent:
		return a.GetName()
	case *RDAgent:
		return a.GetName()
	case *DataAnalystAgent:
		return a.GetName()
	case *CustomerSupportAgent:
		return a.GetName()
	case *OperationsAgent:
		return a.GetName()
	default:
		return "unknown"
	}
}
