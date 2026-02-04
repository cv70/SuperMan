# SuperMan AI 多智能体公司架构设计文档 (Arch.md)

## 1. 概述

### 1.1 项目定位

SuperMan 是一个完整的 AI 公司架构模拟系统，通过 10 个专业智能体（AI Agents）模拟真实企业中的组织结构、决策流程与协作机制。系统采用 LangGraph 进行状态管理和工作流编排，每个智能体具备独立的决策能力和专业技能边界，共同构成一个自我演进的闭环企业系统。

### 1.2 核心设计理念

| 原则 | 描述 |
|------|------|
| **角色专业化** | 每个智能体对应一个明确的岗位角色（CEO/CTO/CPO/CMO/CFO/HR/RD/DataAnalyst/CustomerSupport/Operations） |
| **职责边界清晰** | 通过能力列表（capabilities）明确定义每个角色的职责范围 |
| **协作协议标准化** | 使用标准化的消息类型（MessageType）和优先级系统进行跨角色沟通 |
| **状态共享与隔离** | 全局共享状态（CompanyState）+ 单个角色状态（AgentState）的混合架构 |
| **配置驱动** | 所有配置通过 config.yaml 管理，支持动态调整而无需修改代码 |
| **测试先行** | 内置模拟运行和报告生成功能，便于验证逻辑 |

## 2. 系统架构图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              SuperMan AI 公司系统                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  ┌───────────────────────────────────────────────────────────────────────┐    │
│  │                         Orchestrator (编排器)                           │    │
│  │  • LangGraph StateGraph 编排                                            │    │
│  │  • 管理10个智能体节点                                                   │    │
│  │  • 路由消息 flow                                                        │    │
│  └───────────────────────────────────────────────────────────────────────┘    │
│                                     │                                           │
│  ┌─────────────────────────────────┼───────────────────────────────────────┐  │
│  │        CompanyState (全局共享状态)                                          │  │
│  │  • agents: Dict[AgentRole, AgentState]  │  tasks: Dict[str, Task]         │  │
│  │  • messages: List[Message]              │  kpis: Dict[str, float]         │  │
│  │  • strategic_goals, market_data, user_feedback...                         │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│                                     │                                           │
│  ┌─────────────────────────────────┼───────────────────────────────────────┐  │
│  │                    10 个专业智能体 (AI Agents)                            │  │
│  │  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ │  │
│  │  │CEO │ │CTO │ │CPO │ │CMO │ │CFO │ │ HR │ │RD  │ │DATA│ │CS  │ │OPS │ │  │
│  │  └─────┘ └─────┘ └─────┘ └─────┘ └─────┘ └─────┘ └─────┘ └─────┘ └─────┘ │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│                                     │                                           │
│  ┌─────────────────────────────────┼───────────────────────────────────────┐  │
│  │                         配置管理层 (Config)                              │  │
│  │  • config.yaml (YAML 配置文件)                                          │  │
│  │  • 所有模型配置 (base_url, model, api_key)                             │  │
│  │  • 公司配置 (战略目标、KPIs、市场数据)                                  │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

## 3. 核心数据模型

### 3.1 智能体角色枚举 (AgentRole)

```python
class AgentRole(Enum):
    CEO              # 首席执行官
    CTO              # 首席技术官
    CPO              # 首席产品官
    CMO              # 首席市场官
    CFO              # 首席财务官
    HR               # 人力资源
    RD               # 研发工程师
    DATA_ANALYST     # 数据分析师
    CUSTOMER_SUPPORT # 客户支持
    OPERATIONS       # 运营专员
```

### 3.2 消息系统 (Message)

| 字段 | 类型 | 说明 |
|------|------|------|
| sender | AgentRole | 发送者角色 |
| recipient | AgentRole | 接收者角色 |
| message_type | MessageType | 消息类型（任务分配/状态报告/审批请求等） |
| content | Dict[str, Any] | 消息内容 |
| priority | Priority | 优先级（低/中/高/紧急） |
| timestamp | datetime | 时间戳 |
| message_id | str | 唯一消息ID |

### 3.3 任务系统 (Task)

| 字段 | 类型 | 说明 |
|------|------|------|
| task_id | str | 任务唯一ID |
| title | str | 任务标题 |
| description | str | 任务描述 |
| assigned_to | AgentRole | 分配给的角色 |
| assigned_by | AgentRole | 分配者角色 |
| priority | Priority | 优先级 |
| status | str | 任务状态（pending/in_progress/completed/failed） |
| dependencies | List[str] | 依赖的任务ID列表 |
| deliverables | List[str] | 交付成果列表 |
| deadline | Optional[datetime] | 截止日期 |

