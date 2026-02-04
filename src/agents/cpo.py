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



class CPOAgent(BaseAgent):
    def __init__(self):
        capabilities = [
            "产品策略",
            "市场分析",
            "用户研究",
            "路线图规划",
            "PRD创建",
            "功能优先级排序",
            "竞品分析",
            "产品仪表板",
        ]
        super().__init__(AgentRole.CPO, capabilities)
        default_model_config = app_config.llm.models.get(
            app_config.llm.default_model,
            ModelConfig(
                name=app_config.llm.default_model,
                provider="openai",
                api_key=None,
                config={},
            ),
        )
        agent_config = app_config.agents.get("cpo", AgentConfig())
        self.llm = ChatOpenAI(
            model=app_config.llm.default_model,
            temperature=agent_config.temperature if agent_config.temperature != 0.3 else default_model_config.config.get("temperature", 0.3),
        )
        self.product_backlog = []
        self.roadmap = []
        self.user_feedback = []
        self.competitor_analysis = {}

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
        elif message.message_type == MessageType.ALERT:
            return await self._handle_alert(message, company_state)
        elif message.message_type == MessageType.APPROVAL_REQUEST:
            return await self._handle_approval_request(message, company_state)
        elif message.message_type == MessageType.COLLABORATION:
            return await self._handle_collaboration(message, company_state)

        return None

    async def _handle_status_report(
        self, message: Message, company_state: CompanyState
    ) -> Optional[Message]:
        sender = message.sender
        report_data = message.content

        analysis_prompt = f"""
        作为CPO，分析来自{sender.value}的状态报告：

        报告数据：{json.dumps(report_data, indent=2)}

        当前产品待办列表：{json.dumps(self.product_backlog[:5], indent=2)}
        当前路线图：{json.dumps(self.roadmap[:3], indent=2)}
        用户反馈摘要：{json.dumps(self.user_feedback[:3], indent=2)}

        提供产品指导：
        1. 产品影响是什么？
        2. 这如何影响我们的路线图？
        3. 是否需要新功能或变更？
        4. 什么应该优先处理？

        以JSON格式响应，包含：
        - insights：关键洞察列表
        - impact_score：0-100产品影响评分
        - actions：推荐行动列表
        - priority_adjustment：需要的优先级调整
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
                    "type": "product_guidance",
                    "guidance": guidance,
                    "report_reference": message.message_id,
                },
            )
        except Exception as e:
            return CommunicationProtocol.create_message(
                sender=self.role,
                recipient=sender,
                message_type=MessageType.COLLABORATION,
                content={
                    "type": "acknowledgment",
                    "status": "reviewed",
                    "next_steps": "继续当前产品策略",
                },
            )

    async def _handle_task_assignment(
        self, message: Message, company_state: CompanyState
    ) -> Optional[Message]:
        task_data = message.content.get("task", {})
        task_title = task_data.get("title", "")

        if "development" in task_title.lower() or "feature" in task_title.lower():
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

        if request_type == "product_backlog":
            return CommunicationProtocol.create_message(
                sender=self.role,
                recipient=message.sender,
                message_type=MessageType.DATA_RESPONSE,
                content={
                    "request_id": message.content.get("request_id"),
                    "data": self.product_backlog,
                    "data_type": "product_backlog",
                    "total_items": len(self.product_backlog),
                },
            )
        elif request_type == "roadmap":
            return CommunicationProtocol.create_message(
                sender=self.role,
                recipient=message.sender,
                message_type=MessageType.DATA_RESPONSE,
                content={
                    "request_id": message.content.get("request_id"),
                    "data": self.roadmap,
                    "data_type": "product_roadmap",
                },
            )
        elif request_type == "user_feedback":
            return CommunicationProtocol.create_message(
                sender=self.role,
                recipient=message.sender,
                message_type=MessageType.DATA_RESPONSE,
                content={
                    "request_id": message.content.get("request_id"),
                    "data": self.user_feedback,
                    "data_type": "user_feedback",
                    "sentiment_summary": self._summarize_feedback_sentiment(),
                },
            )
        elif request_type == "competitor_analysis":
            return CommunicationProtocol.create_message(
                sender=self.role,
                recipient=message.sender,
                message_type=MessageType.DATA_RESPONSE,
                content={
                    "request_id": message.content.get("request_id"),
                    "data": self.competitor_analysis,
                    "data_type": "competitor_analysis",
                },
            )

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
    ) -> Optional[Message]:
        request_data = message.content
        request_type = request_data.get("request_type", "")

        if request_type in ["feature_launch", "product_update", "new_feature"]:
            return await self._evaluate_product_approval(message, company_state)

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

    async def _evaluate_product_approval(
        self, message: Message, company_state: CompanyState
    ) -> Message:
        request_data = message.content
        feature_details = request_data.get("feature_details", {})

        evaluation_prompt = f"""
        作为CPO，评估此产品审批请求：

        功能详情：{json.dumps(feature_details, indent=2)}
        当前产品待办列表：{json.dumps(self.product_backlog[:5], indent=2)}
        当前路线图：{json.dumps(self.roadmap[:3], indent=2)}
        用户反馈摘要：{json.dumps(self.user_feedback[:5], indent=2)}

        评估依据：
        1. 与产品愿景的战略一致性
        2. 用户价值和需求
        3. 市场竞争力
        4. 技术可行性
        5. 资源影响
        6. 与路线图的时间线对齐

        提供包含以下内容的建议：
        - approved：布尔值
        - strategic_score：0-100
        - user_value：低/中/高
        - competitive_impact：积极/中性/消极
        - implementation_recommendations：如果批准
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
                    "evaluated_by": "CPO",
                    "product_review": True,
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

    async def _handle_alert(
        self, message: Message, company_state: CompanyState
    ) -> Optional[Message]:
        alert_data = message.content
        alert_type = alert_data.get("alert_type", "")

        if alert_type in ["user_complaint", "feature_issue", "market_opportunity"]:
            return CommunicationProtocol.create_message(
                sender=self.role,
                recipient=AgentRole.CEO,
                message_type=MessageType.ALERT,
                content={
                    "alert_type": "product_alert",
                    "message": f"CPO警报：{alert_data.get('message', '检测到产品相关问题')}",
                    "severity": "high",
                    "product_impact": "high",
                },
                priority=Priority.HIGH,
            )

        return None

    async def _handle_collaboration(
        self, message: Message, company_state: CompanyState
    ) -> Optional[Message]:
        content = message.content

        if content.get("type") == "product_consultation":
            return await self._provide_product_consultation(message, company_state)

        return None

    async def _provide_product_consultation(
        self, message: Message, company_state: CompanyState
    ) -> Message:
        question = message.content.get("question", "")
        context = message.content.get("context", {})

        consultation_prompt = f"""
        作为CPO，就此问题提供产品咨询：

        问题：{question}
        上下文：{json.dumps(context, indent=2)}
        当前产品状态：
        - 待办列表：{json.dumps(self.product_backlog[:3], indent=2)}
        - 路线图：{json.dumps(self.roadmap[:2], indent=2)}
        - 用户反馈：{json.dumps(self.user_feedback[:3], indent=2)}

        提供专家产品建议，涵盖：
        1. 产品战略影响
        2. 功能建议
        3. 用户体验考虑
        4. 竞争定位
        5. 实施方法
        6. 需要跟踪的指标

        以JSON格式提供详细产品咨询。
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
                    "type": "product_consultation_response",
                    "consultation": consultation,
                    "consultant": "CPO",
                },
            )
        except Exception as e:
            return CommunicationProtocol.create_message(
                sender=self.role,
                recipient=message.sender,
                message_type=MessageType.COLLABORATION,
                content={
                    "type": "product_consultation_response",
                    "error": str(e),
                    "status": "consultation_failed",
                },
            )

    async def execute_task(
        self, task: Task, company_state: CompanyState
    ) -> Dict[str, Any]:
        if "strategic" in task.title.lower() or "planning" in task.title.lower():
            return await self._execute_strategic_planning(task, company_state)
        elif "market" in task.title.lower() or "analysis" in task.title.lower():
            return await self._execute_market_analysis(task, company_state)
        elif "strategy" in task.title.lower():
            return await self._execute_product_strategy(task, company_state)
        elif "roadmap" in task.title.lower():
            return await self._execute_roadmap_creation(task, company_state)

        return {
            "status": "completed",
            "result": "任务已由CPO处理",
            "timestamp": datetime.now().isoformat(),
        }

    async def _execute_strategic_planning(
        self, task: Task, company_state: CompanyState
    ) -> Dict[str, Any]:
        planning_prompt = f"""
        作为CPO，基于当前状态创建产品战略计划：

        任务：{task.description}
        当前KPI：{json.dumps(company_state.get("kpis", {}), indent=2)}
        市场数据：{json.dumps(company_state.get("market_data", {}), indent=2)}
        用户反馈：{json.dumps(company_state.get("user_feedback", [])[:5], indent=2)}
        竞争分析：{json.dumps(self.competitor_analysis, indent=2)}

        创建涵盖以下内容的战略计划：
        1. 产品愿景和使命
        2. 目标市场和用户分段
        3. 产品支柱（3-5个关键关注领域）
        4. 战略举措
        5. 成功指标（KPI）
        6. 风险评估
        7. 资源需求

        以JSON格式返回全面的战略计划。
        """

        try:
            response = await self.llm.ainvoke([HumanMessage(content=planning_prompt)])
            content = (
                response.content
                if isinstance(response.content, str)
                else str(response.content)
            )
            strategic_plan = json.loads(content)

            return {
                "status": "completed",
                "result": strategic_plan,
                "type": "product_strategic_plan",
                "timestamp": datetime.now().isoformat(),
                "next_steps": [
                    "与CEO审查战略计划",
                    "与CTO对齐技术可行性",
                    "传达给产品团队",
                ],
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
        analysis_prompt = f"""
        作为CPO，基于当前数据分析市场机会：

        任务：{task.description}
        市场数据：{json.dumps(company_state.get("market_data", {}), indent=2)}
        竞争对手信息：{json.dumps(self.competitor_analysis, indent=2)}
        用户反馈：{json.dumps(self.user_feedback, indent=2)}

        提供涵盖以下内容的市场分析：
        1. 市场规模和增长潜力
        2. 竞争定位
        3. 用户需求和痛点
        4. 市场趋势和机会
        5. SWOT分析
        6. 战略建议

        以JSON格式返回全面市场分析。
        """

        try:
            response = await self.llm.ainvoke([HumanMessage(content=analysis_prompt)])
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
                "action_items": market_analysis.get("recommendations", []),
            }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def _execute_product_strategy(
        self, task: Task, company_state: CompanyState
    ) -> Dict[str, Any]:
        strategy_prompt = f"""
        作为CPO，创建产品策略：

        任务：{task.description}
        战略计划：{json.dumps(company_state.get("strategic_goals", {}), indent=2)}
        当前产品状态：
        - 待办列表：{json.dumps(self.product_backlog[:5], indent=2)}
        - 路线图：{json.dumps(self.roadmap[:3], indent=2)}

        创建涵盖以下内容的产品策略：
        1. 产品定位
        2. 功能优先级排序方法
        3. 上市策略
        4. 定价策略（如适用）
        5. 增长黑客机会
        6. 用户获取计划

        以JSON格式返回详细产品策略。
        """

        try:
            response = await self.llm.ainvoke([HumanMessage(content=strategy_prompt)])
            content = (
                response.content
                if isinstance(response.content, str)
                else str(response.content)
            )
            product_strategy = json.loads(content)

            return {
                "status": "completed",
                "result": product_strategy,
                "type": "product_strategy",
                "timestamp": datetime.now().isoformat(),
                "implementation_plan": product_strategy.get("implementation_plan", []),
            }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def _execute_roadmap_creation(
        self, task: Task, company_state: CompanyState
    ) -> Dict[str, Any]:
        roadmap_prompt = f"""
        作为CPO，创建产品路线图：

        任务：{task.description}
        战略目标：{json.dumps(company_state.get("strategic_goals", {}), indent=2)}
        市场分析：{json.dumps(company_state.get("market_data", {}), indent=2)}
        当前待办列表：{json.dumps(self.product_backlog[:10], indent=2)}

        创建涵盖以下内容的路线图：
        1. 时间周期（Q1/Q2/Q3/Q4或3/6/12个月）
        2. 每个周期的关键里程碑
        3. 功能发布
        4. 技术依赖
        5. 资源分配
        6. 风险缓解

        以JSON格式返回详细路线图。
        """

        try:
            response = await self.llm.ainvoke([HumanMessage(content=roadmap_prompt)])
            content = (
                response.content
                if isinstance(response.content, str)
                else str(response.content)
            )
            roadmap = json.loads(content)

            self.roadmap = roadmap

            return {
                "status": "completed",
                "result": roadmap,
                "type": "product_roadmap",
                "timestamp": datetime.now().isoformat(),
                "next_planning_review": (
                    datetime.now() + timedelta(days=90)
                ).isoformat(),
            }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def generate_report(self, company_state: CompanyState) -> Dict[str, Any]:
        report_prompt = f"""
        作为CPO，生成综合产品仪表板报告：

        产品战略进度：{json.dumps(self._assess_strategic_progress(), indent=2)}
        当前路线图状态：{json.dumps(self.roadmap[:3], indent=2)}
        待办列表优先级：{json.dumps(self.product_backlog[:5], indent=2)}
        用户反馈摘要：{json.dumps(self._summarize_feedback_sentiment(), indent=2)}
        市场定位：{json.dumps(self._assess_market_position(), indent=2)}

        生成涵盖以下内容的产品仪表板：
        1. 执行摘要
        2. 关键产品指标
        3. 路线图进度
        4. 功能管道
        5. 用户满意度
        6. 竞争格局
        7. 关键成就
        8. 挑战和风险
        9. 下一步
        10. 建议

        格式化为专业产品仪表板报告。
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
                "report_type": "product_dashboard",
                "timestamp": datetime.now().isoformat(),
                "data": report,
                "generated_by": "CPO",
            }
        except Exception as e:
            return {
                "agent_role": self.role.value,
                "report_type": "product_dashboard",
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "status": "report_generation_failed",
            }

    def _handle_user_feedback(self, feedback_data: Dict[str, Any]) -> None:
        self.user_feedback.append(
            {
                "feedback_id": create_task_id(),
                "timestamp": datetime.now().isoformat(),
                **feedback_data,
            }
        )

        if len(self.user_feedback) > 100:
            self.user_feedback = self.user_feedback[-100:]

    def _execute_product_strategy(
        self, strategy_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        strategy = {
            "strategy_id": create_task_id(),
            "created_at": datetime.now().isoformat(),
            **strategy_data,
        }

        return {"status": "created", "strategy": strategy}

    def _create_prd(self, prd_data: Dict[str, Any]) -> Dict[str, Any]:
        prd = {
            "prd_id": create_task_id(),
            "created_at": datetime.now().isoformat(),
            "status": "draft",
            **prd_data,
        }

        return {"status": "created", "prd": prd}

    def _analyze_market_opportunities(
        self, market_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        analysis = {
            "analysis_id": create_task_id(),
            "analyzed_at": datetime.now().isoformat(),
            **market_data,
        }

        return {"status": "analyzed", "analysis": analysis}

    def _generate_product_report(self, report_params: Dict[str, Any]) -> Dict[str, Any]:
        report = {
            "report_id": create_task_id(),
            "generated_at": datetime.now().isoformat(),
            **report_params,
        }

        return {"status": "generated", "report": report}

    def _analyze_competitiveness(
        self, competitor_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        self.competitor_analysis = {
            "analysis_id": create_task_id(),
            "analyzed_at": datetime.now().isoformat(),
            **competitor_data,
        }

        return {"status": "analyzed", "analysis": self.competitor_analysis}

    def _prioritize_features(
        self, features: List[Dict[str, Any]], method: str = "moscow"
    ) -> List[Dict[str, Any]]:
        if method == "moscow":
            prioritized = []
            for feature in features:
                priority = feature.get("priority", "medium").lower()
                if priority in ["must", "high"]:
                    feature["moscow_priority"] = "必须"
                elif priority in ["should", "medium"]:
                    feature["moscow_priority"] = "应该"
                elif priority in ["could", "low"]:
                    feature["moscow_priority"] = "可以"
                else:
                    feature["moscow_priority"] = "不会"
                prioritized.append(feature)

            prioritized.sort(
                key=lambda x: {"必须": 1, "应该": 2, "可以": 3, "不会": 4}.get(
                    x.get("moscow_priority"), 5
                )
            )

            return prioritized

        return features

    def _update_roadmap(self, roadmap_updates: Dict[str, Any]) -> Dict[str, Any]:
        self.roadmap.append(
            {
                "update_id": create_task_id(),
                "timestamp": datetime.now().isoformat(),
                **roadmap_updates,
            }
        )

        return {"status": "updated", "roadmap": self.roadmap}

    def _summarize_feedback_sentiment(self) -> Dict[str, Any]:
        if not self.user_feedback:
            return {"summary": "无可用用户反馈"}

        positive = len(
            [f for f in self.user_feedback if f.get("sentiment") == "positive"]
        )
        negative = len(
            [f for f in self.user_feedback if f.get("sentiment") == "negative"]
        )
        neutral = len(
            [f for f in self.user_feedback if f.get("sentiment") == "neutral"]
        )

        return {
            "total_feedback": len(self.user_feedback),
            "sentiment_breakdown": {
                "positive": positive,
                "negative": negative,
                "neutral": neutral,
            },
            "net_promoter_score": self._calculate_nps(positive, negative),
        }

    def _calculate_nps(self, positive: int, negative: int) -> float:
        total = positive + negative
        if total == 0:
            return 0.0
        return ((positive - negative) / total) * 100

    def _assess_strategic_progress(self) -> Dict[str, Any]:
        progress = {}

        for goal in self.roadmap:
            goal_name = goal.get("name", "未知")
            progress[goal_name] = {
                "status": "进行中",
                "completion_percentage": 0,
                "items_completed": 0,
                "total_items": 1,
            }

        return progress

    def _assess_market_position(self) -> Dict[str, Any]:
        return {
            "market_share": self.competitor_analysis.get("market_share", 0),
            "competitive_strength": self.competitor_analysis.get(
                "competitive_strength", "评估中"
            ),
            "growth_potential": self.competitor_analysis.get(
                "growth_potential", "评估中"
            ),
            "key_differentiators": self.competitor_analysis.get("differentiators", []),
        }
