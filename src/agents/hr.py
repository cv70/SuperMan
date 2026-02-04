from typing import Dict, List, Optional, Any
import json
from datetime import datetime, timedelta
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from .base import (
    BaseAgent,
    AgentRole,
    Task,
    Message,
    MessageType,
    Priority,
    CompanyState,
    CommunicationProtocol,
    create_task_id,
)
from .config import app_config, ModelConfig, AgentConfig



class HRAgent(BaseAgent):
    def __init__(self):
        capabilities = [
            "人才招聘",
            "绩效管理",
            "流程优化",
            "KPI设计",
            "冲突解决",
            "组织健康度",
            "角色重构",
        ]
        super().__init__(AgentRole.HR, capabilities)
        default_model_config = app_config.llm.models.get(
            app_config.llm.default_model,
            ModelConfig(
                name=app_config.llm.default_model,
                provider="openai",
                api_key=None,
                config={},
            ),
        )
        agent_config = app_config.agents.get("hr", AgentConfig())
        self.llm = ChatOpenAI(
            model=app_config.llm.default_model,
            temperature=agent_config.temperature if agent_config.temperature != 0.3 else default_model_config.config.get("temperature", 0.3),
        )
        self.team_structure = {}
        self.performance_metrics = {}
        self.kpi_definitions = {}
        self.conflict_registry = {}
        self.organization_health = {}

    async def process_message(
        self, message: Message, company_state: CompanyState
    ) -> Optional[Message]:
        if message.message_type == MessageType.TASK_ASSIGNMENT:
            return await self._handle_task_assignment(message, company_state)
        elif message.message_type == MessageType.STATUS_REPORT:
            return await self._handle_status_report(message, company_state)
        elif message.message_type == MessageType.DATA_REQUEST:
            return await self._handle_data_request(message, company_state)
        elif message.message_type == MessageType.ALERT:
            return await self._handle_alert(message, company_state)
        elif message.message_type == MessageType.APPROVAL_REQUEST:
            return await self._handle_approval_request(message, company_state)
        elif message.message_type == MessageType.COLLABORATION:
            return await self._handle_collaboration(message, company_state)
        return None

    async def _handle_task_assignment(
        self, message: Message, company_state: CompanyState
    ) -> Optional[Message]:
        task_data = message.content.get("task", {})
        if "evaluation" in task_data.get("title", "").lower():
            return await self._process_performance_evaluation(task_data, company_state)
        return None

    async def _handle_status_report(
        self, message: Message, company_state: CompanyState
    ) -> Optional[Message]:
        sender = message.sender
        if sender == AgentRole.OPERATIONS:
            return await self._analyze_operations_report(message.content)
        elif sender == AgentRole.CFO:
            return await self._analyze_cfo_report(message.content)
        return CommunicationProtocol.create_message(
            sender=self.role,
            recipient=sender,
            message_type=MessageType.COLLABORATION,
            content={"type": "hr_review", "status": "acknowledged"},
        )

    async def _handle_data_request(
        self, message: Message, company_state: CompanyState
    ) -> Message:
        request_type = message.content.get("request_type", "")
        data_map = {
            "team_structure": self.team_structure,
            "performance_metrics": self.performance_metrics,
            "kpi_definitions": self.kpi_definitions,
            "organization_health": self.organization_health,
        }
        if request_type in data_map:
            return CommunicationProtocol.create_message(
                sender=self.role,
                recipient=message.sender,
                message_type=MessageType.DATA_RESPONSE,
                content={
                    "request_id": message.content.get("request_id"),
                    "data": data_map[request_type],
                    "data_type": request_type,
                },
            )
        return CommunicationProtocol.create_message(
            sender=self.role,
            recipient=message.sender,
            message_type=MessageType.DATA_RESPONSE,
            content={
                "request_id": message.content.get("request_id"),
                "error": f"Unknown request type: {request_type}",
            },
        )

    async def _handle_alert(
        self, message: Message, company_state: CompanyState
    ) -> Optional[Message]:
        alert_type = message.content.get("alert_type", "")
        if alert_type == "high_failure_rate":
            return await self._trigger_role_reconfiguration(
                message.content, company_state
            )
        elif alert_type == "task_conflict":
            return await self._resolve_conflicts(message.content, company_state)
        return None

    async def _handle_approval_request(
        self, message: Message, company_state: CompanyState
    ) -> Message:
        request_type = message.content.get("request_type", "")
        if request_type == "role_reconfiguration":
            return await self._process_role_reconfiguration_request(
                message, company_state
            )
        elif request_type == "resource_allocation":
            return await self._process_resource_allocation_request(
                message, company_state
            )
        return CommunicationProtocol.create_message(
            sender=self.role,
            recipient=message.sender,
            message_type=MessageType.APPROVAL_RESPONSE,
            content={
                "request_id": message.content.get("request_id"),
                "approved": False,
                "reasoning": f"Unknown type: {request_type}",
            },
        )

    async def _handle_collaboration(
        self, message: Message, company_state: CompanyState
    ) -> Optional[Message]:
        if message.content.get("type") == "organizational_insight":
            return await self._process_organizational_insight(message, company_state)
        return None

    async def _process_performance_evaluation(
        self, task_data: Dict[str, Any], company_state: CompanyState
    ) -> Optional[Message]:
        evaluated_agent = task_data.get("assigned_to")
        if not evaluated_agent:
            return None
        evaluation = await self._evaluate_performance(evaluated_agent, company_state)
        return CommunicationProtocol.create_message(
            sender=self.role,
            recipient=task_data.get("assigned_by", AgentRole.CEO),
            message_type=MessageType.STATUS_REPORT,
            content={
                "evaluation_type": "performance_review",
                "evaluated_agent": str(evaluated_agent),
                "evaluation_result": evaluation,
                "timestamp": datetime.now().isoformat(),
            },
        )

    async def _analyze_operations_report(self, report_data: Dict[str, Any]) -> Message:
        analysis = {
            "system_efficiency": self._assess_system_efficiency(
                report_data.get("system_health", {}),
                report_data.get("task_metrics", {}),
            ),
            "bottleneck_detection": self._detect_bottlenecks(
                report_data.get("task_metrics", {})
            ),
            "team_load_balance": self._assess_team_load_balance(
                report_data.get("task_metrics", {})
            ),
        }
        return CommunicationProtocol.create_message(
            sender=self.role,
            recipient=AgentRole.OPERATIONS,
            message_type=MessageType.COLLABORATION,
            content={
                "type": "hr_system_review",
                "analysis": analysis,
                "recommendations": self._generate_hr_recommendations(analysis),
            },
        )

    async def _analyze_cfo_report(self, report_data: Dict[str, Any]) -> Message:
        analysis = {
            "budget_efficiency": self._assess_budget_efficiency(
                report_data.get("budget", {})
            ),
            "resource_optimization": self._assess_resource_optimization(
                report_data.get("resource_usage", {})
            ),
            "cost_per_productivity": self._calculate_cost_efficiency(
                report_data.get("budget", {}), report_data.get("resource_usage", {})
            ),
        }
        return CommunicationProtocol.create_message(
            sender=self.role,
            recipient=AgentRole.CFO,
            message_type=MessageType.COLLABORATION,
            content={
                "type": "hr_resource_review",
                "analysis": analysis,
                "suggestions": self._generate_resource_suggestions(analysis),
            },
        )

    async def execute_task(
        self, task: Task, company_state: CompanyState
    ) -> Dict[str, Any]:
        task_title = task.title.lower()
        if "performance" in task_title:
            return await self._execute_performance_evaluation_task(task, company_state)
        elif "assignment" in task_title or "assign" in task_title:
            return await self._execute_task_assignment_task(task, company_state)
        elif "workflow" in task_title or "optimization" in task_title:
            return await self._execute_workflow_optimization_task(task, company_state)
        elif "kpi" in task_title:
            return await self._execute_kpi_design_task(task, company_state)
        elif "conflict" in task_title:
            return await self._execute_conflict_resolution_task(task, company_state)
        return {
            "status": "completed",
            "result": "Task processed by HR",
            "timestamp": datetime.now().isoformat(),
        }

    async def _execute_performance_evaluation_task(
        self, task: Task, company_state: CompanyState
    ) -> Dict[str, Any]:
        results = {}
        for role_str in task.metadata.get("evaluated_roles", []):
            role = AgentRole(role_str) if isinstance(role_str, str) else role_str
            results[
                role.value if hasattr(role, "value") else str(role)
            ] = await self._evaluate_performance(role, company_state)
        return {
            "status": "completed",
            "result": results,
            "type": "performance_evaluation",
            "timestamp": datetime.now().isoformat(),
            "summary": self._generate_performance_summary(
                results, task.metadata.get("evaluation_period", "monthly")
            ),
        }

    async def _execute_task_assignment_task(
        self, task: Task, company_state: CompanyState
    ) -> Dict[str, Any]:
        assignments = []
        for task_item in task.metadata.get("tasks", []):
            assignment = await self._assign_tasks(task_item, company_state)
            assignments.extend(assignment)
        return {
            "status": "completed",
            "result": assignments,
            "type": "task_assignment",
            "timestamp": datetime.now().isoformat(),
            "assignment_summary": {
                "total_tasks": len(task.metadata.get("tasks", [])),
                "assignments_made": len(assignments),
            },
        }

    async def _execute_workflow_optimization_task(
        self, task: Task, company_state: CompanyState
    ) -> Dict[str, Any]:
        workflow_analysis = await self._optimize_workflow(company_state)
        return {
            "status": "completed",
            "result": workflow_analysis,
            "type": "workflow_optimization",
            "timestamp": datetime.now().isoformat(),
            "implementation_recommendations": self._generate_implementation_recommendations(
                workflow_analysis
            ),
        }

    async def _execute_kpi_design_task(
        self, task: Task, company_state: CompanyState
    ) -> Dict[str, Any]:
        kpi_designs = await self._design_kpis(
            task.metadata.get("agent_types", []), company_state
        )
        return {
            "status": "completed",
            "result": kpi_designs,
            "type": "kpi_design",
            "timestamp": datetime.now().isoformat(),
            "kpis_created": list(kpi_designs.keys()),
        }

    async def _execute_conflict_resolution_task(
        self, task: Task, company_state: CompanyState
    ) -> Dict[str, Any]:
        resolution = await self._resolve_conflicts(task.metadata, company_state)
        return {
            "status": "completed",
            "result": resolution,
            "type": "conflict_resolution",
            "timestamp": datetime.now().isoformat(),
            "resolution_status": resolution.get("status", "pending"),
        }

    async def generate_report(self, company_state: CompanyState) -> Dict[str, Any]:
        organization_health = await self._assess组织_health(company_state)
        return {
            "agent_role": self.role.value,
            "report_type": "organization_health_report",
            "timestamp": datetime.now().isoformat(),
            "data": organization_health,
            "executive_summary": self._generate_executive_summary(organization_health),
            "recommendations": self._generate_report_recommendations(
                organization_health
            ),
            "next_actions": self._determine_next_actions(organization_health),
        }

    async def _assign_tasks(
        self, task: Dict[str, Any], company_state: CompanyState
    ) -> List[Dict[str, Any]]:
        task_obj = Task(
            task_id=task.get("task_id", create_task_id()),
            title=task.get("title", ""),
            description=task.get("description", ""),
            assigned_to=AgentRole(task.get("assigned_to", "")),
            assigned_by=AgentRole(task.get("assigned_by", "")),
            priority=Priority(task.get("priority", "medium")),
            deadline=datetime.fromisoformat(task["deadline"])
            if task.get("deadline")
            else None,
        )
        available_agents = self._get_available_agents(company_state)
        if not available_agents:
            return [
                {
                    "task_id": task_obj.task_id,
                    "status": "deferred",
                    "reason": "No available agents",
                }
            ]
        best_match = self._find_best_agent_for_task(
            task_obj, available_agents, company_state
        )
        return [
            {
                "task_id": task_obj.task_id,
                "assigned_to": best_match.value if best_match else None,
                "status": "assigned" if best_match else "pending_review",
                "confidence": 0.85 if best_match else 0,
            }
        ]

    async def _evaluate_performance(
        self, agent_role: AgentRole, company_state: CompanyState
    ) -> Dict[str, Any]:
        agents = company_state.get("agents", {})
        agent_state = agents.get(agent_role)
        if not agent_state:
            return {
                "agent_role": agent_role.value,
                "status": "not_found",
                "evaluation": {},
            }
        completed_tasks = len(agent_state.completed_tasks)
        current_tasks = len(agent_state.current_tasks)
        total_tasks = completed_tasks + current_tasks
        completion_rate = completed_tasks / max(1, total_tasks)
        collaboration_score = self._calculate_collaboration_score(agent_role, agents)
        error_rate = self._calculate_error_rate(agent_state)
        response_time_score = self._calculate_response_time_score(agent_state)
        overall_score = (
            completion_rate * 0.4
            + collaboration_score * 0.3
            + (1 - error_rate) * 0.2
            + response_time_score * 0.1
        )
        performance_data = {
            "completion_rate": completion_rate,
            "collaboration_score": collaboration_score,
            "error_rate": error_rate,
            "response_time_score": response_time_score,
            "overall_score": overall_score,
        }
        self.performance_metrics[agent_role.value] = performance_data
        return {
            "agent_role": agent_role.value,
            "metrics": {
                "completed_tasks": completed_tasks,
                "current_tasks": current_tasks,
                "completion_rate": round(completion_rate, 3),
                "collaboration_score": round(collaboration_score, 3),
                "error_rate": round(error_rate, 3),
                "response_time_score": round(response_time_score, 3),
            },
            "overall_performance_score": round(overall_score, 3),
            "performance_tier": self._determine_performance_tier(overall_score),
            "strengths": self._identify_strengths(performance_data),
            "improvement_areas": self._identify_improvement_areas(performance_data),
        }

    async def _optimize_workflow(self, company_state: CompanyState) -> Dict[str, Any]:
        agents = company_state.get("agents", {})
        tasks = company_state.get("tasks", {})
        workflow_analysis = {
            "bottlenecks": [],
            "efficiency_metrics": {},
            "optimization_recommendations": [],
        }
        for role, agent_state in agents.items():
            workload = agent_state.workload
            current_tasks = len(agent_state.current_tasks)
            completed_tasks = len(agent_state.completed_tasks)
            if workload > 0.85:
                workflow_analysis["bottlenecks"].append(
                    {
                        "type": "overload",
                        "agent_role": role.value,
                        "current_tasks": current_tasks,
                        "workload_percentage": round(workload * 100, 2),
                    }
                )
            if completed_tasks > 0 and current_tasks > 0:
                workflow_analysis["efficiency_metrics"][role.value] = {
                    "productivity_ratio": round(completed_tasks / current_tasks, 3),
                    "workload_efficiency": round(1 - workload, 3),
                }
        workflow_analysis["optimization_recommendations"] = (
            self._generate_workflow_recommendations(workflow_analysis)
        )
        return workflow_analysis

    async def _design_kpis(
        self, agent_types: List[AgentRole], company_state: CompanyState
    ) -> Dict[str, Any]:
        kpi_designs = {}
        for agent_type in agent_types:
            agent_role_value = (
                agent_type.value if hasattr(agent_type, "value") else str(agent_type)
            )
            kpi_designs[agent_role_value] = {
                "primary_kpis": self._define_primary_kpis(agent_type, company_state),
                "secondary_kpis": self._define_secondary_kpis(agent_type),
                "targets": self._set_kpi_targets(agent_type),
                "evaluation_frequency": self._determine_evaluation_frequency(
                    agent_type
                ),
            }
        self.kpi_definitions = kpi_designs
        return kpi_designs

    async def _resolve_conflicts(
        self, conflict_data: Dict[str, Any], company_state: CompanyState
    ) -> Dict[str, Any]:
        conflict_id = conflict_data.get("conflict_id")
        involved_agents = conflict_data.get("involved_agents", [])
        conflict_type = conflict_data.get("conflict_type", "task_priority")
        resolution = {
            "conflict_id": conflict_id,
            "involved_agents": involved_agents,
            "conflict_type": conflict_type,
            "status": "resolved",
            "resolution_details": {},
            "recommended_actions": [],
        }
        if conflict_type == "task_priority":
            resolution["resolution_details"] = self._resolve_task_priority_conflict(
                conflict_data, company_state
            )
        elif conflict_type == "resource_allocation":
            resolution["resolution_details"] = self._resolve_resource_conflict(
                conflict_data
            )
        resolution["recommended_actions"] = self._generate_conflict_resolution_actions(
            resolution["resolution_details"]
        )
        self.conflict_registry[conflict_id] = resolution
        return resolution

    async def _assess组织_health(self, company_state: CompanyState) -> Dict[str, Any]:
        agents = company_state.get("agents", {})
        tasks = company_state.get("tasks", {})
        health_assessment = {
            "team_collaboration": self._assess_team_collaboration(agents),
            "workload_balance": self._assess_workload_balance(agents),
            "task_completion_health": self._assess_task_completion_health(tasks),
            "agent_satisfaction": self._assess_agent_satisfaction(agents),
            "organizational_agility": self._assess_organizational_agility(
                company_state
            ),
            "overall_health_score": 0,
            "health_indicators": {},
        }
        overall_score = (
            health_assessment["team_collaboration"]["score"] * 0.25
            + health_assessment["workload_balance"]["score"] * 0.25
            + health_assessment["task_completion_health"]["score"] * 0.25
            + health_assessment["agent_satisfaction"]["score"] * 0.15
            + health_assessment["organizational_agility"]["score"] * 0.10
        )
        health_assessment["overall_health_score"] = round(overall_score, 3)
        health_assessment["health_indicators"] = {
            "turnover_risk": self._assess_turnover_risk(agents),
            "innovation_capacity": self._assess_innovation_capacity(agents),
            "adaptability_index": self._assess_adaptability_index(agents),
        }
        self.organization_health = health_assessment
        return health_assessment

    async def _reassign_roles(
        self, reassignment_data: Dict[str, Any], company_state: CompanyState
    ) -> Dict[str, Any]:
        targets = reassignment_data.get("targets", [])
        justification = reassignment_data.get("justification", "")
        reassignments = []
        for target in targets:
            current_role = target.get("current_role")
            new_role = target.get("new_role")
            if current_role and new_role:
                reassignments.append(
                    {
                        "current_role": current_role,
                        "new_role": new_role,
                        "status": "requested",
                        "justification": justification,
                    }
                )
        return {
            "reassignments": reassignments,
            "status": "pending_approval",
            "timestamp": datetime.now().isoformat(),
            "estimated_impact": self._assess_reassignment_impact(
                reassignments, company_state
            ),
        }

    def _get_available_agents(self, company_state: CompanyState) -> List[AgentRole]:
        available = []
        for role, agent_state in company_state.get("agents", {}).items():
            if agent_state.workload < 0.8:
                available.append(role)
        return available

    def _find_best_agent_for_task(
        self, task: Task, available_agents: List[AgentRole], company_state: CompanyState
    ) -> Optional[AgentRole]:
        agents = company_state.get("agents", {})
        best_match, best_score = None, 0
        for agent_role in available_agents:
            score = 0.5
            task_keywords = (
                task.title.lower().split() + task.description.lower().split()
            )
            agent_state = agents.get(agent_role)
            if agent_state:
                for capability in agent_state.capabilities:
                    if any(kw in capability for kw in task_keywords):
                        score += 0.1
                if agent_state.workload < 0.5:
                    score += 0.2
                completed = len(agent_state.completed_tasks)
                current = len(agent_state.current_tasks)
                if completed > current:
                    score += 0.15
                if score > best_score:
                    best_score, best_match = score, agent_role
        return best_match

    def _calculate_collaboration_score(
        self, agent_role: AgentRole, agents: Dict[AgentRole, "AgentState"]
    ) -> float:
        agent = agents.get(agent_role)
        if not agent:
            return 0.5
        return min(1.0, len(agent.messages) * 0.3)

    def _calculate_error_rate(self, agent_state: "AgentState") -> float:
        completed = len(
            [t for t in agent_state.completed_tasks if t.status == "failed"]
        )
        total = len(agent_state.completed_tasks)
        return completed / max(1, total)

    def _calculate_response_time_score(self, agent_state: "AgentState") -> float:
        if not agent_state.completed_tasks:
            return 0.8
        avg_response = sum(
            (t.updated_at - t.created_at).total_seconds()
            for t in agent_state.completed_tasks
        ) / len(agent_state.completed_tasks)
        if avg_response < 3600:
            return 1.0
        elif avg_response < 86400:
            return 0.8
        return 0.5

    def _determine_performance_tier(self, score: float) -> str:
        if score >= 0.9:
            return "excellent"
        elif score >= 0.75:
            return "good"
        elif score >= 0.5:
            return "needs_improvement"
        return "critical"

    def _identify_strengths(self, performance: Dict[str, float]) -> List[str]:
        strengths = []
        if performance.get("completion_rate", 0) > 0.8:
            strengths.append("High task completion rate")
        if performance.get("collaboration_score", 0) > 0.7:
            strengths.append("Strong collaboration skills")
        if performance.get("error_rate", 1) < 0.1:
            strengths.append("Low error rate")
        return strengths

    def _identify_improvement_areas(self, performance: Dict[str, float]) -> List[str]:
        improvements = []
        if performance.get("completion_rate", 1) < 0.7:
            improvements.append("Improve task completion rate")
        if performance.get("collaboration_score", 0) < 0.6:
            improvements.append("Enhance collaboration with other agents")
        if performance.get("error_rate", 0) > 0.15:
            improvements.append("Reduce error rate")
        return improvements

    def _assess_system_efficiency(
        self, system_health: Dict[str, Any], task_metrics: Dict[str, Any]
    ) -> float:
        uptime = system_health.get("uptime", 99)
        task_completion = task_metrics.get("completion_rate", 0.8)
        return min(1.0, (uptime / 100) * 0.5 + task_completion * 0.5)

    def _detect_bottlenecks(self, task_metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        bottlenecks = []
        if task_metrics.get("pending_tasks", 0) > 50:
            bottlenecks.append(
                {
                    "type": "task_queue",
                    "description": "High number of pending tasks",
                    "severity": "high",
                }
            )
        if task_metrics.get("avg_completion_time", 0) > 86400:
            bottlenecks.append(
                {
                    "type": "processing_speed",
                    "description": "Slow task processing",
                    "severity": "medium",
                }
            )
        return bottlenecks

    def _assess_team_load_balance(self, task_metrics: Dict[str, Any]) -> Dict[str, Any]:
        max_load = task_metrics.get("max_workload", 0.8)
        min_load = task_metrics.get("min_workload", 0.2)
        balance_score = 1.0 - abs(max_load - min_load)
        return {
            "balance_score": round(balance_score, 3),
            "max_load": round(max_load, 3),
            "min_load": round(min_load, 3),
            "status": "balanced" if balance_score > 0.7 else "rebalancing_needed",
        }

    def _assess_budget_efficiency(self, budget_data: Dict[str, Any]) -> Dict[str, Any]:
        total_budget = budget_data.get("total_budget", 0)
        actual_spent = budget_data.get("actual_spent", 0)
        efficiency = actual_spent / max(1, total_budget)
        return {
            "efficiency_score": round(min(1.0, efficiency), 3),
            "total_budget": total_budget,
            "actual_spent": actual_spent,
            "remaining_budget": total_budget - actual_spent,
            "status": "efficient" if efficiency <= 0.9 else "over_spent",
        }

    def _assess_resource_optimization(
        self, resource_usage: Dict[str, Any]
    ) -> Dict[str, Any]:
        cpu_usage = resource_usage.get("cpu_usage", 50)
        memory_usage = resource_usage.get("memory_usage", 50)
        optimization_score = (100 - abs(cpu_usage - 50)) * 0.3 + (
            100 - abs(memory_usage - 50)
        ) * 0.3
        return {
            "optimization_score": round(min(100, optimization_score) / 100, 3),
            "resource_utilization": {"cpu": cpu_usage, "memory": memory_usage},
            "efficiency_rating": "optimal" if optimization_score > 70 else "suboptimal",
        }

    def _calculate_cost_efficiency(
        self, budget_data: Dict[str, Any], resource_usage: Dict[str, Any]
    ) -> Dict[str, Any]:
        total_budget = budget_data.get("total_budget", 100000)
        total_output = resource_usage.get("output_metrics", {}).get(
            "tasks_completed", 0
        ) + resource_usage.get("output_metrics", {}).get("projects_delivered", 0)
        return {
            "total_budget": total_budget,
            "total_output": total_output,
            "cost_per_output": round(total_budget / max(1, total_output), 2),
        }

    def _generate_hr_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        recommendations = []
        if analysis.get("system_efficiency", 1) < 0.8:
            recommendations.append(
                "Optimize task distribution to improve system efficiency"
            )
        for bottleneck in analysis.get("bottleneck_detection", []):
            recommendations.append(f"Address {bottleneck['type']} bottleneck")
        if analysis.get("team_load_balance", {}).get("status") == "rebalancing_needed":
            recommendations.append("Rebalance team workloads")
        return recommendations

    def _generate_resource_suggestions(self, analysis: Dict[str, Any]) -> List[str]:
        suggestions = []
        if analysis.get("budget_efficiency", {}).get("status") == "over_spent":
            suggestions.append("Review and optimize budget allocation")
        if (
            analysis.get("resource_optimization", {}).get("efficiency_rating")
            == "suboptimal"
        ):
            suggestions.append("Optimize resource utilization")
        return suggestions

    async def _trigger_role_reconfiguration(
        self, alert_data: Dict[str, Any], company_state: CompanyState
    ) -> Optional[Message]:
        failure_rate = alert_data.get("failure_rate", 0)
        affected_agents = alert_data.get("affected_agents", [])
        reconfiguration_plan = {
            "justification": f"High failure rate detected: {failure_rate}",
            "targets": [
                {
                    "current_role": agent.value
                    if hasattr(agent, "value")
                    else str(agent),
                    "new_role": "operations",
                }
                for agent in affected_agents
            ],
        }
        reassignments = await self._reassign_roles(reconfiguration_plan, company_state)
        return CommunicationProtocol.create_message(
            sender=self.role,
            recipient=AgentRole.CEO,
            message_type=MessageType.ALERT,
            content={
                "alert_type": "role_reconfiguration_recommended",
                "message": f"Recommended role reconfiguration for {len(affected_agents)} agents",
                "reconfiguration_plan": reassignments,
            },
            priority=Priority.HIGH,
        )

    def _resolve_task_priority_conflict(
        self, conflict_data: Dict[str, Any], company_state: CompanyState
    ) -> Dict[str, Any]:
        involved_agents = conflict_data.get("involved_agents", [])
        tasks = conflict_data.get("conflicting_tasks", [])
        resolved_tasks = []
        for task in tasks:
            task_obj = Task(
                task_id=task.get("task_id", ""),
                title=task.get("title", ""),
                assigned_to=AgentRole(task.get("assigned_to", "")),
                priority=Priority(task.get("priority", "medium")),
            )
            best_agent = self._find_best_agent_for_task(
                task_obj, self._get_available_agents(company_state), company_state
            )
            if best_agent:
                resolved_tasks.append(
                    {
                        "task_id": task_obj.task_id,
                        "assigned_to": best_agent.value,
                        "priority_adjusted": True,
                    }
                )
        return {
            "resolved_tasks": resolved_tasks,
            "conflict_resolution": True,
            "affected_agents": involved_agents,
        }

    def _resolve_resource_conflict(
        self, conflict_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        involved_agents = conflict_data.get("involved_agents", [])
        resource_requests = conflict_data.get("resource_requests", [])
        allocation = {}
        for request in resource_requests:
            allocation[request.get("agent")] = {
                "resource": request.get("resource"),
                "allocated": True,
                "priority": "medium",
            }
        return {
            "allocation": allocation,
            "conflict_resolution": True,
            "affected_agents": involved_agents,
        }

    def _generate_conflict_resolution_actions(
        self, resolution_details: Dict[str, Any]
    ) -> List[str]:
        actions = []
        if resolution_details.get("resolved_tasks"):
            actions.append("Update task assignments")
        if resolution_details.get("allocation"):
            actions.append("Reallocate resources")
        return actions

    async def _process_role_reconfiguration_request(
        self, message: Message, company_state: CompanyState
    ) -> Message:
        request_data = message.content
        reconfiguration_plan = request_data.get("plan", {})
        assessment = {
            "current_state": self._assess_current_team_state(company_state),
            "proposed_changes": reconfiguration_plan,
            "impact_analysis": self._analyze_reconfiguration_impact(
                reconfiguration_plan
            ),
            "risk_assessment": self._assess_reconfiguration_risk(reconfiguration_plan),
        }
        approved = assessment["risk_assessment"]["risk_level"] != "high"
        return CommunicationProtocol.create_message(
            sender=self.role,
            recipient=message.sender,
            message_type=MessageType.APPROVAL_RESPONSE,
            content={
                "request_id": request_data.get("request_id"),
                "decision": {
                    "approved": approved,
                    "assessment": assessment,
                    "implementation_notes": self._generate_implementation_notes(
                        assessment
                    )
                    if approved
                    else [],
                },
            },
        )

    async def _process_resource_allocation_request(
        self, message: Message, company_state: CompanyState
    ) -> Message:
        request_data = message.content
        allocation_plan = request_data.get("allocation_plan", {})
        assessment = {
            "current_resource_status": self._assess_current_resources(company_state),
            "requested_allocation": allocation_plan,
            "strategic_alignment": self._align_with_strategic_goals(
                allocation_plan, company_state
            ),
            "cost_benefit_analysis": self._analyze_cost_benefit(
                allocation_plan, company_state
            ),
        }
        approved = assessment["strategic_alignment"]["alignment_score"] >= 70
        return CommunicationProtocol.create_message(
            sender=self.role,
            recipient=message.sender,
            message_type=MessageType.APPROVAL_RESPONSE,
            content={
                "request_id": request_data.get("request_id"),
                "decision": {
                    "approved": approved,
                    "assessment": assessment,
                    "optimized_allocation": self._optimize_resource_allocation(
                        allocation_plan
                    )
                    if approved
                    else None,
                },
            },
        )

    async def _process_organizational_insight(
        self, message: Message, company_state: CompanyState
    ) -> Message:
        insight_data = message.content.get("data", {})
        response = {
            "insight_processed": True,
            "hr_action": self._generate_hr_actions_from_insight(insight_data),
            "long_term_impact": self._assess_long_term_impact(insight_data),
        }
        return CommunicationProtocol.create_message(
            sender=self.role,
            recipient=message.sender,
            message_type=MessageType.COLLABORATION,
            content={"type": "organizational_insight_response", "response": response},
        )

    def _assess_current_team_state(self, company_state: CompanyState) -> Dict[str, Any]:
        agents = company_state.get("agents", {})
        tasks = company_state.get("tasks", {})
        return {
            "total_agents": len(agents),
            "total_tasks": len(tasks),
            "completed_tasks": len(
                [t for t in tasks.values() if t.status == "completed"]
            ),
            "pending_tasks": len([t for t in tasks.values() if t.status == "pending"]),
            "agent_distribution": {
                role.value: len(agent.completed_tasks) for role, agent in agents.items()
            },
        }

    def _analyze_reconfiguration_impact(
        self, reconfiguration_plan: Dict[str, Any]
    ) -> Dict[str, Any]:
        targets = reconfiguration_plan.get("targets", [])
        return {
            "affected_agents_count": len(targets),
            "transition_complexity": "medium" if len(targets) > 5 else "low",
            "business_impact": "Moderate" if len(targets) > 3 else "minimal",
            "critical_concerns": [],
        }

    def _assess_reconfiguration_risk(
        self, reconfiguration_plan: Dict[str, Any]
    ) -> Dict[str, Any]:
        targets = reconfiguration_plan.get("targets", [])
        risk_level = (
            "high" if len(targets) > 10 else "medium" if len(targets) > 5 else "low"
        )
        return {
            "risk_level": risk_level,
            "affected_roles_count": len(targets),
            "mitigation_required": risk_level != "low",
        }

    def _generate_implementation_notes(self, assessment: Dict[str, Any]) -> List[str]:
        notes = []
        if assessment.get("impact_analysis", {}).get("transition_complexity") == "high":
            notes.extend(["Implement changes in phases", "Provide transition support"])
        if assessment.get("risk_assessment", {}).get("risk_level") == "high":
            notes.extend(
                ["Develop rollback plan", "Schedule during low-activity periods"]
            )
        return notes

    def _assess_current_resources(self, company_state: CompanyState) -> Dict[str, Any]:
        agents = company_state.get("agents", {})
        kpis = company_state.get("kpis", {})
        total_completed = sum(len(agent.completed_tasks) for agent in agents.values())
        total_current = sum(len(agent.current_tasks) for agent in agents.values())
        return {
            "total_agents": len(agents),
            "agent_distribution": {
                role.value: agent.capabilities for role, agent in agents.items()
            },
            "budget": kpis.get("budget", 0),
            "current_efficiency": total_completed
            / max(1, total_completed + total_current),
        }

    def _align_with_strategic_goals(
        self, allocation_plan: Dict[str, Any], company_state: CompanyState
    ) -> Dict[str, Any]:
        strategic_goals = company_state.get("strategic_goals", {})
        allocated_budget = allocation_plan.get("budget", 0)
        alignment_score = 0.8 if allocated_budget > 0 and strategic_goals else 0.5
        return {
            "alignment_score": alignment_score,
            "allocated_budget": allocated_budget,
            "strategic_alignment": "good" if alignment_score > 0.7 else "needs_review",
        }

    def _analyze_cost_benefit(
        self, allocation_plan: Dict[str, Any], company_state: CompanyState
    ) -> Dict[str, Any]:
        budget = allocation_plan.get("budget", 0)
        projected_benefits = allocation_plan.get("projected_benefits", {})
        return {
            "budget": budget,
            "projected_benefits": projected_benefits,
            "roi_estimate": projected_benefits.get("expected_return", 0)
            / max(1, budget)
            if budget > 0
            else 0,
        }

    def _optimize_resource_allocation(
        self, allocation_plan: Dict[str, Any]
    ) -> Dict[str, Any]:
        budget = allocation_plan.get("budget", 0)
        return {
            "budget_allocation": budget * 0.8,
            "contingency": budget * 0.2,
            "recommendations": [
                "Allocate 30% to high-performing agents",
                "Allocate 20% to new initiatives",
                "Maintain 20% as buffer",
                "Invest 15% in training",
                "Reserve 15% for unexpected needs",
            ],
        }

    def _generate_hr_actions_from_insight(
        self, insight_data: Dict[str, Any]
    ) -> List[str]:
        actions = []
        if insight_data.get("type") == "employee_feedback":
            actions.extend(["Analyze feedback themes", "Develop action plan"])
        if insight_data.get("type") == "performance_trend":
            actions.extend(["Identify top performers", "Design recognition programs"])
        return actions

    def _assess_long_term_impact(self, insight_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "impact_duration": "long_term",
            "strategic_alignment": "high",
            "resource_impact": insight_data.get("resource_impact", "moderate"),
        }

    def _generate_workflow_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        recommendations = []
        for bottleneck in analysis.get("bottlenecks", []):
            if bottleneck.get("type") == "overload":
                recommendations.append(
                    f"Reassign tasks from {bottleneck.get('agent_role')} to balance workload"
                )
        efficiency_metrics = analysis.get("efficiency_metrics", {})
        for role, metrics in efficiency_metrics.items():
            if metrics.get("productivity_ratio", 1) < 0.5:
                recommendations.append(f"Review productivity for {role}")
        return recommendations

    def _generate_implementation_recommendations(
        self, workflow_analysis: Dict[str, Any]
    ) -> List[str]:
        recommendations = []
        bottleneck_count = len(workflow_analysis.get("bottlenecks", []))
        if bottleneck_count > 3:
            recommendations.append("Implement automated task routing")
        if len(workflow_analysis.get("efficiency_metrics", {})) > 0:
            recommendations.append("Set up performance dashboards")
        return recommendations

    def _assess_team_collaboration(
        self, agents: Dict[AgentRole, "AgentState"]
    ) -> Dict[str, Any]:
        collaboration_scores = [
            self._calculate_collaboration_score(role, agents) for role in agents.keys()
        ]
        avg_score = sum(collaboration_scores) / max(1, len(collaboration_scores))
        return {
            "score": round(avg_score, 3),
            "status": "healthy" if avg_score > 0.7 else "needs_attention",
            "detailed_scores": {
                role.value: score
                for role, score in zip(agents.keys(), collaboration_scores)
            },
        }

    def _assess_workload_balance(
        self, agents: Dict[AgentRole, "AgentState"]
    ) -> Dict[str, Any]:
        workloads = [agent.workload for agent in agents.values()]
        avg_workload = sum(workloads) / max(1, len(workloads))
        max_workload, min_workload = max(workloads), min(workloads)
        balance_score = 1.0 - (max_workload - min_workload)
        return {
            "score": round(balance_score, 3),
            "avg_workload": round(avg_workload, 3),
            "max_workload": round(max_workload, 3),
            "min_workload": round(min_workload, 3),
            "status": "balanced" if balance_score > 0.7 else "rebalancing_needed",
        }

    def _assess_task_completion_health(
        self, tasks: Dict[str, "Task"]
    ) -> Dict[str, Any]:
        completed = len([t for t in tasks.values() if t.status == "completed"])
        total = len(tasks)
        completion_rate = completed / max(1, total)
        return {
            "score": round(completion_rate, 3),
            "completed_tasks": completed,
            "total_tasks": total,
            "status": "healthy" if completion_rate > 0.8 else "needs_attention",
        }

    def _assess_agent_satisfaction(
        self, agents: Dict[AgentRole, "AgentState"]
    ) -> Dict[str, Any]:
        satisfaction_scores = []
        for role, agent_state in agents.items():
            workload = agent_state.workload
            completed, current = (
                len(agent_state.completed_tasks),
                len(agent_state.current_tasks),
            )
            score = (completed / max(1, current + completed)) * 0.6 + (
                1 - workload
            ) * 0.4
            satisfaction_scores.append(score)
        avg_score = sum(satisfaction_scores) / max(1, len(satisfaction_scores))
        return {
            "score": round(avg_score, 3),
            "status": "high"
            if avg_score > 0.7
            else "medium"
            if avg_score > 0.5
            else "low",
            "individual_scores": {
                role.value: score
                for role, score in zip(agents.keys(), satisfaction_scores)
            },
        }

    def _assess_organizational_agility(
        self, company_state: CompanyState
    ) -> Dict[str, Any]:
        tasks = company_state.get("tasks", {})
        total_completed = len([t for t in tasks.values() if t.status == "completed"])
        total = len(tasks)
        avg_completion = total_completed / max(1, total)
        agility_score = avg_completion * 0.7
        return {
            "score": round(agility_score, 3),
            "status": "agile" if agility_score > 0.7 else "needs_improvement",
        }

    def _assess_turnover_risk(
        self, agents: Dict[AgentRole, "AgentState"]
    ) -> Dict[str, Any]:
        risk_factors = []
        for role, agent_state in agents.items():
            if agent_state.workload > 0.85:
                risk_factors.append(
                    {"agent": role.value, "factor": "overload", "risk_level": "high"}
                )
        high_risk_count = len(
            [f for f in risk_factors if f.get("risk_level") == "high"]
        )
        return {
            "risk_level": "high"
            if high_risk_count > 2
            else "medium"
            if high_risk_count > 0
            else "low",
            "risk_factors": risk_factors,
            "mitigation_needed": high_risk_count > 0,
        }

    def _assess_innovation_capacity(
        self, agents: Dict[AgentRole, "AgentState"]
    ) -> Dict[str, Any]:
        innovation_scores = []
        for role, agent_state in agents.items():
            score = min(1.0, len(agent_state.capabilities) / 10)
            innovation_scores.append(score)
        avg_score = sum(innovation_scores) / max(1, len(innovation_scores))
        return {
            "score": round(avg_score, 3),
            "capacity_rating": "strong"
            if avg_score > 0.7
            else "moderate"
            if avg_score > 0.5
            else "limited",
        }

    def _assess_adaptability_index(
        self, agents: Dict[AgentRole, "AgentState"]
    ) -> float:
        adaptability_scores = [
            min(1.0, len(agent.capabilities) / 10) for agent in agents.values()
        ]
        return round(sum(adaptability_scores) / max(1, len(adaptability_scores)), 3)

    def _generate_executive_summary(self, organization_health: Dict[str, Any]) -> str:
        overall_score = organization_health.get("overall_health_score", 0)
        if overall_score >= 0.85:
            return "Organization is healthy. Continue current practices."
        elif overall_score >= 0.7:
            return "Organization is performing well with minor areas for improvement."
        elif overall_score >= 0.5:
            return "Organization needs attention. Multiple areas require improvement."
        return "Critical organizational health issues detected. Immediate intervention required."

    def _generate_report_recommendations(
        self, organization_health: Dict[str, Any]
    ) -> List[str]:
        recommendations = []
        if (
            organization_health.get("team_collaboration", {}).get("status")
            == "needs_attention"
        ):
            recommendations.append("Facilitate cross-agent collaboration workshops")
        if (
            organization_health.get("workload_balance", {}).get("status")
            == "rebalancing_needed"
        ):
            recommendations.append("Reassign tasks to balance workloads")
        if organization_health.get("agent_satisfaction", {}).get("status") == "low":
            recommendations.append("Review agent workloads and provide support")
        if organization_health.get("turnover_risk", {}).get("risk_level") == "high":
            recommendations.append("Implement retention strategies")
        return recommendations

    def _determine_next_actions(self, organization_health: Dict[str, Any]) -> List[str]:
        next_actions = []
        if organization_health.get("overall_health_score", 1) < 0.7:
            next_actions.extend(
                ["Schedule organizational review meeting", "Identify critical issues"]
            )
        if (
            organization_health.get("workload_balance", {}).get("status")
            == "rebalancing_needed"
        ):
            next_actions.append("Distribute pending tasks across team")
        if (
            organization_health.get("organizational_agility", {}).get("status")
            == "needs_improvement"
        ):
            next_actions.append("Implement agile practices and tools")
        return next_actions

    def _generate_performance_summary(
        self, results: Dict[str, Any], period: str
    ) -> str:
        scores = [
            role_data.get("overall_performance_score", 0)
            for role_data in results.values()
            if isinstance(role_data, dict)
        ]
        if not scores:
            return f"No performance data available for {period} period"
        avg_score = sum(scores) / len(scores)
        if avg_score >= 0.85:
            return f"Overall performance is excellent with average score of {avg_score:.1%} in {period} period"
        elif avg_score >= 0.7:
            return f"Overall performance is good with average score of {avg_score:.1%} in {period} period"
        return f"Overall performance needs improvement with average score of {avg_score:.1%} in {period} period"

    def _define_primary_kpis(
        self, agent_type: AgentRole, company_state: CompanyState
    ) -> List[Dict[str, Any]]:
        kpis = []
        if agent_type == AgentRole.RD:
            kpis.extend(
                [
                    {"name": "code_quality_score", "type": "quality", "target": 85},
                    {
                        "name": "task_completion_rate",
                        "type": "efficiency",
                        "target": 90,
                    },
                ]
            )
        elif agent_type == AgentRole.DATA_ANALYST:
            kpis.extend(
                [
                    {
                        "name": "report_delivery_rate",
                        "type": "efficiency",
                        "target": 95,
                    },
                    {"name": "data_accuracy", "type": "quality", "target": 99.9},
                ]
            )
        elif agent_type == AgentRole.CUSTOMER_SUPPORT:
            kpis.extend(
                [
                    {"name": "response_time", "type": "speed", "target": 2},
                    {"name": "resolution_rate", "type": "quality", "target": 95},
                ]
            )
        return kpis

    def _define_secondary_kpis(self, agent_type: AgentRole) -> List[Dict[str, Any]]:
        return [
            {"name": "collaboration_score", "type": "team", "target": 80},
            {"name": "knowledge_sharing", "type": "development", "target": 70},
        ]

    def _set_kpi_targets(self, agent_type: AgentRole) -> Dict[str, Any]:
        return {
            "period": "quarterly",
            "review_frequency": "monthly",
            "evaluation_method": "weighted_average",
        }

    def _determine_evaluation_frequency(self, agent_type: AgentRole) -> str:
        return (
            "weekly"
            if agent_type in [AgentRole.RD, AgentRole.DATA_ANALYST]
            else "biweekly"
        )

    def _assess_reassignment_impact(
        self, reassignments: List[Dict[str, Any]], company_state: CompanyState
    ) -> Dict[str, Any]:
        return {
            "transition_complexity": "medium",
            "impact_duration": "2-4 weeks",
            "resource_requirements": {
                "training_hours": len(reassignments) * 5,
                "supervision": "moderate",
            },
        }
