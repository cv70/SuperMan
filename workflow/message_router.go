package workflow

import (
	"superman/agents"
)

type MessageRouter interface {
	RouteMessage(msg *agents.Message) []agents.AgentRole
	GetRoutingTable() map[agents.MessageType][]agents.AgentRole
}

type messageRouterImpl struct {
	routingTable map[agents.MessageType][]agents.AgentRole
}

func NewMessageRouter() MessageRouter {
	return &messageRouterImpl{
		routingTable: map[agents.MessageType][]agents.AgentRole{
			agents.MessageTypeStatusReport: {
				agents.AgentRoleCEO,
				agents.AgentRoleCTO,
				agents.AgentRoleCPO,
				agents.AgentRoleCMO,
				agents.AgentRoleCFO,
				agents.AgentRoleHR,
				agents.AgentRoleDataAnalyst,
				agents.AgentRoleCustomerSupport,
				agents.AgentRoleOperations,
			},
			agents.MessageTypeTaskAssignment: {
				agents.AgentRoleCEO,
				agents.AgentRoleCTO,
				agents.AgentRoleCPO,
				agents.AgentRoleCMO,
				agents.AgentRoleCFO,
				agents.AgentRoleHR,
				agents.AgentRoleRD,
				agents.AgentRoleDataAnalyst,
				agents.AgentRoleCustomerSupport,
				agents.AgentRoleOperations,
			},
			agents.MessageTypeDataRequest: {
				agents.AgentRoleDataAnalyst,
			},
			agents.MessageTypeDataResponse: {
				agents.AgentRoleCEO,
				agents.AgentRoleCTO,
				agents.AgentRoleCPO,
				agents.AgentRoleCMO,
				agents.AgentRoleCFO,
				agents.AgentRoleHR,
				agents.AgentRoleRD,
				agents.AgentRoleCustomerSupport,
				agents.AgentRoleOperations,
			},
			agents.MessageTypeApprovalRequest: {
				agents.AgentRoleCTO,
				agents.AgentRoleCEO,
				agents.AgentRoleCPO,
				agents.AgentRoleCMO,
				agents.AgentRoleCFO,
				agents.AgentRoleHR,
				agents.AgentRoleRD,
				agents.AgentRoleDataAnalyst,
				agents.AgentRoleCustomerSupport,
				agents.AgentRoleOperations,
			},
			agents.MessageTypeApprovalResponse: {
				agents.AgentRoleCEO,
				agents.AgentRoleCTO,
				agents.AgentRoleCPO,
				agents.AgentRoleCMO,
				agents.AgentRoleCFO,
				agents.AgentRoleHR,
				agents.AgentRoleRD,
				agents.AgentRoleDataAnalyst,
				agents.AgentRoleCustomerSupport,
				agents.AgentRoleOperations,
			},
			agents.MessageTypeAlert: {
				agents.AgentRoleCEO,
				agents.AgentRoleCTO,
				agents.AgentRoleCPO,
				agents.AgentRoleCMO,
				agents.AgentRoleCFO,
				agents.AgentRoleHR,
				agents.AgentRoleRD,
				agents.AgentRoleDataAnalyst,
				agents.AgentRoleCustomerSupport,
				agents.AgentRoleOperations,
			},
			agents.MessageTypeCollaboration: {
				agents.AgentRoleCEO,
				agents.AgentRoleCTO,
				agents.AgentRoleCPO,
				agents.AgentRoleCMO,
				agents.AgentRoleCFO,
				agents.AgentRoleHR,
				agents.AgentRoleRD,
				agents.AgentRoleDataAnalyst,
				agents.AgentRoleCustomerSupport,
				agents.AgentRoleOperations,
			},
		},
	}
}

func (r *messageRouterImpl) RouteMessage(msg *agents.Message) []agents.AgentRole {
	return []agents.AgentRole{msg.Receiver}
}

func (r *messageRouterImpl) GetRoutingTable() map[agents.MessageType][]agents.AgentRole {
	return r.routingTable
}
