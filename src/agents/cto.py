from __future__ import annotations

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
 
class CTOAgent(BaseAgent):
    def __init__(self):
        capabilities = [
            "系统架构",
            "技术评估",
            "研发管理",
            "安全监督",
            "可扩展性规划",
            "API设计",
            "性能优化",
            "技术债管理",
        ]
        super().__init__(AgentRole.CTO, capabilities)
        default_model_config = app_config.llm.models.get(
            app_config.llm.default_model,
            ModelConfig(
                name=app_config.llm.default_model,
                provider="openai",
                api_key=None,
                config={},
            ),
        )
        agent_config = app_config.agents.get("cto", AgentConfig())
        self.llm = ChatOpenAI(
            model=app_config.llm.default_model,
            temperature=agent_config.temperature if agent_config.temperature != 0.3 else default_model_config.config.get("temperature", 0.3),
        )
        self.technology_stack = {
            "frontend": ["React", "TypeScript", "Tailwind"],
            "backend": ["Python", "FastAPI", "PostgreSQL"],
            "ai": ["LangChain", "LangGraph", "OpenAI"],
            "infrastructure": ["Docker", "Kubernetes", "AWS"],
            "monitoring": ["Prometheus", "Grafana", "ELK"],
        }
        self.system_metrics = {
            "uptime": 99.9,
            "response_time": 150,  # 毫秒
            "error_rate": 0.1,  # 百分比
            "throughput": 1000,  # 请求/秒
            "scalability": 0.8,  # 0-1比例
        }
        self.technical_roadmap = []
        self.security_posture = {
            "vulnerabilities": [],
            "compliance": ["GDPR", "SOC2"],
            "security_score": 85,
        }

    async def process_message(
        self, message: Message, company_state: CompanyState
    ) -> Optional[Message]:
        content = message.content

        if message.message_type == MessageType.STATUS_REPORT:
            return await self._handle_status_report(message, company_state)
        elif message.message_type == MessageType.TASK_ASSIGNMENT:
            return await self._handle_task_assignment(message, company_state)
        elif message.message_type == MessageType.DATA_REQUEST:
            return await self._handle_data_request(message, company_state)
        elif message.message_type == MessageType.APPROVAL_REQUEST:
            return await self._handle_approval_request(message, company_state)
        elif message.message_type == MessageType.ALERT:
            return await self._handle_alert(message, company_state)
        elif message.message_type == MessageType.COLLABORATION:
            return await self._handle_collaboration(message, company_state)

        return None

    async def _handle_status_report(
        self, message: Message, company_state: CompanyState
    ) -> Optional[Message]:
        sender = message.sender
        report_data = message.content

        if sender == AgentRole.RD:
            return await self._analyze_rd_report(message, company_state)
        elif sender == AgentRole.OPERATIONS:
            return await self._analyze_operations_report(message, company_state)

        return CommunicationProtocol.create_message(
            sender=self.role,
            recipient=sender,
            message_type=MessageType.COLLABORATION,
            content={
                "type": "technical_review",
                "status": "已审查",
                "feedback": "技术方面已由CTO审查",
            },
        )

    async def _analyze_rd_report(
        self, message: Message, company_state: CompanyState
    ) -> Message:
        report_data = message.content

        analysis_prompt = f"""
        作为CTO，分析此研发进度报告：

        报告数据：{json.dumps(report_data, indent=2)}
        当前技术路线图：{json.dumps(self.technical_roadmap, indent=2)}
        系统指标：{json.dumps(self.system_metrics, indent=2)}

        提供涵盖以下内容的技术评估：
        1. 代码质量和架构合规性
        2. 性能影响
        3. 安全性考虑
        4. 可扩展性影响
        5. 技术债务生成/减少
        6. 改进建议

        以JSON格式返回评估结果。
        """

        try:
            response = await self.llm.ainvoke([HumanMessage(content=analysis_prompt)])
            assessment = json.loads(response.content)

            return CommunicationProtocol.create_message(
                sender=self.role,
                recipient=AgentRole.RD,
                message_type=MessageType.COLLABORATION,
                content={
                    "type": "code_review",
                    "assessment": assessment,
                    "next_steps": assessment.get("recommendations", []),
                    "approval_status": "批准"
                    if assessment.get("code_quality", 0) > 80
                    else "需修改",
                },
            )
        except Exception as e:
            return CommunicationProtocol.create_message(
                sender=self.role,
                recipient=AgentRole.RD,
                message_type=MessageType.COLLABORATION,
                content={
                    "type": "code_review",
                    "status": "审查错误",
                    "error": str(e),
                },
            )

    async def _analyze_operations_report(
        self, message: Message, company_state: CompanyState
    ) -> Message:
        report_data = message.content

        # 分析系统健康和运行指标
        system_health = report_data.get("system_health", {})
        performance_metrics = report_data.get("performance", {})

        technical_analysis = {
            "system_stability": self._assess_system_stability(system_health),
            "performance_trends": self._analyze_performance_trends(performance_metrics),
            "capacity_planning": self._recommend_capacity_planning(system_health),
            "infrastructure_needs": self._assess_infrastructure_needs(company_state),
            "security_status": self._evaluate_security_status(report_data),
        }

        return CommunicationProtocol.create_message(
            sender=self.role,
            recipient=AgentRole.OPERATIONS,
            message_type=MessageType.COLLABORATION,
            content={
                "type": "technical_operations_review",
                "analysis": technical_analysis,
                "recommendations": self._generate_operations_recommendations(
                    technical_analysis
                ),
            },
        )

    async def _handle_task_assignment(
        self, message: Message, company_state: CompanyState
    ) -> Optional[Message]:
        task_data = message.content.get("task", {})
        task_title = task_data.get("title", "")

        if "development" in task_title.lower() or "coding" in task_title.lower():
            # 分配给研发团队
            rd_task = Task(
                task_id=create_task_id(),
                title=task_title,
                description=task_data.get("description", ""),
                assigned_to=AgentRole.RD,
                assigned_by=self.role,
                priority=Priority(task_data.get("priority", "medium")),
                deadline=datetime.fromisoformat(task_data.get("deadline"))
                if task_data.get("deadline")
                else None,
            )

            return CommunicationProtocol.create_task_assignment(
                assigner=self.role, assignee=AgentRole.RD, task=rd_task
            )

        return None

    async def _handle_data_request(
        self, message: Message, company_state: CompanyState
    ) -> Message:
        request_type = message.content.get("request_type", "")

        if request_type == "technology_stack":
            return CommunicationProtocol.create_message(
                sender=self.role,
                recipient=message.sender,
                message_type=MessageType.DATA_RESPONSE,
                content={
                    "request_id": message.content.get("request_id"),
                    "data": self.technology_stack,
                    "data_type": "technology_stack",
                },
            )
        elif request_type == "system_metrics":
            return CommunicationProtocol.create_message(
                sender=self.role,
                recipient=message.sender,
                message_type=MessageType.DATA_RESPONSE,
                content={
                    "request_id": message.content.get("request_id"),
                    "data": self.system_metrics,
                    "data_type": "system_metrics",
                },
            )
        elif request_type == "security_status":
            return CommunicationProtocol.create_message(
                sender=self.role,
                recipient=message.sender,
                message_type=MessageType.DATA_RESPONSE,
                content={
                    "request_id": message.content.get("request_id"),
                    "data": self.security_posture,
                    "data_type": "security_status",
                },
            )

        # 默认响应
        return CommunicationProtocol.create_message(
            sender=self.role,
            recipient=message.sender,
            message_type=MessageType.DATA_RESPONSE,
            content={
                "request_id": message.content.get("request_id"),
                "error": f"未知请求类型：{request_type}",
            },
        )

    async def _handle_approval_request(
        self, message: Message, company_state: CompanyState
    ) -> Message:
        request_data = message.content
        request_type = request_data.get("request_type", "")

        if request_type == "technology_adoption":
            return await self._evaluate_technology_adoption(message, company_state)
        elif request_type == "architecture_change":
            return await self._evaluate_architecture_change(message, company_state)
        elif request_type == "deployment":
            return await self._evaluate_deployment_request(message, company_state)

        return CommunicationProtocol.create_message(
            sender=self.role,
            recipient=message.sender,
            message_type=MessageType.APPROVAL_RESPONSE,
            content={
                "request_id": request_data.get("request_id"),
                "approved": False,
                "reasoning": f"未知审批请求类型：{request_type}",
            },
        )

    async def _evaluate_technology_adoption(
        self, message: Message, company_state: CompanyState
    ) -> Message:
        request_data = message.content
        tech_details = request_data.get("technology_details", {})

        evaluation_prompt = f"""
        作为CTO，评估此技术采用请求：

        拟议技术：{json.dumps(tech_details, indent=2)}
        当前技术栈：{json.dumps(self.technology_stack, indent=2)}
        系统约束：{json.dumps(self.system_metrics, indent=2)}

        评估依据：
        1. 技术兼容性
        2. 性能影响
        3. 安全性影响
        4. 学习曲线和团队能力
        5. 成本影响
        6. 长期可维护性
        7. 可扩展性潜力

        提供包含以下内容的建议：
        - approved：布尔值
        - technical_score：0-100
        - risk_assessment：低/中/高
        - implementation_plan：如果批准
        - concerns：关注点列表
        - benefits：收益列表

        以JSON格式响应。
        """

        try:
            response = await self.llm.ainvoke([HumanMessage(content=evaluation_prompt)])
            evaluation = json.loads(response.content)

            return CommunicationProtocol.create_message(
                sender=self.role,
                recipient=message.sender,
                message_type=MessageType.APPROVAL_RESPONSE,
                content={
                    "request_id": request_data.get("request_id"),
                    "decision": evaluation,
                    "evaluated_by": "CTO",
                    "technical_evaluation": True,
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
                        "reasoning": "评估失败：" + str(e),
                    },
                },
            )

    async def _evaluate_architecture_change(
        self, message: Message, company_state: CompanyState
    ) -> Message:
        request_data = message.content
        arch_details = request_data.get("architecture_details", {})

        architecture_analysis = {
            "current_architecture": self._get_current_architecture(),
            "proposed_changes": arch_details,
            "impact_analysis": self._analyze_architecture_impact(arch_details),
            "migration_complexity": self._assess_migration_complexity(arch_details),
            "risk_factors": self._identify_architecture_risks(arch_details),
        }

        approval = {
            "approved": self._should_approve_architecture_change(architecture_analysis),
            "technical_justification": architecture_analysis,
            "implementation_timeline": self._estimate_implementation_timeline(
                arch_details
            ),
            "resource_requirements": self._calculate_resource_needs(arch_details),
        }

        return CommunicationProtocol.create_message(
            sender=self.role,
            recipient=message.sender,
            message_type=MessageType.APPROVAL_RESPONSE,
            content={
                "request_id": request_data.get("request_id"),
                "decision": approval,
                "architecture_review": True,
            },
        )

    async def _evaluate_deployment_request(
        self, message: Message, company_state: CompanyState
    ) -> Message:
        request_data = message.content
        deployment_details = request_data.get("deployment_details", {})

        deployment_assessment = {
            "readiness_score": self._assess_deployment_readiness(deployment_details),
            "rollback_plan": self._validate_rollback_plan(deployment_details),
            "performance_impact": self._estimate_performance_impact(deployment_details),
            "security_checks": self._verify_security_checks(deployment_details),
        }

        approved = (
            deployment_assessment["readiness_score"] >= 80
            and deployment_assessment["rollback_plan"]
            and deployment_assessment["security_checks"]
        )

        return CommunicationProtocol.create_message(
            sender=self.role,
            recipient=message.sender,
            message_type=MessageType.APPROVAL_RESPONSE,
            content={
                "request_id": request_data.get("request_id"),
                "decision": {
                    "approved": approved,
                    "assessment": deployment_assessment,
                    "deployment_window": self._suggest_deployment_window(
                        deployment_details
                    ),
                },
            },
        )

    async def _handle_alert(
        self, message: Message, company_state: CompanyState
    ) -> Optional[Message]:
        alert_data = message.content
        alert_type = alert_data.get("alert_type", "")

        if alert_type in [
            "security_breach",
            "performance_degradation",
            "system_failure",
        ]:
            return CommunicationProtocol.create_alert(
                sender=self.role,
                alert_type="technical_incident",
                message=f"CTO处理：{alert_data.get('message', '检测到技术警报')}",
                severity=Priority.HIGH,
                recipient=AgentRole.OPERATIONS,
            )

        return None

    async def _handle_collaboration(
        self, message: Message, company_state: CompanyState
    ) -> Optional[Message]:
        content = message.content

        if content.get("type") == "technical_consultation":
            return await self._provide_technical_consultation(message, company_state)

        return None

    async def _provide_technical_consultation(
        self, message: Message, company_state: CompanyState
    ) -> Message:
        question = message.content.get("question", "")
        context = message.content.get("context", {})

        consultation_prompt = f"""
        作为CTO，就此问题提供技术咨询：

        问题：{question}
        上下文：{json.dumps(context, indent=2)}
        当前系统状态：{json.dumps(self.system_metrics, indent=2)}
        技术栈：{json.dumps(self.technology_stack, indent=2)}

        提供专家技术建议，涵盖：
        1. 技术可行性
        2. 最佳实践建议
        3. 实施方法
        4. 潜在挑战和缓解措施
        5. 资源需求
        6. 时间线估算

        以JSON格式提供详细技术咨询。
        """

        try:
            response = await self.llm.ainvoke(
                [HumanMessage(content=consultation_prompt)]
            )
            consultation = json.loads(response.content)

            return CommunicationProtocol.create_message(
                sender=self.role,
                recipient=message.sender,
                message_type=MessageType.COLLABORATION,
                content={
                    "type": "technical_consultation_response",
                    "consultation": consultation,
                    "consultant": "CTO",
                },
            )
        except Exception as e:
            return CommunicationProtocol.create_message(
                sender=self.role,
                recipient=message.sender,
                message_type=MessageType.COLLABORATION,
                content={
                    "type": "technical_consultation_response",
                    "error": str(e),
                    "status": "咨询失败",
                },
            )

    async def execute_task(
        self, task: Task, company_state: CompanyState
    ) -> Dict[str, Any]:
        if "architecture" in task.title.lower():
            return await self._execute_architecture_design(task, company_state)
        elif "technology" in task.title.lower():
            return await self._execute_technology_assessment(task, company_state)
        elif "security" in task.title.lower():
            return await self._execute_security_audit(task, company_state)
        elif "scalability" in task.title.lower():
            return await self._execute_scalability_planning(task, company_state)

        return {
            "status": "completed",
            "result": "任务已由CTO处理",
            "timestamp": datetime.now().isoformat(),
        }

    async def _execute_architecture_design(
        self, task: Task, company_state: CompanyState
    ) -> Dict[str, Any]:
        design_prompt = f"""
        作为CTO，根据需求设计系统架构：

        任务：{task.description}
        当前需求：{json.dumps(task.metadata.get("requirements", {}), indent=2)}
        当前系统：{json.dumps(self.system_metrics, indent=2)}

        设计涵盖以下内容的架构：
        1. 高层架构图（文本描述）
        2. 组件分解
        3. 数据流设计
        4. API规范
        5. 安全性考虑
        6. 可扩展性设计
        7. 技术推荐
        8. 实施阶段

        以JSON格式提供全面的架构设计。
        """

        try:
            response = await self.llm.ainvoke([HumanMessage(content=design_prompt)])
            architecture = json.loads(response.content)

            return {
                "status": "completed",
                "result": architecture,
                "type": "architecture_design",
                "timestamp": datetime.now().isoformat(),
                "implementation_plan": architecture.get("implementation_phases", []),
            }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def _execute_technology_assessment(
        self, task: Task, company_state: CompanyState
    ) -> Dict[str, Any]:
        assessment_prompt = f"""
        作为CTO，评估技术格局并提出建议：

        任务：{task.description}
        当前技术栈：{json.dumps(self.technology_stack, indent=2)}
        行业趋势：分析当前技术趋势

        提供涵盖以下内容的评估：
        1. 当前技术评估
        2. 值得关注的新兴技术
        3. 技术债务评估
        4. 现代化机会
        5. 竞争技术分析
        6. 改进建议
        7. 实施路线图

        以JSON格式提供全面技术评估。
        """

        try:
            response = await self.llm.ainvoke([HumanMessage(content=assessment_prompt)])
            assessment = json.loads(response.content)

            return {
                "status": "completed",
                "result": assessment,
                "type": "technology_assessment",
                "timestamp": datetime.now().isoformat(),
                "action_items": assessment.get("recommendations", []),
            }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def _execute_security_audit(
        self, task: Task, company_state: CompanyState
    ) -> Dict[str, Any]:
        audit_prompt = f"""
        作为CTO，进行综合安全审计：

        任务：{task.description}
        当前安全态势：{json.dumps(self.security_posture, indent=2)}
        系统架构：{self._get_current_architecture()}

        执行涵盖以下内容的安全审计：
        1. 漏洞评估
        2. 合规性验证
        3. 访问控制审查
        4. 数据保护分析
        5. 网络安全评估
        6. 应用安全审查
        7. 事件响应能力
        8. 安全建议

        以JSON格式提供详细安全审计。
        """

        try:
            response = await self.llm.ainvoke([HumanMessage(content=audit_prompt)])
            audit = json.loads(response.content)

            # 根据审计更新安全态势
            self.security_posture.update(audit.get("updated_security_posture", {}))

            return {
                "status": "completed",
                "result": audit,
                "type": "security_audit",
                "timestamp": datetime.now().isoformat(),
                "critical_issues": audit.get("critical_vulnerabilities", []),
            }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def _execute_scalability_planning(
        self, task: Task, company_state: CompanyState
    ) -> Dict[str, Any]:
        planning_prompt = f"""
        作为CTO，制定可扩展性计划：

        任务：{task.description}
        当前指标：{json.dumps(self.system_metrics, indent=2)}
        增长预测：{json.dumps(company_state.get("kpis", {}).get("growth_projections", {}), indent=2)}

        创建涵盖以下内容的可扩展性计划：
        1. 当前可扩展性评估
        2. 瓶颈识别
        3. 6/12/24个月容量规划
        4. 水平扩展策略
        5. 垂直扩展机会
        6. 数据库扩展方法
        7. 缓存策略
        8. 负载均衡设计
        9. 性能监控
        10. 实施时间线

        以JSON格式提供全面可扩展性计划。
        """

        try:
            response = await self.llm.ainvoke([HumanMessage(content=planning_prompt)])
            plan = json.loads(response.content)

            return {
                "status": "completed",
                "result": plan,
                "type": "scalability_plan",
                "timestamp": datetime.now().isoformat(),
                "immediate_actions": plan.get("immediate_actions", []),
            }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def generate_report(self, company_state: CompanyState) -> Dict[str, Any]:
        report_prompt = f"""
        作为CTO，生成综合技术报告：

        系统性能：{json.dumps(self.system_metrics, indent=2)}
        技术栈：{json.dumps(self.technology_stack, indent=2)}
        安全态势：{json.dumps(self.security_posture, indent=2)}
        团队绩效：{json.dumps(self._analyze_rd_performance(company_state), indent=2)}

        生成涵盖以下内容的技术仪表板：
        1. 执行摘要
        2. 系统性能指标
        3. 技术评估
        4. 安全状态
        5. 研发生产力
        6. 技术债务分析
        7. 即将启动的项目
        8. 资源需求
        9. 风险评估
        10. 建议

        格式化为专业技术报告。
        """

        try:
            response = await self.llm.ainvoke([HumanMessage(content=report_prompt)])
            report = json.loads(response.content)

            return {
                "agent_role": self.role.value,
                "report_type": "technical_dashboard",
                "timestamp": datetime.now().isoformat(),
                "data": report,
                "technical_health_score": self._calculate_technical_health_score(),
            }
        except Exception as e:
            return {
                "agent_role": self.role.value,
                "report_type": "technical_dashboard",
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "status": "report_generation_failed",
            }

    # 技术分析辅助方法
    def _assess_system_stability(self, system_health: Dict[str, Any]) -> Dict[str, Any]:
        uptime = system_health.get("uptime", 0)
        error_rate = system_health.get("error_rate", 100)

        return {
            "stability_score": min(100, (uptime / 100) * (100 - error_rate)),
            "status": "稳定" if uptime > 99 and error_rate < 1 else "需关注",
            "recommendations": self._generate_stability_recommendations(system_health),
        }

    def _analyze_performance_trends(
        self, performance_metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        current_response_time = performance_metrics.get(
            "response_time", self.system_metrics["response_time"]
        )
        baseline_response_time = self.system_metrics["response_time"]

        trend = "改善" if current_response_time < baseline_response_time else "恶化"
        change_percentage = (
            (current_response_time - baseline_response_time) / baseline_response_time
        ) * 100

        return {
            "trend": trend,
            "change_percentage": change_percentage,
            "status": "optimal" if abs(change_percentage) < 10 else "investigate",
            "bottlenecks": self._identify_bottlenecks(performance_metrics),
        }

    def _recommend_capacity_planning(self, system_health: Dict[str, Any]) -> List[str]:
        cpu_usage = system_health.get("cpu_usage", 50)
        memory_usage = system_health.get("memory_usage", 50)

        recommendations = []
        if cpu_usage > 80:
            recommendations.append("为CPU密集型工作负载进行水平扩展")
        if memory_usage > 80:
            recommendations.append("增加内存分配或优化内存使用")
        if cpu_usage < 30 and memory_usage < 30:
            recommendations.append("考虑调整资源大小以优化成本")

        return recommendations

    def _assess_infrastructure_needs(
        self, company_state: CompanyState
    ) -> Dict[str, Any]:
        kpis = company_state.get("kpis", {})
        user_growth = kpis.get("user_growth", 0)

        return {
            "current_capacity": "充足" if user_growth < 50 else "需扩展",
            "scaling_timeline": self._estimate_scaling_timeline(user_growth),
            "investment_needed": self._calculate_infrastructure_investment(user_growth),
        }

    def _evaluate_security_status(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        recent_incidents = report_data.get("security_incidents", [])
        vulnerability_scan = report_data.get("vulnerability_scan", {})

        return {
            "security_score": self.security_posture["security_score"],
            "recent_incidents": len(recent_incidents),
            "critical_vulnerabilities": vulnerability_scan.get("critical", 0),
            "compliance_status": "合规" if len(recent_incidents) == 0 else "需审查",
        }

    def _generate_operations_recommendations(
        self, analysis: Dict[str, Any]
    ) -> List[str]:
        recommendations = []

        if analysis["system_stability"]["stability_score"] < 80:
            recommendations.append("实施改进的监控和告警")

        if analysis["performance_trends"]["status"] == "investigate":
            recommendations.append("进行性能分析和优化")

        if analysis["security_status"]["security_score"] < 90:
            recommendations.append("加强安全措施并进行审计")

        return recommendations

    def _get_current_architecture(self) -> Dict[str, Any]:
        return {
            "pattern": "微服务",
            "communication": "REST API + 消息队列",
            "database": "PostgreSQL + Redis",
            "deployment": "Docker + Kubernetes",
            "monitoring": "Prometheus + Grafana",
        }

    def _analyze_architecture_impact(
        self, arch_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        return {
            "complexity_change": "medium",
            "migration_risk": "low",
            "performance_impact": "positive",
            "maintenance_impact": "reduced",
        }

    def _assess_migration_complexity(self, arch_details: Dict[str, Any]) -> str:
        # 简化复杂度评估
        return "medium"

    def _identify_architecture_risks(self, arch_details: Dict[str, Any]) -> List[str]:
        return ["数据迁移复杂性", "过渡期间的服务中断"]

    def _should_approve_architecture_change(self, analysis: Dict[str, Any]) -> bool:
        return (
            analysis["migration_complexity"] != "high"
            and len([r for r in analysis["risk_factors"] if "critical" in r.lower()])
            == 0
        )

    def _estimate_implementation_timeline(self, arch_details: Dict[str, Any]) -> str:
        complexity = arch_details.get("complexity", "medium")
        timelines = {"low": "2-4周", "medium": "1-2个月", "high": "3-6个月"}
        return timelines.get(complexity, "2-3个月")

    def _calculate_resource_needs(self, arch_details: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "developers": 3,
            "devops_engineers": 1,
            "qa_engineers": 2,
            "estimated_cost": "150,000美元",
        }

    def _assess_deployment_readiness(self, deployment_details: Dict[str, Any]) -> float:
        # 简化就绪评分
        score = 100

        if not deployment_details.get("testing_completed", False):
            score -= 30
        if not deployment_details.get("documentation_updated", False):
            score -= 20
        if not deployment_details.get("rollback_plan", False):
            score -= 25
        if not deployment_details.get("performance_testing", False):
            score -= 25

        return max(0, score)

    def _validate_rollback_plan(self, deployment_details: Dict[str, Any]) -> bool:
        return bool(deployment_details.get("rollback_plan"))

    def _estimate_performance_impact(self, deployment_details: Dict[str, Any]) -> str:
        return "minimal" if deployment_details.get("performance_testing") else "unknown"

    def _verify_security_checks(self, deployment_details: Dict[str, Any]) -> bool:
        return deployment_details.get("security_scan_completed", False)

    def _suggest_deployment_window(self, deployment_details: Dict[str, Any]) -> str:
        risk_level = deployment_details.get("risk_level", "medium")
        if risk_level == "high":
            return "周末凌晨2-4点"
        elif risk_level == "medium":
            return "工作日晚10-12点"
        else:
            return "随时（需监控）"

    def _analyze_rd_performance(self, company_state: CompanyState) -> Dict[str, Any]:
        agents = company_state.get("agents", {})
        rd_agent = agents.get(AgentRole.RD)

        if not rd_agent:
            return {"status": "未找到研发代理"}

        completed_tasks = len(rd_agent.get("completed_tasks", []))
        current_tasks = len(rd_agent.get("current_tasks", []))

        return {
            "tasks_completed": completed_tasks,
            "current_workload": current_tasks,
            "productivity_score": min(100, completed_tasks * 10),
            "code_quality": "good",  # 基于实际代码审查
            "innovation_index": 85,
        }

    def _calculate_technical_health_score(self) -> float:
        weights = {
            "uptime": 0.3,
            "performance": 0.25,
            "security": 0.25,
            "scalability": 0.2,
        }

        scores = {
            "uptime": self.system_metrics["uptime"],
            "performance": max(0, 100 - (self.system_metrics["response_time"] / 10)),
            "security": self.security_posture["security_score"],
            "scalability": self.system_metrics["scalability"] * 100,
        }

        return sum(weights[metric] * scores[metric] for metric in weights)

    def _generate_stability_recommendations(
        self, system_health: Dict[str, Any]
    ) -> List[str]:
        recommendations = []

        if system_health.get("uptime", 100) < 99:
            recommendations.append("调查停机原因并实施冗余")

        if system_health.get("error_rate", 0) > 1:
            recommendations.append("实施更好的错误处理和监控")

        return recommendations

    def _identify_bottlenecks(self, performance_metrics: Dict[str, Any]) -> List[str]:
        bottlenecks = []

        response_time = performance_metrics.get("response_time", 150)
        if response_time > 200:
            bottlenecks.append("高响应时间")

        cpu_usage = performance_metrics.get("cpu_usage", 50)
        if cpu_usage > 80:
            bottlenecks.append("高CPU利用率")

        return bottlenecks

    def _estimate_scaling_timeline(self, user_growth: float) -> str:
        if user_growth < 20:
            return "6个月规划窗口"
        elif user_growth < 50:
            return "3个月需立即行动"
        else:
            return "1个月紧急扩展"

    def _calculate_infrastructure_investment(self, user_growth: float) -> str:
        if user_growth < 20:
            return "50,000 - 100,000美元"
        elif user_growth < 50:
            return "100,000 - 250,000美元"
        else:
            return "250,000+美元"
