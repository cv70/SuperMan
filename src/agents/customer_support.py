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



class CustomerSupportAgent(BaseAgent):
    def __init__(self):
        capabilities = [
            "用户咨询处理",
            "问题分类",
            "知识库查询",
            "工单管理",
            "用户反馈收集",
            "情感安抚",
            "问题升级",
            "报告生成"
        ]
        super().__init__(AgentRole.CUSTOMER_SUPPORT, capabilities)
        default_model_config = app_config.llm.models.get(
            app_config.llm.default_model,
            ModelConfig(
                name=app_config.llm.default_model,
                provider="openai",
                api_key=None,
                config={},
            ),
        )
        agent_config = app_config.agents.get("customer_support", AgentConfig())
        self.llm = ChatOpenAI(
            model=app_config.llm.default_model,
            temperature=agent_config.temperature if agent_config.temperature != 0.3 else default_model_config.config.get("temperature", 0.3),
        )
        self.knowledge_base = {}
        self.open_tickets = []
        self.user_sentiment = {}
        self.common_issues = []
        self.satisfaction_scores = []
    
    async def process_message(self, message: Message, company_state: CompanyState) -> Optional[Message]:
        if message.message_type == MessageType.TASK_ASSIGNMENT:
            return await self._handle_task_assignment(message, company_state)
        elif message.message_type == MessageType.STATUS_REPORT:
            return await self._handle_status_report(message, company_state)
        elif message.message_type == MessageType.DATA_REQUEST:
            return await self._handle_data_request(message, company_state)
        elif message.message_type == MessageType.ALERT:
            return await self._handle_alert(message, company_state)
        elif message.message_type == MessageType.COLLABORATION:
            return await self._handle_collaboration(message, company_state)
        elif message.message_type == MessageType.APPROVAL_REQUEST:
            return await self._handle_approval_request(message, company_state)
        elif message.message_type == MessageType.DATA_RESPONSE:
            return await self._handle_data_response(message, company_state)
        
        return None
    
    async def _handle_task_assignment(self, message: Message, company_state: CompanyState) -> Optional[Message]:
        task_data = message.content.get("task", {})
        task_title = task_data.get("title", "")
        
        if "support" in task_title.lower() or "customer" in task_title.lower():
            return await self._handle_customer_support_task(message, company_state)
        
        return None
    
    async def _handle_customer_support_task(self, message: Message, company_state: CompanyState) -> Message:
        task_data = message.content.get("task", {})
        task_description = task_data.get("description", {})
        
        response = await self._handle_user_inquiry(task_description, company_state)
        
        return CommunicationProtocol.create_message(
            sender=self.role,
            recipient=message.sender,
            message_type=MessageType.STATUS_REPORT,
            content={
                "response": response,
                "task_reference": task_data.get("task_id"),
                "handled_by": "customer_support"
            }
        )
    
    async def _handle_status_report(self, message: Message, company_state: CompanyState) -> Optional[Message]:
        return None
    
    async def _handle_data_request(self, message: Message, company_state: CompanyState) -> Message:
        request_type = message.content.get("request_type", "")
        
        if request_type == "support_tickets":
            return CommunicationProtocol.create_message(
                sender=self.role,
                recipient=message.sender,
                message_type=MessageType.DATA_RESPONSE,
                content={
                    "request_id": message.content.get("request_id"),
                    "data": {
                        "open_tickets": self.open_tickets,
                        "ticket_count": len(self.open_tickets),
                        "avg_resolution_time": self._calculate_avg_resolution_time()
                    },
                    "data_type": "support_tickets"
                }
            )
        elif request_type == "user_sentiment":
            return CommunicationProtocol.create_message(
                sender=self.role,
                recipient=message.sender,
                message_type=MessageType.DATA_RESPONSE,
                content={
                    "request_id": message.content.get("request_id"),
                    "data": {
                        "sentiment_scores": self.user_sentiment,
                        "satisfaction_scores": self.satisfaction_scores,
                        "average_satisfaction": self._calculate_average_satisfaction()
                    },
                    "data_type": "user_sentiment"
                }
            )
        elif request_type == "common_issues":
            return CommunicationProtocol.create_message(
                sender=self.role,
                recipient=message.sender,
                message_type=MessageType.DATA_RESPONSE,
                content={
                    "request_id": message.content.get("request_id"),
                    "data": {
                        "common_issues": self.common_issues,
                        "issue_count": len(self.common_issues)
                    },
                    "data_type": "common_issues"
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
    
    async def _handle_alert(self, message: Message, company_state: CompanyState) -> Optional[Message]:
        alert_data = message.content
        alert_type = alert_data.get("alert_type", "")
        
        if alert_type in ["customer_complaint", "systemic_issue"]:
            severity = alert_data.get("severity", "high")
            
            if severity in ["critical", "high"]:
                return await self._handle_critical_alert(message, company_state)
        
        return None
    
    async def _handle_critical_alert(self, message: Message, company_state: CompanyState) -> Message:
        alert_data = message.content
        
        if self._is_systemic_issue(alert_data):
            return await self._escalate_systemic_issue(message, company_state)
        
        return await self._escalate_issue(message, company_state)
    
    async def _handle_collaboration(self, message: Message, company_state: CompanyState) -> Optional[Message]:
        content = message.content
        
        if content.get("type") == "customer_feedback":
            return await self._process_customer_feedback(message, company_state)
        
        return None
    
    async def _process_customer_feedback(self, message: Message, company_state: CompanyState) -> Message:
        feedback_data = message.content.get("data", {})
        
        self._collect_feedback(feedback_data)
        
        sentiment = feedback_data.get("sentiment", "neutral")
        
        if sentiment in ["negative", "angry"]:
            await self._安抚_emotional(feedback_data)
        
        return CommunicationProtocol.create_message(
            sender=self.role,
            recipient=AgentRole.CPO,
            message_type=MessageType.STATUS_REPORT,
            content={
                "feedback_processed": True,
                "sentiment": sentiment,
                "action_taken": "feedback_collected" if sentiment == "positive" else "escalation_reviewed"
            }
        )
    
    async def _handle_approval_request(self, message: Message, company_state: CompanyState) -> Optional[Message]:
        return None
    
    async def _handle_data_response(self, message: Message, company_state: CompanyState) -> Optional[Message]:
        return None
    
    async def _handle_user_inquiry(self, inquiry: Dict[str, Any], company_state: CompanyState) -> Dict[str, Any]:
        user_question = inquiry.get("question", "")
        user_id = inquiry.get("user_id", "unknown")
        
        classification = self._classify_issue(user_question)
        
        if classification == "routine":
            answer = await self._query_knowledge_base(user_question)
            return {
                "response": answer,
                "classification": "routine",
                "source": "knowledge_base",
                "confidence": 0.9
            }
        elif classification == "complex":
            await self._escalate_issue(inquiry, company_state, AgentRole.CPO)
            return {
                "response": "Your complex inquiry has been escalated to our CPO team. They will contact you shortly.",
                "classification": "complex",
                "escalation_target": "CPO",
                "ticket_id": create_task_id()
            }
        elif classification == "urgent":
            await self._escalate_issue(inquiry, company_state, AgentRole.CEO)
            return {
                "response": "Your urgent issue has been escalated to our CEO team for immediate attention.",
                "classification": "urgent",
                "escalation_target": "CEO",
                "ticket_id": create_task_id(),
                "priority": "high"
            }
        
        return {
            "response": "Unable to process your inquiry. We have created a support ticket for further investigation.",
            "classification": "unknown",
            "ticket_id": create_task_id()
        }
    
    def _classify_issue(self, question: str) -> str:
        question_lower = question.lower()
        
        keywords_urgent = ["critical", "emergency", "urgent", "break", "down", "cannot use", "not working", "fire"]
        keywords_complex = ["integration", "architecture", "strategy", "roadmap", "complex", " difficult", "expensive"]
        keywords_knowledge = ["how", "what", "why", "where", "when", "price", "feature", "tutorial", "guide"]
        
        if any(kw in question_lower for kw in keywords_urgent):
            return "urgent"
        elif any(kw in question_lower for kw in keywords_complex):
            return "complex"
        elif any(kw in question_lower for kw in keywords_knowledge):
            return "routine"
        
        return "routine"
    
    async def _query_knowledge_base(self, question: str) -> str:
        if not self.knowledge_base:
            return "I'm processing your query. Could you provide more details about your issue?"
        
        question_lower = question.lower()
        
        for query, answer in self.knowledge_base.items():
            if query.lower() in question_lower or question_lower in query.lower():
                return answer
        
        return f"I don't have specific information about '{question}' in my knowledge base. A support ticket has been created for further assistance."
    
    async def _collect_feedback(self, feedback_data: Dict[str, Any]) -> None:
        user_id = feedback_data.get("user_id")
        if not user_id:
            user_id = feedback_data.get("user_identifier", "anonymous")
        
        sentiment = feedback_data.get("sentiment", "neutral")
        feedback_text = feedback_data.get("feedback", "")
        satisfaction_score = feedback_data.get("satisfaction_score", 0)
        
        self.user_sentiment[user_id] = {
            "sentiment": sentiment,
            "feedback": feedback_text,
            "timestamp": datetime.now().isoformat()
        }
        
        self.satisfaction_scores.append({
            "user_id": user_id,
            "score": satisfaction_score,
            "timestamp": datetime.now().isoformat()
        })
        
        if satisfaction_score > 0:
            self.satisfaction_scores = [s for s in self.satisfaction_scores if s.get("score", 0) > 0]
        
        self._analyze_common_issues(feedback_text)
    
    async def _安抚_emotional(self, feedback_data: Dict[str, Any]) -> None:
        user_id = feedback_data.get("user_id", feedback_data.get("user_identifier", "anonymous"))
        sentiment = feedback_data.get("sentiment", "neutral")
        issue = feedback_data.get("issue", "")
        
        安抚_message = await self._generate_安抚_response(sentiment, issue)
        
        self.user_sentiment[user_id]["安抚_applied"] = True
        self.user_sentiment[user_id]["安抚_message"] = 安抚_message
    
    async def _generate_安抚_response(self, sentiment: str, issue: str) -> str:
        安抚_prompts = {
            "angry": f"""
As a customer support agent, provide an empathetic安抚 response to an angry user.

User's sentiment: ANGRY
Issue reported: {issue}

Generate a response that:
1. Acknowledges their frustration
2. Apologizes sincerely
3. assures them we're fixing it
4. provides estimated timeline
5. offers compensation if applicable

Keep it professional but empathetic.
""",
            "negative": f"""
As a customer support agent, provide a安抚 response to a negative user.

User's sentiment: NEGATIVE
Issue reported: {issue}

Generate a response that:
1. Acknowledges their concerns
2. Shows understanding
3. assures improvement
4. provides next steps

Keep it professional and supportive.
""",
            "frustrated": f"""
As a customer support agent, provide a安抚 response to a frustrated user.

User's sentiment: FRUSTRASTED
Issue reported: {issue}

Generate a response that:
1. Recognizes their frustration
2. Apologizes for the inconvenience
3. assures resolution
4. explains what we're doing

Keep it empathetic and reassuring.
"""
        }
        
        prompt = 安抚_prompts.get(sentiment.lower(), 安抚_prompts.get("negative"))
        
        try:
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            return response.content if isinstance(response.content, str) else str(response.content)
        except Exception:
            return "We understand your concerns and are working to resolve this issue. Thank you for your patience."
    
    async def _escalate_issue(self, inquiry: Dict[str, Any], company_state: CompanyState, target_role: AgentRole) -> None:
        ticket = {
            "ticket_id": create_task_id(),
            "user_id": inquiry.get("user_id", "unknown"),
            "issue": inquiry.get("question", "") or inquiry.get("issue", ""),
            "classification": "complex" if target_role == AgentRole.CPO else "urgent",
            "escalated_to": target_role.value,
            "escalated_at": datetime.now().isoformat(),
            "priority": "high" if target_role == AgentRole.CEO else "medium",
            "status": "pending"
        }
        
        self.open_tickets.append(ticket)
        
        target_agent_state = company_state.get("agents", {}).get(target_role, {})
        if target_agent_state:
            task = Task(
                task_id=ticket["ticket_id"],
                title=f"Customer Issue: {inquiry.get('question', '')[:50]}",
                description=f"Customer escalation: {inquiry.get('question', '')}",
                assigned_to=target_role,
                assigned_by=self.role,
                priority=Priority.HIGH if target_role == AgentRole.CEO else Priority.MEDIUM,
                metadata={
                    "customer_support_ticket": ticket,
                    "origin": "customer_support"
                }
            )
            
            task_msg = CommunicationProtocol.create_task_assignment(self.role, target_role, task)
            company_state["messages"].append(task_msg)
    
    async def _escalate_systemic_issue(self, message: Message, company_state: CompanyState) -> Message:
        alert_data = message.content
        
        cpo_task = Task(
            task_id=create_task_id(),
            title=f"Systemic Issue: {alert_data.get('message', '')[:50]}",
            description=f"Multiple users reporting: {alert_data.get('message', '')}",
            assigned_to=AgentRole.CPO,
            assigned_by=self.role,
            priority=Priority.HIGH
        )
        
        cto_task = Task(
            task_id=create_task_id(),
            title=f"Technical Investigation: {alert_data.get('message', '')[:50]}",
            description=f"Systemic technical issue requiring investigation: {alert_data.get('message', '')}",
            assigned_to=AgentRole.CTO,
            assigned_by=self.role,
            priority=Priority.HIGH
        )
        
        company_state["messages"].append(CommunicationProtocol.create_task_assignment(self.role, AgentRole.CPO, cpo_task))
        company_state["messages"].append(CommunicationProtocol.create_task_assignment(self.role, AgentRole.CTO, cto_task))
        
        return CommunicationProtocol.create_message(
            sender=self.role,
            recipient=AgentRole.CEO,
            message_type=MessageType.ALERT,
            content={
                "alert_type": "systemic_issue",
                "message": "Customer Support has identified a systemic issue requiring CPO and CTO collaboration",
                "severity": "critical",
                "details": alert_data,
                "escalated_teams": ["CPO", "CTO"]
            },
            priority=Priority.CRITICAL
        )
    
    async def _handle_user_query(self, query: Dict[str, Any], company_state: CompanyState) -> Dict[str, Any]:
        question = query.get("question", "")
        user_id = query.get("user_id", "anonymous")
        
        classification = self._classify_issue(question)
        
        if classification == "routine":
            answer = await self._query_knowledge_base(question)
            return {
                "response": answer,
                "classification": "routine",
                "ticket_id": None
            }
        else:
            await self._escalate_issue(query, company_state, AgentRole.CPO if classification == "complex" else AgentRole.CEO)
            return {
                "response": f"Your {classification} issue has been escalated to {classification.upper()} team.",
                "classification": classification,
                "ticket_id": create_task_id()
            }
    
    async def _process_user_inquiry(self, inquiry: str, user_context: Dict[str, Any], company_state: CompanyState) -> Dict[str, Any]:
        question = inquiry
        classification = self._classify_issue(question)
        
        if classification == "routine":
            answer = await self._query_knowledge_base(question)
            return {
                "response": answer,
                "classification": "routine",
                "confidence": 0.85
            }
        elif classification == "complex":
            await self._escalate_issue({"question": question, **user_context}, company_state, AgentRole.CPO)
            return {
                "response": "Your complex inquiry has been escalated to CPO for detailed analysis.",
                "classification": "complex",
                "ticket_id": create_task_id()
            }
        else:
            await self._escalate_issue({"question": question, **user_context}, company_state, AgentRole.CEO)
            return {
                "response": "Your urgent issue has been escalated to CEO for immediate attention.",
                "classification": "urgent",
                "ticket_id": create_task_id(),
                "priority": "high"
            }
    
    async def execute_task(self, task: Task, company_state: CompanyState) -> Dict[str, Any]:
        task_title = task.title.lower()
        task_description = task.description.lower()
        
        if "inquiry" in task_title or "question" in task_description:
            return await self._execute_user_inquiry(task, company_state)
        elif "classification" in task_title or "categorize" in task_description:
            return await self._execute_issue_classification(task, company_state)
        elif "knowledge" in task_title or "query" in task_description or "answer" in task_description:
            return await self._execute_kb_query(task, company_state)
        
        return {
            "status": "completed",
            "result": "Task processed by Customer Support",
            "timestamp": datetime.now().isoformat()
        }
    
    async def _execute_user_inquiry(self, task: Task, company_state: CompanyState) -> Dict[str, Any]:
        inquiry = {
            "question": task.description,
            "user_id": task.metadata.get("user_id", "unknown"),
            "user_context": task.metadata
        }
        
        response = await self._process_user_inquiry(task.description, task.metadata, company_state)
        
        return {
            "status": "completed",
            "result": response,
            "task_id": task.task_id,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _execute_issue_classification(self, task: Task, company_state: CompanyState) -> Dict[str, Any]:
        question = task.description
        classification = self._classify_issue(question)
        
        classification_result = {
            "classification": classification,
            "reasoning": f"Based on keywords in: {question}",
            "recommended_action": self._get_action_for_classification(classification)
        }
        
        if classification in ["complex", "urgent"]:
            await self._escalate_issue({"question": question}, company_state, 
                                    AgentRole.CPO if classification == "complex" else AgentRole.CEO)
        
        return {
            "status": "completed",
            "result": classification_result,
            "task_id": task.task_id,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _execute_kb_query(self, task: Task, company_state: CompanyState) -> Dict[str, Any]:
        question = task.description
        answer = await self._query_knowledge_base(question)
        
        return {
            "status": "completed",
            "result": {
                "question": question,
                "answer": answer,
                "source": "knowledge_base"
            },
            "task_id": task.task_id,
            "timestamp": datetime.now().isoformat()
        }
    
    async def generate_report(self, company_state: CompanyState) -> Dict[str, Any]:
        report_data = await self._compile_support_metrics(company_state)
        
        generation_prompt = f"""
As a Customer Support Agent, generate a comprehensive support dashboard report:

Open Tickets: {len(self.open_tickets)}
Satisfaction Scores: {self._calculate_average_satisfaction()}
Common Issues: {json.dumps(self.common_issues[:5], indent=2)}
Response Statistics: {json.dumps(report_data.get("response_stats", {}), indent=2)}

Generate support dashboard report with:
1. Executive Summary
2. Ticket Overview (open, resolved, pending)
3. User Satisfaction Metrics
4. Top Issues Summary
5. Response Time Analysis
6. Escalation Summary
7. Recommendations

Format as professional support dashboard report.
"""
        
        try:
            response = await self.llm.ainvoke([HumanMessage(content=generation_prompt)])
            content = response.content if isinstance(response.content, str) else str(response.content)
            report = json.loads(content) if isinstance(content, str) else {}
            
            return {
                "agent_role": self.role.value,
                "report_type": "support_dashboard",
                "timestamp": datetime.now().isoformat(),
                "data": report if isinstance(report, dict) else {"summary": content},
                "metrics": report_data
            }
        except Exception as e:
            return {
                "agent_role": self.role.value,
                "report_type": "support_dashboard",
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "status": "report_generation_failed"
            }
    
    def _get_action_for_classification(self, classification: str) -> str:
        actions = {
            "routine": "Answer from knowledge base",
            "complex": "Escalate to CPO",
            "urgent": "Escalate to CEO immediately"
        }
        return actions.get(classification, "Escalate to appropriate team")
    
    async def _compile_support_metrics(self, company_state: CompanyState) -> Dict[str, Any]:
        return {
            "total_tickets": len(self.open_tickets),
            "open_tickets": len([t for t in self.open_tickets if t.get("status") == "pending"]),
            "resolved_tickets": len([t for t in self.open_tickets if t.get("status") == "completed"]),
            "escalation_count": len([t for t in self.open_tickets if t.get("escalated_to")]),
            "avg_satisfaction": self._calculate_average_satisfaction(),
            "common_issues": self.common_issues[:10],
            "response_stats": {
                "total_queries": len(self.user_sentiment),
                "positiveSentiment": len([s for s in self.user_sentiment.values() if s.get("sentiment") == "positive"]),
                "negativeSentiment": len([s for s in self.user_sentiment.values() if s.get("sentiment") in ["negative", "angry"]])
            },
            "daily_summary": self._generate_daily_summary()
        }
    
    def _calculate_average_satisfaction(self) -> float:
        if not self.satisfaction_scores:
            return 0.0
        total = sum(s.get("score", 0) for s in self.satisfaction_scores)
        return round(total / len(self.satisfaction_scores), 2)
    
    def _calculate_avg_resolution_time(self) -> float:
        if not self.open_tickets:
            return 0.0
        return 0.0
    
    def _generate_daily_summary(self) -> Dict[str, Any]:
        today = datetime.now().date()
        return {
            "date": today.isoformat(),
            "total_inquiries": len(self.user_sentiment),
            "issues_resolved": len([t for t in self.open_tickets if t.get("status") == "completed"]),
            "daily_satisfaction": self._calculate_average_satisfaction()
        }
    
    def _analyze_common_issues(self, feedback_text: str) -> None:
        if not feedback_text:
            return
        
        keywords = ["bug", "error", "slow", "crash", "don't work", "issue", "problem"]
        
        feedback_lower = feedback_text.lower()
        found_keywords = [kw for kw in keywords if kw in feedback_lower]
        
        if found_keywords:
            for kw in found_keywords:
                existing = next((i for i in self.common_issues if i.get("keyword") == kw), None)
                if existing:
                    existing["count"] += 1
                    existing["last_seen"] = datetime.now().isoformat()
                else:
                    self.common_issues.append({
                        "keyword": kw,
                        "count": 1,
                        "last_seen": datetime.now().isoformat(),
                        "category": "technical"
                    })
    
    def _is_systemic_issue(self, alert_data: Dict[str, Any]) -> bool:
        message = alert_data.get("message", "").lower()
        severity = alert_data.get("severity", "")
        
        systemic_keywords = ["multiple users", "many users", "system", "global", "widespread", "outage", "down"]
        
        return severity in ["critical", "high"] or any(kw in message for kw in systemic_keywords)
    
    def _get_common_issues_summary(self) -> Dict[str, Any]:
        return {
            "total_common_issues": len(self.common_issues),
            "top_issues": sorted(self.common_issues, key=lambda x: x.get("count", 0), reverse=True)[:5],
            "trend": self._analyze_issue_trend()
        }
    
    def _analyze_issue_trend(self) -> str:
        if not self.common_issues:
            return "no_data"
        
        recent = [i for i in self.common_issues if i.get("count", 0) > 2]
        if len(recent) > 3:
            return "increasing"
        elif len(recent) < 2:
            return "decreasing"
        return "stable"
