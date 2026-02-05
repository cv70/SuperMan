# SuperMan AI 多智能体公司架构设计文档 (Arch.md)

## 1. 概述

### 1.1 项目定位

SuperMan 是一个完整的 AI 公司架构模拟系统，通过 10 个专业智能体（AI Agents）模拟真实企业中的组织结构、决策流程与协作机制。系统采用 **Go 语言** 实现，使用 **Mailbox 消息队列系统** 进行异步通信，每个智能体具备独立的决策能力和专业技能边界，共同构成一个自我演进的闭环企业系统。

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
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              SuperMan AI 公司系统 (Go实现)                            │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                       │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │                         Orchestrator (编排器)                                  │   │
│  │  • 集成 MailboxManager 消息管理器                                             │   │
│  │  • 管理10个智能体节点                                                          │   │
│  │  • 路由消息 flow                                                              │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                     │                                                 │
│  ┌──────────────────────────────────┼────────────────────────────────────────┐    │
│  │  ┌────────────────────────────────────────────────────────────────────┐  │    │
│  │  │                    Mailbox System (消息队列系统)                      │  │    │
│  │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │  │    │
│  │  │  │CEO Mailbox │  │CTO Mailbox │  │CPO Mailbox │  ... (10个)       │  │    │
│  │  │  │• 优先级队列 │  │• 优先级队列 │  │• 优先级队列 │                  │  │    │
│  │  │  │• 幂等性检查 │  │• 幂等性检查 │  │• 幂等性检查 │                  │  │    │
│  │  │  │• 超时处理   │  │• 超时处理   │  │• 超时处理   │                  │  │    │
│  │  │  └─────────────┘  └─────────────┘  └─────────────┘                 │  │    │
│  │  │  • MailboxManager: 统一管理、指标收集、死信队列(DLQ)                  │  │    │
│  │  └────────────────────────────────────────────────────────────────────┘  │    │
│  └──────────────────────────────────┼────────────────────────────────────────┘    │
│                                     │                                                 │
│  ┌──────────────────────────────────┼────────────────────────────────────────┐    │
│  │        CompanyState (全局共享状态)                                            │    │
│  │  • agents: map[AgentRole]*AgentState  │  tasks: map[string]*Task           │    │
│  │  • messages: []*Message                │  kpis: map[string]float64          │    │
│  │  • strategic_goals, market_data, user_feedback...                           │    │
│  └────────────────────────────────────────────────────────────────────────────┘    │
│                                     │                                                 │
│  ┌──────────────────────────────────┼────────────────────────────────────────┐    │
│  │                    10 个专业智能体 (AI Agents)                                │    │
│  │  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐   │    │
│  │  │CEO  │ │CTO  │ │CPO  │ │CMO  │ │CFO  │ │ HR  │ │RD   │ │DATA │ │CS   │ │OPS  │   │    │
│  │  └─────┘ └─────┘ └─────┘ └─────┘ └─────┘ └─────┘ └─────┘ └─────┘ └─────┘   │    │
│  └────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                       │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

## 3. 核心数据模型

### 3.1 智能体角色枚举 (AgentRole)

```go
type AgentRole string

const (
    AgentRoleCEO             AgentRole = "ceo"
    AgentRoleCTO             AgentRole = "cto"
    AgentRoleCPO             AgentRole = "cpo"
    AgentRoleCMO             AgentRole = "cmo"
    AgentRoleCFO             AgentRole = "cfo"
    AgentRoleHR              AgentRole = "hr"
    AgentRoleRD              AgentRole = "rd"
    AgentRoleDataAnalyst     AgentRole = "data_analyst"
    AgentRoleCustomerSupport AgentRole = "customer_support"
    AgentRoleOperations      AgentRole = "operations"
)
```

### 3.2 消息系统 (Message)

**基础消息结构 (`agents` 包):**

