from typing import Dict, List, Optional, Any
import json
import asyncio
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



class OperationsAgent(BaseAgent):
    def __init__(self):
        capabilities = [
            "任务编排",
            "系统监控",
            "流程管理",
            "异常检测",
            "熔断实现",
            "资源调度",
            "性能优化",
            "自动恢复",
        ]
        super().__init__(AgentRole.OPERATIONS, capabilities)
        default_model_config = app_config.llm.models.get(
            app_config.llm.default_model,
            ModelConfig(
                name=app_config.llm.default_model,
                provider="openai",
                api_key=None,
                config={},
            ),
        )
        agent_config = app_config.agents.get("operations", AgentConfig())
        self.llm = ChatOpenAI(
            model=app_config.llm.default_model,
            temperature=agent_config.temperature if agent_config.temperature != 0.3 else default_model_config.config.get("temperature", 0.3),
        )
        self.task_queue: List[Task] = []
        self.system_health: Dict[str, Any] = {
            "uptime": 99.9,
            "error_rate": 0.1,
            "response_time": 150,
            "agent_states": {},
        }
        self.workflow_registry: Dict[str, Dict[str, Any]] = {}
        self.anomaly_registry: Dict[str, Dict[str, Any]] = {}
        self.circuit_breakers: Dict[str, Dict[str, Any]] = {}
        self.last_health_report_time: Optional[datetime] = None
        self.monitoring_interval: int = 1
        self.report_interval: int = 3600

    async def process_message(
        self, message: Message, company_state: CompanyState
    ) -> Optional[Message]:
        if message.message_type == MessageType.TASK_ASSIGNMENT:
            return await self._handle_task_assignment(message, company_state)
        elif message.message_type == MessageType.STATUS_REPORT:
            return await self._handle_status_report(message, company_state)
        elif message.message_type == MessageType.ALERT:
            return await self._handle_alert(message, company_state)
        elif message.message_type == MessageType.DATA_REQUEST:
            return await self._handle_data_request(message, company_state)
        elif message.message_type == MessageType.APPROVAL_REQUEST:
            return await self._handle_approval_request(message, company_state)
        elif message.message_type == MessageType.APPROVAL_RESPONSE:
            return await self._handle_approval_response(message, company_state)
        elif message.message_type == MessageType.COLLABORATION:
            return await self._handle_collaboration(message, company_state)
        elif message.message_type == MessageType.DATA_RESPONSE:
            return await self._handle_data_response(message, company_state)

        return None

    async def _handle_task_assignment(
        self, message: Message, company_state: CompanyState
    ) -> Optional[Message]:
        task_data = message.content.get("task", {})
        task = Task(**task_data)

        self.task_queue.append(task)

        return CommunicationProtocol.create_message(
            sender=self.role,
            recipient=message.sender,
            message_type=MessageType.COLLABORATION,
            content={
                "type": "task_acknowledgment",
                "task_id": task.task_id,
                "status": "queued",
                "priority": task.priority.value,
            },
        )

    async def _handle_status_report(
        self, message: Message, company_state: CompanyState
    ) -> Optional[Message]:
        report_data = message.content
        sender = message.sender

        self.system_health["agent_states"][sender.value] = {
            "last_report": datetime.now().isoformat(),
            "status": report_data.get("status", "unknown"),
            "metrics": report_data.get("metrics", {}),
        }

        return CommunicationProtocol.create_message(
            sender=self.role,
            recipient=sender,
            message_type=MessageType.COLLABORATION,
            content={
                "type": "status_acknowledgment",
                "received": True,
                "timestamp": datetime.now().isoformat(),
            },
        )

    async def _handle_alert(
        self, message: Message, company_state: CompanyState
    ) -> Optional[Message]:
        alert_data = message.content
        alert_type = alert_data.get("alert_type", "unknown")
        severity = alert_data.get("severity", "medium")

        self.anomaly_registry[alert_type] = {
            "detected_at": datetime.now().isoformat(),
            "severity": severity,
            "message": alert_data.get("message", ""),
            "status": "new",
        }

        circuit_breaker = self.circuit_breakers.get(alert_type, {})
        if circuit_breaker.get("state") == "open":
            return CommunicationProtocol.create_alert(
                sender=self.role,
                alert_type="circuit_breaker_active",
                message=f"Circuit breaker is open for {alert_type}. Automatic recovery initiated.",
                severity=Priority.HIGH,
            )

        return await self._process_alert(alert_data, company_state)

    async def _handle_data_request(
        self, message: Message, company_state: CompanyState
    ) -> Message:
        request_type = message.content.get("request_type", "")

        if request_type == "system_health":
            return CommunicationProtocol.create_message(
                sender=self.role,
                recipient=message.sender,
                message_type=MessageType.DATA_RESPONSE,
                content={
                    "request_id": message.content.get("request_id"),
                    "data": self.system_health,
                    "data_type": "system_health",
                },
            )
        elif request_type == "task_queue":
            return CommunicationProtocol.create_message(
                sender=self.role,
                recipient=message.sender,
                message_type=MessageType.DATA_RESPONSE,
                content={
                    "request_id": message.content.get("request_id"),
                    "data": {
                        "tasks": [t.__dict__ for t in self.task_queue],
                        "task_count": len(self.task_queue),
                    },
                    "data_type": "task_queue",
                },
            )
        elif request_type == "anomalies":
            return CommunicationProtocol.create_message(
                sender=self.role,
                recipient=message.sender,
                message_type=MessageType.DATA_RESPONSE,
                content={
                    "request_id": message.content.get("request_id"),
                    "data": self.anomaly_registry,
                    "data_type": "anomaly_registry",
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

    async def _handle_approval_request(
        self, message: Message, company_state: CompanyState
    ) -> Message:
        request_data = message.content
        request_type = request_data.get("request_type", "")

        if request_type == "workflow_execution":
            return await self._evaluate_workflow_execution(message, company_state)
        elif request_type == "resource_allocation":
            return await self._evaluate_resource_allocation(message, company_state)

        return CommunicationProtocol.create_message(
            sender=self.role,
            recipient=message.sender,
            message_type=MessageType.APPROVAL_RESPONSE,
            content={
                "request_id": request_data.get("request_id"),
                "approved": False,
                "reasoning": f"Unknown approval request type: {request_type}",
            },
        )

    async def _handle_approval_response(
        self, message: Message, company_state: CompanyState
    ) -> Optional[Message]:
        response_data = message.content
        approval_result = response_data.get("decision", {})

        if approval_result.get("approved"):
            task_id = message.content.get("task_id")
            if task_id:
                for task in self.task_queue:
                    if task.task_id == task_id:
                        task.status = "approved"
                        break

        return None

    async def _handle_collaboration(
        self, message: Message, company_state: CompanyState
    ) -> Optional[Message]:
        content = message.content
        collaboration_type = content.get("type", "")

        if collaboration_type == "orchestration_request":
            return await self._handle_orchestration_request(message, company_state)
        elif collaboration_type == "workflow_trigger":
            return await self._handle_workflow_trigger(message, company_state)

        return None

    async def _handle_data_response(
        self, message: Message, company_state: CompanyState
    ) -> Optional[Message]:
        data = message.content
        response_type = data.get("data_type", "")

        if response_type == "performance_metrics":
            self.system_health["performance"] = data.get("data", {})
        elif response_type == "agent_states":
            self.system_health["agent_states"].update(data.get("data", {}))

        return CommunicationProtocol.create_message(
            sender=self.role,
            recipient=message.sender,
            message_type=MessageType.COLLABORATION,
            content={
                "type": "data_received",
                "data_type": response_type,
                "status": "processed",
            },
        )

    async def execute_task(
        self, task: Task, company_state: CompanyState
    ) -> Dict[str, Any]:
        if task.assigned_to == AgentRole.OPERATIONS:
            return await self._execute_orchestration_task(task, company_state)
        elif "monitoring" in task.title.lower():
            return await self._execute_monitoring_task(task, company_state)
        elif "workflow" in task.title.lower():
            return await self._execute_workflow_task(task, company_state)
        else:
            return await self._execute_general_task(task, company_state)

    async def _execute_orchestration_task(
        self, task: Task, company_state: CompanyState
    ) -> Dict[str, Any]:
        try:
            orchestration_result = await self._orchestrate_task_flow(
                task, company_state
            )

            return {
                "status": "completed",
                "result": orchestration_result,
                "type": "orchestration",
                "timestamp": datetime.now().isoformat(),
                "execution_summary": {
                    "tasks_orchestrated": len(
                        orchestration_result.get("executed_tasks", [])
                    ),
                    "success_rate": orchestration_result.get("success_rate", 100),
                    "failed_tasks": orchestration_result.get("failed_tasks", []),
                },
            }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def _execute_monitoring_task(
        self, task: Task, company_state: CompanyState
    ) -> Dict[str, Any]:
        try:
            monitoring_result = await self._monitor_system_health(company_state)

            return {
                "status": "completed",
                "result": monitoring_result,
                "type": "monitoring",
                "timestamp": datetime.now().isoformat(),
                "health_score": monitoring_result.get("health_score", 100),
            }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def _execute_workflow_task(
        self, task: Task, company_state: CompanyState
    ) -> Dict[str, Any]:
        try:
            workflow_name = task.metadata.get("workflow_name", task.title)
            workflow_result = await self._trigger_workflow(
                workflow_name, task.metadata, company_state
            )

            return {
                "status": "completed",
                "result": workflow_result,
                "type": "workflow_execution",
                "timestamp": datetime.now().isoformat(),
                "workflow_name": workflow_name,
            }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def _execute_general_task(
        self, task: Task, company_state: CompanyState
    ) -> Dict[str, Any]:
        try:
            result = {
                "status": "completed",
                "result": {
                    "task_id": task.task_id,
                    "title": task.title,
                    "description": task.description,
                    "priority": task.priority.value,
                },
                "type": "general_task",
                "timestamp": datetime.now().isoformat(),
            }

            return result
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def generate_report(self, company_state: CompanyState) -> Dict[str, Any]:
        return await self._generate_system_health_report(company_state)

    async def _orchestrate_task_flow(
        self, task: Task, company_state: CompanyState
    ) -> Dict[str, Any]:
        executed_tasks = []
        failed_tasks = []

        dependencies = task.dependencies if task.dependencies else []

        for dep_task_id in dependencies:
            dep_task = company_state.get("tasks", {}).get(dep_task_id)
            if dep_task and dep_task.status == "completed":
                executed_tasks.append(dep_task_id)

        current_tasks = company_state.get("tasks", {})

        if len(current_tasks) == 0:
            return {
                "executed_tasks": executed_tasks,
                "failed_tasks": failed_tasks,
                "success_rate": 100.0,
                "total_tasks": 0,
                "status": "no_tasks_to_orchestrate",
            }

        success_count = len(executed_tasks)
        total_count = len(executed_tasks) + len(failed_tasks) + len(current_tasks)

        return {
            "executed_tasks": executed_tasks,
            "failed_tasks": failed_tasks,
            "success_rate": (success_count / max(1, total_count)) * 100,
            "total_tasks": total_count,
            "status": "orchestration_complete",
        }

    async def _monitor_system_health(
        self, company_state: CompanyState
    ) -> Dict[str, Any]:
        agents = company_state.get("agents", {})
        agent_health = {}
        health_scores = []

        for role, agent_state in agents.items():
            if role == AgentRole.OPERATIONS:
                continue

            current_tasks = len(agent_state.current_tasks)
            completed_tasks = len(agent_state.completed_tasks)
            workload = agent_state.workload

            if current_tasks + completed_tasks > 0:
                task_completion_rate = completed_tasks / (
                    current_tasks + completed_tasks
                )
            else:
                task_completion_rate = 1.0

            time_since_active = (
                datetime.now() - agent_state.last_active
            ).total_seconds()
            is_active = time_since_active < 3600

            score = 100
            if not is_active:
                score -= 20
            if workload > 0.8:
                score -= 15
            if workload > 0.95:
                score -= 30
            if task_completion_rate < 0.7:
                score -= 20

            health_scores.append(score)

            agent_health[role.value] = {
                "current_tasks": current_tasks,
                "completed_tasks": completed_tasks,
                "workload": workload,
                "is_active": is_active,
                "task_completion_rate": task_completion_rate,
                "health_score": score,
                "last_active": agent_state.last_active.isoformat(),
            }

        overall_health_score = sum(health_scores) / max(1, len(health_scores))

        queue_size = len(self.task_queue)
        queue_pressure = (
            "low" if queue_size < 10 else "medium" if queue_size < 50 else "high"
        )

        anomaly_count = len(self.anomaly_registry)
        anomaly_status = "normal" if anomaly_count == 0 else "attention_required"

        return {
            "overall_health_score": overall_health_score,
            "agent_health": agent_health,
            "task_queue": {
                "size": queue_size,
                "pressure": queue_pressure,
                "bottlenecks": self._detect_bottlenecks(company_state),
            },
            "anomalies": {
                "count": anomaly_count,
                "status": anomaly_status,
                "registry": self.anomaly_registry,
            },
            "circuit_breakers": {
                "active_count": sum(
                    1
                    for cb in self.circuit_breakers.values()
                    if cb.get("state") == "open"
                ),
                "status": "healthy"
                if sum(
                    1
                    for cb in self.circuit_breakers.values()
                    if cb.get("state") == "open"
                )
                == 0
                else "degraded",
            },
            "timestamp": datetime.now().isoformat(),
        }

    async def _detect_anomalies(
        self, company_state: CompanyState
    ) -> List[Dict[str, Any]]:
        anomalies = []

        agents = company_state.get("agents", {})
        for role, agent_state in agents.items():
            if role == AgentRole.OPERATIONS:
                continue

            workload = agent_state.workload
            if workload > 0.95:
                anomalies.append(
                    {
                        "type": "high_workload",
                        "agent": role.value,
                        "value": workload,
                        "threshold": 0.95,
                        "severity": "high",
                        "detected_at": datetime.now().isoformat(),
                    }
                )

            timeout = (datetime.now() - agent_state.last_active).total_seconds()
            if timeout > 300 and workload > 0.5:
                anomalies.append(
                    {
                        "type": "inactive_agent_with_load",
                        "agent": role.value,
                        "value": timeout,
                        "threshold": 300,
                        "severity": "critical",
                        "detected_at": datetime.now().isoformat(),
                    }
                )

        for agent_state in agents.values():
            completed = len(agent_state.completed_tasks)
            failed = completed * 0.1
            if failed > 5:
                anomalies.append(
                    {
                        "type": "high_failure_rate",
                        "agent": agent_state.role.value,
                        "value": failed,
                        "threshold": 5,
                        "severity": "medium",
                        "detected_at": datetime.now().isoformat(),
                    }
                )

        return anomalies

    async def _trigger_workflow(
        self, workflow_name: str, metadata: Dict[str, Any], company_state: CompanyState
    ) -> Dict[str, Any]:
        workflow = self.workflow_registry.get(workflow_name, {})

        if not workflow:
            return {
                "status": "workflow_not_found",
                "workflow_name": workflow_name,
                "triggered_at": datetime.now().isoformat(),
            }

        workflow_config = workflow.get("config", {})
        triggers = workflow_config.get("triggers", [])

        for trigger in triggers:
            if trigger.get("type") in metadata.get("trigger_type", ""):
                return {
                    "status": "workflow_triggered",
                    "workflow_name": workflow_name,
                    "config": workflow_config,
                    "metadata": metadata,
                    "triggers_fired": triggers,
                    "triggered_at": datetime.now().isoformat(),
                }

        return {
            "status": "workflow_triggered",
            "workflow_name": workflow_name,
            "config": workflow_config,
            "metadata": metadata,
            "triggers_fired": [],
            "triggered_at": datetime.now().isoformat(),
        }

    async def _implement_circuit_breaker(
        self, circuit_name: str, failure_threshold: int = 5, timeout: int = 300
    ) -> Dict[str, Any]:
        current_breaker = self.circuit_breakers.get(
            circuit_name,
            {
                "state": "closed",
                "failure_count": 0,
                "last_failure": None,
                "opened_at": None,
                "timeout": timeout,
            },
        )

        if current_breaker.get("state") == "open":
            opened_at = current_breaker.get("opened_at")
            if opened_at:
                elapsed = (
                    datetime.now() - datetime.fromisoformat(opened_at)
                ).total_seconds()
                if elapsed >= timeout:
                    current_breaker["state"] = "half_open"
                    current_breaker["last_failure"] = None
                    self.circuit_breakers[circuit_name] = current_breaker
                    return {
                        "circuit_name": circuit_name,
                        "previous_state": "open",
                        "new_state": "half_open",
                        "message": "Circuit breaker transitioning to half-open for testing",
                    }
            return {
                "circuit_name": circuit_name,
                "state": "open",
                "message": "Circuit breaker remains open",
            }

        if current_breaker["failure_count"] >= failure_threshold:
            current_breaker["state"] = "open"
            current_breaker["opened_at"] = datetime.now().isoformat()
            self.circuit_breakers[circuit_name] = current_breaker
            return {
                "circuit_name": circuit_name,
                "previous_state": "closed",
                "new_state": "open",
                "failure_count": current_breaker["failure_count"],
                "message": "Circuit breaker opened due to threshold exceeded",
            }

        return {
            "circuit_name": circuit_name,
            "state": current_breaker["state"],
            "failure_count": current_breaker["failure_count"],
            "message": "Circuit breaker operating normally",
        }

    async def _generate_system_health_report(
        self, company_state: CompanyState
    ) -> Dict[str, Any]:
        monitoring_result = await self._monitor_system_health(company_state)
        anomalies = await self._detect_anomalies(company_state)

        report = {
            "agent_role": self.role.value,
            "report_type": "system_health",
            "timestamp": datetime.now().isoformat(),
            "generated_for": "CEO, HR",
            "data": {
                "overall_health": monitoring_result,
                "anomalies_detected": len(anomalies),
                "anomalies_list": anomalies,
                "recommendations": self._generate_health_recommendations(
                    monitoring_result, anomalies
                ),
            },
        }

        return report

    async def _process_alert(
        self, alert_data: Dict[str, Any], company_state: CompanyState
    ) -> Optional[Message]:
        alert_type = alert_data.get("alert_type", "unknown")
        message = alert_data.get("message", "")
        severity = alert_data.get("severity", "medium")

        if severity == "critical":
            return CommunicationProtocol.create_alert(
                sender=self.role,
                alert_type=f"critical_{alert_type}",
                message=f"ALERT: {message}",
                severity=Priority.CRITICAL,
                recipient=AgentRole.CEO,
            )
        elif severity == "high":
            return CommunicationProtocol.create_alert(
                sender=self.role,
                alert_type=alert_type,
                message=f"URGENT: {message}",
                severity=Priority.HIGH,
                recipient=AgentRole.CTO,
            )

        return CommunicationProtocol.create_message(
            sender=self.role,
            recipient=AgentRole.CTO,
            message_type=MessageType.STATUS_REPORT,
            content={
                "type": "alert_processed",
                "alert_type": alert_type,
                "status": "acknowledged",
                "message": message,
            },
        )

    def _detect_bottlenecks(self, company_state: CompanyState) -> List[Dict[str, Any]]:
        bottlenecks = []
        agents = company_state.get("agents", {})

        for role, agent_state in agents.items():
            if role == AgentRole.OPERATIONS:
                continue

            current_tasks = len(agent_state.current_tasks)
            if current_tasks > 20:
                bottlenecks.append(
                    {
                        "type": "task_queue_bottleneck",
                        "agent": role.value,
                        "current_tasks": current_tasks,
                        "threshold": 20,
                        "severity": "high",
                    }
                )

            workload = agent_state.workload
            if workload > 0.9:
                bottlenecks.append(
                    {
                        "type": "workload_bottleneck",
                        "agent": role.value,
                        "workload": workload,
                        "threshold": 0.9,
                        "severity": "high" if workload > 0.95 else "medium",
                    }
                )

        return bottlenecks

    async def _handle_orchestration_request(
        self, message: Message, company_state: CompanyState
    ) -> Message:
        orchestration_request = message.content.get("orchestration_request", {})

        orchestration_prompt = f"""
        As Operations Agent, orchestrate this request:
        
        Request: {json.dumps(orchestration_request, indent=2)}
        Current System State: {json.dumps(self.system_health, indent=2)}
        Task Queue: {json.dumps([t.__dict__ for t in self.task_queue[:10]], indent=2)}
        
        Create orchestration plan:
        1. Task prioritization
        2. Agent assignment
        3. Dependencies resolution
        4. Resource allocation
        5. Execution timeline
        6. Contingency planning
        
        Respond with JSON format orchestration plan.
        """

        try:
            response = await self.llm.ainvoke(
                [HumanMessage(content=orchestration_prompt)]
            )
            content = (
                response.content
                if isinstance(response.content, str)
                else str(response.content)
            )
            plan = json.loads(content)

            return CommunicationProtocol.create_message(
                sender=self.role,
                recipient=message.sender,
                message_type=MessageType.COLLABORATION,
                content={
                    "type": "orchestration_plan",
                    "plan": plan,
                    "timestamp": datetime.now().isoformat(),
                },
            )
        except Exception as e:
            return CommunicationProtocol.create_message(
                sender=self.role,
                recipient=message.sender,
                message_type=MessageType.COLLABORATION,
                content={
                    "type": "orchestration_error",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat(),
                },
            )

    async def _handle_workflow_trigger(
        self, message: Message, company_state: CompanyState
    ) -> Message:
        workflow_trigger = message.content.get("workflow_trigger", {})
        workflow_name = workflow_trigger.get("workflow_name", "")

        self.workflow_registry[workflow_name] = {
            "config": workflow_trigger,
            "last_triggered": datetime.now().isoformat(),
        }

        return CommunicationProtocol.create_message(
            sender=self.role,
            recipient=message.sender,
            message_type=MessageType.COLLABORATION,
            content={
                "type": "workflow_registered",
                "workflow_name": workflow_name,
                "timestamp": datetime.now().isoformat(),
            },
        )

    async def _evaluate_workflow_execution(
        self, message: Message, company_state: CompanyState
    ) -> Message:
        request_data = message.content
        workflow_name = request_data.get("workflow_name", "")

        evaluation_prompt = f"""
        As Operations Agent, evaluate this workflow execution request:
        
        Workflow: {workflow_name}
        Request Details: {json.dumps(request_data, indent=2)}
        Current System State: {json.dumps(self.system_health, indent=2)}
        Active Workflows: {json.dumps(list(self.workflow_registry.keys()), indent=2)}
        
        Evaluate:
        1. Workflow feasibility
        2. Resource requirements
        3. Potential conflicts
        4. Success probability
        5. Recommended execution time
        
        Respond with JSON format evaluation.
        """

        try:
            response = await self.llm.ainvoke([HumanMessage(content=evaluation_prompt)])
            content = (
                response.content
                if isinstance(response.content, str)
                else str(response.content)
            )
            evaluation = json.loads(content)

            return CommunicationProtocol.create_message(
                sender=self.role,
                recipient=message.sender,
                message_type=MessageType.APPROVAL_RESPONSE,
                content={
                    "request_id": request_data.get("request_id"),
                    "decision": evaluation,
                    "evaluated_by": "OperationsAgent",
                },
            )
        except Exception as e:
            return CommunicationProtocol.create_message(
                sender=self.role,
                recipient=message.sender,
                message_type=MessageType.APPROVAL_RESPONSE,
                content={
                    "request_id": request_data.get("request_id"),
                    "decision": {
                        "approved": False,
                        "reasoning": f"Evaluation failed: {str(e)}",
                    },
                },
            )

    async def _evaluate_resource_allocation(
        self, message: Message, company_state: CompanyState
    ) -> Message:
        request_data = message.content
        allocation_request = request_data.get("allocation_request", {})

        allocation_prompt = f"""
        As Operations Agent, evaluate this resource allocation request:
        
        Request: {json.dumps(allocation_request, indent=2)}
        Available Resources: {json.dumps(company_state.get("kpis", {}), indent=2)}
        Current Workload: {json.dumps(self.system_health.get("agent_states", {}), indent=2)}
        
        Evaluate:
        1. Resource availability
        2. Priority alignment
        3. Efficiency impact
        4. Cost implications
        5. Recommended allocation
        
        Respond with JSON format evaluation.
        """

        try:
            response = await self.llm.ainvoke([HumanMessage(content=allocation_prompt)])
            content = (
                response.content
                if isinstance(response.content, str)
                else str(response.content)
            )
            evaluation = json.loads(content)

            return CommunicationProtocol.create_message(
                sender=self.role,
                recipient=message.sender,
                message_type=MessageType.APPROVAL_RESPONSE,
                content={
                    "request_id": request_data.get("request_id"),
                    "decision": evaluation,
                    "evaluated_by": "OperationsAgent",
                },
            )
        except Exception as e:
            return CommunicationProtocol.create_message(
                sender=self.role,
                recipient=message.sender,
                message_type=MessageType.APPROVAL_RESPONSE,
                content={
                    "request_id": request_data.get("request_id"),
                    "decision": {
                        "approved": False,
                        "reasoning": f"Evaluation failed: {str(e)}",
                    },
                },
            )

    def _generate_health_recommendations(
        self, monitoring_result: Dict[str, Any], anomalies: List[Dict[str, Any]]
    ) -> List[str]:
        recommendations = []

        overall_score = monitoring_result.get("overall_health_score", 100)
        if overall_score < 80:
            recommendations.append("Investigate overall system health issues")

        agent_health = monitoring_result.get("agent_health", {})
        for agent_name, health in agent_health.items():
            if health.get("health_score", 100) < 80:
                recommendations.append(f"Address {agent_name} agent performance issues")

            if health.get("workload", 0) > 0.9:
                recommendations.append(f"Redistribute workload from {agent_name} agent")

            if not health.get("is_active", True):
                recommendations.append(f"Verify {agent_name} agent connectivity")

        queue_info = monitoring_result.get("task_queue", {})
        if queue_info.get("pressure") == "high":
            recommendations.append("Scale task processing capacity")

        circuit_breakers = monitoring_result.get("circuit_breakers", {})
        if circuit_breakers.get("status") == "degraded":
            recommendations.append("Investigate circuit breaker activations")

        for anomaly in anomalies:
            if anomaly.get("severity") == "critical":
                recommendations.append(
                    f"Immediate action required for {anomaly.get('type')} in {anomaly.get('agent')}"
                )

        return recommendations


__all__ = ["OperationsAgent", "Operations"]
