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


class CEOAgent(BaseAgent):
    def __init__(self):
        capabilities = [
            "战略规划",
            "资源分配",
            "风险评估",
            "市场分析",
            "领导力",
            "决策能力",
            "财务建模",
            "利益相关者管理",
        ]
        super().__init__(AgentRole.CEO, capabilities)
        default_model_config = app_config.llm.models.get(
            app_config.llm.default_model,
            ModelConfig(
                name=app_config.llm.default_model,
                base_url="https://api.openai.com/v1",
                model=app_config.llm.default_model,
                api_key=None,
                config={},
            ),
        )
        agent_config = app_config.agents.get("ceo", AgentConfig())
        self.llm = ChatOpenAI(
            model=app_config.llm.default_model,
            temperature=agent_config.temperature
            if agent_config.temperature != 0.3
            else default_model_config.config.get("temperature", 0.3),
        )
        self.strategic_goals = {}
        self.market_trends = []
        self.performance_metrics = {
            "revenue_growth": 0.0,
            "user_growth": 0.0,
            "market_share": 0.0,
            "operational_efficiency": 0.0,
        }

    async def process_message(
        self, message: Message, company_state: CompanyState
    ) -> Optional[Message]:
        content = message.content

        if message.message_type == MessageType.STATUS_REPORT:
            return await self._handle_status_report(message, company_state)
        elif message.message_type == MessageType.ALERT:
            return await self._handle_alert(message, company_state)
        elif message.message_type == MessageType.APPROVAL_REQUEST:
            return await self._handle_approval_request(message, company_state)
        elif message.message_type == MessageType.DATA_RESPONSE:
            return await self._handle_data_response(message, company_state)
        elif message.message_type == MessageType.COLLABORATION:
            return await self._handle_collaboration(message, company_state)

        return None

    async def _handle_status_report(
        self, message: Message, company_state: CompanyState
    ) -> Optional[Message]:
        sender = message.sender
        report_data = message.content

        # 分析报告并提供战略指导
        analysis_prompt = f"""
        作为CEO，分析来自{sender.value}的状态报告：

        报告数据：{json.dumps(report_data, indent=2)}

        当前战略目标：{json.dumps(self.strategic_goals, indent=2)}

        提供战略指导与决策：
        1. 关键洞察是什么？
        2. 这与战略目标的契合度如何？
        3. 需要采取哪些行动或做出哪些决策？
        4. 是否需要重新分配任何资源？

        以JSON格式响应，包含：
        - insights：关键洞察列表
        - alignment_score：与目标的契合度评分（0-100）
        - actions：推荐行动列表
        - decisions：关键决策列表
        - resource_needs：需调整的资源分配
        """

        try:
            response = await self.llm.ainvoke([HumanMessage(content=analysis_prompt)])
            content = (
                response.content
                if isinstance(response.content, str)
                else str(response.content)
            )
            guidance = json.loads(content)

            return CommunicationProtocol.create_message(
                sender=self.role,
                recipient=sender,
                message_type=MessageType.COLLABORATION,
                content={
                    "type": "strategic_guidance",
                    "guidance": guidance,
                    "report_reference": message.message_id,
                },
            )
        except Exception as e:
            # 后备响应
            return CommunicationProtocol.create_message(
                sender=self.role,
                recipient=sender,
                message_type=MessageType.COLLABORATION,
                content={
                    "type": "acknowledgment",
                    "status": "reviewed",
                    "next_steps": "继续当前战略",
                },
            )

    async def _handle_alert(
        self, message: Message, company_state: CompanyState
    ) -> Optional[Message]:
        alert_data = message.content

        # 处理需要立即响应的关键警报
        if alert_data.get("severity") in ["critical", "high"]:
            return CommunicationProtocol.create_message(
                sender=self.role,
                recipient=AgentRole.OPERATIONS,
                message_type=MessageType.TASK_ASSIGNMENT,
                content={
                    "task": {
                        "task_id": create_task_id(),
                        "title": f"紧急：处理{alert_data.get('alert_type', '关键警报')}",
                        "description": f"CEO优先级：{alert_data.get('message', '需立即处理的紧急事项')}",
                        "priority": Priority.CRITICAL.value,
                        "deadline": (datetime.now() + timedelta(hours=2)).isoformat(),
                        "requires_immediate_action": True,
                    }
                },
                priority=Priority.CRITICAL,
            )

        return None

    async def _handle_approval_request(
        self, message: Message, company_state: CompanyState
    ) -> Optional[Message]:
        request_data = message.content
        request_type = request_data.get("request_type", "unknown")

        # 根据战略契合度评估审批请求
        evaluation_prompt = f"""
        作为CEO，评估此审批请求：

        请求类型：{request_type}
        请求详情：{json.dumps(request_data, indent=2)}

        当前战略目标：{json.dumps(self.strategic_goals, indent=2)}
        可用资源：{json.dumps(self._assess_available_resources(company_state), indent=2)}

        考虑以下因素：
        1. 战略契合度（0-100）
        2. 资源影响（低/中/高）
        3. 风险等级（低/中/高）
        4. 预期ROI
        5. 时间线可行性

        以JSON格式响应：
        - approved：布尔值
        - reasoning：详细说明
        - conditions：如果批准，列出条件
        - alternative_suggestions：如果未批准
        - strategic_alignment_score：0-100
        """

        try:
            response = await self.llm.ainvoke([HumanMessage(content=evaluation_prompt)])
            content = (
                response.content
                if isinstance(response.content, str)
                else str(response.content)
            )
            decision = json.loads(content)

            return CommunicationProtocol.create_message(
                sender=self.role,
                recipient=message.sender,
                message_type=MessageType.APPROVAL_RESPONSE,
                content={
                    "request_id": request_data.get("request_id"),
                    "decision": decision,
                    "reviewed_by": "CEO",
                },
            )
        except Exception as e:
            # 保守后备方案 - 不清楚时拒绝
            return CommunicationProtocol.create_message(
                sender=self.role,
                recipient=message.sender,
                message_type=MessageType.APPROVAL_RESPONSE,
                content={
                    "request_id": request_data.get("request_id"),
                    "decision": {
                        "approved": False,
                        "reasoning": "当前无法评估请求。请提供更多细节。",
                    },
                    "reviewed_by": "CEO",
                },
            )

    async def _handle_data_response(
        self, message: Message, company_state: CompanyState
    ) -> Optional[Message]:
        data = message.content

        if "market_analysis" in data:
            self.market_trends.append(data["market_analysis"])

        return CommunicationProtocol.create_message(
            sender=self.role,
            recipient=message.sender,
            message_type=MessageType.COLLABORATION,
            content={
                "type": "data_received",
                "status": "acknowledged",
                "next_action": "已纳入战略规划",
            },
        )

    async def _handle_collaboration(
        self, message: Message, company_state: CompanyState
    ) -> Optional[Message]:
        content = message.content

        if content.get("type") == "strategic_input":
            # 处理来自C级高管的战略输入
            return await self._process_strategic_input(message, company_state)

        return None

    async def _process_strategic_input(
        self, message: Message, company_state: CompanyState
    ) -> Message:
        input_data = message.content.get("data", {})

        # 将战略输入整合到规划中
        integration_prompt = f"""
        作为CEO，将此战略输入整合到公司整体战略中：

        来自{message.sender.value}的输入：{json.dumps(input_data, indent=2)}
        当前战略：{json.dumps(self.strategic_goals, indent=2)}

        提供整合计划：
        1. 此输入如何影响当前战略
        2. 需要进行哪些调整
        3. 需要通知哪些部门
        4. 实现时间线

        以JSON格式响应。
        """

        try:
            response = await self.llm.ainvoke(
                [HumanMessage(content=integration_prompt)]
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
                    "type": "strategic_integration",
                    "integration_plan": plan,
                    "status": "已整合",
                },
            )
        except Exception as e:
            return CommunicationProtocol.create_message(
                sender=self.role,
                recipient=message.sender,
                message_type=MessageType.COLLABORATION,
                content={"type": "acknowledgment", "status": "under_review"},
            )

    async def execute_task(
        self, task: Task, company_state: CompanyState
    ) -> Dict[str, Any]:
        if "strategic_planning" in task.title.lower():
            return await self._execute_strategic_planning(task, company_state)
        elif "resource_allocation" in task.title.lower():
            return await self._execute_resource_allocation(task, company_state)
        elif "market_analysis" in task.title.lower():
            return await self._execute_market_analysis(task, company_state)

        return {
            "status": "completed",
            "result": "任务已由CEO处理",
            "timestamp": datetime.now().isoformat(),
        }

    async def _execute_strategic_planning(
        self, task: Task, company_state: CompanyState
    ) -> Dict[str, Any]:
        planning_prompt = f"""
        作为CEO，基于当前状态创建战略规划：

        任务：{task.description}
        当前KPI：{json.dumps(company_state.get("kpis", {}), indent=2)}
        市场数据：{json.dumps(company_state.get("market_data", {}), indent=2)}
        用户反馈：{json.dumps(company_state.get("user_feedback", [])[:5], indent=2)}

        创建涵盖以下内容的战略规划：
        1. 愿景与使命（重申或更新）
        2. 战略目标（未来12个月的SMART目标）
        3. 关键举措（3-5个主要举措）
        4. 资源需求
        5. 成功指标
        6. 风险评估

        以JSON格式提供全面的战略规划。
        """

        try:
            response = await self.llm.ainvoke([HumanMessage(content=planning_prompt)])
            content = (
                response.content
                if isinstance(response.content, str)
                else str(response.content)
            )
            strategic_plan = json.loads(content)

            self.strategic_goals = strategic_plan

            return {
                "status": "completed",
                "result": strategic_plan,
                "type": "strategic_plan",
                "timestamp": datetime.now().isoformat(),
                "next_steps": [
                    "将战略规划分发给C级高管",
                    "安排实施规划会议",
                    "设置KPI跟踪仪表板",
                ],
            }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def _execute_resource_allocation(
        self, task: Task, company_state: CompanyState
    ) -> Dict[str, Any]:
        # 分析当前资源使用情况并最优分配
        allocation_prompt = f"""
        作为CEO，根据战略优先级分配公司资源：

        战略目标：{json.dumps(self.strategic_goals, indent=2)}
        当前团队绩效：{json.dumps(self._analyze_team_performance(company_state), indent=2)}
        可用预算：{company_state.get("kpis", {}).get("budget", 1000000)}

        创建资源分配计划：
        1. 部门预算分配
        2. 人员编制调整
        3. 技术投资
        4. 营销支出
        5. 研发投资
        6. 应急预案

        优化战略目标达成与ROI。

        以JSON格式提供详细的分配计划。
        """

        try:
            response = await self.llm.ainvoke([HumanMessage(content=allocation_prompt)])
            content = (
                response.content
                if isinstance(response.content, str)
                else str(response.content)
            )
            allocation_plan = json.loads(content)

            return {
                "status": "completed",
                "result": allocation_plan,
                "type": "resource_allocation",
                "timestamp": datetime.now().isoformat(),
                "implementation": "需CFO和部门负责人批准",
            }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def _execute_market_analysis(
        self, task: Task, company_state: CompanyState
    ) -> Dict[str, Any]:
        market_prompt = f"""
        作为CEO，分析市场定位与机会：

        市场数据：{json.dumps(company_state.get("market_data", {}), indent=2)}
        竞争对手情报：{self._get_competitor_intelligence(company_state)}
        用户反馈摘要：{self._summarize_user_feedback(company_state)}

        提供涵盖以下内容的市场分析：
        1. 市场定位与份额
        2. 竞争格局
        3. 增长机会
        4. 市场威胁与风险
        5. 战略建议

        以JSON格式提供全面的市场分析。
        """

        try:
            response = await self.llm.ainvoke([HumanMessage(content=market_prompt)])
            content = (
                response.content
                if isinstance(response.content, str)
                else str(response.content)
            )
            market_analysis = json.loads(content)

            return {
                "status": "completed",
                "result": market_analysis,
                "type": "market_analysis",
                "timestamp": datetime.now().isoformat(),
                "action_items": self._extract_action_items(market_analysis),
            }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def generate_report(self, company_state: CompanyState) -> Dict[str, Any]:
        report_prompt = f"""
        作为CEO，生成综合执行报告：

        战略目标进展：{json.dumps(self._assess_goal_progress(), indent=2)}
        公司绩效：{json.dumps(self.performance_metrics, indent=2)}
        团队生产力：{json.dumps(self._analyze_team_productivity(company_state), indent=2)}
        市场定位：{json.dumps(self._assess_market_position(), indent=2)}

        生成执行仪表板报告，包含：
        1. 执行摘要
        2. 关键成就
        3. 挑战与风险
        4. 战略建议
        5. 未来优先事项

        格式化为专业执行报告。
        """

        try:
            response = await self.llm.ainvoke([HumanMessage(content=report_prompt)])
            content = (
                response.content
                if isinstance(response.content, str)
                else str(response.content)
            )
            report = json.loads(content)

            return {
                "agent_role": self.role.value,
                "report_type": "executive_dashboard",
                "timestamp": datetime.now().isoformat(),
                "data": report,
                "next_actions": self._determine_next_actions(report),
            }
        except Exception as e:
            return {
                "agent_role": self.role.value,
                "report_type": "executive_dashboard",
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "status": "report_generation_failed",
            }

    def _assess_available_resources(
        self, company_state: CompanyState
    ) -> Dict[str, Any]:
        kpis = company_state.get("kpis", {})
        return {
            "budget": kpis.get("budget", 0),
            "headcount": len(
                [agent for agent in company_state.get("agents", {}).values()]
            ),
            "technology_capacity": kpis.get("tech_capacity", 0),
            "market_position": kpis.get("market_share", 0),
        }

    def _analyze_team_performance(self, company_state: CompanyState) -> Dict[str, Any]:
        agents = company_state.get("agents", {})
        performance = {}

        for role, agent_state in agents.items():
            completed_tasks = len(agent_state.completed_tasks)
            current_tasks = len(agent_state.current_tasks)
            workload = agent_state.workload

            performance[role.value] = {
                "completed_tasks": completed_tasks,
                "current_tasks": current_tasks,
                "workload": workload,
                "productivity": completed_tasks
                / max(1, current_tasks + completed_tasks),
            }

        return performance

    def _get_competitor_intelligence(
        self, company_state: CompanyState
    ) -> Dict[str, Any]:
        market_data = company_state.get("market_data", {})
        return market_data.get("competitors", {})

    def _summarize_user_feedback(self, company_state: CompanyState) -> Dict[str, Any]:
        feedback = company_state.get("user_feedback", [])
        if not feedback:
            return {"summary": "无可用用户反馈"}

        positive = len([f for f in feedback if f.get("sentiment") == "positive"])
        negative = len([f for f in feedback if f.get("sentiment") == "negative"])
        neutral = len([f for f in feedback if f.get("sentiment") == "neutral"])

        return {
            "total_feedback": len(feedback),
            "sentiment_breakdown": {
                "positive": positive,
                "negative": negative,
                "neutral": neutral,
            },
            "key_themes": self._extract_themes_from_feedback(feedback),
        }

    def _extract_themes_from_feedback(
        self, feedback: List[Dict[str, Any]]
    ) -> List[str]:
        # 简单主题提取 - 可通过NLP增强
        themes = []
        for f in feedback[:10]:  # 采样前10条
            message = f.get("message", "").lower()
            if "feature" in message:
                themes.append("功能请求")
            if "bug" in message or "error" in message:
                themes.append("错误报告")
            if "slow" in message or "performance" in message:
                themes.append("性能问题")

        return list(set(themes))

    def _assess_goal_progress(self) -> Dict[str, Any]:
        progress = {}
        for goal, target in self.strategic_goals.items():
            # 简化进度计算
            current = self.performance_metrics.get(goal, 0)
            target_value = target.get("target", 100)
            progress[goal] = {
                "current": current,
                "target": target_value,
                "completion_percentage": min(100, (current / target_value) * 100)
                if target_value > 0
                else 0,
            }

        return progress

    def _analyze_team_productivity(self, company_state: CompanyState) -> Dict[str, Any]:
        agents = company_state.get("agents", {})
        total_completed = sum(len(agent.completed_tasks) for agent in agents.values())
        total_current = sum(len(agent.current_tasks) for agent in agents.values())

        # 直接访问AgentState.workload
        total_workload = sum(agent.workload for agent in agents.values())

        return {
            "total_tasks_completed": total_completed,
            "total_tasks_in_progress": total_current,
            "completion_rate": total_completed
            / max(1, total_completed + total_current),
            "team_efficiency": total_workload / max(1, len(agents)),
        }

    def _assess_market_position(self) -> Dict[str, Any]:
        return {
            "market_share": self.performance_metrics.get("market_share", 0),
            "revenue_growth": self.performance_metrics.get("revenue_growth", 0),
            "user_growth": self.performance_metrics.get("user_growth", 0),
            "competitive_strength": "基于当前指标评估",
        }

    def _extract_action_items(self, analysis: Dict[str, Any]) -> List[str]:
        recommendations = analysis.get("strategic_recommendations", [])
        if isinstance(recommendations, list):
            return recommendations[:5]  # 前5个行动项
        return []

    def _determine_next_actions(self, report: Dict[str, Any]) -> List[str]:
        recommendations = report.get("strategic_recommendations", [])
        if isinstance(recommendations, list):
            return recommendations[:3]  # 前3个优先行动项
        return []