| 字段 | 类型 | 说明 |
|------|------|------|
| sender | AgentRole | 发送者角色 |
| receiver | AgentRole | 接收者角色 |
| message_type | MessageType | 消息类型（任务分配/状态报告/审批请求等） |
| content | map[string]any | 消息内容 |
| priority | Priority | 优先级（低/中/高/紧急） |
| timestamp | time.Time | 时间戳 |
| message_id | string | 唯一消息ID |

**Mailbox 消息结构 (`mailbox` 包):**

```go
type Message struct {
    MessageID      string                 // 唯一消息ID
    Sender         agents.AgentRole       // 发送者
    Receiver       agents.AgentRole       // 接收者
    MessageType    agents.MessageType     // 消息类型
    Content        map[string]interface{} // 消息内容
    Priority       agents.Priority        // 优先级
    Timestamp      time.Time              // 时间戳
    Context        *MessageContext        // 追踪上下文（可选）
    IdempotencyKey string                 // 幂等键（可选）
}
```

### 3.3 Mailbox 系统架构

#### 3.3.1 核心组件

| 组件 | 功能 | 关键特性 |
|------|------|----------|
| **Mailbox** | 单个Agent的消息收件箱 | 优先级队列、异步处理、超时控制、重试机制 |
| **MailboxManager** | 统一管理所有Mailbox | 生命周期管理、指标收集、死信队列(DLQ) |
| **PriorityQueue** | 优先级消息队列 | 支持 Critical > High > Medium > Low |
| **IdempotencyChecker** | 幂等性检查 | 防止重复处理，24小时窗口 |
| **DeadLetterQueue** | 死信队列 | 存储处理失败的消息（可选SQLite持久化） |
| **Metrics** | 指标收集 | 消息吞吐量、延迟、队列深度、处理成功率 |

#### 3.3.2 Mailbox 处理流程

```
发送消息 → Inbox Channel → Priority Queue → 处理Handler → 结果统计
                                          ↓
                                    [幂等性检查]
                                          ↓
                                    [超时控制]
                                          ↓
                                    [失败重试] → [DLQ] (超过最大重试次数)
```

#### 3.3.3 配置参数

```go
type MailboxConfig struct {
    Receiver          agents.AgentRole                  // 接收者角色
    InboxBufferSize   int                               // 收件箱channel缓冲区大小 (默认: 1000)
    MaxRetries        int                               // 最大重试次数 (默认: 3)
    BaseDelay         time.Duration                     // 基础退避延迟 (默认: 1s)
    MaxDelay          time.Duration                     // 最大退避延迟 (默认: 5min)
    ProcessingTimeout map[agents.Priority]time.Duration // 各优先级超时
    MaxQueueDepth     int                               // 最大队列深度 (默认: 10000)
    EnableDLQ         bool                              // 是否启用死信队列
}
```

### 3.4 任务系统 (Task)

| 字段 | 类型 | 说明 |
|------|------|------|
| task_id | string | 任务唯一ID |
| title | string | 任务标题 |
| description | string | 任务描述 |
| assigned_to | AgentRole | 分配给的角色 |
| assigned_by | AgentRole | 分配者角色 |
| priority | Priority | 优先级 |
| status | string | 任务状态（pending/in_progress/completed/failed） |
| dependencies | []string | 依赖的任务ID列表 |
| deliverables | []string | 交付成果列表 |
| deadline | *time.Time | 截止日期（可选） |

### 3.5 全局状态 (CompanyState)

```go
type CompanyState struct {
    Agents               map[AgentRole]*AgentState      // 所有智能体状态
    Tasks                map[string]*Task                // 所有任务
    Messages             []*Message                      // 所有消息
    CurrentTime          time.Time                       // 当前时间
    StrategicGoals       map[string]any                  // 战略目标
    KPIs                 map[string]float64              // 关键绩效指标
    MarketData           map[string]any                  // 市场数据
    UserFeedback         []map[string]any                // 用户反馈
    SystemHealth         map[string]any                  // 系统健康
    BudgetAllocation     map[string]any                  // 预算分配
    TechnicalDebt        []map[string]any                // 技术债
    // ... 更多字段
}
```

