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



class CMOAgent(BaseAgent):
    def __init__(self):
        capabilities = [
            "营销策略",
            "活动管理",
            "品牌管理",
            "市场分析",
            "预算分配",
            "ROI分析",
            "数字营销",
            "公共关系",
        ]
        super().__init__(AgentRole.CMO, capabilities)
        default_model_config = app_config.llm.models.get(
            app_config.llm.default_model,
            ModelConfig(
                name=app_config.llm.default_model,
                provider="openai",
                api_key=None,
                config={},
            ),
        )
        agent_config = app_config.agents.get("cmo", AgentConfig())
        self.llm = ChatOpenAI(
            model=app_config.llm.default_model,
            temperature=agent_config.temperature if agent_config.temperature != 0.3 else default_model_config.config.get("temperature", 0.3),
        )
        self.marketing_channels = {
            "social_media": ["LinkedIn", "Twitter", "Facebook", "Instagram", "WeChat"],
            "email_marketing": ["Mailchimp", "HubSpot"],
            "search_ads": ["Google Ads", "Bing Ads"],
            "display_ads": ["Google Display Network", "LinkedIn Ads"],
            "content_marketing": ["Blog", "Whitepapers", "Webinars"],
            "influencer_marketing": ["Micro-influencers", "Industry experts"],
        }
        self.campaign_metrics = {
            "total_campaigns": 0,
            "average_conversion_rate": 0.0,
            "total_leads": 0,
            "total_revenue": 0.0,
            "campaign_success_rate": 0.0,
        }
        self.brand_health = {
            "brand_awareness_score": 0,
            "brand_sentiment_score": 50,
            "brand_consistency_score": 0,
            "market_position": "emerging",
            "customer_perception": {},
        }
        self.market_trends = []
        self.budget_allocation = {
            "total_budget": 100000,
            "allocated_budget": 0,
            "channels": {},
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
        elif message.message_type == MessageType.DATA_RESPONSE:
            return await self._handle_data_response(message, company_state)
        elif message.message_type == MessageType.APPROVAL_RESPONSE:
            return await self._handle_approval_response(message, company_state)

        return None

    async def _handle_status_report(
        self, message: Message, company_state: CompanyState
    ) -> Optional[Message]:
        sender = message.sender
        report_data = message.content

        marketing_analysis_prompt = f"""
        作为CMO，分析来自{sender.value}的营销状态报告：

        报告数据：{json.dumps(report_data, indent=2)}

        当前活动指标：{json.dumps(self.campaign_metrics, indent=2)}
        品牌健康度：{json.dumps(self.brand_health, indent=2)}
        市场趋势：{json.dumps(self.market_trends[-5:], indent=2) if self.market_trends else "无趋势数据"}

        提供营销指导和建议：
        1. 对营销目标的达成情况
        2. 渠道有效性分析
        3. 品牌情感观察
        4. 市场机会评估
        5. 推荐行动

        以JSON格式响应，包含：
        - insights：关键洞察列表
        - performance_score：0-100营销绩效评分
        - channel_recommendations：推荐的渠道调整列表
        - action_items：推荐行动列表
        - priority_adjustments：需要的优先级变更
        """

        try:
            response = await self.llm.ainvoke(
                [HumanMessage(content=marketing_analysis_prompt)]
            )
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
                    "type": "marketing_review",
                    "review": guidance,
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
                    "note": "已收到并审查营销报告",
                },
            )

    async def _handle_task_assignment(
        self, message: Message, company_state: CompanyState
    ) -> Optional[Message]:
        task_data = message.content.get("task", {})
        task_title = task_data.get("title", "")

        if "marketing" in task_title.lower() or "campaign" in task_title.lower():
            return CommunicationProtocol.create_task_assignment(
                assigner=self.role,
                assignee=AgentRole.OPERATIONS,
                task=Task(
                    task_id=create_task_id(),
                    title=task_title,
                    description=task_data.get("description", ""),
                    assigned_to=AgentRole.OPERATIONS,
                    assigned_by=self.role,
                    priority=Priority(task_data.get("priority", "medium")),
                    deadline=datetime.fromisoformat(task_data.get("deadline"))
                    if task_data.get("deadline")
                    else None,
                    metadata={"marketing": True},
                ),
            )

        return None

    async def _handle_data_request(
        self, message: Message, company_state: CompanyState
    ) -> Message:
        request_type = message.content.get("request_type", "")

        if request_type == "marketing_channels":
            return CommunicationProtocol.create_message(
                sender=self.role,
                recipient=message.sender,
                message_type=MessageType.DATA_RESPONSE,
                content={
                    "request_id": message.content.get("request_id"),
                    "data": self.marketing_channels,
                    "data_type": "marketing_channels",
                },
            )
        elif request_type == "campaign_metrics":
            return CommunicationProtocol.create_message(
                sender=self.role,
                recipient=message.sender,
                message_type=MessageType.DATA_RESPONSE,
                content={
                    "request_id": message.content.get("request_id"),
                    "data": self.campaign_metrics,
                    "data_type": "campaign_metrics",
                },
            )
        elif request_type == "brand_health":
            return CommunicationProtocol.create_message(
                sender=self.role,
                recipient=message.sender,
                message_type=MessageType.DATA_RESPONSE,
                content={
                    "request_id": message.content.get("request_id"),
                    "data": self.brand_health,
                    "data_type": "brand_health",
                },
            )
        elif request_type == "market_trends":
            return CommunicationProtocol.create_message(
                sender=self.role,
                recipient=message.sender,
                message_type=MessageType.DATA_RESPONSE,
                content={
                    "request_id": message.content.get("request_id"),
                    "data": self.market_trends,
                    "data_type": "market_trends",
                },
            )
        elif request_type == "budget_allocation":
            return CommunicationProtocol.create_message(
                sender=self.role,
                recipient=message.sender,
                message_type=MessageType.DATA_RESPONSE,
                content={
                    "request_id": message.content.get("request_id"),
                    "data": self.budget_allocation,
                    "data_type": "budget_allocation",
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
        request_type = request_data.get("request_type", "unknown")

        if request_type == "campaign_approval":
            return await self._evaluate_campaign_approval(message, company_state)
        elif request_type == "budget_allocation":
            return await self._evaluate_budget_allocation(message, company_state)
        elif request_type == "marketing_strategy":
            return await self._evaluate_marketing_strategy(message, company_state)

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

    async def _handle_alert(
        self, message: Message, company_state: CompanyState
    ) -> Optional[Message]:
        alert_data = message.content

        if alert_data.get("alert_type") in [
            "marketing_crisis",
            "brand_sentiment_negative",
            "campaign_underperformance",
        ]:
            return CommunicationProtocol.create_alert(
                sender=self.role,
                alert_type="marketing_incident",
                message=f"CMO处理：{alert_data.get('message', '检测到营销警报')}",
                severity=Priority.HIGH,
                recipient=AgentRole.OPERATIONS,
            )

        return None

    async def _handle_collaboration(
        self, message: Message, company_state: CompanyState
    ) -> Optional[Message]:
        content = message.content

        if content.get("type") == "marketing_input":
            return await self._process_marketing_input(message, company_state)

        return None

    async def _handle_data_response(
        self, message: Message, company_state: CompanyState
    ) -> Optional[Message]:
        data = message.content

        if "campaign_performance" in data:
            self._update_campaign_metrics(data["campaign_performance"])

        if "market_research" in data:
            self.market_trends.append(data["market_research"])

        return CommunicationProtocol.create_message(
            sender=self.role,
            recipient=message.sender,
            message_type=MessageType.COLLABORATION,
            content={
                "type": "marketing_data_received",
                "status": "已纳入",
                "next_action": "更新营销策略",
            },
        )

    async def _handle_approval_response(
        self, message: Message, company_state: CompanyState
    ) -> Optional[Message]:
        response_data = message.content
        decision = response_data.get("decision", {})

        if decision.get("approved"):
            return CommunicationProtocol.create_message(
                sender=self.role,
                recipient=message.sender,
                message_type=MessageType.COLLABORATION,
                content={
                    "type": "approval_confirmed",
                    "status": "ready_for_execution",
                    "next_steps": ["执行已批准的活动", "分配资源", "监控绩效"],
                },
            )

        return None

    async def _process_marketing_input(
        self, message: Message, company_state: CompanyState
    ) -> Message:
        input_data = message.content.get("data", {})

        integration_prompt = f"""
        作为CMO，将此营销输入整合到整体营销策略中：

        来自{message.sender.value}的输入：{json.dumps(input_data, indent=2)}
        当前营销计划：{json.dumps(self.campaign_metrics, indent=2)}
        品牌健康度：{json.dumps(self.brand_health, indent=2)}

        提供整合计划：
        1. 此输入如何影响当前营销策略
        2. 需要哪些活动调整
        3. 哪些渠道需要重新考虑
        4. 是否需要预算重新分配

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
                    "type": "marketing_integration",
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
        if "campaign" in task.title.lower() or "marketing" in task.title.lower():
            return await self._execute_marketing_campaign(task, company_state)
        elif "roi" in task.title.lower():
            return await self._calculate_marketing_roi(task, company_state)
        elif "strategy" in task.title.lower():
            return await self._execute_marketing_strategy(task, company_state)
        elif "brand" in task.title.lower():
            return await self._analyze_brand_health(task, company_state)
        elif "trend" in task.title.lower() or "market" in task.title.lower():
            return await self._monitor_market_trends(task, company_state)
        elif "budget" in task.title.lower():
            return await self._allocate_budget(task, company_state)
        elif "optimize" in task.title.lower():
            return await self._optimize_campaigns(task, company_state)

        return {
            "status": "completed",
            "result": "任务已由CMO处理",
            "timestamp": datetime.now().isoformat(),
        }

    async def _execute_marketing_campaign(
        self, task: Task, company_state: CompanyState
    ) -> Dict[str, Any]:
        campaign_prompt = f"""
        作为CMO，创建并执行营销活动计划：

        任务：{task.description}
        活动详情：{json.dumps(task.metadata.get("campaign_details", {}), indent=2)}
        当前市场状态：{json.dumps(company_state.get("market_data", {}), indent=2)}
        可用预算：{self.budget_allocation.get("total_budget", 100000)}
        目标受众：{company_state.get("user_feedback", [{}])[0] if company_state.get("user_feedback") else "未指定"}

        创建涵盖以下内容的全面活动计划：
        1. 活动目标和KPI
        2. 目标受众细分
        3. 渠道选择和组合
        4. 内容策略和信息传递
        5. 时间线和里程碑
        6. 按渠道划分的预算明细
        7. 成功指标和评估
        8. 风险缓解策略

        以JSON格式返回全面的活动计划。
        """

        try:
            response = await self.llm.ainvoke([HumanMessage(content=campaign_prompt)])
            content = (
                response.content
                if isinstance(response.content, str)
                else str(response.content)
            )
            campaign_plan = json.loads(content)

            self.campaign_metrics["total_campaigns"] += 1

            return {
                "status": "completed",
                "result": campaign_plan,
                "type": "marketing_campaign",
                "timestamp": datetime.now().isoformat(),
                "campaign_id": create_task_id(),
                "execution_steps": campaign_plan.get("timeline", []),
                "resource_requirements": campaign_plan.get("budget_breakdown", {}),
            }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def _calculate_marketing_roi(
        self, task: Task, company_state: CompanyState
    ) -> Dict[str, Any]:
        roi_prompt = f"""
        作为CMO，计算营销活动的ROI：

        任务：{task.description}
        活动数据：{json.dumps(company_state.get("campaign_data", {}), indent=2)}
        当前指标：{json.dumps(self.campaign_metrics, indent=2)}
        成本：{json.dumps(task.metadata.get("costs", {}), indent=2)}
        收入：{company_state.get("kpis", {}).get("revenue", 0)}

        执行全面的ROI分析：
        1. 活动ROI计算
        2. 按渠道的ROI比较
        3. 客户获取成本（CAC）分析
        4. 客户生命周期价值（LTV）比较
        5. 转化率优化机会
        6. 投资回报建议

        以JSON格式返回ROI分析。
        """

        try:
            response = await self.llm.ainvoke([HumanMessage(content=roi_prompt)])
            content = (
                response.content
                if isinstance(response.content, str)
                else str(response.content)
            )
            roi_analysis = json.loads(content)

            return {
                "status": "completed",
                "result": roi_analysis,
                "type": "roi_analysis",
                "timestamp": datetime.now().isoformat(),
                "overall_roi": roi_analysis.get("overall_roi", 0),
                "最优渠道": roi_analysis.get("best_performing_channel", "未知"),
                "optimization_recommendations": roi_analysis.get("recommendations", []),
            }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def _analyze_brand_health(
        self, task: Task, company_state: CompanyState
    ) -> Dict[str, Any]:
        brand_prompt = f"""
        作为CMO，分析当前品牌健康度：

        任务：{task.description}
        品牌数据：{json.dumps(company_state.get("brand_data", {}), indent=2)}
        用户反馈：{json.dumps(company_state.get("user_feedback", [])[:10], indent=2)}
        市场定位：{json.dumps(company_state.get("market_data", {}).get("positioning", {}), indent=2)}

        执行全面的品牌健康度分析：
        1. 品牌知晓度评估
        2. 品牌情感分析
        3. 品牌一致性评估
        4. 竞争定位
        5. 品牌资产计算
        6. 品牌强度评分（0-100）
        7. 改进领域
        8. 品牌增强建议

        以JSON格式返回品牌健康度分析。
        """

        try:
            response = await self.llm.ainvoke([HumanMessage(content=brand_prompt)])
            content = (
                response.content
                if isinstance(response.content, str)
                else str(response.content)
            )
            brand_analysis = json.loads(content)

            self.brand_health.update(brand_analysis.get("brand_health_metrics", {}))

            return {
                "status": "completed",
                "result": brand_analysis,
                "type": "brand_health_analysis",
                "timestamp": datetime.now().isoformat(),
                "brand_score": brand_analysis.get("brand_strength_score", 0),
                "sentiment": brand_analysis.get("sentiment", "neutral"),
                "recommendations": brand_analysis.get("recommendations", []),
            }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def _monitor_market_trends(
        self, task: Task, company_state: CompanyState
    ) -> Dict[str, Any]:
        trends_prompt = f"""
        作为CMO，监控和分析市场趋势：

        任务：{task.description}
        市场数据：{json.dumps(company_state.get("market_data", {}), indent=2)}
        竞争对手活动：{json.dumps(company_state.get("competitor_data", {}), indent=2)}
        行业报告：{json.dumps(company_state.get("industry_reports", {}), indent=2)}

        执行全面的市场趋势分析：
        1. 新兴市场趋势
        2. 竞争对手营销策略
        3. 用户行为变化
        4. 渠道绩效趋势
        5. 市场机会和威胁
        6. 预测的市场变化
        7. 战略影响
        8. 推荐响应

        以JSON格式返回市场分析。
        """

        try:
            response = await self.llm.ainvoke([HumanMessage(content=trends_prompt)])
            content = (
                response.content
                if isinstance(response.content, str)
                else str(response.content)
            )
            market_analysis = json.loads(content)

            self.market_trends.append(
                {"analysis": market_analysis, "timestamp": datetime.now().isoformat()}
            )

            return {
                "status": "completed",
                "result": market_analysis,
                "type": "market_trends",
                "timestamp": datetime.now().isoformat(),
                "trends_identified": market_analysis.get("trends", [])[:10],
                "opportunities": market_analysis.get("opportunities", []),
                "threats": market_analysis.get("threats", []),
            }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def _allocate_budget(
        self, task: Task, company_state: CompanyState
    ) -> Dict[str, Any]:
        budget_prompt = f"""
        作为CMO，最优分配营销预算：

        任务：{task.description}
        总预算：{self.budget_allocation.get("total_budget", 100000)}
        当前分配：{json.dumps(self.budget_allocation.get("channels", {}), indent=2)}
        活动计划：{json.dumps(task.metadata.get("campaign_plans", {}), indent=2)}
        ROI历史：{json.dumps(self.campaign_metrics, indent=2)}

        创建最优预算分配：
        1. 按渠道预算分配
        2. 渠道优先级排名
        3. 按渠道预期ROI
        4. 应急储备
        5. 季度预算审查点
        6. 预算优化建议

        以JSON格式返回预算分配计划。
        """

        try:
            response = await self.llm.ainvoke([HumanMessage(content=budget_prompt)])
            content = (
                response.content
                if isinstance(response.content, str)
                else str(response.content)
            )
            budget_allocation = json.loads(content)

            self.budget_allocation["allocated_budget"] = sum(
                budget_allocation.get("channel_allocations", {}).values()
            )

            return {
                "status": "completed",
                "result": budget_allocation,
                "type": "budget_allocation",
                "timestamp": datetime.now().isoformat(),
                "total_budget": self.budget_allocation["total_budget"],
                "channel_allocations": budget_allocation.get("channel_allocations", {}),
                "optimization_score": budget_allocation.get("optimization_score", 0),
            }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def _optimize_campaigns(
        self, task: Task, company_state: CompanyState
    ) -> Dict[str, Any]:
        optimize_prompt = f"""
        作为CMO，优化营销活动：

        任务：{task.description}
        活动数据：{json.dumps(company_state.get("campaign_data", {}), indent=2)}
        当前绩效：{json.dumps(self.campaign_metrics, indent=2)}
        预算约束：{json.dumps(self.budget_allocation, indent=2)}
        渠道绩效：{json.dumps(task.metadata.get("channel_metrics", {}), indent=2)}

        制定全面的优化策略：
        1. 绩效不佳的活动分析
        2. 渠道组合优化
        3. 预算重新分配建议
        4. 内容优化建议
        5. 时机和频率调整
        6. 测试和学习建议
        7. 预期优化影响
        8. 实施路线图

        以JSON格式返回优化计划。
        """

        try:
            response = await self.llm.ainvoke([HumanMessage(content=optimize_prompt)])
            content = (
                response.content
                if isinstance(response.content, str)
                else str(response.content)
            )
            optimization_plan = json.loads(content)

            return {
                "status": "completed",
                "result": optimization_plan,
                "type": "campaign_optimization",
                "timestamp": datetime.now().isoformat(),
                "optimization_score": optimization_plan.get("expected_impact", {}).get(
                    "improvement_percentage", 0
                ),
                "immediate_actions": optimization_plan.get("immediate_actions", []),
                "long_term_changes": optimization_plan.get("long_term_changes", []),
            }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def generate_report(self, company_state: CompanyState) -> Dict[str, Any]:
        report_prompt = f"""
        作为CMO，生成综合营销仪表板报告：

        营销绩效：{json.dumps(self.campaign_metrics, indent=2)}
        品牌健康度：{json.dumps(self.brand_health, indent=2)}
        市场趋势：{json.dumps(self.market_trends[-10:], indent=2) if self.market_trends else "无趋势"}
        预算状态：{json.dumps(self.budget_allocation, indent=2)}
        KPI：{json.dumps(company_state.get("kpis", {}), indent=2)}

        生成涵盖以下内容的综合营销仪表板：
        1. 执行摘要
        2. 活动绩效概述
        3. 渠道有效性
        4. 品牌健康度指标
        5. 市场趋势摘要
        6. 预算利用率
        7. ROI分析
        8. 用户获取洞察
        9. 关键挑战
        10. 建议
        11. 下季度优先事项

        格式化为专业营销仪表板报告。
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
                "report_type": "marketing_dashboard",
                "timestamp": datetime.now().isoformat(),
                "data": report,
                "marketing_health_score": self._calculate_marketing_health_score(),
                "next_actions": self._determine_marketing_next_actions(report),
            }
        except Exception as e:
            return {
                "agent_role": self.role.value,
                "report_type": "marketing_dashboard",
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "status": "report_generation_failed",
            }

    def _update_campaign_metrics(self, performance_data: Dict[str, Any]):
        if "conversion_rate" in performance_data:
            self.campaign_metrics["average_conversion_rate"] = performance_data[
                "conversion_rate"
            ]

        if "total_leads" in performance_data:
            self.campaign_metrics["total_leads"] += performance_data["total_leads"]

        if "revenue_generated" in performance_data:
            self.campaign_metrics["total_revenue"] += performance_data[
                "revenue_generated"
            ]

        if "campaign_success" in performance_data:
            self.campaign_metrics["campaign_success_rate"] = performance_data[
                "campaign_success"
            ]

    def _calculate_marketing_health_score(self) -> float:
        weights = {
            "conversion_rate": 0.25,
            "campaign_success": 0.25,
            "brand_health": 0.25,
            "roi": 0.25,
        }

        scores = {
            "conversion_rate": self.campaign_metrics.get("average_conversion_rate", 0)
            * 100,
            "campaign_success": self.campaign_metrics.get("campaign_success_rate", 0)
            * 100,
            "brand_health": self.brand_health.get("brand_sentiment_score", 50),
            "roi": self.campaign_metrics.get("roi_score", 50),
        }

        return sum(weights[metric] * scores[metric] for metric in weights)

    def _determine_marketing_next_actions(self, report: Dict[str, Any]) -> List[str]:
        recommendations = report.get("recommendations", [])
        if isinstance(recommendations, list):
            return recommendations[:5]
        return []
