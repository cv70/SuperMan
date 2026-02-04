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



class DataAnalystAgent(BaseAgent):
    def __init__(self):
        capabilities = [
            "数据收集",
            "数据分析",
            "仪表板生成",
            "异常检测",
            "预测建模",
            "指标计算",
            "用户行为分析",
            "成本利润分析",
        ]
        super().__init__(AgentRole.DATA_ANALYST, capabilities)
        default_model_config = app_config.llm.models.get(
            app_config.llm.default_model,
            ModelConfig(
                name=app_config.llm.default_model,
                provider="openai",
                api_key=None,
                config={},
            ),
        )
        agent_config = app_config.agents.get("data_analyst", AgentConfig())
        self.llm = ChatOpenAI(
            model=app_config.llm.default_model,
            temperature=agent_config.temperature if agent_config.temperature != 0.3 else default_model_config.config.get("temperature", 0.3),
        )
        self.data_warehouse = {}
        self.dashboards = {}
        self.prediction_models = {}
        self.anomaly_detected = False
        self.metrics_definitions = {
            "revenue": {"type": "monetary", "unit": "USD"},
            "user_growth": {"type": "count", "unit": "users"},
            "churn_rate": {"type": "percentage", "unit": "%"},
            "roi": {"type": "percentage", "unit": "%"},
            "response_time": {"type": "duration", "unit": "ms"},
            "error_rate": {"type": "percentage", "unit": "%"},
        }

    async def process_message(
        self, message: Message, company_state: CompanyState
    ) -> Optional[Message]:
        content = message.content

        if message.message_type == MessageType.STATUS_REPORT:
            return await self._handle_status_report(message, company_state)
        elif message.message_type == MessageType.ALERT:
            return await self._handle_alert(message, company_state)
        elif message.message_type == MessageType.DATA_REQUEST:
            return await self._handle_data_request(message, company_state)
        elif message.message_type == MessageType.DATA_RESPONSE:
            return await self._handle_data_response(message, company_state)
        elif message.message_type == MessageType.APPROVAL_REQUEST:
            return await self._handle_approval_request(message, company_state)
        elif message.message_type == MessageType.COLLABORATION:
            return await self._handle_collaboration(message, company_state)
        elif message.message_type == MessageType.TASK_ASSIGNMENT:
            return await self._handle_task_assignment(message, company_state)

        return None

    async def _handle_status_report(
        self, message: Message, company_state: CompanyState
    ) -> Optional[Message]:
        sender = message.sender
        report_data = message.content

        analysis_prompt = f"""
        As Data Analyst, analyze this status report from {sender.value}:
        
        Report Data: {json.dumps(report_data, indent=2)}
        
        Current Data Warehouse Status: {json.dumps(self.data_warehouse, indent=2)}
        
        Provide data-driven insights:
        1. Key trends and patterns
        2. Anomalies or outliers
        3. Metric correlations
        4. Recommendations based on data
        
        Respond with JSON format containing:
        - insights: list of key insights
        - anomalies: list of detected anomalies
        - correlations: key metric relationships
        - recommendations: actionable recommendations
        """

        try:
            response = await self.llm.ainvoke([HumanMessage(content=analysis_prompt)])
            content = (
                response.content
                if isinstance(response.content, str)
                else str(response.content)
            )
            insights = json.loads(content)

            return CommunicationProtocol.create_message(
                sender=self.role,
                recipient=sender,
                message_type=MessageType.COLLABORATION,
                content={
                    "type": "data_insights",
                    "insights": insights,
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

    async def _handle_alert(
        self, message: Message, company_state: CompanyState
    ) -> Optional[Message]:
        alert_data = message.content

        if alert_data.get("severity") in ["critical", "high"]:
            return CommunicationProtocol.create_message(
                sender=self.role,
                recipient=AgentRole.OPERATIONS,
                message_type=MessageType.ALERT,
                content={
                    "alert_type": "data_anomaly_detected",
                    "message": f"Data Analyst detected anomaly: {alert_data.get('message', 'Anomaly detected')}",
                    "severity": alert_data.get("severity", "high"),
                    "analysis": self._analyze_anomaly(alert_data),
                },
                priority=Priority(alert_data.get("severity", "high")),
            )

        return None

    async def _handle_data_request(
        self, message: Message, company_state: CompanyState
    ) -> Message:
        request_type = message.content.get("request_type", "")
        data_category = message.content.get("data_category", "")
        request_id = message.content.get("request_id", "")

        if request_type == "user_behavior" or data_category == "product":
            return await self._provide_user_behavior_analysis(message, company_state)
        elif request_type == "cost_profit" or data_category == "financial":
            return await self._provide_cost_profit_analysis(message, company_state)
        elif request_type == "metrics" or data_category == "general":
            return await self._provide_metrics_data(message, company_state)
        elif request_type == "prediction" or data_category == "forecast":
            return await self._provide_prediction_data(message, company_state)

        return CommunicationProtocol.create_message(
            sender=self.role,
            recipient=message.sender,
            message_type=MessageType.DATA_RESPONSE,
            content={
                "request_id": request_id,
                "error": f"Unknown data request type: {request_type}",
            },
        )

    async def _handle_data_response(
        self, message: Message, company_state: CompanyState
    ) -> Optional[Message]:
        data = message.content

        if self.data_warehouse:
            self.data_warehouse.update(data)
        else:
            self.data_warehouse = data

        return CommunicationProtocol.create_message(
            sender=self.role,
            recipient=message.sender,
            message_type=MessageType.DATA_RESPONSE,
            content={
                "type": "data_received",
                "status": "ingested",
                "warehouse_size": len(self.data_warehouse),
            },
        )

    async def _handle_approval_request(
        self, message: Message, company_state: CompanyState
    ) -> Optional[Message]:
        request_data = message.content
        request_type = request_data.get("request_type", "")

        if request_type in ["budget", "financial"]:
            return await self._evaluate_data_investment_approval(message, company_state)

        return CommunicationProtocol.create_message(
            sender=self.role,
            recipient=message.sender,
            message_type=MessageType.APPROVAL_RESPONSE,
            content={
                "request_id": request_data.get("request_id"),
                "approved": False,
                "reasoning": "Data Analyst does not typically handle this approval type",
            },
        )

    async def _handle_collaboration(
        self, message: Message, company_state: CompanyState
    ) -> Optional[Message]:
        content = message.content

        if content.get("type") == "data_insight_request":
            return await self._process_data_insight_request(message, company_state)

        return None

    async def _handle_task_assignment(
        self, message: Message, company_state: CompanyState
    ) -> Optional[Message]:
        task_data = message.content.get("task", {})
        task_title = task_data.get("title", "")

        if "analyze" in task_title.lower() or "report" in task_title.lower():
            return CommunicationProtocol.create_message(
                sender=self.role,
                recipient=message.sender,
                message_type=MessageType.DATA_RESPONSE,
                content={
                    "type": "task_acknowledgment",
                    "status": "queued_for_analysis",
                    "estimated_completion": (
                        datetime.now() + timedelta(hours=4)
                    ).isoformat(),
                },
            )

        return None

    async def _process_data_insight_request(
        self, message: Message, company_state: CompanyState
    ) -> Message:
        request_data = message.content.get("data", {})

        insight_prompt = f"""
        As Data Analyst, provide detailed insights for this request:
        
        Request Details: {json.dumps(request_data, indent=2)}
        Current Data Warehouse: {json.dumps(self.data_warehouse, indent=2)}
        
        Provide comprehensive data analysis including:
        1. Trend analysis
        2. Pattern recognition
        3. Anomaly detection
        4. Comparative analysis
        5. Predictive indicators
        
        Respond with detailed analysis in JSON format.
        """

        try:
            response = await self.llm.ainvoke([HumanMessage(content=insight_prompt)])
            content = (
                response.content
                if isinstance(response.content, str)
                else str(response.content)
            )
            analysis = json.loads(content)

            return CommunicationProtocol.create_message(
                sender=self.role,
                recipient=message.sender,
                message_type=MessageType.COLLABORATION,
                content={
                    "type": "data_insight_response",
                    "analysis": analysis,
                    "timestamp": datetime.now().isoformat(),
                },
            )
        except Exception as e:
            return CommunicationProtocol.create_message(
                sender=self.role,
                recipient=message.sender,
                message_type=MessageType.COLLABORATION,
                content={
                    "type": "data_insight_response",
                    "error": str(e),
                    "status": "analysis_failed",
                },
            )

    async def execute_task(
        self, task: Task, company_state: CompanyState
    ) -> Dict[str, Any]:
        task_title = task.title.lower()

        if "collect" in task_title or "gathering" in task_title:
            return await self._execute_data_collection(task, company_state)
        elif "analyze" in task_title or "analysis" in task_title:
            return await self._execute_data_analysis(task, company_state)
        elif "model" in task_title or "predict" in task_title:
            return await self._execute_modeling(task, company_state)
        elif "dashboard" in task_title or "report" in task_title:
            return await self._execute_dashboard_generation(task, company_state)

        return {
            "status": "completed",
            "result": "Task processed by Data Analyst",
            "timestamp": datetime.now().isoformat(),
        }

    async def _execute_data_collection(
        self, task: Task, company_state: CompanyState
    ) -> Dict[str, Any]:
        collection_result = await self._collect_data(company_state)

        return {
            "status": "completed",
            "result": collection_result,
            "type": "data_collection",
            "timestamp": datetime.now().isoformat(),
            "records_collected": len(collection_result.get("logs", [])),
        }

    async def _execute_data_analysis(
        self, task: Task, company_state: CompanyState
    ) -> Dict[str, Any]:
        analysis_result = await self._build_datawarehouse(company_state)

        return {
            "status": "completed",
            "result": analysis_result,
            "type": "data_analysis",
            "timestamp": datetime.now().isoformat(),
            "warehouse_size": len(analysis_result.get("tables", {})),
        }

    async def _execute_modeling(
        self, task: Task, company_state: CompanyState
    ) -> Dict[str, Any]:
        modeling_result = await self._build_prediction_model(task, company_state)

        return {
            "status": "completed",
            "result": modeling_result,
            "type": "prediction_modeling",
            "timestamp": datetime.now().isoformat(),
            "models_built": list(modeling_result.get("models", {}).keys()),
        }

    async def _execute_dashboard_generation(
        self, task: Task, company_state: CompanyState
    ) -> Dict[str, Any]:
        report = await self.generate_report(company_state)

        return {
            "status": "completed",
            "result": report,
            "type": "dashboard_generation",
            "timestamp": datetime.now().isoformat(),
            "dashboard_id": f"dashboard_{datetime.now().strftime('%Y%m%d')}",
        }

    async def generate_report(self, company_state: CompanyState) -> Dict[str, Any]:
        week_of = (datetime.now() - timedelta(days=datetime.now().weekday())).strftime(
            "%Y-%m-%d"
        )

        report_prompt = f"""
        As Data Analyst, generate comprehensive weekly data report for CEO, CFO, CMO, CPO:
        
        Current Date: {datetime.now().isoformat()}
        Week Of: {week_of}
        
        Data Warehouse: {json.dumps(self.data_warehouse, indent=2)}
        Prediction Models: {json.dumps(self.prediction_models, indent=2)}
        Detected Anomalies: {self.anomaly_detected}
        
        Generate weekly dashboard report with:
        1. Executive Summary
        2. Key Metrics Overview (Revenue, User Growth, Churn, ROI)
        3. User Behavior Analysis
        4. Anomaly Detection Summary
        5. Prediction Insights
        6. Metric Trend Analysis
        7. Recommendations
        8. Next Week's Focus Areas
        
        Format as professional data dashboard report.
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
                "report_type": "weekly_data_dashboard",
                "timestamp": datetime.now().isoformat(),
                "week_of": week_of,
                "recipients": ["CEO", "CFO", "CMO", "CPO"],
                "data": report,
                "anomaly_status": "detected" if self.anomaly_detected else "normal",
                "next_actions": report.get("recommendations", []),
            }
        except Exception as e:
            return {
                "agent_role": self.role.value,
                "report_type": "weekly_data_dashboard",
                "timestamp": datetime.now().isoformat(),
                "week_of": week_of,
                "error": str(e),
                "status": "report_generation_failed",
            }

    async def _collect_data(self, company_state: CompanyState) -> Dict[str, Any]:
        agents = company_state.get("agents", {})
        all_logs = []

        for role, agent_state in agents.items():
            for task in agent_state.completed_tasks:
                all_logs.append(
                    {
                        "agent": role.value,
                        "task": task.title,
                        "status": task.status,
                        "timestamp": task.updated_at.isoformat()
                        if hasattr(task, "updated_at")
                        else datetime.now().isoformat(),
                    }
                )

            for task in agent_state.current_tasks:
                all_logs.append(
                    {
                        "agent": role.value,
                        "task": task.title,
                        "status": "in_progress",
                        "timestamp": task.created_at.isoformat()
                        if hasattr(task, "created_at")
                        else datetime.now().isoformat(),
                    }
                )

        return {
            "logs": all_logs,
            "total_records": len(all_logs),
            "collected_at": datetime.now().isoformat(),
            "by_agent": {
                role.value: len(agent_state.completed_tasks)
                + len(agent_state.current_tasks)
                for role, agent_state in agents.items()
            },
        }

    async def _build_datawarehouse(self, company_state: CompanyState) -> Dict[str, Any]:
        collection_result = await self._collect_data(company_state)

        tables = {
            "agent_performance": self._build_agent_performance_table(collection_result),
            "task_metrics": self._build_task_metrics_table(company_state),
            "kpi_trends": self._build_kpi_trends_table(company_state),
            "user_feedback": self._build_user_feedback_table(company_state),
        }

        self.data_warehouse = {
            "tables": tables,
            "metadata": {
                "built_at": datetime.now().isoformat(),
                "record_counts": {name: len(data) for name, data in tables.items()},
                "source_systems": list(collection_result.get("by_agent", {}).keys()),
            },
        }

        return self.data_warehouse

    def _build_agent_performance_table(
        self, collection_result: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        by_agent = collection_result.get("by_agent", {})
        total = sum(by_agent.values())

        return [
            {
                "agent": agent,
                "tasks_completed": count,
                "percentage": (count / total * 100) if total > 0 else 0,
            }
            for agent, count in by_agent.items()
        ]

    def _build_task_metrics_table(
        self, company_state: CompanyState
    ) -> List[Dict[str, Any]]:
        tasks = company_state.get("tasks", {})
        metrics = []

        for task_id, task in tasks.items():
            metrics.append(
                {
                    "task_id": task_id,
                    "title": task.title,
                    "status": task.status,
                    "assigned_to": task.assigned_to.value,
                    "priority": task.priority.value,
                    "created_at": task.created_at.isoformat()
                    if hasattr(task, "created_at")
                    else None,
                    "deadline": task.deadline.isoformat() if task.deadline else None,
                }
            )

        return metrics

    def _build_kpi_trends_table(
        self, company_state: CompanyState
    ) -> List[Dict[str, Any]]:
        kpis = company_state.get("kpis", {})

        return [
            {
                "metric": metric,
                "current_value": value,
                "target": kpis.get(f"{metric}_target", "N/A"),
                "progress": min(100, (value / kpis.get(f"{metric}_target", 1)) * 100)
                if kpis.get(f"{metric}_target", 0) > 0
                else 0,
            }
            for metric, value in kpis.items()
            if not metric.endswith("_target")
        ]

    def _build_user_feedback_table(
        self, company_state: CompanyState
    ) -> List[Dict[str, Any]]:
        feedback = company_state.get("user_feedback", [])

        return [
            {
                "id": idx,
                "sentiment": item.get("sentiment", "unknown"),
                "category": item.get("category", "general"),
                "message": item.get("message", "")[:100] + "..."
                if len(item.get("message", "")) > 100
                else item.get("message", ""),
            }
            for idx, item in enumerate(feedback[:50])
        ]

    async def _detect_anomalies(
        self, company_state: CompanyState
    ) -> List[Dict[str, Any]]:
        anomalies = []

        kpis = company_state.get("kpis", {})
        system_health = company_state.get("system_health", {})
        agents = company_state.get("agents", {})

        if kpis.get("response_time", 0) > 500:
            anomalies.append(
                {
                    "type": "slow_response",
                    "severity": "warning",
                    "message": "Response time exceeds threshold",
                    "current_value": kpis.get("response_time"),
                    "threshold": 500,
                }
            )

        if kpis.get("error_rate", 0) > 5:
            anomalies.append(
                {
                    "type": "high_error_rate",
                    "severity": "critical",
                    "message": "Error rate exceeds threshold",
                    "current_value": kpis.get("error_rate"),
                    "threshold": 5,
                }
            )

        for role, agent_state in agents.items():
            failed_tasks = len(
                [t for t in agent_state.completed_tasks if t.status == "failed"]
            )
            if failed_tasks > 10:
                anomalies.append(
                    {
                        "type": "agent_failure_rate",
                        "severity": "high",
                        "message": f"{role.value} has high failure rate",
                        "current_value": failed_tasks,
                        "threshold": 10,
                    }
                )

        self.anomaly_detected = len(anomalies) > 0

        if self.anomaly_detected and company_state.get("agents", {}).get(
            AgentRole.OPERATIONS
        ):
            await self._alert_operations(anomalies)

        return anomalies

    async def _alert_operations(self, anomalies: List[Dict[str, Any]]):
        alert_content = {
            "alert_type": "data_anomaly_detected",
            "message": f"Data Analyst detected {len(anomalies)} anomalies",
            "severity": "high",
            "anomalies": anomalies,
        }

        alert_message = CommunicationProtocol.create_alert(
            sender=self.role,
            alert_type=alert_content["alert_type"],
            message=alert_content["message"],
            severity=Priority(alert_content.get("severity", "high")),
            recipient=AgentRole.OPERATIONS,
        )

        self.state.messages.append(alert_message)

    async def _build_prediction_model(
        self, task: Task, company_state: CompanyState
    ) -> Dict[str, Any]:
        collection_result = await self._collect_data(company_state)

        models_prompt = f"""
        As Data Analyst, build prediction models based on available data:
        
        Task: {task.description}
        Collected Data: {json.dumps(collection_result, indent=2)}
        Current KPIs: {json.dumps(company_state.get("kpis", {}), indent=2)}
        
        Build prediction models for:
        1. User Churn Prediction (classification)
        2. ROI Prediction (regression)
        3. Growth Forecasting (time series if data permits)
        
        For each model, provide:
        - Model type and rationale
        - Key features
        - Expected accuracy
        - Implementation requirements
        - Performance metrics
        
        Respond with model details in JSON format.
        """

        try:
            response = await self.llm.ainvoke([HumanMessage(content=models_prompt)])
            content = (
                response.content
                if isinstance(response.content, str)
                else str(response.content)
            )
            models = json.loads(content)

            self.prediction_models = models

            return {
                "models": models,
                "status": "built",
                "model_count": len(models),
                "built_at": datetime.now().isoformat(),
            }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def _respond_to_query(
        self, query: Dict[str, Any], company_state: CompanyState
    ) -> Dict[str, Any]:
        query_prompt = f"""
        As Data Analyst, answer this adhoc data query:
        
        Query: {json.dumps(query, indent=2)}
        
        Data Warehouse: {json.dumps(self.data_warehouse, indent=2)}
        
        Provide a comprehensive answer including:
        1. Direct answer to the query
        2. Supporting data points
        3. Context and explanations
        4. Related insights
        
        Respond in clear, concise JSON format.
        """

        try:
            response = await self.llm.ainvoke([HumanMessage(content=query_prompt)])
            content = (
                response.content
                if isinstance(response.content, str)
                else str(response.content)
            )
            answer = json.loads(content)

            return {
                "query": query,
                "answer": answer,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            return {
                "query": query,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def _calculate_metrics(self, company_state: CompanyState) -> Dict[str, Any]:
        kpis = company_state.get("kpis", {})
        metrics = {}

        for metric, definition in self.metrics_definitions.items():
            if metric in kpis:
                current_value = kpis[metric]
                target_value = kpis.get(f"{metric}_target", 0)

                metrics[metric] = {
                    "current_value": current_value,
                    "target_value": target_value,
                    "unit": definition["unit"],
                    "completion_percentage": min(
                        100, (current_value / target_value) * 100
                    )
                    if target_value > 0
                    else 0,
                    "trend": self._calculate_trend(metric, company_state),
                }

        metrics["_metadata"] = {
            "calculated_at": datetime.now().isoformat(),
            "total_metrics": len(metrics),
            "metrics_performed": len(
                [
                    m
                    for m in metrics.values()
                    if m.get("completion_percentage", 0) >= 100
                ]
            ),
        }

        return metrics

    def _calculate_trend(
        self, metric: str, company_state: CompanyState
    ) -> Dict[str, Any]:
        historical_data = company_state.get("kpis", {}).get(f"{metric}_history", [])

        if len(historical_data) < 2:
            return {"direction": "insufficient_data", "change_percentage": 0}

        current = historical_data[-1]
        previous = historical_data[-2]
        change = current - previous
        change_percentage = (change / previous * 100) if previous != 0 else 0

        if change_percentage > 5:
            direction = "up"
        elif change_percentage < -5:
            direction = "down"
        else:
            direction = "stable"

        return {
            "direction": direction,
            "change_percentage": round(change_percentage, 2),
            "previous_value": previous,
            "current_value": current,
        }

    async def _analyze_anomaly(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "detected_by": "data_analyst",
            "severity": alert_data.get("severity", "unknown"),
            "analysis": "Initial anomaly detected. Detailed data analysis required.",
            "recommended_actions": [
                "Investigate root cause",
                "Review related metrics",
                "Check for data quality issues",
            ],
        }

    async def _provide_user_behavior_analysis(
        self, message: Message, company_state: CompanyState
    ) -> Message:
        request_id = message.content.get("request_id", "")

        analysis_result = await self._analyze_user_behavior(company_state)

        return CommunicationProtocol.create_message(
            sender=self.role,
            recipient=message.sender,
            message_type=MessageType.DATA_RESPONSE,
            content={
                "request_id": request_id,
                "data_category": "user_behavior",
                "analysis": analysis_result,
            },
        )

    async def _analyze_user_behavior(
        self, company_state: CompanyState
    ) -> Dict[str, Any]:
        feedback = company_state.get("user_feedback", [])

        analysis_prompt = f"""
        As Data Analyst, analyze user behavior:
        
        User Feedback: {json.dumps(feedback, indent=2)}
        
        Analyze:
        1. Sentiment distribution (positive/negative/neutral)
        2. Common themes and topics
        3. User journey patterns
        4. Feature usage patterns
        5. Pain points and opportunities
        
        Respond with comprehensive user behavior analysis in JSON format.
        """

        try:
            response = await self.llm.ainvoke([HumanMessage(content=analysis_prompt)])
            content = (
                response.content
                if isinstance(response.content, str)
                else str(response.content)
            )
            analysis = json.loads(content)

            return {"analysis": analysis, "timestamp": datetime.now().isoformat()}
        except Exception as e:
            return {"error": str(e), "timestamp": datetime.now().isoformat()}

    async def _provide_cost_profit_analysis(
        self, message: Message, company_state: CompanyState
    ) -> Message:
        request_id = message.content.get("request_id", "")

        analysis_result = await self._analyze_cost_profit(company_state)

        return CommunicationProtocol.create_message(
            sender=self.role,
            recipient=message.sender,
            message_type=MessageType.DATA_RESPONSE,
            content={
                "request_id": request_id,
                "data_category": "cost_profit",
                "analysis": analysis_result,
            },
        )

    async def _analyze_cost_profit(self, company_state: CompanyState) -> Dict[str, Any]:
        kpis = company_state.get("kpis", {})

        analysis_prompt = f"""
        As Data Analyst, analyze cost-profit correlation:
        
        Current KPIs: {json.dumps(kpis, indent=2)}
        
        Analyze:
        1. Revenue vs. Cost breakdown
        2. Profit margin trends
        3. Cost efficiency metrics
        4. ROI by category
        5. Correlation between costs and profits
        
        Provide correlation analysis and recommendations.
        
        Respond with comprehensive analysis in JSON format.
        """

        try:
            response = await self.llm.ainvoke([HumanMessage(content=analysis_prompt)])
            content = (
                response.content
                if isinstance(response.content, str)
                else str(response.content)
            )
            analysis = json.loads(content)

            return {"analysis": analysis, "timestamp": datetime.now().isoformat()}
        except Exception as e:
            return {"error": str(e), "timestamp": datetime.now().isoformat()}

    async def _provide_metrics_data(
        self, message: Message, company_state: CompanyState
    ) -> Message:
        request_id = message.content.get("request_id", "")

        metrics = await self._calculate_metrics(company_state)

        return CommunicationProtocol.create_message(
            sender=self.role,
            recipient=message.sender,
            message_type=MessageType.DATA_RESPONSE,
            content={
                "request_id": request_id,
                "data_category": "metrics",
                "metrics": metrics,
            },
        )

    async def _provide_prediction_data(
        self, message: Message, company_state: CompanyState
    ) -> Message:
        request_id = message.content.get("request_id", "")

        if not self.prediction_models:
            await self._build_prediction_model(
                Task(
                    task_id=create_task_id(),
                    title="Build prediction models",
                    description="Build prediction models for churn and ROI",
                    assigned_to=AgentRole.DATA_ANALYST,
                    assigned_by=self.role,
                    priority=Priority.MEDIUM,
                ),
                company_state,
            )

        return CommunicationProtocol.create_message(
            sender=self.role,
            recipient=message.sender,
            message_type=MessageType.DATA_RESPONSE,
            content={
                "request_id": request_id,
                "data_category": "prediction",
                "models": self.prediction_models,
            },
        )

    async def _evaluate_data_investment_approval(
        self, message: Message, company_state: CompanyState
    ) -> Message:
        request_data = message.content

        approval_prompt = f"""
        As Data Analyst, evaluate this investment request from data perspective:
        
        Request: {json.dumps(request_data, indent=2)}
        Current KPIs: {json.dumps(company_state.get("kpis", {}), indent=2)}
        Prediction Models: {json.dumps(self.prediction_models, indent=2)}
        
        Evaluate based on:
        1. Data-driven ROI
        2. Predictive impact on KPIs
        3. Resource allocation efficiency
        4. Alignment with data strategy
        
        Provide investment recommendation with data-backed reasoning.
        
        Respond with JSON format:
        - approved: boolean
        - data_analysis: detailed analysis
        - expected_impact: projected KPI changes
        - recommendations: implementation suggestions
        """

        try:
            response = await self.llm.ainvoke([HumanMessage(content=approval_prompt)])
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
                    "evaluated_by": "DataAnalyst",
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
                        "reasoning": "Evaluation failed: " + str(e),
                    },
                },
            )