## 4. 编排器工作流 (Orchestrator Workflow)

### 4.1 架构概览

```
┌─────────────────────────────────────────────────────────────────┐
│                      Orchestrator (编排器)                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                     核心方法                               │  │
│  │  • RegisterAgent(role, agent)    // 注册智能体            │  │
│  │  • RunTask(task)                 // 通过Mailbox分配任务   │  │
│  │  • SendMessage(msg)              // 发送消息              │  │
│  │  • SendMessageTo(...)            // 发送消息到指定角色    │  │
│  │  • Start() / Stop()              // 启停Mailbox系统       │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                              ↓                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                  MailboxManager                           │  │
│  │  • RegisterMailbox(role, handler)  // 注册Mailbox         │  │
│  │  • Send(msg) / SendTo(...)         // 发送消息            │  │
│  │  • Start() / Stop()                // 启停所有Mailbox     │  │
│  │  • GetAllStats()                   // 获取统计信息        │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                   │
│              ┌───────────────┼───────────────┐                   │
│              ↓               ↓               ↓                   │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐        │
│  │ CEO Mailbox   │  │ CTO Mailbox   │  │ CPO Mailbox   │ ...    │
│  │ ┌───────────┐ │  │ ┌───────────┐ │  │ ┌───────────┐ │        │
│  │ │ Priority  │ │  │ │ Priority  │ │  │ │ Priority  │ │        │
│  │ │   Queue   │ │  │ │   Queue   │ │  │ │   Queue   │ │        │
│  │ └───────────┘ │  │ └───────────┘ │  │ └───────────┘ │        │
│  │ ┌───────────┐ │  │ ┌───────────┐ │  │ ┌───────────┐ │        │
│  │ │  Handler  │ │  │ │  Handler  │ │  │ │  Handler  │ │        │
│  │ │  (Agent)  │ │  │ │  (Agent)  │ │  │ │  (Agent)  │ │        │
│  │ └───────────┘ │  │ └───────────┘ │  │ └───────────┘ │        │
│  └───────────────┘  └───────────────┘  └───────────────┘        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 消息路由流程

```
发送任务/消息
     │
     ↓
┌─────────────────┐
│  Orchestrator   │
│  .RunTask()     │
│  .SendMessage() │
└────────┬────────┘
         │
         ↓
┌─────────────────┐     ┌─────────────────┐
│ MailboxManager  │────→│   StateManager  │
│    .SendTo()    │     │   .AddTask()    │
└────────┬────────┘     └─────────────────┘
         │
         ↓
┌─────────────────┐
│  Target Mailbox │
│   .Send(msg)    │
└────────┬────────┘
         │
         ↓
