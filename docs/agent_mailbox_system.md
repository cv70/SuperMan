# Agent私有信箱和执行历史系统

## 概述

SuperMan AI多智能体系统现在支持每个Agent维护私有信箱和执行历史，以及公司级公有信箱。这个架构大大增强了Agent的上下文感知能力和系统的可追溯性。

## 核心功能

### 1. Agent私有信箱 (Agentmailbox)

每个Agent现在拥有三个私有消息队列：

- **收件箱 (Inbox)**: 存储接收到的消息
- **发件箱 (Outbox)**: 存储发送的消息
- **归档箱 (Archive)**: 存储已处理的消息

```go
type Agentmailbox struct {
    mu           sync.RWMutex
    role         AgentRole
    inbox        *list.List // 私有收件箱
    outbox       *list.List // 私的发件箱
    archive      *list.List // 已归档消息
    maxSize      int        // 信箱最大容量
    processing   bool       // 是否正在处理消息
}
```

#### 主要方法

- `PushInbox(msg *Message) bool`: 推送消息到收件箱
- `PopInbox() *Message`: 从收件箱弹出消息
- `PeekInbox() *Message`: 查看收件箱首条消息
- `PushOutbox(msg *Message) bool`: 推送消息到发件箱
- `ArchiveMessage(msg *Message)`: 归档消息
- `GetMailboxStats() map[string]int`: 获取信箱统计信息

### 2. 执行历史 (AgentExecutionHistory)

每个Agent维护详细的执行历史记录：

```go
type AgentExecutionHistory struct {
    ExecutionID   string                 // 执行唯一ID
    Timestamp     time.Time              // 执行时间
    TaskID        string                 // 关联任务ID
    MessageID     string                 // 触发消息ID
    Action        string                 // 执行的动作
    Input         map[string]any         // 输入数据
    Output        map[string]any         // 输出结果
    Status        string                 // 执行状态: success/failed/timeout
    Duration      time.Duration          // 执行耗时
    ErrorMessage  string                 // 错误信息(如果有)
    Dependencies  []string               // 依赖的其他执行记录
    Metadata      map[string]any         // 其他元数据
}
```

#### 主要方法

- `AddExecutionHistory(history *AgentExecutionHistory)`: 添加执行历史
- `GetExecutionHistory() []*AgentExecutionHistory`: 获取所有执行历史
- `GetExecutionHistoryByTaskID(taskID string)`: 根据任务ID获取历史
- `GetExecutionHistoryByTimeRange(start, end time.Time)`: 根据时间范围获取历史
- `GetRecentExecutions(count int)`: 获取最近的执行记录
- `GetExecutionStats()`: 获取执行统计信息

### 3. 公司公有信箱 (CompanyPublicMailbox)

系统维护一个公司级公有信箱，用于全局通信：

```go
type CompanyPublicMailbox struct {
    mu           sync.RWMutex
    messages     []*Message  // 一般消息
    announcements []*Message // 公告消息
    broadcasts   []*Message  // 广播消息
    maxSize      int
}
```

#### 主要方法

- `AddMessage(msg *Message) bool`: 添加一般消息
- `AddAnnouncement(msg *Message) bool`: 添加公告
- `AddBroadcast(msg *Message) bool`: 添加广播
- `GetMessagesByRole(role AgentRole)`: 获取角色相关消息
- `GetMailboxStats() map[string]int`: 获取统计信息

## 使用示例

### 1. Agent处理消息（自动记录执行历史）

