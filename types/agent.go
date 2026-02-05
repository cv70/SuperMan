package types

type AgentRole string

const (
	AgentRoleChairman        AgentRole = "chairman"
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