┌─────────────────┐     ┌─────────────────┐
│  PriorityQueue  │────→│  Agent Handler  │
│   .Enqueue()    │     │ processMessage()│
└─────────────────┘     └─────────────────┘
```

### 4.3 智能体消息处理逻辑

```go
// createAgentMessageHandler 创建Agent的mailbox消息处理器
func createAgentMessageHandler(agent interface{}, stateManager StateManager) mailbox.MessageHandler {
    return func(msg *mailbox.Message) error {
        // 将mailbox消息转换为agents消息格式
        agentMsg := &agents.Message{
            MessageID:   msg.MessageID,
            Sender:      msg.Sender,
            Receiver:    msg.Receiver,
            MessageType: agents.MessageType(msg.MessageType),
            Content:     convertMailboxContent(msg.Content),
            Priority:    agents.Priority(msg.Priority),
            Timestamp:   msg.Timestamp,
        }
        
        // 将消息添加到stateManager
        stateManager.AddMessage(agentMsg)
        
        // 如果agent实现了BaseAgent接口，调用ProcessMessage
        if baseAgent, ok := agent.(agents.BaseAgent); ok {
            return baseAgent.ProcessMessage(agentMsg)
        }
        
        return nil
    }
}
```

## 5. 配置系统架构

### 5.1 项目结构

```
superman/
├── main.go                      # 程序入口
├── go.mod / go.sum             # Go模块依赖
├── ARCH.md                      # 架构文档
├── deploy.md                    # 部署文档
├── README.md                    # 项目说明
├── agents/                      # 智能体定义
│   ├── agents.go               # 角色、消息、任务、状态定义
│   ├── agent_base.go           # BaseAgent接口和实现
│   ├── ceo.go                  # CEO智能体
│   ├── cto.go                  # CTO智能体
│   ├── cpo.go                  # CPO智能体
│   ├── cmo.go                  # CMO智能体
│   ├── cfo.go                  # CFO智能体
│   ├── hr.go                   # HR智能体
│   ├── rd.go                   # 研发智能体
│   ├── data_analyst.go         # 数据分析师
│   ├── customer_support.go     # 客户支持
│   └── operations.go           # 运营专员
├── mailbox/                     # Mailbox消息系统
│   ├── mailbox.go              # Mailbox核心实现
│   ├── manager.go              # MailboxManager管理器
│   ├── message.go              # 消息结构定义
│   ├── priority_queue.go       # 优先级队列
│   ├── idempotency.go          # 幂等性检查
│   ├── dead_letter.go          # 死信队列(DLQ)
│   ├── metrics.go              # 指标收集
│   └── mailbox_test.go         # 单元测试
├── workflow/                    # 工作流编排
│   ├── orchestrator.go         # 编排器实现
│   ├── state_manager.go        # 状态管理
│   └── message_router.go       # 消息路由
├── config/                      # 配置管理
└── utils/                       # 工具函数
```

### 5.2 Mailbox 配置

```go
// MailboxManagerConfig 管理器配置
type MailboxManagerConfig struct {
    DLQConfig            *DLQConfig            // 死信队列配置
    IdempotencyMaxSize   int                   // 幂等缓存最大大小 (默认: 100000)
    IdempotencyWindow    int                   // 幂等窗口（小时）(默认: 24)
    EnableMetrics        bool                  // 是否启用指标 (默认: true)
    EnableDLQ            bool                  // 是否启用DLQ (默认: true，需要SQLite)
    DefaultMailboxConfig *MailboxConfig        // 默认Mailbox配置
}

// 默认配置示例
config := &MailboxManagerConfig{
    DLQConfig:          DefaultDLQConfig(),
    IdempotencyMaxSize: 100000,
    IdempotencyWindow:  24,
    EnableMetrics:      true,
    EnableDLQ:          false,  // 如果无CGO支持，设为false
}
```

## 6. 消息类型说明

### 6.1 消息类型 (MessageType)

```go
const (
    MessageTypeTaskAssignment MessageType = iota   // 任务分配
    MessageTypeStatusReport                         // 状态报告
    MessageTypeDataRequest                          // 数据请求
    MessageTypeDataResponse                         // 数据响应
    MessageTypeApprovalRequest                      // 审批请求
    MessageTypeApprovalResponse                     // 审批响应
    MessageTypeAlert                                // 警报
    MessageTypeCollaboration                        // 协作请求
)
```

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

### 6.2 优先级系统 (Priority)

```go
const (
    PriorityLow Priority = iota      // 低优先级
    PriorityMedium                   // 中等优先级
    PriorityHigh                     // 高优先级
    PriorityCritical                 // 紧急优先级
)
```

| 级别 | 说明 | 默认超时时间 | 用途 |
|------|------|-------------|------|
| LOW | 低优先级 | 60s | 批量任务、非紧急通知 |
| MEDIUM | 中等优先级 | 30s | 普通任务分配、常规报告 |
| HIGH | 高优先级 | 10s | 重要审批、紧急数据请求 |
| CRITICAL | 紧急优先级 | 5s | 系统告警、紧急故障 |

### 6.3 优先级队列实现

```go
type PriorityQueue struct {
    queues map[agents.Priority][]*Message  // 按优先级分队列
    mu     sync.RWMutex
}