```go
// 创建消息
msg := &agents.Message{
    MessageID:   "msg_001",
    Sender:      agents.AgentRoleCTO,
    Receiver:    agents.AgentRoleCEO,
    MessageType: agents.MessageTypeStatusReport,
    Content: map[string]any{
        "report_type": "financial",
        "revenue":     1500000.0,
    },
    Priority:  agents.PriorityHigh,
    Timestamp: time.Now(),
}

// Agent处理消息（自动记录执行历史和使用私有信箱）
err := ceoAgent.ProcessMessage(msg)

// 查看私有信箱状态
mailbox := ceoAgent.Getmailbox()
stats := mailbox.GetMailboxStats()
fmt.Printf("Inbox: %d, Outbox: %d, Archive: %d\n", 
    stats["inbox_count"], stats["outbox_count"], stats["archive_count"])

// 查看执行历史
history := ceoAgent.GetRecentExecutions(5)
for _, exec := range history {
    fmt.Printf("[%s] %s - %s (%v)\n", 
        exec.Timestamp.Format("15:04:05"), 
        exec.Action, 
        exec.Status, 
        exec.Duration)
}
```

### 2. CEO发布公告

```go
// CEO向公司发布公告（使用GlobalState）
err := ceoAgent.AnnounceToCompany(
    "Q1 2024 Strategic Goals",
    "Our Q1 performance exceeded expectations with 15% revenue growth.",
)

// CEO发送紧急广播（使用GlobalState）
err = ceoAgent.SendBroadcast(map[string]any{
    "type":        "urgent_meeting",
    "title":       "Emergency Strategy Meeting",
    "time":        "2:00 PM Today",
    "location":    "Conference Room A",
})
```

### 3. 查看系统健康状态

```go
// 获取系统健康报告
healthReport := stateManager.GetHealthReport()

// 查看公司公有信箱状态
if publicMailbox, ok := healthReport["public_mailbox"].(map[string]int); ok {
    fmt.Printf("Announcements: %d, Broadcasts: %d\n", 
        publicMailbox["announcements_count"], 
        publicMailbox["broadcasts_count"])
}

// 查看Agent状态
agentsMap := healthReport["agents"].(map[string]workflow.AgentStatus)
for role, status := range agentsMap {
    fmt.Printf("%s: %d tasks, %.1f workload\n", 
        role, status.TaskCount, status.Workload)
}
```

## 架构优势

### 1. 上下文保持
- **私有信箱**确保Agent能够访问自己的消息历史
- **执行历史**提供完整的操作记录和决策过程
- **状态追踪**支持调试和性能优化

### 2. 可追溯性
- 每个操作都有详细的时间戳和执行记录
- 支持按任务ID、时间范围等多维度查询
- 错误信息和依赖关系完整记录

### 3. 监控和调试
- 实时统计消息处理情况
- 执行性能指标（成功率、耗时等）
- 系统健康状态可视化

### 4. 灵活的通信
- **私有通信**: Agent间的直接消息交换
- **公有通信**: 公司级别的公告和广播
- **分级处理**: 支持不同优先级和类型的消息

## 配置参数

### 私有信箱配置
```go
mailbox := NewAgentmailbox(role, 1000) // 容量1000条消息
```

### 执行历史配置
```go
BaseAgentImpl{
    // ...
    historyMaxSize: 10000, // 最大保留10000条执行历史
}
```

### 公司公有信箱配置
```go
PublicMailbox: &CompanyPublicMailbox{
    maxSize: 10000, // 最大容量
}
```

## 性能特性

- **内存管理**: 采用LRU策略，自动清理旧记录
- **并发安全**: 使用读写锁保证线程安全
- **高效查询**: 支持多维度的快速历史查询
- **统计优化**: 实时计算关键性能指标

## 扩展性

系统设计支持未来扩展：
- 持久化存储到数据库
- 分布式消息队列集成
- 机器学习驱动的智能决策
- 更复杂的消息路由策略

## 运行演示

```bash
# 运行完整的演示程序
go run examples/agent_mailbox_demo.go
```

演示程序展示了：
- Agent消息处理和执行历史记录
- 私有信箱的使用
- 公司公有信箱的公告和广播功能
- 系统健康状态监控

---

这个增强的架构为SuperMan AI多智能体系统提供了强大的上下文管理和可追溯性，为构建更加智能和可靠的AI企业系统奠定了坚实基础。