### 3.4 全局状态 (CompanyState)

```python
class CompanyState(TypedDict):
    agents: Dict[AgentRole, AgentState]      # 所有智能体状态
    tasks: Dict[str, Task]                    # 所有任务
    messages: List[Message]                   # 所有消息
    current_time: datetime                    # 当前时间
    strategic_goals: Dict[str, Any]           # 战略目标
    kpis: Dict[str, float]                    # 关键绩效指标
    market_data: Dict[str, Any]               # 市场数据
    user_feedback: List[Dict[str, Any]]       # 用户反馈
    system_health: Dict[str, Any]             # 系统健康
    budget_allocation: Dict[str, Any]         # 预算分配
    technical_debt: List[Dict[str, Any]]      # 技术债
     # ... 更多字段
 ```

 ## 4. 编排器工作流 (Orchestrator Workflow)

### 5.1 状态图结构

```
┌──────────────────────────────────────────────────────────────┐
│              CompanyOrchestrator StateGraph                  │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  入口点: OPERATIONS                                          │
│                                                              │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐             │
│  │  OPERATIONS├─→│   CEO      ├─────→│   CTO      │             │
│  └────────────┘  └────────────┘  │    └────────────┘             │
│                                   │                              │
│                                   ├─────→│   CPO      │             │
│                                   │    └────────────┘             │
│                                   │        │                      │
│                                   │        ↓                      │
│                                   │  ┌────────────┐              │
│                                   └─→│ CUSTOMER_SUPPORT │       │
│                                      └────────────┘              │
│                                                              │
│                                   ┌────────────┐              │
│                                   │   CMO      │             │
│                                   └────────────┘              │
│                                                              │
│                                   ┌────────────┐              │
│                                   │   CFO      │             │
│                                   └────────────┘              │
│                                                              │
│  CEO → CTO → RD                                              │
│  CEO → CPO → CUSTOMER_SUPPORT                                │
│  CEO → CMO                                                   │
│  CEO → CFO                                                   │
│  OPERATIONS → END                                            │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### 5.2 智能体节点处理逻辑

```python
async def agent_node(state: CompanyState) -> CompanyState:
    agent = agents.get(role)
    
    # 1. 处理挂起消息
    messages = state.get("messages", [])
    for message in messages:
        if message.recipient == role:
            response = await agent.process_message(message, state)
            if response:
                state["messages"].append(response)
    
    return state
```

## 6. 配置系统架构

### 6.1 配置结构树

```
config.yaml
├── llm (LLM 配置)
│   ├── models (模型列表)
│   │   ├── name (模型名称)
│   │   ├── base_url (API 基础 URL)
│   │   ├── model (实际模型名称)
│   │   ├── api_key (API 密钥)
│   │   ├── default (是否为默认模型)
│   │   ├── capabilities (能力列表)
│   │   └── config (模型配置: temperature, max_tokens...)
│   └── default_model (默认模型名称)
├── company (公司配置)
│   ├── name, description, created_at
│   ├── strategic_goals (战略目标)
│   ├── kpis (KPIs)
│   ├── resources (资源配置)
│   └── market_data (市场数据)
├── agents (智能体配置)
│   ├── {role_name}
│   │   ├── model (使用的模型)
│   │   ├── temperature
│   │   └── capabilities
├── communication (通信协议配置)
│   ├── timeout
│   ├── retry
│   └── qos (服务质量)
├── workflow (工作流配置)
│   ├── state_graph
│   ├── scheduling
│   └── automated_workflows
├── security (安全配置)
├── monitoring (监控配置)
├── performance (性能配置)
└── other (其他配置)
```

### 6.2 模型配置示例

```yaml
llm:
  models:
    - name: "gpt-4"
      base_url: "https://api.openai.com/v1"
      model: "gpt-4"
      api_key: ${OPENAI_API_KEY}
      default: true
      capabilities:
        - "strategic_planning"
        - "complex_analysis"
      config:
        temperature: 0.2
        max_tokens: 4096
    
    - name: "claude-3-opus"
      base_url: "https://api.anthropic.com/v1"
      model: "claude-3-opus-20240229"
      api_key: ${ANTHROPIC_API_KEY}
      default: false