// 出队顺序: Critical > High > Medium > Low
func (pq *PriorityQueue) Dequeue() *Message {
    // 优先处理 Critical 消息
    if len(pq.queues[agents.PriorityCritical]) > 0 {
        msg := pq.queues[agents.PriorityCritical][0]
        pq.queues[agents.PriorityCritical] = pq.queues[agents.PriorityCritical][1:]
        return msg
    }
    // 其次处理 High 消息
    if len(pq.queues[agents.PriorityHigh]) > 0 {
        msg := pq.queues[agents.PriorityHigh][0]
        pq.queues[agents.PriorityHigh] = pq.queues[agents.PriorityHigh][1:]
        return msg
    }
    // ... Medium, Low
}
```

## 7. 技术栈

| 层级 | 技术选型 | 说明 |
|------|----------|------|
| **编程语言** | Go 1.24+ | 高性能、原生并发支持 |
| **智能体框架** | Google ADK | Google Agent Development Kit |
| **消息队列** | Mailbox (自研) | 基于 Go Channel 的异步消息系统 |
| **消息通信** | 异步消息传递 | 支持优先级、幂等性、超时控制 |
| **配置管理** | YAML / 代码配置 | 灵活的配置方式 |
| **状态存储** | 内存 | 运行时状态管理 |
| **单元测试** | Go testing | 标准测试框架 |
| **依赖管理** | Go Modules | 标准依赖管理 |

### 7.1 Mailbox 技术特性

| 特性 | 实现方式 | 说明 |
|------|---------|------|
| **异步处理** | Go Channel + Goroutine | 非阻塞消息投递 |
| **优先级队列** | 多级队列 | Critical/High/Medium/Low |
| **幂等性保证** | LRU Cache + 时间窗口 | 防止重复处理 |
| **超时控制** | Context.WithTimeout | 各优先级独立超时 |
| **重试机制** | 指数退避 | 最多3次重试，1s~5min退避 |
| **死信队列** | SQLite (可选) | 持久化失败消息 |
| **指标收集** | 内存统计 | 实时消息统计 |

## 8. 运行机制

### 8.1 系统启动流程

```go
// main.go
func main() {
    // 1. 初始化配置
    config.InitConfig()
    ctx := context.Background()

    // 2. 创建核心组件
    companyState := agents.CreateEmptyState()
    stateManager := workflow.NewStateManager(companyState)
    router := workflow.NewMessageRouter()
    
    // 3. 创建Mailbox管理器
    mailboxConfig := mailbox.DefaultMailboxManagerConfig()
    mailboxConfig.EnableDLQ = false  // 禁用DLQ避免CGO依赖
    mailboxManager, err := mailbox.NewMailboxManager(mailboxConfig)
    
    // 4. 创建编排器
    orchestrator := workflow.NewOrchestrator(stateManager, router, mailboxManager)

    // 5. 注册所有Agent和Mailbox
    agentsMap := map[agents.AgentRole]interface{}{
        agents.AgentRoleCEO:             agents.NewCEOAgent(),
        agents.AgentRoleCTO:             agents.NewCTOAgent(),
        // ... 其他8个Agent
    }
    
    for role, agent := range agentsMap {
        stateManager.CreateAgentState(role)
        orchestrator.RegisterAgent(role, agent)
        
        // 为每个agent注册mailbox handler
        handler := createAgentMessageHandler(agent, stateManager)
        mailboxManager.RegisterMailbox(role, handler)
    }

    // 6. 启动Mailbox系统
    orchestrator.Start()

    // 7. 启动ADK Launcher
    launcher := full.NewLauncher()
    launcher.Execute(ctx, nil, os.Args[1:])
}
```

### 8.2 消息生命周期

```
┌─────────────────────────────────────────────────────────────────────┐
│                         消息生命周期                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  1. 创建消息                                                          │
│     msg := mailbox.NewMessage(sender, receiver, msgType, content)   │
│                              │                                       │
│                              ↓                                       │
│  2. 设置属性                                                          │
│     msg.WithPriority(agents.PriorityHigh)                           │
│     msg.WithIdempotencyKey("unique-key")                            │
│                              │                                       │
│                              ↓                                       │
│  3. 发送消息                                                          │
│     mailboxManager.Send(msg) 或 orchestrator.SendMessage(msg)       │
│                              │                                       │
│                              ↓                                       │
│  4. 入队                                                              │
│     Target Mailbox → Inbox Channel → Priority Queue                 │
│                              │                                       │
│                              ↓                                       │
│  5. 处理                                                              │
│     ┌──────────────────────────────────────────────┐                │
│     │ • 幂等性检查                                  │                │
│     │ • 超时控制 (Context.WithTimeout)             │                │
│     │ • 调用 Agent Handler                         │                │
│     │ • 成功: 记录指标                              │                │
│     │ • 失败: 重试 (最多3次) → DLQ (可选)          │                │
│     └──────────────────────────────────────────────┘                │
│                              │                                       │
│                              ↓                                       │
│  6. 更新状态                                                          │
│     StateManager.AddMessage()                                       │
│     Agent.ProcessMessage()                                          │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 8.3 指标收集

