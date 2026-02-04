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



class CFOAgent(BaseAgent):
    def __init__(self):
        capabilities = [
            "财务建模",
            "预算规划",
            "成本分析",
            "投资规划",
            "融资",
            "财务合规",
            "税务筹划",
            "盈利能力分析",
            "现金流预测",
            "ROI分析",
        ]
        super().__init__(AgentRole.CFO, capabilities)
        default_model_config = app_config.llm.models.get(
            app_config.llm.default_model,
            ModelConfig(
                name=app_config.llm.default_model,
                provider="openai",
                api_key=None,
                config={},
            ),
        )
        agent_config = app_config.agents.get("cfo", AgentConfig())
        self.llm = ChatOpenAI(
            model=app_config.llm.default_model,
            temperature=agent_config.temperature if agent_config.temperature != 0.3 else default_model_config.config.get("temperature", 0.3),
        )
        self.budget_allocation = {
            "total_budget": 1000000,
            "allocated_budget": 0,
            "departments": {
                "R&D": {"budget": 300000, "allocated": 0},
                "Marketing": {"budget": 200000, "allocated": 0},
                "Operations": {"budget": 150000, "allocated": 0},
                "Sales": {"budget": 150000, "allocated": 0},
                "CustomerSupport": {"budget": 100000, "allocated": 0},
                "HR": {"budget": 100000, "allocated": 0},
            },
        }
        self.financial_metrics = {
            "revenue": 0.0,
            "cost_of_revenue": 0.0,
            "gross_profit": 0.0,
            "operating_expenses": 0.0,
            "net_income": 0.0,
            "cash_on_hand": 1000000,
            "burn_rate": 50000,
            "runway_months": 20,
        }
        self.funding_plans = {
            "current_round": None,
            "target_round": "angel",
            "target_valuation": 5000000,
            "amount_raised": 0,
            "investors": [],
            "valuation_models": {},
        }
        self.cost_metrics = {
            "ai_compute_costs": 0.0,
            "cloud_services": 0.0,
            "model_api_calls": 0.0,
            "office_expenses": 0.0,
            "personnel_costs": 0.0,
            "marketing_costs": 0.0,
        }
        self.internal_cost_allocation = {
            "cost_centers": {},
            "resource_billing": {},
            "efficiency_targets": {},
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

        financial_analysis_prompt = f"""
        作为CFO，分析来自{sender.value}的财务状态报告：

        报告数据：{json.dumps(report_data, indent=2)}

        当前预算分配：{json.dumps(self.budget_allocation, indent=2)}
        财务指标：{json.dumps(self.financial_metrics, indent=2)}
        成本指标：{json.dumps(self.cost_metrics, indent=2)}

        提供财务指导和决策：
        1. 关键财务见解和趋势
        2. 预算执行情况和偏差分析
        3. 成本控制建议
        4. 现金流预测.update
        5. 风险评估和缓解措施

        以JSON格式响应：
        - insights: 关键洞察列表
        - budget_variance: 预算偏差百分比
        - cash_flow_projection: 现金流预测（下个月）
        - recommendations: 建议的操作
        - risk_level: 风险等级（低/中/高）
        """

        try:
            response = await self.llm.ainvoke(
                [HumanMessage(content=financial_analysis_prompt)]
            )
            content = (
                response.content
                if isinstance(response.content, str)
                else str(response.content)
            )
            analysis = json.loads(content)

            return CommunicationProtocol.create_message(
                sender=self.role,
                recipient=sender,
                message_type=MessageType.COLLABORATION,
                content={
                    "type": "financial_review",
                    "analysis": analysis,
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
                    "error": str(e),
                },
            )

    async def _handle_task_assignment(
        self, message: Message, company_state: CompanyState
    ) -> Optional[Message]:
        task_data = message.content.get("task", {})
        task_title = task_data.get("title", "")

        if "budget" in task_title.lower() or "financial" in task_title.lower():
            return await self._process_financial_task(task_data, company_state)
        elif "cost" in task_title.lower() or "expense" in task_title.lower():
            return await self._process_cost_analysis_task(task_data, company_state)
        elif "investment" in task_title.lower() or "funding" in task_title.lower():
            return await self._process_investment_task(task_data, company_state)
        elif "roi" in task_title.lower() or "profitability" in task_title.lower():
            return await self._process_profitability_task(task_data, company_state)

        return None

    async def _process_financial_task(
        self, task_data: Dict[str, Any], company_state: CompanyState
    ) -> Optional[Message]:
        task_title = task_data.get("title", "")
        task_description = task_data.get("description", "")

        if "annual_budget" in task_title.lower():
            result = await self._execute_annual_budget_planning(
                task_data, company_state
            )
        elif "monthly_forecast" in task_title.lower():
            result = await self._execute_cash_flow_forecasting(task_data, company_state)
        elif "budget_allocation" in task_title.lower():
            result = await self._execute_budget_allocation(task_data, company_state)
        else:
            result = await self._execute_generic_financial_analysis(
                task_data, company_state
            )

        return CommunicationProtocol.create_message(
            sender=self.role,
            recipient=task_data.get("assigned_by", AgentRole.CEO),
            message_type=MessageType.STATUS_REPORT,
            content={
                "task_reference": task_data.get("task_id"),
                "result": result,
                "processed_by": "CFO",
            },
        )

    async def _process_cost_analysis_task(
        self, task_data: Dict[str, Any], company_state: CompanyState
    ) -> Optional[Message]:
        result = await self._execute_cost_analysis(task_data, company_state)

        return CommunicationProtocol.create_message(
            sender=self.role,
            recipient=task_data.get("assigned_by", AgentRole.CEO),
            message_type=MessageType.STATUS_REPORT,
            content={
                "task_reference": task_data.get("task_id"),
                "result": result,
                "processed_by": "CFO",
            },
        )

    async def _process_investment_task(
        self, task_data: Dict[str, Any], company_state: CompanyState
    ) -> Optional[Message]:
        result = await self._execute_investment_planning(task_data, company_state)

        return CommunicationProtocol.create_message(
            sender=self.role,
            recipient=task_data.get("assigned_by", AgentRole.CEO),
            message_type=MessageType.STATUS_REPORT,
            content={
                "task_reference": task_data.get("task_id"),
                "result": result,
                "processed_by": "CFO",
            },
        )

    async def _process_profitability_task(
        self, task_data: Dict[str, Any], company_state: CompanyState
    ) -> Optional[Message]:
        result = await self._execute_profitability_analysis(task_data, company_state)

        return CommunicationProtocol.create_message(
            sender=self.role,
            recipient=task_data.get("assigned_by", AgentRole.CEO),
            message_type=MessageType.STATUS_REPORT,
            content={
                "task_reference": task_data.get("task_id"),
                "result": result,
                "processed_by": "CFO",
            },
        )

    async def _handle_data_request(
        self, message: Message, company_state: CompanyState
    ) -> Message:
        request_type = message.content.get("request_type", "")

        if request_type == "budget_allocation":
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
        elif request_type == "financial_metrics":
            return CommunicationProtocol.create_message(
                sender=self.role,
                recipient=message.sender,
                message_type=MessageType.DATA_RESPONSE,
                content={
                    "request_id": message.content.get("request_id"),
                    "data": self.financial_metrics,
                    "data_type": "financial_metrics",
                },
            )
        elif request_type == "cost_metrics":
            return CommunicationProtocol.create_message(
                sender=self.role,
                recipient=message.sender,
                message_type=MessageType.DATA_RESPONSE,
                content={
                    "request_id": message.content.get("request_id"),
                    "data": self.cost_metrics,
                    "data_type": "cost_metrics",
                },
            )
        elif request_type == "funding_plans":
            return CommunicationProtocol.create_message(
                sender=self.role,
                recipient=message.sender,
                message_type=MessageType.DATA_RESPONSE,
                content={
                    "request_id": message.content.get("request_id"),
                    "data": self.funding_plans,
                    "data_type": "funding_plans",
                },
            )
        elif request_type == "internal_cost_allocation":
            return CommunicationProtocol.create_message(
                sender=self.role,
                recipient=message.sender,
                message_type=MessageType.DATA_RESPONSE,
                content={
                    "request_id": message.content.get("request_id"),
                    "data": self.internal_cost_allocation,
                    "data_type": "internal_cost_allocation",
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

        if request_type == "budget_allocation":
            return await self._evaluate_budget_allocation_request(
                message, company_state
            )
        elif request_type == "capital_expenditure":
            return await self._evaluate_capital_expenditure_request(
                message, company_state
            )
        elif request_type == "investment_approval":
            return await self._evaluate_investment_approval_request(
                message, company_state
            )
        elif request_type == "expense_reimbursement":
            return await self._evaluate_expense_reimbursement_request(
                message, company_state
            )

        return CommunicationProtocol.create_message(
            sender=self.role,
            recipient=message.sender,
            message_type=MessageType.APPROVAL_RESPONSE,
            content={
                "request_id": request_data.get("request_id"),
                "approved": False,
                "reasoning": f"Unknown request type: {request_type}",
            },
        )

    async def _handle_alert(
        self, message: Message, company_state: CompanyState
    ) -> Optional[Message]:
        alert_data = message.content
        alert_type = alert_data.get("alert_type", "")

        if alert_type == "budget_overrun":
            return CommunicationProtocol.create_message(
                sender=self.role,
                recipient=AgentRole.CEO,
                message_type=MessageType.STATUS_REPORT,
                content={
                    "alert_type": "budget_overrun_detected",
                    "message": f"CFO Alert: Budget overrun detected for {alert_data.get('department', 'unknown department')}",
                    "severity": alert_data.get("severity", "high"),
                    "analysis": self._analyze_budget_overrun(alert_data),
                    "recommended_actions": self._generate_budget_overrun_actions(
                        alert_data
                    ),
                },
            )
        elif alert_type == "cash_flow_risk":
            return CommunicationProtocol.create_message(
                sender=self.role,
                recipient=AgentRole.CEO,
                message_type=MessageType.ALERT,
                content={
                    "alert_type": "cash_flow_warning",
                    "message": f"CFO Alert: Cash flow runway below threshold: {alert_data.get('runway', 'unknown')} months",
                    "severity": "critical",
                    "financial_impact": self._assess_cash_flow_impact(alert_data),
                    "mitigation_steps": self._generate_cash_flow_mitigations(
                        alert_data
                    ),
                },
            )
        elif alert_type == "high_cost_alert":
            return CommunicationProtocol.create_message(
                sender=self.role,
                recipient=AgentRole.OPERATIONS,
                message_type=MessageType.COLLABORATION,
                content={
                    "alert_type": "cost_optimization_recommended",
                    "message": f"CFO: Cost optimization recommended - {alert_data.get('cost_category', 'unknown')}",
                    "severity": alert_data.get("severity", "medium"),
                    "savings_potential": self._estimate_cost_savings(alert_data),
                    "optimization_strategies": self._generate_cost_optimization_strategies(
                        alert_data
                    ),
                },
            )

        return None

    async def _handle_collaboration(
        self, message: Message, company_state: CompanyState
    ) -> Optional[Message]:
        content = message.content

        if content.get("type") == "financial_consultation":
            return await self._provide_financial_consultation(message, company_state)

        return None

    async def _provide_financial_consultation(
        self, message: Message, company_state: CompanyState
    ) -> Message:
        question = message.content.get("question", "")
        context = message.content.get("context", {})

        consultation_prompt = f"""
        作为CFO，提供财务咨询服务：

        问题：{question}
        背景信息：{json.dumps(context, indent=2)}
        当前财务状态：{json.dumps(self.financial_metrics, indent=2)}
        当前预算：{json.dumps(self.budget_allocation, indent=2)}

        提供财务专家建议，涵盖：
        1. 财务可行性分析
        2. 成本效益评估
        3. 投资回报率计算
        4. 现金流影响评估
        5. 风险评估和缓解措施
        6. 长期财务影响

        以JSON格式详细财务咨询 responds。
        """

        try:
            response = await self.llm.ainvoke(
                [HumanMessage(content=consultation_prompt)]
            )
            content = (
                response.content
                if isinstance(response.content, str)
                else str(response.content)
            )
            consultation = json.loads(content)

            return CommunicationProtocol.create_message(
                sender=self.role,
                recipient=message.sender,
                message_type=MessageType.COLLABORATION,
                content={
                    "type": "financial_consultation_response",
                    "consultation": consultation,
                    "consultant": "CFO",
                },
            )
        except Exception as e:
            return CommunicationProtocol.create_message(
                sender=self.role,
                recipient=message.sender,
                message_type=MessageType.COLLABORATION,
                content={
                    "type": "financial_consultation_response",
                    "error": str(e),
                    "status": "consultation_failed",
                },
            )

    async def execute_task(
        self, task: Task, company_state: CompanyState
    ) -> Dict[str, Any]:
        task_title_lower = task.title.lower()

        if "budget" in task_title_lower:
            if "annual" in task_title_lower:
                return await self._execute_annual_budget_planning(task, company_state)
            elif "monthly" in task_title_lower or "forecast" in task_title_lower:
                return await self._execute_cash_flow_forecasting(task, company_state)
            else:
                return await self._execute_budget_allocation(task, company_state)
        elif "cost" in task_title_lower:
            return await self._execute_cost_analysis(task, company_state)
        elif "roi" in task_title_lower or "profitability" in task_title_lower:
            return await self._execute_profitability_analysis(task, company_state)
        elif "investment" in task_title_lower or "funding" in task_title_lower:
            return await self._execute_investment_planning(task, company_state)
        elif "valuation" in task_title_lower or "pitch" in task_title_lower:
            return await self._execute_valuation_modeling(task, company_state)

        return {
            "status": "completed",
            "result": "Task processed by CFO",
            "timestamp": datetime.now().isoformat(),
        }

    async def _execute_annual_budget_planning(
        self, task: Task, company_state: CompanyState
    ) -> Dict[str, Any]:
        planning_prompt = f"""
        作为CFO，制定公司年度预算计划：

        任务：{task.description}
        公司战略目标：{json.dumps(company_state.get("strategic_goals", {}), indent=2)}
        当前KPI：{json.dumps(company_state.get("kpis", {}), indent=2)}
        市场数据：{json.dumps(company_state.get("market_data", {}), indent=2)}

        制定全面的年度预算计划，涵盖：
        1. 收入预测（按季度）
        2. 各部门预算分配
        3. 运营成本预算（固定成本 vs 可变成本）
        4. 资本支出计划
        5. 现金流预测（月度）
        6. 盈亏平衡点分析
        7. 预算风险管理

        以JSON格式返回完整的预算计划。
        """

        try:
            response = await self.llm.ainvoke([HumanMessage(content=planning_prompt)])
            content = (
                response.content
                if isinstance(response.content, str)
                else str(response.content)
            )
            budget_plan = json.loads(content)

            self.budget_allocation = budget_plan.get(
                "budget_allocation", self.budget_allocation
            )

            return {
                "status": "completed",
                "result": budget_plan,
                "type": "annual_budget_plan",
                "timestamp": datetime.now().isoformat(),
                "next_steps": [
                    "向CEO提交预算计划供审批",
                    "与各部门主管沟通预算分配",
                    "建立预算追踪机制",
                    "设置月度预算审查会议",
                ],
            }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def _execute_cash_flow_forecasting(
        self, task: Task, company_state: CompanyState
    ) -> Dict[str, Any]:
        forecasting_prompt = f"""
        作为CFO，进行月度现金流预测：

        任务：{task.description}
        当前财务指标：{json.dumps(self.financial_metrics, indent=2)}
        历史现金流数据：{json.dumps(company_state.get("historical_cashflow", {}), indent=2)}
        计划中的支出：{json.dumps(task.metadata.get("planned_expenses", {}), indent=2)}

        创建详细的现金流预测模型：
        1. 期初现金余额
        2. 预计收入（按来源细分）
        3. 预计现金支出（运营、资本、融资）
        4. 期末现金余额
        5. 现金流敏感性分析
        6. 现金流缺口预测（如有）
        7. 现金管理建议

        以JSON格式返回预测结果。
        """

        try:
            response = await self.llm.ainvoke(
                [HumanMessage(content=forecasting_prompt)]
            )
            content = (
                response.content
                if isinstance(response.content, str)
                else str(response.content)
            )
            forecast = json.loads(content)

            self.financial_metrics["runway_months"] = forecast.get(
                "runway_months", self.financial_metrics["runway_months"]
            )

            return {
                "status": "completed",
                "result": forecast,
                "type": "cash_flow_forecast",
                "timestamp": datetime.now().isoformat(),
                "key_metrics": {
                    "projected_end_cash": forecast.get("projected_end_cash", 0),
                    "runway_months": forecast.get("runway_months", 0),
                    "cash_gap_months": forecast.get("cash_gap_months", 0),
                },
            }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def _execute_budget_allocation(
        self, task: Task, company_state: CompanyState
    ) -> Dict[str, Any]:
        allocation_prompt = f"""
        作为CFO，进行预算分配决策：

        任务：{task.description}
        需求部门：{task.metadata.get("department", "unknown")}
        预算申请：{json.dumps(task.metadata.get("budget_request", {}), indent=2)}
        公司总体预算约束：{json.dumps(self.budget_allocation.get("total_budget", {}), indent=2)}

        分析预算请求并做出决策：
        1. 申请合理性评估
        2. 与战略目标的对齐程度
        3. ROI预测
        4. 成本效益分析
        5. 建议的预算额度（可能修改原始申请）
        6. 附带条件（如KPI目标）

        以JSON格式返回预算分配决策。
        """

        try:
            response = await self.llm.ainvoke([HumanMessage(content=allocation_prompt)])
            content = (
                response.content
                if isinstance(response.content, str)
                else str(response.content)
            )
            allocation_decision = json.loads(content)

            return {
                "status": "completed",
                "result": allocation_decision,
                "type": "budget_allocation",
                "timestamp": datetime.now().isoformat(),
                "recommendation": allocation_decision.get(
                    "recommended_allocation", "pending"
                ),
            }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def _execute_cost_analysis(
        self, task: Task, company_state: CompanyState
    ) -> Dict[str, Any]:
        analysis_prompt = f"""
        作为CFO，进行成本分析：

        任务：{task.description}
        成本类别：{task.metadata.get("cost_category", "total")}
        时间范围：{task.metadata.get("time_range", "last_30_days")}
        当前成本指标：{json.dumps(self.cost_metrics, indent=2)}
        收入数据：{json.dumps(self.financial_metrics.get("revenue", 0), indent=2)}

        进行全面的成本分析：
        1. 成本结构分解（固定成本、可变成本、边际成本）
        2. 成本驱动因素识别
        3. 与行业基准的比较
        4. 成本优化机会识别
        5. 效率比率分析（成本/收入、人力成本/产出）
        6. 建议的优化措施

        以JSON格式返回成本分析报告。
        """

        try:
            response = await self.llm.ainvoke([HumanMessage(content=analysis_prompt)])
            content = (
                response.content
                if isinstance(response.content, str)
                else str(response.content)
            )
            cost_analysis = json.loads(content)

            self.cost_metrics = cost_analysis.get("optimized_costs", self.cost_metrics)

            return {
                "status": "completed",
                "result": cost_analysis,
                "type": "cost_analysis",
                "timestamp": datetime.now().isoformat(),
                "key_findings": cost_analysis.get("key_findings", []),
                "optimization_recommendations": cost_analysis.get(
                    "optimization_recommendations", []
                ),
            }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def _execute_profitability_analysis(
        self, task: Task, company_state: CompanyState
    ) -> Dict[str, Any]:
        analysis_prompt = f"""
        作为CFO，进行盈利能力和ROI分析：

        任务：{task.description}
        分析对象：{task.metadata.get("product_line", "company_wide")}
        当前财务指标：{json.dumps(self.financial_metrics, indent=2)}
        客户数据：{json.dumps(company_state.get("customer_data", {}), indent=2)}
        产品数据：{json.dumps(company_state.get("product_data", {}), indent=2)}

        进行全面的盈利能力分析：
        1. 各产品线/功能模块的收入与成本
        2. 毛利率和净利率分析
        3. 边际贡献分析
        4. 客户获取成本（CAC）与客户生命周期价值（LTV）
        5. ROI计算
        6. 盈利能力驱动因素识别
        7. 不盈利产品的建议（持续/改进/终止）

        以JSON格式返回盈利能力分析报告。
        """

        try:
            response = await self.llm.ainvoke([HumanMessage(content=analysis_prompt)])
            content = (
                response.content
                if isinstance(response.content, str)
                else str(response.content)
            )
            profitability_analysis = json.loads(content)

            return {
                "status": "completed",
                "result": profitability_analysis,
                "type": "profitability_analysis",
                "timestamp": datetime.now().isoformat(),
                "key_metrics": {
                    "overall_margin": profitability_analysis.get("overall_margin", 0),
                    "top_performers": profitability_analysis.get("top_performers", []),
                    "underperformers": profitability_analysis.get(
                        "underperformers", []
                    ),
                },
            }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def _execute_investment_planning(
        self, task: Task, company_state: CompanyState
    ) -> Dict[str, Any]:
        planning_prompt = f"""
        作为CFO，制定投融资计划：

        任务：{task.description}
        资金需求：{task.metadata.get("funding_amount", "unknown")}
        资金用途用途：{task.metadata.get("use_of_funds", "unknown")}
        当前融资计划：{json.dumps(self.funding_plans, indent=2)}
        市场条件：{json.dumps(company_state.get("market_conditions", {}), indent=2)}

        制定完整的投融资计划：
        1. 融资路径选择（天使轮、A轮、B轮等）
        2. 目标估值范围
        3. 投资者类型（VC、angel、战略投资者）
        4. 融资时间表
        5. 估值建模（DCF、可比公司分析、先例交易）
        6. 资金使用计划（详细到各季度）
        7. 融资风险和谈判策略

        以JSON格式返回完整的投融资计划。
        """

        try:
            response = await self.llm.ainvoke([HumanMessage(content=planning_prompt)])
            content = (
                response.content
                if isinstance(response.content, str)
                else str(response.content)
            )
            investment_plan = json.loads(content)

            self.funding_plans = investment_plan.get("funding_plan", self.funding_plans)

            return {
                "status": "completed",
                "result": investment_plan,
                "type": "investment_plan",
                "timestamp": datetime.now().isoformat(),
                "recommended_actions": investment_plan.get("recommended_actions", []),
                "估值_model": investment_plan.get("valuation_model", {}),
            }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def _execute_valuation_modeling(
        self, task: Task, company_state: CompanyState
    ) -> Dict[str, Any]:
        modeling_prompt = f"""
        作为CFO，进行公司估值建模：

        任务：{task.description}
        估值目的：{task.metadata.get("valuation_purpose", "fundraising")}
        当前财务数据：{json.dumps(self.financial_metrics, indent=2)}
        历史财务数据：{json.dumps(company_state.get("historical_financials", {}), indent=2)}
        市场数据：{json.dumps(company_state.get("market_data", {}), indent=2)}

        使用多种方法进行估值建模：
        1. DCF（现金流折现）法估值
        2. 可比公司分析（Comps）
        3. 先例交易分析（Precedents）
        4. 风险投资法（VC Method）
        5. 分步定价法（Berkus Method）- 适用于早期

        提供估值范围、关键假设、敏感性分析。

        以JSON格式返回完整的估值报告。
        """

        try:
            response = await self.llm.ainvoke([HumanMessage(content=modeling_prompt)])
            content = (
                response.content
                if isinstance(response.content, str)
                else str(response.content)
            )
            valuation_report = json.loads(content)

            return {
                "status": "completed",
                "result": valuation_report,
                "type": "valuation_model",
                "timestamp": datetime.now().isoformat(),
                "valuation_ranges": valuation_report.get("valuation_ranges", {}),
                "recommended_valuation": valuation_report.get(
                    "recommended_valuation", {}
                ),
            }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def _execute_generic_financial_analysis(
        self, task: Task, company_state: CompanyState
    ) -> Dict[str, Any]:
        analysis_prompt = f"""
        作为CFO，进行通用财务分析：

        任务：{task.description}
        财务数据：{json.dumps(company_state.get("financial_data", {}), indent=2)}
        业务指标：{json.dumps(company_state.get("business_metrics", {}), indent=2)}

        提供综合性财务分析：
        1. 关键指标趋势
        2. 异常检测
        3. 相关性分析
        4. 建议的行动项

        以JSON格式返回分析结果。
        """

        try:
            response = await self.llm.ainvoke([HumanMessage(content=analysis_prompt)])
            content = (
                response.content
                if isinstance(response.content, str)
                else str(response.content)
            )
            analysis = json.loads(content)

            return {
                "status": "completed",
                "result": analysis,
                "type": "financial_analysis",
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def generate_report(self, company_state: CompanyState) -> Dict[str, Any]:
        report_prompt = f"""
        作为CFO，生成综合财务报告：

        当前财务指标：{json.dumps(self.financial_metrics, indent=2)}
        预算执行情况：{json.dumps(self.budget_allocation, indent=2)}
        成本分析：{json.dumps(self.cost_metrics, indent=2)}
        筹资计划：{json.dumps(self.funding_plans, indent=2)}

        生成财务仪表板报告，包含：
        1. 执行摘要
        2. 财务状况概览（资产负债、利润、现金流）
        3. 预算与实际对比
        4. 成本结构分析
        5. 盈利能力指标
        6. 现金流预测
        7. 财务风险评估
        8. 管理层建议和行动项

        以专业财务报告格式呈现。
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
                "report_type": "financial_dashboard",
                "timestamp": datetime.now().isoformat(),
                "data": report,
                "financial_health_score": self._calculate_financial_health_score(),
            }
        except Exception as e:
            return {
                "agent_role": self.role.value,
                "report_type": "financial_dashboard",
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "status": "report_generation_failed",
            }

    def _analyze_budget_overrun(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        department = alert_data.get("department", "unknown")
        overrun_amount = alert_data.get("overrun_amount", 0)
        budget = (
            self.budget_allocation.get("departments", {})
            .get(department, {})
            .get("budget", 0)
        )

        return {
            "department": department,
            "budget": budget,
            "overrun_amount": overrun_amount,
            "overrun_percentage": (overrun_amount / budget * 100) if budget > 0 else 0,
            "severity": "high" if overrun_amount / budget > 0.1 else "medium",
        }

    def _generate_budget_overrun_actions(self, alert_data: Dict[str, Any]) -> List[str]:
        department = alert_data.get("department", "unknown")
        return [
            f"立即审查{department}部门的所有支出",
            "识别非必要支出并削减",
            "与部门主管召开紧急会议",
            "评估是否需要从其他部门重新分配预算",
            "更新月度现金流预测",
        ]

    def _assess_cash_flow_impact(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        runway = alert_data.get("runway", 12)
        burn_rate = self.financial_metrics.get("burn_rate", 50000)

        return {
            "current_runway": runway,
            "burn_rate": burn_rate,
            "cash_on_hand": self.financial_metrics.get("cash_on_hand", 0),
            "risk_level": "critical"
            if runway < 6
            else "high"
            if runway < 12
            else "medium",
            "warning_signs": self._identify_cash_flow_warning_signs(runway),
        }

    def _identify_cash_flow_warning_signs(self, runway: int) -> List[str]:
        warnings = []
        if runway < 6:
            warnings.append("严重：现金储备不足6个月")
        if runway < 12:
            warnings.append("警告：现金储备不足12个月")
        if self.financial_metrics.get("burn_rate", 0) > 100000:
            warnings.append("高烧速率：每月支出超过$100K")
        if self.financial_metrics.get("revenue", 0) < self.financial_metrics.get(
            "burn_rate", 0
        ):
            warnings.append("负现金流：收入不足以覆盖支出")
        return warnings

    def _generate_cash_flow_mitigations(self, alert_data: Dict[str, Any]) -> List[str]:
        runway = alert_data.get("runway", 12)
        mitigations = []

        if runway < 6:
            mitigations.append("启动紧急成本削减计划（30%）")
            mitigations.append("加速收款流程")
            mitigations.append("延迟非关键资本支出")
        if runway < 12:
            mitigations.append("审查并优化费用报销政策")
            mitigations.append(" renegotiate 合同付款条款")
        mitigations.append("更新6个月现金流预测")
        mitigations.append("准备备选融资方案")

        return mitigations

    def _estimate_cost_savings(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        cost_category = alert_data.get("cost_category", "unknown")
        current_cost = self.cost_metrics.get(cost_category, 0)

        return {
            "cost_category": cost_category,
            "current_cost": current_cost,
            "potential_savings_percentage": 15 if current_cost > 10000 else 10,
            "estimated_savings": current_cost * 0.15
            if current_cost > 10000
            else current_cost * 0.1,
        }

    def _generate_cost_optimization_strategies(
        self, alert_data: Dict[str, Any]
    ) -> List[str]:
        cost_category = alert_data.get("cost_category", "unknown")
        strategies = []

        if cost_category == "ai_compute_costs":
            strategies.extend(
                [
                    "优化模型使用，使用更高效的推理",
                    "实施缓存策略减少重复API调用",
                    "批量处理请求",
                    "考虑开源模型替代",
                ]
            )
        elif cost_category == "cloud_services":
            strategies.extend(
                [
                    "审查并停用未使用的资源",
                    "应用预留实例折扣",
                    "实施自动缩放策略",
                    "优化存储层级",
                ]
            )
        elif cost_category == "personnel_costs":
            strategies.extend(
                [
                    "审查组织效率指标",
                    "优化工作流程自动化",
                    "考虑混合工作模式",
                ]
            )
        else:
            strategies.extend(
                [
                    "进行全面的成本结构审查",
                    "实施预算审批流程强化",
                    "建立成本控制KPI",
                ]
            )

        return strategies

    async def _evaluate_budget_allocation_request(
        self, message: Message, company_state: CompanyState
    ) -> Message:
        request_data = message.content
        budget_request = request_data.get("budget_request", {})

        evaluation_prompt = f"""
        作为CFO，评估此预算分配请求：

        部门：{request_data.get("department", "unknown")}
        申请金额：{budget_request.get("amount", 0)}
        申请用途：{budget_request.get("purpose", "unknown")}
        预期收益：{budget_request.get("expected_benefits", [])}

        当前总预算：{self.budget_allocation.get("total_budget", 0)}
        已分配预算：{self.budget_allocation.get("allocated_budget", 0)}
        当前财务状况：{json.dumps(self.financial_metrics, indent=2)}

        进行综合评估：
        1. 申请合理性
        2. 与公司战略的一致性
        3. ROI预测
        4. 财务风险
        5. 建议的预算额度

        以JSON格式返回评估结果。
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
                    "decision": {
                        "approved": evaluation.get("approved", False),
                        "recommended_amount": evaluation.get("recommended_amount", 0),
                        "justification": evaluation.get("justification", ""),
                        "conditions": evaluation.get("conditions", []),
                    },
                    "evaluated_by": "CFO",
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
                        "justification": f"评估失败: {str(e)}",
                    },
                    "evaluated_by": "CFO",
                },
            )

    async def _evaluate_capital_expenditure_request(
        self, message: Message, company_state: CompanyState
    ) -> Message:
        request_data = message.content
        capex_request = request_data.get("capex_request", {})

        evaluation = {
            "approved": False,
            "justification": "未实现",
            "required_analysis": ["NPV", "IRR", "Payback Period"],
            "estimated_cost": capex_request.get("estimated_cost", 0),
        }

        return CommunicationProtocol.create_message(
            sender=self.role,
            recipient=message.sender,
            message_type=MessageType.APPROVAL_RESPONSE,
            content={
                "request_id": request_data.get("request_id"),
                "decision": evaluation,
                "evaluated_by": "CFO",
            },
        )

    async def _evaluate_investment_approval_request(
        self, message: Message, company_state: CompanyState
    ) -> Message:
        request_data = message.content
        investment_details = request_data.get("investment_details", {})

        evaluation = {
            "approved": False,
            "justification": "需要更详细的财务建模",
            "required_information": [
                "投资目的",
                "预期回报",
                "风险评估",
                "退出策略",
            ],
        }

        return CommunicationProtocol.create_message(
            sender=self.role,
            recipient=message.sender,
            message_type=MessageType.APPROVAL_RESPONSE,
            content={
                "request_id": request_data.get("request_id"),
                "decision": evaluation,
                "evaluated_by": "CFO",
            },
        )

    async def _evaluate_expense_reimbursement_request(
        self, message: Message, company_state: CompanyState
    ) -> Message:
        request_data = message.content
        expense_details = request_data.get("expense_details", {})

        approved = expense_details.get("amount", 0) < 5000

        return CommunicationProtocol.create_message(
            sender=self.role,
            recipient=message.sender,
            message_type=MessageType.APPROVAL_RESPONSE,
            content={
                "request_id": request_data.get("request_id"),
                "decision": {
                    "approved": approved,
                    "amount_approved": expense_details.get("amount", 0)
                    if approved
                    else 0,
                    "justification": "符合常规费用政策"
                    if approved
                    else "超过常规审批限额",
                },
                "evaluated_by": "CFO",
            },
        )

    def _calculate_financial_health_score(self) -> float:
        weights = {
            "liquidity": 0.3,
            "profitability": 0.3,
            "growing": 0.2,
            "efficiency": 0.2,
        }

        liquidity_score = min(
            100,
            (
                self.financial_metrics.get("cash_on_hand", 0)
                / max(1, self.financial_metrics.get("burn_rate", 1) * 12)
            )
            * 100,
        )
        profitability_score = (
            100 if self.financial_metrics.get("net_income", 0) > 0 else 50
        )
        growing_score = (
            100
            if self.financial_metrics.get("revenue", 0)
            > self.financial_metrics.get("cost_of_revenue", 0)
            else 50
        )
        efficiency_score = 80

        return (
            weights["liquidity"] * liquidity_score
            + weights["profitability"] * profitability_score
            + weights["growing"] * growing_score
            + weights["efficiency"] * efficiency_score
        )
