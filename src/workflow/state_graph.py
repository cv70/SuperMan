# SuperMan AI 多智能体公司状态定义
from typing import Dict, List, TypedDict, Any
from datetime import datetime
from typing import Dict, List, TypedDict, Any

from ..agents import AgentRole, MessageType, Priority, Message, Task, AgentState


class CompanyState(TypedDict):
    """公司状态类型定义 - 全局共享状态"""

    agents: Dict[AgentRole, AgentState]  # 所有智能体的状态
    tasks: Dict[str, Task]  # 所有任务
    messages: List[Message]  # 所有消息
    current_time: datetime  # 当前时间
    strategic_goals: Dict[str, Any]  # 战略目标
    kpis: Dict[str, float]  # 关键绩效指标
    market_data: Dict[str, Any]  # 市场数据
    user_feedback: List[Dict[str, Any]]  # 用户反馈
    system_health: Dict[str, Any]  # 系统健康状态
    budget_allocation: Dict[str, Any]  # 预算分配
    financial_metrics: Dict[str, Any]  # 财务指标
    campaign_metrics: Dict[str, Any]  # 活动指标
    product_backlog: List[Dict[str, Any]]  # 产品待办事项
    technical_debt: List[Dict[str, Any]]  # 技术债
    campaign_data: Dict[str, Any]  # 活动数据
    brand_data: Dict[str, Any]  # 品牌数据
    industry_reports: Dict[str, Any]  # 行业报告
    historical_cashflow: Dict[str, Any]  # 历史现金流
    competitor_data: Dict[str, Any]  # 竞争对手数据
    customer_data: Dict[str, Any]  # 客户数据
    product_data: Dict[str, Any]  # 产品数据
    business_metrics: Dict[str, Any]  # 业务指标
    historical_financials: Dict[str, Any]  # 历史财务数据


def create_empty_state() -> CompanyState:
    """创建空公司状态"""
    return CompanyState(
        agents={},
        tasks={},
        messages=[],
        current_time=datetime.now(),
        strategic_goals={},
        kpis={},
        market_data={},
        user_feedback=[],
        system_health={},
        budget_allocation={},
        financial_metrics={},
        campaign_metrics={},
        product_backlog=[],
        technical_debt=[],
        campaign_data={},
        brand_data={},
        industry_reports={},
        historical_cashflow={},
        competitor_data={},
        customer_data={},
        product_data={},
        business_metrics={},
        historical_financials={},
    )