```go
// Metrics 指标收集器
type Metrics struct {
    messagesSent        map[string]int64     // 消息发送统计
    messagesReceived    map[string]int64     // 消息接收统计
    messagesProcessed   map[string]int64     // 消息处理统计
    queueDepth          map[string]int64     // 队列深度
    processingDuration  time.Duration        // 处理耗时
    retryCount          map[string]int64     // 重试次数
    dlqDepth            int64                // 死信队列深度
}

// 获取统计快照
stats := mailboxManager.GetAllStats()
// {
//   "mailboxes": {
//     "ceo": {"queue_depth": 5, "processing_count": 2, "started": true},
//     "cto": {"queue_depth": 3, "processing_count": 1, "started": true},
//     ...
//   },
//   "metrics": {
//     "messages_sent_total": {...},
//     "messages_received_total": {...},
//     "messages_processed_total": {...},
//     "processing_duration_avg": 150ms,
//     ...
//   }
// }
```

## 9. 扩展性设计

### 9.1 新增角色

1. **在 `agents/agents.go` 中添加新角色**
```go
const (
    AgentRoleCEO         AgentRole = "ceo"
    // ... 现有角色
    AgentRoleNewRole     AgentRole = "new_role"  // 新角色
)
```

2. **创建对应的智能体类**（在 `agents/` 目录下新建文件）
```go
// agents/new_role.go
type NewRoleAgent struct {
    *BaseAgentImpl
}

func NewNewRoleAgent() *NewRoleAgent {
    return &NewRoleAgent{
        BaseAgentImpl: NewBaseAgent(
            AgentRoleNewRole,
            []string{"capability1", "capability2"},
            3, // hierarchy level
        ),
    }
}

func (a *NewRoleAgent) GetName() string {
    return "new_role_agent"
}
```

3. **在 `main.go` 中注册新Agent**
```go
agentsMap := map[agents.AgentRole]interface{}{
    // ... 现有agent
    agents.AgentRoleNewRole: agents.NewNewRoleAgent(),
}
```

4. **Mailbox 会自动为新角色创建Mailbox**（无需额外配置）

### 9.2 新增消息类型

1. **在 `agents/agents.go` 中添加新消息类型**
```go
const (
    MessageTypeTaskAssignment MessageType = iota
    // ... 现有类型
    MessageTypeNewType        // 新消息类型
)
```

2. **在智能体的 ProcessMessage 中实现处理逻辑**
```go
func (a *NewRoleAgent) ProcessMessage(msg *Message) error {
    switch msg.MessageType {
    case MessageTypeNewType:
        // 处理新消息类型
        return a.handleNewType(msg)
    // ... 其他类型
    }
    return nil
}
```

3. **更新消息路由表**（如需要）
```go
// workflow/message_router.go
func NewMessageRouter() MessageRouter {
    return &messageRouterImpl{
        routingTable: map[agents.MessageType][]agents.AgentRole{
            agents.MessageTypeNewType: {
                agents.AgentRoleNewRole,
                agents.AgentRoleCEO,
            },
        },
    }
}
```

