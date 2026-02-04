#!/usr/bin/env python3
"""配置系统测试脚本

import sys
import os

# 添加 src 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from agents.config import app_config

# 测试完整配置加载
print("=" * 60)
print("配置加载测试")
print("=" * 60)
print(f"默认模型: {app_config.llm.default_model}")
print(f"模型列表: {list(app_config.llm.models.keys())}")
print(f"公司名称: {app_config.company.name}")
print(f"资源预算: {app_config.company.resources.get('budget', 'N/A')}")
print(f"默认 KPIs: {list(app_config.company.kpis.keys())}")
print(f"默认通信超时: {app_config.communication.timeout}")
print(f"默认并发配置: {app_config.performance.concurrency}")

# 测试智能体配置
print("\n智能体配置:")
for agent_name in ['ceo', 'cto', 'cfo', 'rd']:
    agent = app_config.agents.get(agent_name)
    if agent:
        print(f"{agent_name.upper()} 模型: {agent.model}")
        print(f"{agent_name.upper()} 温度: {agent.temperature}")
    else:
        print(f"{agent_name.upper()} 配置未找到")

print("\n" + "=" * 60)
print("测试通过！")
print("=" * 60)