```

## 7. 消息类型说明

### 7.1 消息类型 (MessageType)

| 类型 | 说明 | 使用场景 |
|------|------|----------|
| TASK_ASSIGNMENT | 任务分配 | CEO 分配任务给 CPO/CTO |
| STATUS_REPORT | 状态报告 | 各 C-level 汇报周报 |
| DATA_REQUEST | 数据请求 | CFO 请求数据分析 |
| DATA_RESPONSE | 数据响应 | DataAnalyst 响应数据请求 |
| APPROVAL_REQUEST | 审批请求 | R&D 请求代码审查通过 |
| APPROVAL_RESPONSE | 审批响应 | CTO 批准/拒绝 PR |
| ALERT | 警报 | 运营专员发出系统异常告警 |
| COLLABORATION | 协作请求 | 跨角色协作需求 |

### 7.2 优先级系统 (Priority)

| 级别 | 说明 | 超时时间 |
|------|------|----------|
| LOW | 低优先级 | 默认(30s) |
| MEDIUM | 中等优先级 | 默认(30s) |
| HIGH | 高优先级 | 10s |
| CRITICAL | 紧急优先级 | 5s |

## 8. 技术栈

| 层级 | 技术选型 | 说明 |
|------|----------|------|
| **智能体编排** | LangGraph | 状态图编排，支持复杂工作流 |
| **LLM 接口** | LangChain | 统一的 LLM 接口 |
| **消息通信** | JSON-RPC / REST API | 异步消息传递 |
| **配置管理** | YAML | config.yaml |
| **状态存储** | 内存 + JSON 文件 | 公司状态持久化 |
| **单元测试** | Pytest | 测试框架 |
| **类型检查** | Type Hints | Python 类型提示 |

## 9. 运行机制

### 9.1 系统启动流程

```python
# main.py
async def main():
    orchestrator = CompanyOrchestrator()  # 创建编排器
    
    # 加载配置
    app_config = AppConfig.from_yaml()
    
    # 启动交互模式
    while True:
        cmd = input("> ").strip()
        if cmd == "status":
            await orchestrator.get_status()
        elif cmd == "report":
            await orchestrator.generate_report()
        elif cmd == "run-test":
            state = await orchestrator.run_simulation(steps=5)
```

### 9.2 模拟执行流程

```
run_simulation(steps=5):
    1. 创建初始状态
    2. for step in range(5):
        - step 0: CEO 发起战略规划任务
        - step 1-4: 各智能体处理消息并响应
    3. 返回最终状态
```

### 9.3 消息处理流程

```
process_message(message, state):
    1. 检查接收者是否匹配当前角色
    2. 根据 message_type 调用对应处理器
    3. 生成响应消息
    4. 更新全局状态
    5. 返回响应
```

## 10. 扩展性设计

### 10.1 新增角色

1. 在 `AgentRole` 枚举中添加新角色
2. 创建对应的智能体类（继承 `BaseAgent`）
3. 在 `agents/config.yaml` 中添加角色配置
4. 在 `orchestrator.py` 中添加节点和工作流

### 10.2 新增消息类型

1. 在 `MessageType` 枚举中添加新类型
2. 在智能体中实现对应的处理器
3. 更新 `process_message` 的消息路由逻辑

### 10.3 新增模型

在 `config.yaml` 的 `llm.models` 列表中添加：

```yaml
    - name: "gemini-pro"
      base_url: "https://generativelanguage.googleapis.com/v1beta"
      model: "gemini-pro"
      api_key: ${GEMINI_API_KEY}
      default: false
      capabilities: [...]
```

## 11. 监控与运维

### 11.1 关键指标

| 指标 | 说明 | 阈值 |
|------|------|------|
| API 调用延迟 | 从发送到接收的耗时 | >5s 需要告警 |
| 任务完成率 | 完成任务数 / 总任务数 | <90% 需要关注 |
| 智能体响应时间 | 从消息到达到响应的耗时 | >10s 需要告警 |
| 消息积压量 | 待处理消息数量 | >100 需要扩容 |

### 11.2 日志结构

```json
{
  "timestamp": "2026-02-05T10:30:00Z",
  "level": "INFO",
  "message": "Task completed",
  "agent": "rd",
  "task_id": "task_abc123",
  "duration_ms": 1500
}
```

## 12. 许可证

Apache-2.0
