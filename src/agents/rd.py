from typing import Dict, List, Optional, Any
import json
from datetime import datetime, timedelta
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from .base import (
    BaseAgent, AgentRole, Task, Message, MessageType, Priority,
    CompanyState, CommunicationProtocol, create_task_id
)
from .config import app_config, ModelConfig, AgentConfig



class RDAgent(BaseAgent):
    def __init__(self):
        capabilities = [
            "功能实现",
            "测试",
            "代码审查",
            "部署",
            "文档编写",
            "Bug修复",
            "Python开发",
            "TypeScript开发"
        ]
        super().__init__(AgentRole.RD, capabilities)
        default_model_config = app_config.llm.models.get(
            app_config.llm.default_model,
            ModelConfig(
                name=app_config.llm.default_model,
                provider="openai",
                api_key=None,
                config={},
            ),
        )
        agent_config = app_config.agents.get("rd", AgentConfig())
        self.llm = ChatOpenAI(
            model=app_config.llm.default_model,
            temperature=agent_config.temperature if agent_config.temperature != 0.3 else default_model_config.config.get("temperature", 0.3),
        )
        
        # 状态变量
        self.current_features: List[Dict[str, Any]] = []
        self.codebase_status: Dict[str, Any] = {
            "overall_health": 85,
            "last_commit_hash": "",
            "branch": "main",
            "build_status": "passing",
            "coverage": 0.0,
            "technical_debt_score": 0.0
        }
        self.test_coverage: Dict[str, float] = {
            "unit": 0.0,
            "integration": 0.0,
            "e2e": 0.0,
            "total": 0.0
        }
        self.deployment_status: Dict[str, Any] = {
            "environment": "development",
            "last_deployment": None,
            "deployment_frequency": "weekly",
            "rollback_available": True
        }
        self.technical_debt: Dict[str, Any] = {
            "score": 0.0,
            "categories": {},
            "recommendations": []
        }

    async def process_message(self, message: Message, company_state: CompanyState) -> Optional[Message]:
        content = message.content

        if message.message_type == MessageType.TASK_ASSIGNMENT:
            return await self._handle_task_assignment(message, company_state)
        elif message.message_type == MessageType.STATUS_REPORT:
            return await self._handle_status_report(message, company_state)
        elif message.message_type == MessageType.DATA_RESPONSE:
            return await self._handle_data_response(message, company_state)
        elif message.message_type == MessageType.COLLABORATION:
            return await self._handle_collaboration(message, company_state)
        elif message.message_type == MessageType.ALERT:
            return await self._handle_alert(message, company_state)
        elif message.message_type == MessageType.APPROVAL_RESPONSE:
            return await self._handle_approval_response(message, company_state)
        elif message.message_type == MessageType.DATA_REQUEST:
            return await self._handle_data_request(message, company_state)
        elif message.message_type == MessageType.APPROVAL_REQUEST:
            return await self._handle_approval_request(message, company_state)

        return None

    async def _handle_task_assignment(self, message: Message, company_state: CompanyState) -> Optional[Message]:
        task_data = message.content.get("task", {})
        task_title = task_data.get("title", "").lower()
        assigned_by = message.sender

        if assigned_by != AgentRole.CTO:
            return CommunicationProtocol.create_message(
                sender=self.role,
                recipient=assigned_by,
                message_type=MessageType.COLLABORATION,
                content={
                    "type": "task_rejection",
                    "reason": "Only CTO can assign tasks to RD"
                }
            )

        task = Task(
            task_id=task_data.get("task_id", create_task_id()),
            title=task_data.get("title", ""),
            description=task_data.get("description", ""),
            assigned_to=AgentRole.RD,
            assigned_by=AgentRole.CTO,
            priority=Priority(task_data.get("priority", "medium")),
            deadline=datetime.fromisoformat(task_data.get("deadline")) if task_data.get("deadline") else None,
            dependencies=task_data.get("dependencies", []),
            deliverables=task_data.get("deliverables", [])
        )

        self.add_task(task)
        self.state.last_active = datetime.now()

        if "feature" in task_title or "implement" in task_title or "development" in task_title:
            return await self._process_development_task(task, company_state)
        elif "test" in task_title or "testing" in task_title:
            return await self._process_testing_task(task, company_state)
        elif "review" in task_title or "quality" in task_title:
            return await self._process_code_review_task(task, company_state)
        elif "bug" in task_title or "fix" in task_title:
            return await self._process_bug_fix_task(task, company_state)

        return CommunicationProtocol.create_message(
            sender=self.role,
            recipient=assigned_by,
            message_type=MessageType.COLLABORATION,
            content={
                "type": "task_received",
                "task_id": task.task_id,
                "status": "queued",
                "notes": "Task will be processed based on priority"
            }
        )

    async def _handle_status_report(self, message: Message, company_state: CompanyState) -> Optional[Message]:
        report_data = message.content

        if message.sender == AgentRole.CTO:
            return CommunicationProtocol.create_message(
                sender=self.role,
                recipient=AgentRole.CTO,
                message_type=MessageType.STATUS_REPORT,
                content={
                    "type": "progress_update",
                    "status": "active",
                    "current_features": self.current_features,
                    "codebase_status": self.codebase_status,
                    "test_coverage": self.test_coverage,
                    "deployment_status": self.deployment_status,
                    "technical_debt": self.technical_debt,
                    "timestamp": datetime.now().isoformat()
                }
            )

        return None

    async def _handle_data_response(self, message: Message, company_state: CompanyState) -> Optional[Message]:
        data = message.content

        if data.get("data_type") == "api_specification":
            api_spec = data.get("data", {})
            self._update_api_spec(api_spec)

        return CommunicationProtocol.create_message(
            sender=self.role,
            recipient=message.sender,
            message_type=MessageType.COLLABORATION,
            content={
                "type": "data_received",
                "status": "acknowledged",
                "action": "data_processed_for_integration"
            }
        )

    async def _handle_collaboration(self, message: Message, company_state: CompanyState) -> Optional[Message]:
        content = message.content

        if content.get("type") == "bug_report":
            return await self._process_collaboration_bug(message, company_state)
        elif content.get("type") == "data_interface_request":
            return await self._process_data_interface_request(message, company_state)

        return None

    async def _handle_alert(self, message: Message, company_state: CompanyState) -> Optional[Message]:
        alert_data = message.content

        if alert_data.get("alert_type") == "deployment_failure":
            return await self._handle_deployment_failure(alert_data, message.sender)
        elif alert_data.get("alert_type") == "high_priority_bug":
            return await self._handle_high_priority_bug(alert_data, message.sender)

        return None

    async def _handle_approval_response(self, message: Message, company_state: CompanyState) -> Optional[Message]:
        approval_data = message.content
        approval_status = approval_data.get("decision", {})

        if approval_status.get("approved"):
            deployment_details = message.content.get("deployment_details", {})
            return await self._process_approved_deployment(deployment_details)

        return CommunicationProtocol.create_message(
            sender=self.role,
            recipient=AgentRole.CTO,
            message_type=MessageType.COLLABORATION,
            content={
                "type": "approval_declined",
                "reason": approval_status.get("reasoning", "Unknown"),
                "next_steps": "Address concerns and resubmit"
            }
        )

    async def _handle_data_request(self, message: Message, company_state: CompanyState) -> Optional[Message]:
        request_type = message.content.get("request_type", "")

        if request_type == "api_documentation":
            return CommunicationProtocol.create_message(
                sender=self.role,
                recipient=message.sender,
                message_type=MessageType.DATA_RESPONSE,
                content={
                    "request_id": message.content.get("request_id"),
                    "data": self._get_api_documentation(),
                    "data_type": "api_documentation"
                }
            )
        elif request_type == "feature_status":
            return CommunicationProtocol.create_message(
                sender=self.role,
                recipient=message.sender,
                message_type=MessageType.DATA_RESPONSE,
                content={
                    "request_id": message.content.get("request_id"),
                    "data": self.current_features,
                    "data_type": "feature_status"
                }
            )
        elif request_type == "test_coverage":
            return CommunicationProtocol.create_message(
                sender=self.role,
                recipient=message.sender,
                message_type=MessageType.DATA_RESPONSE,
                content={
                    "request_id": message.content.get("request_id"),
                    "data": self.test_coverage,
                    "data_type": "test_coverage"
                }
            )

        return CommunicationProtocol.create_message(
            sender=self.role,
            recipient=message.sender,
            message_type=MessageType.DATA_RESPONSE,
            content={
                "request_id": message.content.get("request_id"),
                "error": f"Unknown request type: {request_type}"
            }
        )

    async def _handle_approval_request(self, message: Message, company_state: CompanyState) -> Optional[Message]:
        request_data = message.content
        request_type = request_data.get("request_type", "")

        if request_type == "deployment":
            return await self._process_deployment_approval_request(message, company_state)
        elif request_type == "feature_completion":
            return await self._process_feature_completion_request(message, company_state)

        return None

    async def execute_task(self, task: Task, company_state: CompanyState) -> Dict[str, Any]:
        task_title = task.title.lower()

        if "feature" in task_title or "implement" in task_title:
            return await self._execute_feature_implementation(task, company_state)
        elif "test" in task_title:
            return await self._execute_testing(task, company_state)
        elif "review" in task_title:
            return await self._execute_code_review(task, company_state)
        elif "deploy" in task_title or "release" in task_title:
            return await self._execute_deployment(task, company_state)

        return {
            "status": "completed",
            "result": "Task processed by R&D",
            "timestamp": datetime.now().isoformat()
        }

    async def generate_report(self, company_state: CompanyState) -> Dict[str, Any]:
        report_prompt = f"""
        As R&D Engineer, generate comprehensive development status report:

        Current Features: {json.dumps(self.current_features, indent=2)}
        Codebase Status: {json.dumps(self.codebase_status, indent=2)}
        Test Coverage: {json.dumps(self.test_coverage, indent=2)}
        Deployment Status: {json.dumps(self.deployment_status, indent=2)}
        Technical Debt: {json.dumps(self.technical_debt, indent=2)}

        Generate development report covering:
        1. Feature Implementation Status
        2. Code Quality Metrics
        3. Test Coverage Analysis
        4. Deployment History
        5. Technical Debt Assessment
        6. Blockers and Risks
        7. Next Sprint Planning

        Format as professional development report.
        """

        try:
            response = await self.llm.ainvoke([HumanMessage(content=report_prompt)])
            content = response.content if isinstance(response.content, str) else str(response.content)
            report = json.loads(content)

            return {
                "agent_role": self.role.value,
                "report_type": "development_status",
                "timestamp": datetime.now().isoformat(),
                "data": report,
                "status_summary": self._generate_status_summary()
            }
        except Exception as e:
            return {
                "agent_role": self.role.value,
                "report_type": "development_status",
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "status": "report_generation_failed"
            }

    async def _implement_feature(self, feature: Dict[str, Any], company_state: CompanyState) -> Dict[str, Any]:
        feature_prompt = f"""
        As R&D Engineer, implement this product feature:

        Feature: {json.dumps(feature, indent=2)}
        Current Codebase Status: {json.dumps(self.codebase_status, indent=2)}
        System Architecture: Microservices with Python/TypeScript

        Provide implementation plan covering:
        1. Architecture design
        2. Component breakdown
        3. Database schema changes (if any)
        4. API endpoints
        5. Technology stack considerations
        6. Estimate effort and timeline
        7. Potential risks

        Respond with comprehensive implementation plan in JSON format.
        """

        try:
            response = await self.llm.ainvoke([HumanMessage(content=feature_prompt)])
            content = response.content if isinstance(response.content, str) else str(response.content)
            implementation = json.loads(content)

            self.current_features.append({
                "feature_id": feature.get("feature_id"),
                "name": feature.get("name"),
                "status": "implementation_planned",
                "implementation_details": implementation,
                "created_at": datetime.now().isoformat()
            })

            self._update_codebase_status(implementation_status="in_progress")

            return {
                "status": "success",
                "implementation_plan": implementation,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def _write_tests(self, feature: Dict[str, Any], test_type: str, company_state: CompanyState) -> Dict[str, Any]:
        test_prompt = f"""
        As R&D Engineer, write {test_type} test cases:

        Feature: {json.dumps(feature, indent=2)}
        Test Type: {test_type}
        Current Test Coverage: {json.dumps(self.test_coverage, indent=2)}

        Write comprehensive test cases covering:
        1. Test scenarios
        2. Test data requirements
        3. Expected outcomes
        4. Edge cases
        5. Mock dependencies

        Respond with test specifications in JSON format.
        """

        try:
            response = await self.llm.ainvoke([HumanMessage(content=test_prompt)])
            content = response.content if isinstance(response.content, str) else str(response.content)
            tests = json.loads(content)

            self.test_coverage[test_type] = min(100.0, self.test_coverage.get(test_type, 0) + 15.0)
            self.test_coverage["total"] = sum(self.test_coverage.values()) / len(self.test_coverage)

            return {
                "status": "success",
                "test_cases": tests,
                "test_type": test_type,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def _review_code(self, code_details: Dict[str, Any], company_state: CompanyState) -> Dict[str, Any]:
        code_review_prompt = f"""
        As R&D Engineer, conduct code review:

        Code Details: {json.dumps(code_details, indent=2)}
        Current Codebase Status: {json.dumps(self.codebase_status, indent=2)}

        Review covering:
        1. Code quality and style
        2. Architecture compliance
        3. Security considerations
        4. Performance optimization
        5. Test coverage adequacy
        6. Documentation completeness

        Provide review feedback with:
        - approval_status: approved/needs_revision
        - code_quality_score: 0-100
        - issues_found: list of issues
        - recommendations: list of recommendations

        Respond with review report in JSON format.
        """

        try:
            response = await self.llm.ainvoke([HumanMessage(content=code_review_prompt)])
            content = response.content if isinstance(response.content, str) else str(response.content)
            review_report = json.loads(content)

            if review_report.get("approval_status") == "approved":
                self.codebase_status["overall_health"] = min(100, self.codebase_status["overall_health"] + 2)
            else:
                self.codebase_status["technical_debt_score"] += review_report.get("code_quality_score", 0) / 20

            return {
                "status": "completed",
                "review_report": review_report,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def _deploy_service(self, deployment_details: Dict[str, Any], company_state: CompanyState) -> Dict[str, Any]:
        deploy_prompt = f"""
        As R&D Engineer, deploy service:

        Deployment Details: {json.dumps(deployment_details, indent=2)}
        Current Status: {json.dumps(self.deployment_status, indent=2)}
        System Health: {json.dumps(self.codebase_status, indent=2)}

        Prepare deployment plan covering:
        1. Pre-deployment checks
        2. Deployment steps
        3. Rollback procedure
        4. Post-deployment verification
        5. Monitoring setup

        Respond with deployment plan in JSON format.
        """

        try:
            response = await self.llm.ainvoke([HumanMessage(content=deploy_prompt)])
            content = response.content if isinstance(response.content, str) else str(response.content)
            deploy_plan = json.loads(content)

            self.deployment_status["last_deployment"] = datetime.now().isoformat()
            self.deployment_status["environment"] = deployment_details.get("environment", "production")

            return {
                "status": "pending",
                "deployment_plan": deploy_plan,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def _generate_prd_details(self, prd_data: Dict[str, Any]) -> Dict[str, Any]:
        prd_prompt = f"""
        As R&D Engineer, generate implementation details from PRD:

        PRD: {json.dumps(prd_data, indent=2)}
        Current Codebase: {json.dumps(self.codebase_status, indent=2)}

        Generate implementation details covering:
        1. Feature requirements breakdown
        2. API specifications
        3. Database schema
        4. Component dependencies
        5. Integration points
        6. Acceptance criteria

        Respond with implementation details in JSON format.
        """

        try:
            response = self.llm.invoke([HumanMessage(content=prd_prompt)])
            content = response.content if isinstance(response.content, str) else str(response.content)
            prd_details = json.loads(content)

            return {
                "status": "success",
                "prd_details": prd_details,
                "generated_at": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "generated_at": datetime.now().isoformat()
            }

    async def _fix_bug(self, bug_report: Dict[str, Any], company_state: CompanyState) -> Dict[str, Any]:
        bug_prompt = f"""
        As R&D Engineer, fix this bug:

        Bug Report: {json.dumps(bug_report, indent=2)}
        Current Status: {json.dumps(self.codebase_status, indent=2)}

        Provide fix plan covering:
        1. Root cause analysis
        2. Fix approach
        3. Test cases for verification
        4. Regression testing needs
        5. Estimate effort

        Respond with fix plan in JSON format.
        """

        try:
            response = await self.llm.ainvoke([HumanMessage(content=bug_prompt)])
            content = response.content if isinstance(response.content, str) else str(response.content)
            fix_plan = json.loads(content)

            self.codebase_status["overall_health"] = max(0, self.codebase_status["overall_health"] - 5)
            self.deployment_status["environment"] = "fix_in_progress"

            return {
                "status": "in_progress",
                "fix_plan": fix_plan,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def _update_documentation(self, doc_type: str, content: Dict[str, Any]) -> Dict[str, Any]:
        documentation = {
            "doc_type": doc_type,
            "content_summary": content.get("summary", ""),
            "generated_at": datetime.now().isoformat()
        }

        return {
            "status": "completed",
            "documentation": documentation,
            "timestamp": datetime.now().isoformat()
        }

    async def _process_development_task(self, task: Task, company_state: CompanyState) -> Message:
        feature = {
            "feature_id": task.task_id,
            "name": task.title,
            "description": task.description,
            "priority": task.priority.value,
            "deadline": task.deadline.isoformat() if task.deadline else None
        }

        implementation = await self._implement_feature(feature, company_state)

        if implementation["status"] == "success":
            return CommunicationProtocol.create_message(
                sender=self.role,
                recipient=AgentRole.CTO,
                message_type=MessageType.COLLABORATION,
                content={
                    "type": "feature_implemented",
                    "feature_id": task.task_id,
                    "implementation_plan": implementation.get("implementation_plan", {}),
                    "next_steps": ["Write tests", "Code review", "Deployment"]
                }
            )

        return CommunicationProtocol.create_message(
            sender=self.role,
            recipient=AgentRole.CTO,
            message_type=MessageType.ALERT,
            content={
                "alert_type": "feature_implementation_failed",
                "message": f"Failed to implement feature {task.title}",
                "error": implementation.get("error", "Unknown error")
            },
            severity=Priority.HIGH
        )

    async def _process_testing_task(self, task: Task, company_state: CompanyState) -> Message:
        feature = {
            "feature_id": task.task_id,
            "name": task.title,
            "description": task.description
        }

        test_type = "unit" if "unit" in task.title.lower() else "integration" if "integration" in task.title.lower() else "e2e"
        test_result = await self._write_tests(feature, test_type, company_state)

        if test_result["status"] == "success":
            return CommunicationProtocol.create_message(
                sender=self.role,
                recipient=AgentRole.CTO,
                message_type=MessageType.STATUS_REPORT,
                content={
                    "type": "test_completion",
                    "feature_id": task.task_id,
                    "test_type": test_type,
                    "test_coverage": self.test_coverage.copy(),
                    "timestamp": datetime.now().isoformat()
                }
            )

        return CommunicationProtocol.create_message(
            sender=self.role,
            recipient=AgentRole.CTO,
            message_type=MessageType.ALERT,
            content={
                "alert_type": "testing_failed",
                "message": f"Failed to generate tests for {task.title}",
                "error": test_result.get("error", "Unknown error")
            },
            severity=Priority.HIGH
        )

    async def _process_code_review_task(self, task: Task, company_state: CompanyState) -> Message:
        code_details = {
            "code_files": task.metadata.get("files", []),
            "changes": task.metadata.get("changes", []),
            "feature_id": task.task_id
        }

        review_result = await self._review_code(code_details, company_state)

        if review_result["status"] == "completed":
            return CommunicationProtocol.create_message(
                sender=self.role,
                recipient=AgentRole.CTO,
                message_type=MessageType.COLLABORATION,
                content={
                    "type": "code_review_completion",
                    "review_report": review_result.get("review_report", {}),
                    "approved": review_result.get("review_report", {}).get("approval_status") == "approved"
                }
            )

        return CommunicationProtocol.create_message(
            sender=self.role,
            recipient=AgentRole.CTO,
            message_type=MessageType.COLLABORATION,
            content={
                "type": "code_review_error",
                "message": "Code review failed",
                "error": review_result.get("error", "Unknown error")
            }
        )

    async def _process_bug_fix_task(self, task: Task, company_state: CompanyState) -> Message:
        bug_report = {
            "bug_id": task.task_id,
            "title": task.title,
            "description": task.description,
            "severity": task.priority.value
        }

        fix_result = await self._fix_bug(bug_report, company_state)

        if fix_result["status"] == "in_progress":
            return CommunicationProtocol.create_message(
                sender=self.role,
                recipient=AgentRole.CTO,
                message_type=MessageType.COLLABORATION,
                content={
                    "type": "bug_fix_started",
                    "bug_id": task.task_id,
                    "fix_plan": fix_result.get("fix_plan", {}),
                    "estimated_resolution": "2-4 hours"
                }
            )

        return CommunicationProtocol.create_message(
            sender=self.role,
            recipient=AgentRole.CTO,
            message_type=MessageType.ALERT,
            content={
                "alert_type": "bug_fix_failed",
                "message": f"Failed to fix bug {task.title}",
                "error": fix_result.get("error", "Unknown error")
            },
            severity=Priority.HIGH
        )

    async def _process_collaboration_bug(self, message: Message, company_state: CompanyState) -> Message:
        bug_report = message.content.get("bug", {})

        fix_result = await self._fix_bug(bug_report, company_state)

        return CommunicationProtocol.create_message(
            sender=self.role,
            recipient=AgentRole.CUSTOMER_SUPPORT,
            message_type=MessageType.COLLABORATION,
            content={
                "type": "bug_acknowledged",
                "bug_id": bug_report.get("bug_id"),
                "status": fix_result.get("status", "unknown"),
                "next_steps": ["Analysis", "Fix implementation", "Testing", "Deployment"]
            }
        )

    async def _process_data_interface_request(self, message: Message, company_state: CompanyState) -> Message:
        request_data = message.content.get("data_request", {})

        api_spec = {
            "endpoint": request_data.get("endpoint", ""),
            "method": request_data.get("method", "GET"),
            "request_schema": request_data.get("request_schema", {}),
            "response_schema": request_data.get("response_schema", {})
        }

        impl_details = self._generate_prd_details({
            "feature_id": create_task_id(),
            "name": f"Data Interface: {api_spec['endpoint']}",
            "description": f"API endpoint for data interface: {api_spec['endpoint']}",
            "api_spec": api_spec
        })

        return CommunicationProtocol.create_message(
            sender=self.role,
            recipient=AgentRole.DATA_ANALYST,
            message_type=MessageType.DATA_RESPONSE,
            content={
                "request_id": request_data.get("request_id"),
                "api_spec": api_spec,
                "implementation_details": impl_details.get("prd_details", {}),
                "status": "implementation_planned"
            }
        )

    async def _handle_deployment_failure(self, alert_data: Dict[str, Any], sender: AgentRole) -> Message:
        return CommunicationProtocol.create_message(
            sender=self.role,
            recipient=AgentRole.CTO,
            message_type=MessageType.ALERT,
            content={
                "alert_type": "deployment_issue",
                "message": f"Deployment issue detected: {alert_data.get('message', 'Unknown')}",
                "recommended_action": "Review logs and rollback if necessary"
            },
            severity=Priority.CRITICAL
        )

    async def _handle_high_priority_bug(self, alert_data: Dict[str, Any], sender: AgentRole) -> Message:
        return CommunicationProtocol.create_message(
            sender=self.role,
            recipient=AgentRole.CTO,
            message_type=MessageType.ALERT,
            content={
                "alert_type": "high_priority_bug_detected",
                "message": alert_data.get("message", "High priority bug detected"),
                "recommended_action": "Immediate investigation required"
            },
            severity=Priority.CRITICAL
        )

    async def _process_approved_deployment(self, deployment_details: Dict[str, Any]) -> Message:
        deploy_result = await self._deploy_service(deployment_details, {})

        return CommunicationProtocol.create_message(
            sender=self.role,
            recipient=AgentRole.CTO,
            message_type=MessageType.COLLABORATION,
            content={
                "type": "deployment_initiated",
                "deployment_result": deploy_result,
                "next_steps": ["Monitor deployment", "Verify functionality", "Report results"]
            }
        )

    async def _process_deployment_approval_request(self, message: Message, company_state: CompanyState) -> Message:
        request_data = message.content
        deployment_details = request_data.get("deployment_details", {})

        deployment_assessment = {
            "readiness_score": self._assess_deployment_readiness(deployment_details),
            "rollback_plan": bool(deployment_details.get("rollback_plan")),
            "performance_impact": "minimal" if deployment_details.get("performance_testing") else "unknown",
            "security_checks": deployment_details.get("security_scan_completed", False)
        }

        return CommunicationProtocol.create_message(
            sender=self.role,
            recipient=AgentRole.CTO,
            message_type=MessageType.APPROVAL_RESPONSE,
            content={
                "request_id": request_data.get("request_id"),
                "decision": {
                    "approved": deployment_assessment["readiness_score"] >= 70,
                    "assessment": deployment_assessment,
                    "deployment_window": self._suggest_deployment_window(deployment_details)
                },
                "prepared_by": AgentRole.RD.value
            }
        )

    async def _process_feature_completion_request(self, message: Message, company_state: CompanyState) -> Message:
        request_data = message.content
        feature_id = request_data.get("feature_id", "")

        feature = next((f for f in self.current_features if f.get("feature_id") == feature_id), None)

        if feature:
            return CommunicationProtocol.create_message(
                sender=self.role,
                recipient=AgentRole.CTO,
                message_type=MessageType.COLLABORATION,
                content={
                    "type": "feature_completion_report",
                    "feature_id": feature_id,
                    "status": "completed",
                    "test_coverage": self.test_coverage.copy(),
                    "code_quality": self.codebase_status["overall_health"],
                    "timestamp": datetime.now().isoformat()
                }
            )

        return CommunicationProtocol.create_message(
            sender=self.role,
            recipient=AgentRole.CTO,
            message_type=MessageType.COLLABORATION,
            content={
                "type": "feature_not_found",
                "feature_id": feature_id,
                "status": "unknown"
            }
        )

    async def _execute_feature_implementation(self, task: Task, company_state: CompanyState) -> Dict[str, Any]:
        feature = {
            "feature_id": task.task_id,
            "name": task.title,
            "description": task.description,
            "priority": task.priority.value
        }

        implementation = await self._implement_feature(feature, company_state)

        if implementation["status"] == "success":
            prd_details = self._generate_prd_details({
                "feature_id": task.task_id,
                "name": task.title,
                "description": task.description,
                "api_spec": {"endpoint": f"/api/v1/{task.task_id}", "method": "POST"}
            })

            test_result = await self._write_tests(feature, "unit", company_state)

            code_review = await self._review_code({
                "code_files": [f"{task.task_id}.py"],
                "changes": implementation.get("implementation_plan", {}).get("code_changes", []),
                "feature_id": task.task_id
            }, company_state)

            return {
                "status": "completed",
                "results": {
                    "implementation": implementation,
                    "prd_details": prd_details,
                    "test_generation": test_result,
                    "code_review": code_review
                },
                "timestamp": datetime.now().isoformat()
            }

        return {
            "status": "failed",
            "error": implementation.get("error", "Unknown error"),
            "timestamp": datetime.now().isoformat()
        }

    async def _execute_testing(self, task: Task, company_state: CompanyState) -> Dict[str, Any]:
        feature = {
            "feature_id": task.task_id,
            "name": task.title,
            "description": task.description
        }

        test_type = "unit" if "unit" in task.title.lower() else "integration" if "integration" in task.title.lower() else "e2e"
        test_result = await self._write_tests(feature, test_type, company_state)

        return {
            "status": test_result["status"],
            "results": test_result,
            "timestamp": datetime.now().isoformat()
        }

    async def _execute_code_review(self, task: Task, company_state: CompanyState) -> Dict[str, Any]:
        code_details = {
            "code_files": task.metadata.get("files", []),
            "changes": task.metadata.get("changes", []),
            "feature_id": task.task_id
        }

        review_result = await self._review_code(code_details, company_state)

        return {
            "status": review_result["status"],
            "results": review_result,
            "timestamp": datetime.now().isoformat()
        }

    async def _execute_deployment(self, task: Task, company_state: CompanyState) -> Dict[str, Any]:
        deployment_details = {
            "environment": task.metadata.get("environment", "production"),
            "version": task.metadata.get("version", "1.0.0"),
            "rollback_plan": task.metadata.get("rollback_plan", True),
            "performance_testing": True,
            "security_scan_completed": True
        }

        deploy_result = await self._deploy_service(deployment_details, company_state)

        return {
            "status": deploy_result["status"],
            "results": deploy_result,
            "timestamp": datetime.now().isoformat()
        }

    def _update_api_spec(self, api_spec: Dict[str, Any]):
        self.codebase_status["last_commit_hash"] = f"api_{datetime.now().timestamp()}"

    def _get_api_documentation(self) -> Dict[str, Any]:
        return {
            "endpoints": [
                {"path": f"/api/v1/features/{f['feature_id']}", "method": "GET", "description": f["name"]}
                for f in self.current_features[:5]
            ],
            "version": "1.0.0",
            "documentation_updated": datetime.now().isoformat()
        }

    def _update_codebase_status(self, implementation_status: str = "completed"):
        self.codebase_status["build_status"] = "passing" if implementation_status == "completed" else "building"
        self.codebase_status["last_commit_hash"] = f"commit_{datetime.now().timestamp()}"

    def _assess_deployment_readiness(self, deployment_details: Dict[str, Any]) -> float:
        score = 100.0

        if not deployment_details.get("testing_completed", False):
            score -= 30
        if not deployment_details.get("documentation_updated", False):
            score -= 20
        if not deployment_details.get("rollback_plan", False):
            score -= 25
        if not deployment_details.get("performance_testing", False):
            score -= 25

        return max(0, score)

    def _suggest_deployment_window(self, deployment_details: Dict[str, Any]) -> str:
        risk_level = deployment_details.get("risk_level", "medium")
        if risk_level == "high":
            return "Weekend 2-4 AM"
        elif risk_level == "medium":
            return "Weekday 10-12 PM"
        else:
            return "Any time with monitoring"

    def _generate_status_summary(self) -> Dict[str, Any]:
        return {
            "features_in_progress": len([f for f in self.current_features if f.get("status") == "in_progress"]),
            "features_completed": len([f for f in self.current_features if f.get("status") == "completed"]),
            "features_planned": len([f for f in self.current_features if f.get("status") == "planned"]),
            "code_health": self.codebase_status["overall_health"],
            "total_test_coverage": self.test_coverage["total"],
            "deployment_ready": self.deployment_status["environment"] == "development"
        }