### 9.3 扩展 Mailbox 功能

#### 添加自定义消息处理器
```go
// 创建自定义处理器
customHandler := func(msg *mailbox.Message) error {
    // 自定义处理逻辑
    fmt.Printf("Custom processing: %s\n", msg.MessageID)
    return nil
}

// 注册到Mailbox
mailboxManager.RegisterMailbox(agents.AgentRoleNewRole, customHandler)
```

#### 自定义 Mailbox 配置
```go
config := &mailbox.MailboxConfig{
    Receiver:        agents.AgentRoleNewRole,
    InboxBufferSize: 2000,           // 更大的缓冲区
    MaxRetries:      5,              // 更多重试次数
    BaseDelay:       2 * time.Second, // 更长退避
    MaxQueueDepth:   50000,          // 更大队列深度
    EnableDLQ:       true,
    ProcessingTimeout: map[agents.Priority]time.Duration{
        agents.PriorityCritical: 10 * time.Second,  // 自定义超时
        agents.PriorityHigh:     20 * time.Second,
        agents.PriorityMedium:   60 * time.Second,
        agents.PriorityLow:      120 * time.Second,
    },
}

mb, _ := mailbox.NewMailbox(config, idChecker, dlq, metrics)
```

## 10. 监控与运维

### 10.1 Mailbox 关键指标

| 指标 | 说明 | 告警阈值 |
|------|------|---------|
| message_sent_total | 消息发送总数 | - |
| message_received_total | 消息接收总数 | - |
| messages_processed_total | 消息处理统计（success/failed）| failed > 10% 告警 |
| mailbox_queue_depth | 各Mailbox队列深度 | > 5000 需要关注 |
| processing_duration_avg | 平均处理耗时 | > 5s 需要优化 |
| processing_duration_p99 | P99处理耗时 | > 10s 需要告警 |
| mailbox_retry_total | 重试次数统计 | 持续增长需要关注 |
| dlq_depth_total | 死信队列深度 | > 0 需要检查 |

### 10.2 运行时统计获取

```go
// 获取所有Mailbox统计
stats := orchestrator.GetMailboxManager().GetAllStats()

// 获取单个Mailbox状态
mb, _ := orchestrator.GetMailboxManager().GetMailbox(agents.AgentRoleCEO)
queueDepth := mb.GetQueueDepth()
processingCount := mb.GetProcessingCount()

// 获取指标快照
metrics := orchestrator.GetMailboxManager().GetMetrics()
snapshot := metrics.GetSnapshot()
```

### 10.3 日志结构

```go
// 系统启动日志
2026-02-07T20:12:09 [INFO] SuperMan AI Multi-Agent Company System starting...
2026-02-07T20:12:09 [INFO] Creating AI agents...
2026-02-07T20:12:09 [INFO]   Created: ceo_agent (ceo)
2026-02-07T20:12:09 [INFO]   Created: cto_agent (cto)
...
2026-02-07T20:12:09 [INFO] Starting Mailbox system...
2026-02-07T20:12:09 [INFO] Mailbox system started successfully

// 消息处理日志（在Handler中自定义）
2026-02-07T20:12:10 [DEBUG] [ceo] Received message from cto: msg_abc123
2026-02-07T20:12:10 [INFO]  [ceo] Processed task assignment: task_xyz789
2026-02-07T20:12:11 [WARN]  [cto] Message processing timeout: msg_def456
2026-02-07T20:12:11 [ERROR] [rd] Failed to process message: err_details
```

### 10.4 健康检查

```go
// 检查Mailbox系统状态
func HealthCheck(orchestrator workflow.Orchestrator) map[string]interface{} {
    mm := orchestrator.GetMailboxManager()
    
    return map[string]interface{}{
        "mailbox_manager_started": mm.IsStarted(),
        "all_mailboxes": mm.GetAllStats(),
        "timestamp": time.Now(),
    }
}
```

## 12. 许可证

Apache-2.0
