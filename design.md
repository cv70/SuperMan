# SuperMan AI Multi-Agent System -- 设计报告与开发报告

**日期**: 2026-02-16
**版本**: v2.0
**范围**: 系统架构分析、现状评估、优化方案、自主运行设计

---

## 目录

1. [项目概述](#1-项目概述)
2. [现有架构分析](#2-现有架构分析)
3. [代码结构与模块分析](#3-代码结构与模块分析)
4. [核心问题诊断](#4-核心问题诊断)
5. [优化方案设计：消息传输系统](#5-优化方案设计消息传输系统)
6. [优化方案设计：任务分配与调度](#6-优化方案设计任务分配与调度)
7. [优化方案设计：Skills 与配置文件驱动的 Agent 扩展](#7-优化方案设计skills-与配置文件驱动的-agent-扩展)
8. [优化方案设计：24/7 自主运行](#8-优化方案设计247-自主运行)
9. [目标架构总览](#9-目标架构总览)
10. [实施路线图](#10-实施路线图)

---

## 1. 项目概述

### 1.1 项目定位

SuperMan 是一个基于 Go 语言的多智能体 AI 公司系统。系统通过 11 个具有不同职能角色的 AI Agent 模拟完整的企业组织，涵盖从董事长到一线运营的完整层级体系。每个 Agent 由 LLM（通义千问）驱动，具备独立思考、任务执行和跨角色协作能力。

### 1.2 技术栈

| 层级 | 技术 | 用途 |
|------|------|------|
| 语言 | Go 1.24 | 高并发、goroutine 原生支持 |
| AI 框架 | Cloudwego Eino ADK | Agent 构建、Tool Calling、Skill 中间件 |
| LLM | 通义千问 (Qwen) | 推理与决策引擎 |
| 持久化 | SQLite + GORM | 轻量级数据库 |
| 配置 | YAML | 系统与 Agent 配置 |
| 唯一 ID | UUID v7 | 有序、时间可排序 |

### 1.3 Agent 角色体系

```
Hierarchy 0:  Chairman (董事长)
Hierarchy 1:  CEO (首席执行官)
Hierarchy 2:  CTO | CPO | CMO | CFO | HR
Hierarchy 3:  R&D | Data Analyst | Customer Support | Operations
```

---

## 2. 现有架构分析

### 2.1 系统组件拓扑

```
                        ┌──────────────┐
                        │  config.yaml │
                        └──────┬───────┘
                               │ InitConfig()
                               ▼
┌──────────────────────────────────────────────────────────┐
│                        main.go                            │
│                                                           │
│  Registry ──► LLM Models (Qwen)                          │
│            ──► SQLite DB                                  │
│                                                           │
│  MailboxBus ──► 消息中枢                                   │
│  Orchestrator ──► 工作流编排                               │
│  AutoScheduler ──► 任务调度                                │
│                                                           │
│  for each AgentConfig:                                    │
│    ├─ NewBaseAgent(llm, config, skills)                   │
│    ├─ RegisterAgent → Orchestrator                        │
│    ├─ RegisterMailbox → MailboxBus                        │
│    ├─ agent.Start() → goroutine: messageProcessingLoop   │
│    └─ GenerateTasks() → AutoScheduler                    │
│                                                           │
│  Interactive Console (stdin loop)                         │
└──────────────────────────────────────────────────────────┘
```

### 2.2 消息流转路径

```
Agent A (Send)
    │
    ▼
MailboxBus.Send(msg)
    │  根据 msg.Receiver 查找 Mailbox
    ▼
Agent B 的 Mailbox.Inbox (chan *ds.Message, buffer=1000)
    │
    ▼
messageProcessingLoop() [goroutine]
    │
    ├── msg 是 TaskCreate？──► ProcessTask(ctx, task)
    │                              │
    │                              ├─ 更新 currentTasks
    │                              ├─ 更新 GlobalState
    │                              ├─ 调用 LLM agent.Run()
    │                              └─ 记录 ExecutionHistory
    │
    └── msg 是 其他类型？──► ProcessMessage(ctx, msg)
                                │
                                ├─ Request  → handleRequestMessage()
                                ├─ Notification → handleNotificationMessage()
                                ├─ Response → handleResponseMessage()
                                └─ Default → agent.Run() with msg.Body
```

### 2.3 任务调度流程

```
Agent.GenerateTasks() ──► []*ds.Task
         │
         ▼
AutoScheduler.AddTask(task, priority)
         │
         ▼
TaskQueue (per priority: Critical/High/Medium/Low)
         │
         ▼
  ※ 当前缺少：主动从队列取出并分配的循环 ※
```

### 2.4 Skill 加载机制

```
config.yaml 中定义:
  skill_dir: "skills/ceo"

NewBaseAgent() 中:
  skill.NewLocalBackend({BaseDir: agentConfig.SkillDir})
  skill.New(ctx, {Backend, UseChinese: true})

  → 作为 Middleware 注入 deep.New() 的 Agent
```

每个 Skill 是一个 Markdown 文件，路径格式为 `skills/{role}/{category}/skill.md`，描述该角色的某项专业能力。Eino ADK 的 skill 中间件会加载这些文件作为 Agent 的背景知识。

---

## 3. 代码结构与模块分析

### 3.1 文件清单与职责

| 包 | 文件 | 行数 | 职责 | 健壮性评估 |
|---|------|------|------|-----------|
| `main` | main.go | 143 | 入口、初始化、交互控制台 | 缺少 graceful shutdown |
| `agents` | base_agent.go | 689 | Agent 核心实现 | 功能完整，但耦合度高 |
| `config` | config.go | 44 | YAML 配置加载 | 缺少验证和默认值 |
| `ds` | message.go | 256 | 消息类型定义 | 设计合理，类型丰富 |
| `ds` | task.go | 218 | 任务结构定义 | 完备，含 Copy/Clone |
| `mailbox` | mailbox.go | 103 | 单体信箱实现 | PushInbox 可能阻塞 |
| `mailbox` | mailbox_bus.go | 126 | 消息总线 | 缺少错误处理和监控 |
| `scheduler` | auto_scheduler.go | 107 | 任务调度器 | **缺少主动调度循环** |
| `scheduler` | priority_queue.go | 109 | 优先级队列 | O(n^2) 排序算法 |
| `workflow` | orchestrator.go | 153 | 工作流编排 | 消息路由完整 |
| `state` | global_state.go | 462 | 全局状态管理 | 线程安全，字段过多 |
| `state` | agent_state.go | 255 | Agent 状态 | 无线程安全 |
| `tools` | send_message.go | 73 | Agent 间通信工具 | 功能单一但完整 |
| `infra` | registry.go | 34 | 组件注册中心 | 简洁 |
| `infra` | llm.go | 19 | LLM 初始化 | 仅支持 Qwen |
| `infra` | db.go | 17 | 数据库初始化 | 缺少连接配置 |
| `utils` | uuid.go | 12 | UUID 生成 | 使用 v7，合理 |

### 3.2 依赖关系图

```
main
 ├── config
 ├── infra ──► config
 ├── agents ──► config, ds, mailbox, state, tools, utils
 │              ├── eino/adk
 │              ├── eino/adk/middlewares/skill
 │              └── eino/adk/prebuilt/deep
 ├── mailbox ──► ds, state
 ├── scheduler ──► ds, state
 ├── workflow ──► agents, ds, mailbox
 ├── state ──► ds
 ├── ds ──► utils
 └── tools ──► ds, mailbox
```

---

## 4. 核心问题诊断

通过逐行阅读所有源文件，识别出以下关键问题，按严重程度排序：

### 4.1 [严重] AutoScheduler 缺少主动调度循环

**位置**: `scheduler/auto_scheduler.go`

**问题**: AutoScheduler 仅提供了 `AddTask()` 和 `GetTask()` 方法，但系统中 **没有任何地方主动调用 `GetTask()` 来从队列中取出任务并分配给 Agent**。`main.go` 中通过 `GenerateTasks()` 将任务添加到队列后，这些任务永远留在队列中，不会被执行。

**影响**: 系统虽然生成了任务，但自动调度机制完全失效。当前唯一能被执行的任务是通过 MailboxBus 直接发送 TaskCreate 消息到特定 Agent 的任务。

**代码证据**:
```go
// main.go:61-68 -- 任务被加入队列
tasks, err := agent.GenerateTasks(ctx)
for _, task := range tasks {
    schedulerInstance.AddTask(task, scheduler.PriorityMedium)
}
// 此后 schedulerInstance 再未被使用（除了 status 命令显示队列长度）
```

### 4.2 [严重] GenerateTasks 始终返回空列表

**位置**: `agents/base_agent.go:684-688`

**问题**: `GenerateTasks()` 的默认实现始终返回空切片。注释说"子类可以重写此方法"，但 Go 没有继承机制。当前所有 Agent 都是 `BaseAgentImpl` 实例，没有任何角色特定的任务生成逻辑。

**影响**: 系统启动后，没有任何自动生成的任务。Agent 只能响应外部通过控制台发送的消息。

### 4.3 [严重] 消息发送可能永久阻塞

**位置**: `mailbox/mailbox.go:48-50`

```go
func (mb *Mailbox) PushInbox(msg *ds.Message) {
    mb.Inbox <- msg  // 当 buffer 满时，发送方 goroutine 会永久阻塞
}
```

**问题**: 当 Inbox channel 的 1000 容量缓冲区满时，发送方会永久阻塞。如果一个 Agent 的消息处理速度跟不上接收速度，会导致发送方 Agent 也被阻塞，产生级联故障。

**影响**: 在高负载场景下，可能导致整个系统死锁。

### 4.4 [中等] AgentState 无线程安全保护

**位置**: `state/agent_state.go`

**问题**: `AgentState` 的所有方法都没有加锁，但它被多个 goroutine 访问（`BaseAgentImpl` 中的 `messageProcessingLoop`、`ProcessTask`、外部查询等）。

**影响**: 并发读写可能导致 data race 和不可预测的行为。

### 4.5 [中等] GlobalState 字段膨胀

**位置**: `state/global_state.go`

**问题**: GlobalState 包含约 25 个顶级字段（`MarketData`, `CampaignData`, `BrandData`, `CompetitorData` 等），且 `Set()/Get()` 方法固定操作 `SystemHealth` 字段，语义不明确。

**影响**: 随着系统演进，状态管理将变得混乱，难以维护。

### 4.6 [中等] 优先级队列排序算法效率低

**位置**: `scheduler/priority_queue.go:98-108`

**问题**: `sortByPriority()` 使用 O(n^2) 冒泡排序，且在每次 `Dequeue()` 和 `Peek()` 时都执行排序。

**影响**: 当任务队列较大时，性能显著下降。

### 4.7 [中等] 系统缺少 Graceful Shutdown

**位置**: `main.go:136-137`

```go
case "exit":
    os.Exit(0)  // 直接退出，不停止任何 Agent，不持久化状态
```

**问题**: 退出时不调用 Agent.Stop()，不刷新未处理的消息，不持久化内存状态到数据库。

### 4.8 [低等] SendMessage Tool 中 MailboxBus 为 nil

**位置**: `agents/base_agent.go:109`

```go
sendMessage := tools.SendMessage{
    Sender:     agentConfig.Name,
    Receivers:  allAgentNames,
    MailboxBus: mailbox.GetMailboxBus(),  // mailbox 刚创建，bus 还是 nil
}
```

**问题**: `NewMailbox()` 创建时 `MailboxBus` 字段由 config 传入，但 `DefaultMailboxConfig` 不设置 `MailboxBus`。直到 `mailboxBus.RegisterMailbox()` 时才通过 `mailbox.bus = b` 赋值。但 `SendMessage` tool 已经在 `RegisterMailbox` 之前创建，获取到的是 nil。

**影响**: Agent 通过 SendMessage tool 发送消息时会 panic（nil pointer dereference）。

### 4.9 [低等] Task ID 生成冲突

**位置**: `ds/task.go:80-82`

```go
func GenerateTaskID() string {
    return "auto_" + time.Now().Format("20060102_150405")
}
```

**问题**: 精度只到秒，同一秒内生成的多个任务会有相同 ID。

### 4.10 [低等] ExecutionHistoryByAgent 实现错误

**位置**: `state/global_state.go:298-308`

```go
func (gs *GlobalState) GetExecutionHistoryByAgent(name string) []*ExecutionHistory {
    // ...
    for _, h := range gs.CompanyExecHistory {
        _ = name  // name 被忽略了！
        history = append(history, h)  // 返回全部记录
    }
    return history
}
```

**问题**: 参数 `name` 未被使用，函数返回所有执行历史而非特定 Agent 的。

---

## 5. 优化方案设计：消息传输系统

### 5.1 当前问题总结

1. `PushInbox` 阻塞风险 -- channel 满时发送方永久等待
2. 无消息确认机制 -- 消息发送后无法知道是否成功处理
3. 无消息优先级 -- 所有消息平等竞争 channel buffer
4. 无消息持久化 -- 进程崩溃后消息丢失
5. 无流量控制 -- 无法限制消息发送速率
6. 无死信队列 -- 处理失败的消息无处归档

### 5.2 优化方案

#### 5.2.1 非阻塞消息发送

```go
// 改造 PushInbox，增加超时和背压机制
func (mb *Mailbox) PushInbox(msg *ds.Message) error {
    select {
    case mb.Inbox <- msg:
        return nil
    case <-time.After(5 * time.Second):
        // 超时后进入溢出队列或死信队列
        mb.handleOverflow(msg)
        return fmt.Errorf("mailbox full, message queued to overflow")
    }
}
```

#### 5.2.2 消息优先级分级

在 Mailbox 内部引入多级 channel，按消息优先级分流：

```go
type Mailbox struct {
    receiver    string
    priorityInbox [4]chan *ds.Message  // Critical, High, Medium, Low
    overflow    []*ds.Message          // 溢出缓冲
    mu          sync.RWMutex
}

// 消息处理循环中优先读取高优先级队列
func (mb *Mailbox) NextMessage() *ds.Message {
    for _, ch := range mb.priorityInbox {
        select {
        case msg := <-ch:
            return msg
        default:
            continue
        }
    }
    // 所有队列为空，阻塞等待任意一个
    select {
    case msg := <-mb.priorityInbox[0]:
        return msg
    case msg := <-mb.priorityInbox[1]:
        return msg
    case msg := <-mb.priorityInbox[2]:
        return msg
    case msg := <-mb.priorityInbox[3]:
        return msg
    }
}
```

#### 5.2.3 消息确认（ACK）机制

```go
type Message struct {
    ID       string
    Sender   string
    Receiver string
    Type     MessageType
    Body     any
    // 新增字段
    Priority    MessagePriority
    AckCh       chan *MessageAck  // 可选：同步等待处理结果
    CreatedAt   time.Time
    RetryCount  int
    MaxRetries  int
}

type MessageAck struct {
    MessageID string
    Status    string  // "processed" | "failed" | "rejected"
    Error     error
}
```

#### 5.2.4 死信队列（DLQ）

```go
type DeadLetterQueue struct {
    mu       sync.Mutex
    messages []*DeadLetter
    db       *gorm.DB  // 可选持久化
}

type DeadLetter struct {
    OriginalMessage *ds.Message
    FailReason      string
    FailedAt        time.Time
    RetryCount      int
}

// 在消息处理失败时自动进入 DLQ
func (mb *Mailbox) processWithRetry(msg *ds.Message, handler MessageHandler) {
    for i := 0; i <= msg.MaxRetries; i++ {
        err := handler(msg)
        if err == nil {
            return
        }
        msg.RetryCount++
        time.Sleep(time.Duration(1<<i) * time.Second)  // 指数退避
    }
    mb.deadLetterQueue.Push(msg, "max retries exceeded")
}
```

#### 5.2.5 MailboxBus 增强

```go
type MailboxBus struct {
    mu          sync.RWMutex
    mailboxes   map[string]*Mailbox
    globalState *state.GlobalState
    // 新增
    metrics     *BusMetrics       // 消息吞吐量、延迟统计
    dlq         *DeadLetterQueue  // 全局死信队列
    middleware  []MessageMiddleware // 消息拦截器链
}

// 消息中间件接口 -- 支持日志、限流、路由等扩展
type MessageMiddleware interface {
    Before(msg *ds.Message) (*ds.Message, error)  // 发送前
    After(msg *ds.Message, err error)             // 发送后
}
```

### 5.3 消息流转改进后的架构

```
Agent A 发送消息
    │
    ▼
MailboxBus.Send(msg)
    │
    ├── Middleware Chain (限流/日志/路由)
    │
    ├── 根据 msg.Priority 选择目标队列
    │
    ▼
Agent B Mailbox
    ├── priorityInbox[Critical] ──┐
    ├── priorityInbox[High]     ──┤
    ├── priorityInbox[Medium]   ──┤── NextMessage() 按优先级出队
    └── priorityInbox[Low]      ──┘
                                    │
                                    ▼
                            processWithRetry()
                                    │
                            ┌───────┴───────┐
                            ▼               ▼
                        处理成功         处理失败
                            │               │
                            ▼               ▼
                        发送 ACK      重试/进入 DLQ
```

---

## 6. 优化方案设计：任务分配与调度

### 6.1 当前问题总结

1. AutoScheduler 只有队列存储，**没有主动调度循环**
2. 任务无法自动从队列分配给空闲的 Agent
3. 任务依赖关系（Dependencies）虽然在数据结构中定义了，但没有实际的依赖检查逻辑
4. 排序算法 O(n^2)，不适合大量任务
5. GenerateTasks() 返回空列表，Agent 没有自驱能力

### 6.2 调度器重构方案

#### 6.2.1 主动调度循环

这是最关键的缺失部分。需要一个独立的 goroutine 持续从队列取出任务并分配：

```go
type AutoScheduler struct {
    mu            sync.RWMutex
    taskQueues    map[string]*TaskQueue
    agentStates   map[string]*SchedulableAgent
    orchestrator  workflow.Orchestrator
    globalState   *state.GlobalState

    stopCh        chan struct{}
    wg            sync.WaitGroup

    // 调度策略
    tickInterval  time.Duration  // 调度轮询间隔
}

type SchedulableAgent struct {
    Name        string
    MaxTasks    int
    CurrentLoad int
    Hierarchy   int
    Skills      []string  // Agent 具备的技能标签
}

// 启动调度循环
func (s *AutoScheduler) Start() {
    s.wg.Add(1)
    go s.scheduleLoop()
}

func (s *AutoScheduler) scheduleLoop() {
    defer s.wg.Done()
    ticker := time.NewTicker(s.tickInterval)
    defer ticker.Stop()

    for {
        select {
        case <-s.stopCh:
            return
        case <-ticker.C:
            s.dispatchTasks()
        }
    }
}

func (s *AutoScheduler) dispatchTasks() {
    s.mu.Lock()
    defer s.mu.Unlock()

    for {
        task := s.getNextReady()  // 从优先级队列中取出依赖已满足的任务
        if task == nil {
            break
        }

        agent := s.findBestAgent(task)  // 根据负载、技能匹配选择 Agent
        if agent == nil {
            // 所有 Agent 都满载，任务回到队列
            s.requeueTask(task)
            break
        }

        // 通过 Orchestrator 将任务发送给 Agent
        err := s.orchestrator.RunTask(task)
        if err != nil {
            s.requeueTask(task)
            continue
        }
        agent.CurrentLoad++
    }
}
```

#### 6.2.2 任务依赖检查

```go
func (s *AutoScheduler) getNextReady() *ds.Task {
    priorities := []string{PriorityCritical, PriorityHigh, PriorityMedium, PriorityLow}
    for _, priority := range priorities {
        queue := s.taskQueues[priority]
        if queue == nil || queue.IsEmpty() {
            continue
        }
        // 遍历队列，找到依赖已满足的任务
        task := queue.DequeueIf(func(t *ds.Task) bool {
            return s.areDependenciesMet(t)
        })
        if task != nil {
            return task
        }
    }
    return nil
}

func (s *AutoScheduler) areDependenciesMet(task *ds.Task) bool {
    if len(task.Dependencies) == 0 {
        return true
    }
    for _, depID := range task.Dependencies {
        depTask := s.globalState.GetTask(depID)
        if depTask == nil || depTask.Status != ds.TaskStatusCompleted {
            return false
        }
    }
    return true
}
```

#### 6.2.3 智能任务分配策略

```go
func (s *AutoScheduler) findBestAgent(task *ds.Task) *SchedulableAgent {
    // 策略 1：如果任务指定了 AssignedTo，优先使用
    if task.AssignedTo != "" {
        if agent, ok := s.agentStates[task.AssignedTo]; ok {
            if agent.CurrentLoad < agent.MaxTasks {
                return agent
            }
        }
    }

    // 策略 2：按负载率排序，选择最空闲且技能匹配的 Agent
    var candidates []*SchedulableAgent
    for _, agent := range s.agentStates {
        if agent.CurrentLoad >= agent.MaxTasks {
            continue
        }
        candidates = append(candidates, agent)
    }

    // 按负载率升序排序
    sort.Slice(candidates, func(i, j int) bool {
        loadI := float64(candidates[i].CurrentLoad) / float64(candidates[i].MaxTasks)
        loadJ := float64(candidates[j].CurrentLoad) / float64(candidates[j].MaxTasks)
        return loadI < loadJ
    })

    if len(candidates) > 0 {
        return candidates[0]
    }
    return nil
}
```

#### 6.2.4 任务完成回调

当 Agent 完成任务后，需要通知 Scheduler 更新负载计数：

```go
// 在 BaseAgentImpl.ProcessTask 完成后，发送 TaskComplete 消息
func (a *BaseAgentImpl) notifyTaskComplete(task *ds.Task, success bool) {
    msg, _ := ds.NewTaskCompleteMessage(task.ID, success, "", nil)
    msg.Receiver = "scheduler"  // 发送给调度器
    a.mailbox.PushOutbox(msg)
}
```

### 6.3 改进后的调度架构

```
                     ┌─────────────────────┐
                     │  Task Sources        │
                     │                      │
                     │  • Agent.Generate()  │
                     │  • TimerEngine       │
                     │  • User Input        │
                     │  • Task Chain        │
                     └──────────┬───────────┘
                                │
                                ▼
                     ┌──────────────────────┐
                     │   AutoScheduler      │
                     │                      │
                     │  ┌──────────────┐    │
                     │  │ Priority     │    │
                     │  │ Queues       │    │
                     │  │ C > H > M > L│    │
                     │  └──────┬───────┘    │
                     │         │             │
                     │  ┌──────▼───────┐    │
                     │  │ Dependency   │    │
                     │  │ Checker      │    │
                     │  └──────┬───────┘    │
                     │         │             │
                     │  ┌──────▼───────┐    │
                     │  │ Agent        │    │
                     │  │ Matcher      │    │
                     │  │ (负载+技能)   │    │
                     │  └──────┬───────┘    │
                     └─────────┼────────────┘
                               │
                     ┌─────────▼────────────┐
                     │   Orchestrator        │
                     │   RunTask()           │
                     └─────────┬────────────┘
                               │
            ┌──────────────────┼──────────────────┐
            ▼                  ▼                   ▼
    ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
    │   Agent A    │  │   Agent B    │  │   Agent C    │
    │  (Mailbox)   │  │  (Mailbox)   │  │  (Mailbox)   │
    └──────┬───────┘  └──────┬───────┘  └──────┬───────┘
           │                 │                  │
           └─────── TaskComplete ───────────────┘
                         │
                         ▼
                  Scheduler 更新负载
```

---

## 7. 优化方案设计：Skills 与配置文件驱动的 Agent 扩展

### 7.1 当前 Skill 系统分析

**优势**:
- 使用 Eino ADK 的 `skill.LocalBackend`，支持从本地目录加载 Markdown 格式的 Skill
- Skill 作为 Middleware 注入 Agent，自动增强 Agent 的知识库
- 目录结构清晰：`skills/{role}/{category}/skill.md`

**局限**:
- Skill 仅作为静态知识注入，不包含可执行逻辑（如自定义 Tool）
- Agent 只能使用一个固定的 `SendMessage` tool，无法通过 Skill 扩展工具集
- 无法动态加载/卸载 Skill
- 配置文件中只定义了 `skill_dir`，没有更细粒度的 Skill 启用/禁用机制

### 7.2 增强型 Skill 系统设计

#### 7.2.1 Skill 分层架构

```
Skill 类型划分:

1. Knowledge Skill (知识型，当前已有)
   └── 纯 Markdown 描述，注入 Agent 上下文
   └── 例: skills/ceo/strategy/skill.md

2. Tool Skill (工具型，新增)
   └── 定义可调用的 Tool，绑定到 Agent
   └── 例: skills/ceo/strategy/tools.yaml + handler.go

3. Workflow Skill (流程型，新增)
   └── 定义任务生成模板和触发条件
   └── 例: skills/ceo/strategy/workflow.yaml
```

#### 7.2.2 Skill 配置文件格式

每个 Skill 目录下可包含以下文件：

```
skills/{role}/{category}/
├── skill.md          # Knowledge Skill (已有)
├── tools.yaml        # Tool Skill 定义 (新增)
├── workflow.yaml     # Workflow Skill 定义 (新增)
└── config.yaml       # Skill 元配置 (新增)
```

**config.yaml** -- Skill 元数据：
```yaml
name: "strategy"
version: "1.0"
description: "CEO 战略规划技能"
enabled: true
dependencies:
  - "market_analysis"
  - "financial_overview"
tags:
  - "planning"
  - "decision"
```

**tools.yaml** -- 工具定义：
```yaml
tools:
  - name: "query_market_data"
    description: "查询市场数据"
    parameters:
      - name: "market"
        type: "string"
        description: "目标市场"
        required: true
      - name: "period"
        type: "string"
        description: "时间范围"
        enum: ["daily", "weekly", "monthly", "quarterly"]
    handler: "builtin:query_global_state"  # 内置处理器
    handler_config:
      state_key: "market_data"

  - name: "create_strategic_task"
    description: "创建战略任务并分配给下级"
    parameters:
      - name: "title"
        type: "string"
        required: true
      - name: "assigned_to"
        type: "string"
        required: true
        enum_from: "agents"  # 动态从 Agent 列表填充
      - name: "priority"
        type: "string"
        enum: ["Critical", "High", "Medium", "Low"]
    handler: "builtin:create_task"
```

**workflow.yaml** -- 任务生成模板：
```yaml
task_templates:
  - name: "weekly_strategy_review"
    title: "周度战略复盘"
    description: "审阅各部门本周进展，评估战略目标达成情况"
    priority: "High"
    trigger:
      type: "cron"
      cron: "0 9 * * 1"  # 每周一 9:00

  - name: "kpi_anomaly_response"
    title: "KPI 异常响应"
    description: "检测到 KPI 异常指标，分析原因并制定应对方案"
    priority: "Critical"
    trigger:
      type: "state_watch"
      condition: "kpi.revenue_growth < 0.05"

  - name: "quarterly_planning"
    title: "季度战略规划"
    description: "制定下季度战略目标与资源分配方案"
    priority: "High"
    trigger:
      type: "cron"
      cron: "0 0 1 1,4,7,10 *"  # 每季度第一天
    chain:
      - assigned_to: "cfo"
        title: "编制季度预算方案"
      - assigned_to: "cto"
        title: "制定季度技术路线"
      - assigned_to: "cpo"
        title: "更新产品路线图"
```

#### 7.2.3 Agent 配置增强

```yaml
# config.yaml

agents:
  - name: "ceo"
    desc: "首席执行官 - 制定战略、分配资源、监督运营"
    model: "qwen-plus"
    temperature: 0.7
    hierarchy: 1
    skill_dir: "skills/ceo"
    max_concurrent_tasks: 3

    # 新增：细粒度 Skill 控制
    skills:
      enabled:
        - "strategy"
        - "decision_making"
        - "leadership"
        - "market_analysis"
        - "financial_overview"
        - "governance"
      disabled: []

    # 新增：Agent 专属 Tools
    tools:
      - "send_message"      # 内置
      - "create_task"        # 内置
      - "query_state"        # 内置
      - "broadcast"          # 内置：广播消息给多个 Agent

    # 新增：系统提示词配置
    system_prompt: |
      你是 SuperMan AI 公司的 CEO。你的职责是制定公司战略、
      分配资源、监督运营，并与各高管协作推动公司发展。
      你可以通过 send_message 与其他高管沟通，
      通过 create_task 分配任务给下属。

    # 新增：自动行为配置
    auto_behaviors:
      task_generation:
        enabled: true
        interval: "30m"    # 每 30 分钟检查是否需要生成新任务
      state_scanning:
        enabled: true
        interval: "10m"    # 每 10 分钟扫描全局状态
        watch_keys:
          - "kpis.*"
          - "system_health.*"
```

#### 7.2.4 动态 Agent 注册

支持通过配置文件动态添加新的 Agent 角色，无需修改代码：

```yaml
# 新增一个 "法务顾问" Agent，只需添加配置：
agents:
  # ... 现有 agents ...

  - name: "legal_counsel"
    desc: "法务顾问 - 合规审查、合同审核、法律风险评估"
    model: "qwen-plus"
    temperature: 0.3
    hierarchy: 2
    skill_dir: "skills/legal_counsel"
    skills:
      enabled:
        - "contract_review"
        - "compliance"
        - "risk_assessment"
    tools:
      - "send_message"
      - "query_state"
    system_prompt: |
      你是 SuperMan AI 公司的法务顾问...
```

对应的 Skill 只需创建 Markdown 文件：

```
skills/legal_counsel/
├── contract_review/
│   └── skill.md
├── compliance/
│   └── skill.md
└── risk_assessment/
    └── skill.md
```

#### 7.2.5 Skill 加载器实现

```go
type SkillLoader struct {
    baseDir string
}

type LoadedSkill struct {
    Name        string
    Config      SkillConfig
    Knowledge   string            // Markdown 内容
    Tools       []ToolDefinition  // 工具定义
    Workflows   []WorkflowDef     // 任务模板
}

func (sl *SkillLoader) LoadSkills(enabledSkills []string) ([]*LoadedSkill, error) {
    var skills []*LoadedSkill
    for _, skillName := range enabledSkills {
        skillDir := filepath.Join(sl.baseDir, skillName)
        skill, err := sl.loadSkill(skillDir, skillName)
        if err != nil {
            return nil, fmt.Errorf("failed to load skill %s: %w", skillName, err)
        }
        skills = append(skills, skill)
    }
    return skills, nil
}

func (sl *SkillLoader) loadSkill(dir, name string) (*LoadedSkill, error) {
    skill := &LoadedSkill{Name: name}

    // 1. 加载 config.yaml (可选)
    configPath := filepath.Join(dir, "config.yaml")
    if exists(configPath) {
        // parse config
    }

    // 2. 加载 skill.md (Knowledge)
    mdPath := filepath.Join(dir, "skill.md")
    if data, err := os.ReadFile(mdPath); err == nil {
        skill.Knowledge = string(data)
    }

    // 3. 加载 tools.yaml (可选)
    toolsPath := filepath.Join(dir, "tools.yaml")
    if exists(toolsPath) {
        // parse tool definitions
    }

    // 4. 加载 workflow.yaml (可选)
    workflowPath := filepath.Join(dir, "workflow.yaml")
    if exists(workflowPath) {
        // parse workflow definitions
    }

    return skill, nil
}
```

### 7.3 扩展 Agent 的完整流程

```
添加新 Agent 角色的步骤（零代码修改）:

1. 在 config.yaml 的 agents 列表中添加配置
   ↓
2. 创建 skills/{role}/ 目录，编写 Skill 文件
   ├── {category}/skill.md     (知识描述)
   ├── {category}/tools.yaml   (工具定义，可选)
   └── {category}/workflow.yaml (任务模板，可选)
   ↓
3. 重启系统（或热重载配置）
   ↓
4. 系统自动:
   ├── 创建 Agent 实例
   ├── 加载 Skills & Tools
   ├── 注册 Mailbox
   ├── 启动消息处理循环
   └── 根据 workflow.yaml 自动生成任务
```

---

## 8. 优化方案设计：24/7 自主运行

### 8.1 自主运行的核心要求

1. **无人值守**: 系统启动后不需要任何人类输入即可持续运行
2. **任务自生成**: Agent 根据角色职责和全局状态自动产生任务
3. **故障自恢复**: 单个 Agent 或组件失败不影响整体系统
4. **状态持久化**: 崩溃后能从上次状态恢复
5. **自适应调节**: 根据系统负载动态调整调度策略

### 8.2 三驱动模型

```
┌─────────────────────────────────────────────────────────┐
│                    Drive Model                           │
│                                                          │
│   ┌──────────────┐ ┌──────────────┐ ┌──────────────┐   │
│   │ Event-Driven │ │ Time-Driven  │ │ Goal-Driven  │   │
│   │              │ │              │ │              │   │
│   │ • 消息到达    │ │ • CRON 定时   │ │ • KPI 偏离    │   │
│   │ • 任务完成    │ │ • 周期检查    │ │ • 状态异常    │   │
│   │ • 状态变更    │ │ • 日报/周报   │ │ • 目标缺口    │   │
│   └──────┬───────┘ └──────┬───────┘ └──────┬───────┘   │
│          │                │                 │            │
│          └────────────────┼─────────────────┘            │
│                           ▼                              │
│                  ┌────────────────┐                      │
│                  │ Task Generator │                      │
│                  │ + AutoScheduler│                      │
│                  └────────┬───────┘                      │
│                           ▼                              │
│                  Agent Execution                         │
└─────────────────────────────────────────────────────────┘
```

### 8.3 TimerEngine 实现

```go
type TimerEngine struct {
    mu        sync.RWMutex
    jobs      []*CronJob
    scheduler *AutoScheduler
    stopCh    chan struct{}
    wg        sync.WaitGroup
}

type CronJob struct {
    Name         string
    CronExpr     string        // "0 9 * * 1"
    TargetAgent  string
    TaskTemplate TaskTemplate
    LastRun      time.Time
    NextRun      time.Time
    Enabled      bool
}

type TaskTemplate struct {
    Title       string
    Description string
    Priority    string
    Chain       []ChainStep  // 后续任务链
}

type ChainStep struct {
    AssignedTo  string
    Title       string
    Description string
    DependsOn   string  // 前置步骤名称
}

func (te *TimerEngine) Start() {
    te.wg.Add(1)
    go te.tickLoop()
}

func (te *TimerEngine) tickLoop() {
    defer te.wg.Done()
    ticker := time.NewTicker(1 * time.Minute)
    defer ticker.Stop()

    for {
        select {
        case <-te.stopCh:
            return
        case now := <-ticker.C:
            te.checkAndFire(now)
        }
    }
}

func (te *TimerEngine) checkAndFire(now time.Time) {
    te.mu.RLock()
    defer te.mu.RUnlock()

    for _, job := range te.jobs {
        if !job.Enabled {
            continue
        }
        if now.After(job.NextRun) {
            te.fireJob(job)
            job.LastRun = now
            job.NextRun = calculateNextRun(job.CronExpr, now)
        }
    }
}
```

### 8.4 Agent 自驱任务生成

改造 `GenerateTasks` 为基于 Skill workflow 的自动任务生成：

```go
func (a *BaseAgentImpl) GenerateTasks(ctx context.Context) ([]*ds.Task, error) {
    var tasks []*ds.Task

    // 1. 从 Skill 的 workflow.yaml 中加载任务模板
    for _, skill := range a.loadedSkills {
        for _, template := range skill.Workflows {
            if template.Trigger.Type == "startup" || template.Trigger.Type == "periodic" {
                task := templateToTask(template, a.name)
                tasks = append(tasks, task)
            }
        }
    }

    // 2. 基于全局状态扫描生成响应式任务
    if a.globalState != nil {
        reactiveTask := a.scanStateForTasks(ctx)
        tasks = append(tasks, reactiveTask...)
    }

    // 3. 调用 LLM 根据当前上下文生成任务（可选）
    if a.autoBehaviors.TaskGeneration.LLMAssisted {
        llmTasks, err := a.llmGenerateTasks(ctx)
        if err == nil {
            tasks = append(tasks, llmTasks...)
        }
    }

    return tasks, nil
}

// 定期任务生成循环
func (a *BaseAgentImpl) taskGenerationLoop() {
    defer a.wg.Done()
    interval := a.autoBehaviors.TaskGeneration.Interval
    ticker := time.NewTicker(interval)
    defer ticker.Stop()

    for {
        select {
        case <-a.stopCh:
            return
        case <-ticker.C:
            tasks, err := a.GenerateTasks(context.Background())
            if err != nil {
                slog.Error("task generation failed", slog.String("agent", a.name), slog.Any("err", err))
                continue
            }
            for _, task := range tasks {
                // 发送到 Scheduler
                a.globalState.AddTask(task)
                a.scheduler.AddTask(task, string(task.Priority))
            }
        }
    }
}
```

### 8.5 故障恢复机制

```go
// Supervisor 监控和恢复 Agent
type Supervisor struct {
    agents      map[string]agents.Agent
    healthCheck time.Duration
    maxRestarts int
    restartMap  map[string]int  // Agent 重启次数
}

func (s *Supervisor) Start() {
    go s.monitorLoop()
}

func (s *Supervisor) monitorLoop() {
    ticker := time.NewTicker(s.healthCheck)
    defer ticker.Stop()

    for range ticker.C {
        for name, agent := range s.agents {
            if !agent.IsRunning() {
                if s.restartMap[name] < s.maxRestarts {
                    slog.Warn("agent crashed, restarting", slog.String("agent", name))
                    agent.Start()
                    s.restartMap[name]++
                } else {
                    slog.Error("agent exceeded max restarts", slog.String("agent", name))
                    // 通知 HR/CEO Agent
                }
            }
        }
    }
}
```

### 8.6 状态持久化方案

```go
// StateStore 将内存状态定期同步到 SQLite
type StateStore struct {
    db          *gorm.DB
    globalState *state.GlobalState
    interval    time.Duration
}

func (ss *StateStore) Start() {
    go ss.persistLoop()
}

func (ss *StateStore) persistLoop() {
    ticker := time.NewTicker(ss.interval)
    defer ticker.Stop()

    for range ticker.C {
        ss.snapshot()
    }
}

func (ss *StateStore) snapshot() {
    // 持久化任务状态
    tasks := ss.globalState.GetAllTasks()
    for _, task := range tasks {
        ss.db.Save(task)
    }

    // 持久化执行历史
    history := ss.globalState.GetExecutionHistory()
    for _, h := range history {
        ss.db.Save(h)
    }
}

// 启动时从 DB 恢复状态
func (ss *StateStore) Restore() error {
    var tasks []ds.Task
    ss.db.Find(&tasks)
    for _, task := range tasks {
        t := task
        ss.globalState.AddTask(&t)
    }
    return nil
}
```

### 8.7 Graceful Shutdown

```go
func main() {
    // ... 初始化代码 ...

    // 注册信号处理
    sigCh := make(chan os.Signal, 1)
    signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)

    go func() {
        <-sigCh
        slog.Info("shutdown signal received, graceful shutdown starting...")

        // 1. 停止 TimerEngine（不再生成新任务）
        timerEngine.Stop()

        // 2. 停止 AutoScheduler（不再分配新任务）
        schedulerInstance.Stop()

        // 3. 等待所有 Agent 完成当前任务并停止
        for name, agent := range agentMap {
            slog.Info("stopping agent", slog.String("name", name))
            agent.Stop()
        }

        // 4. 持久化最终状态
        stateStore.Snapshot()

        // 5. 关闭数据库连接
        db.Close()

        slog.Info("shutdown complete")
        os.Exit(0)
    }()
}
```

---

## 9. 目标架构总览

### 9.1 完整系统架构

```
┌──────────────────────────────────────────────────────────────────────┐
│                     SuperMan AI System v2.0                          │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐     │
│  │                    Configuration Layer                       │     │
│  │  config.yaml  │  skills/**/config.yaml  │  cron.yaml        │     │
│  └─────────────────────────┬───────────────────────────────────┘     │
│                             │                                         │
│  ┌──────────────────────────▼──────────────────────────────────┐     │
│  │                    Initialization Layer                      │     │
│  │  Registry (DB + LLM Models) │ SkillLoader │ AgentFactory    │     │
│  └──────────────────────────┬──────────────────────────────────┘     │
│                              │                                        │
│  ┌───────────────────────────▼─────────────────────────────────┐     │
│  │                     Agent Layer                              │     │
│  │                                                              │     │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐          │     │
│  │  │Chairman │ │  CEO    │ │  CTO    │ │  ...    │ (N 个)    │     │
│  │  │         │ │         │ │         │ │         │          │     │
│  │  │ Skills: │ │ Skills: │ │ Skills: │ │ Skills: │          │     │
│  │  │ • Know  │ │ • Know  │ │ • Know  │ │ • Know  │          │     │
│  │  │ • Tools │ │ • Tools │ │ • Tools │ │ • Tools │          │     │
│  │  │ • WFlow │ │ • WFlow │ │ • WFlow │ │ • WFlow │          │     │
│  │  │         │ │         │ │         │ │         │          │     │
│  │  │ Mailbox │ │ Mailbox │ │ Mailbox │ │ Mailbox │          │     │
│  │  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘          │     │
│  │       │           │           │            │               │     │
│  └───────┼───────────┼───────────┼────────────┼───────────────┘     │
│          │           │           │            │                      │
│  ┌───────▼───────────▼───────────▼────────────▼───────────────┐     │
│  │                   MailboxBus (消息总线)                      │     │
│  │  • 优先级路由  • 中间件链  • 指标收集  • 死信队列             │     │
│  └───────────────────────┬────────────────────────────────────┘     │
│                           │                                          │
│  ┌────────────────────────▼───────────────────────────────────┐     │
│  │                   Scheduling Layer                          │     │
│  │                                                             │     │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │     │
│  │  │AutoScheduler │  │ TimerEngine  │  │ TaskGenerator │     │     │
│  │  │              │  │              │  │              │     │     │
│  │  │ • 优先级队列  │  │ • CRON 表达式 │  │ • 状态扫描    │     │     │
│  │  │ • 依赖检查   │  │ • 任务链     │  │ • LLM 生成    │     │     │
│  │  │ • 负载均衡   │  │ • 定期触发    │  │ • 模板实例化  │     │     │
│  │  │ • 调度循环   │  │              │  │              │     │     │
│  │  └──────────────┘  └──────────────┘  └──────────────┘     │     │
│  └────────────────────────────────────────────────────────────┘     │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────┐     │
│  │                   Infrastructure Layer                      │     │
│  │                                                             │     │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │     │
│  │  │ SQLite   │  │StateStore│  │Supervisor │  │ Metrics  │  │     │
│  │  │ (GORM)   │  │(持久化)   │  │(故障恢复) │  │ (监控)    │  │     │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │     │
│  └────────────────────────────────────────────────────────────┘     │
└──────────────────────────────────────────────────────────────────────┘
```

### 9.2 核心改造清单

| # | 改造项 | 优先级 | 影响范围 | 描述 |
|---|--------|--------|---------|------|
| 1 | AutoScheduler 调度循环 | **Critical** | scheduler/ | 添加主动从队列取任务、分配给 Agent 的调度循环 |
| 2 | SendMessage MailboxBus nil 修复 | **Critical** | agents/, tools/ | 修复 Tool 创建时 MailboxBus 为 nil 的问题 |
| 3 | PushInbox 非阻塞化 | **High** | mailbox/ | 防止 channel 满时发送方永久阻塞 |
| 4 | TimerEngine | **High** | 新模块 | CRON 定时任务引擎 |
| 5 | Workflow Skill 任务模板 | **High** | agents/, skills/ | 让每个 Agent 能从 Skill 定义中自动生成任务 |
| 6 | Graceful Shutdown | **High** | main.go | 信号处理、有序停止、状态持久化 |
| 7 | StateStore 持久化 | **Medium** | 新模块 | 定期将内存状态同步到 SQLite |
| 8 | Supervisor 故障恢复 | **Medium** | 新模块 | Agent 健康检查和自动重启 |
| 9 | 消息优先级 & DLQ | **Medium** | mailbox/ | Mailbox 内部优先级分级和死信队列 |
| 10 | Agent 配置增强 | **Medium** | config/ | 支持 tools、system_prompt、auto_behaviors 等配置 |
| 11 | 优先级队列优化 | **Low** | scheduler/ | 用 heap 替换 O(n^2) 冒泡排序 |
| 12 | GlobalState 重构 | **Low** | state/ | 拆分为子状态模块，减少字段膨胀 |

---

## 10. 实施路线图

### Phase 1: 修复核心缺陷

**目标**: 让系统的基本消息传输和任务分配能正确工作

- 修复 SendMessage Tool 中 MailboxBus 为 nil 的问题
  - 在 `main.go` 中调整初始化顺序，先注册 Mailbox 再创建 Tool
  - 或在 `RegisterMailbox` 时回填 Tool 的 MailboxBus 引用
- 实现 AutoScheduler 的主动调度循环
  - 添加 `Start()` 方法启动 goroutine
  - 添加 `dispatchTasks()` 方法，按优先级从队列取任务
  - 通过 Orchestrator.RunTask() 将任务发送给 Agent
  - 添加任务完成回调，更新 Agent 负载
- 修复 PushInbox 阻塞问题
  - 改为 select + timeout 机制
- 添加 Graceful Shutdown
  - 信号监听 + 有序停止

### Phase 2: 实现自驱任务生成

**目标**: Agent 能够自动产生任务，系统可以无人值守运行

- 实现 TimerEngine (CRON 定时任务)
  - 支持从配置文件加载 CRON 任务
  - 定时触发任务生成
- 改造 GenerateTasks()
  - 从 Skill 的 workflow.yaml 加载任务模板
  - 基于全局状态扫描生成响应式任务
  - 添加任务生成循环（定期执行）
- 实现 TaskChain (任务链)
  - 任务完成后自动触发后续任务

### Phase 3: 增强 Skill 系统

**目标**: 通过 Skill 和配置文件实现零代码 Agent 扩展

- 实现增强型 SkillLoader
  - 支持加载 config.yaml、tools.yaml、workflow.yaml
  - 支持 Skill 依赖管理
- 实现 Tool Skill
  - 根据 tools.yaml 定义动态创建 Eino Tool
  - 内置 handler：query_state、create_task、broadcast 等
- 增强 Agent 配置
  - 支持 system_prompt、tools 列表、auto_behaviors
  - 支持细粒度 Skill 启用/禁用

### Phase 4: 基础设施完善

**目标**: 生产级的稳定性和可观测性

- 实现 StateStore (状态持久化)
  - 定期快照到 SQLite
  - 启动时从 DB 恢复状态
- 实现 Supervisor (故障恢复)
  - Agent 健康检查
  - 自动重启
  - 超限告警
- 实现消息增强
  - 消息优先级路由
  - 死信队列
  - 消息中间件
  - 指标收集
- 移除交互式控制台依赖
  - 改为可选的管理 API 或 Web 界面
  - 系统默认以 daemon 模式运行

---

## 附录 A: 关键数据结构变更对照

### Message (变更前 vs 变更后)

```go
// 变更前
type Message struct {
    ID       string
    Sender   string
    Receiver string
    Type     MessageType
    Body     any
}

// 变更后
type Message struct {
    ID         string
    Sender     string
    Receiver   string
    Type       MessageType
    Body       any
    Priority   MessagePriority  // 新增
    CreatedAt  time.Time        // 新增
    RetryCount int              // 新增
    MaxRetries int              // 新增
    TraceID    string           // 新增：链路追踪
}
```

### AgentConfig (变更前 vs 变更后)

```go
// 变更前
type AgentConfig struct {
    Name        string
    Desc        string
    Model       string
    Temperature float64
    Hierarchy   int
    SkillDir    string
}

// 变更后
type AgentConfig struct {
    Name        string
    Desc        string
    Model       string
    Temperature float64
    Hierarchy   int
    SkillDir    string
    // 新增
    MaxConcurrentTasks int
    Skills      SkillsConfig
    Tools       []string
    SystemPrompt string
    AutoBehaviors AutoBehaviorsConfig
}

type SkillsConfig struct {
    Enabled  []string
    Disabled []string
}

type AutoBehaviorsConfig struct {
    TaskGeneration TaskGenerationConfig
    StateScanning  StateScanningConfig
}
```

## 附录 B: 已发现的 Bug 清单

| # | 文件 | 行号 | 严重性 | 描述 |
|---|------|------|--------|------|
| 1 | agents/base_agent.go | 109 | High | SendMessage.MailboxBus 在 RegisterMailbox 前获取，值为 nil |
| 2 | state/global_state.go | 304 | Low | GetExecutionHistoryByAgent 未使用 name 参数过滤 |
| 3 | ds/task.go | 80-82 | Low | GenerateTaskID 精度只到秒，同秒冲突 |
| 4 | state/agent_state.go | 191 | Low | UpdateMetric 将 LastActive 设为零值 `time.Time{}` 而非 `time.Now()` |
| 5 | mailbox/mailbox.go | 48-50 | High | PushInbox 在 buffer 满时永久阻塞 |
| 6 | scheduler/auto_scheduler.go | 全文件 | Critical | 无主动调度循环，任务永远在队列中 |

---

*本文档基于 2026-02-16 对 SuperMan 项目全部源码的逐文件审阅编写。*
