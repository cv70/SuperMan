# SuperMan AI 消息通信优化设计文档

日期: 2026-02-07  
主题: Agent信箱通信系统优化

## 1. 设计目标

- **高可靠性**: 消息不丢失、可重试
- **高可观测性**: 链路追踪、指标监控
- **分区有序**: 同一任务的消息按顺序处理
- **单机部署**: 单进程、零外部依赖

## 2. 核心架构

### 2.1 信箱模式

- 每个Agent拥有独立Mailbox
- Mailbox包含优先级队列（最小堆）
- 直接点对点投递，无中间代理

```
┌────────────────────────────────────────────────────────┐
│                    Agent A (CEO)                       │
│  ┌─────────────────────────────────────────────────┐   │
│  │              CEO Mailbox                        │   │
│  │  ┌───────────────────────────────────────────┐  │   │
│  │  │           优先级队列 (最小堆)              │  │   │
│  │  │  [紧急] msg1 (来自CFO)                    │  │   │
│  │  │  [高]   msg2 (来自CTO)                    │  │   │
│  │  │  [中]   msg3 (来自Operations)             │  │   │
│  │  │  [低]   msg4 (来自HR)                     │  │   │
│  │  └───────────────────────────────────────────┘  │   │
│  │                                                 │   │
│  │  • 接收通道 (chan)                             │   │
│  │  • 处理中消息表 (map[msgID]Message)             │   │
│  │  • 持久化WAL (Write-Ahead Log)                 │   │
│  └─────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────┘
                            │
              ┌─────────────┼─────────────┐
              │             │             │
              ▼             ▼             ▼
       ┌──────────┐  ┌──────────┐  ┌──────────┐
       │CTO信箱   │  │CFO信箱   │  │HR信箱    │
       │          │  │          │  │          │
       │[高]msg5  │  │[紧急]msg6│  │[低]msg7  │
       │[中]msg8  │  │[高]msg9  │  │[中]msg10 │
       └──────────┘  └──────────┘  └──────────┘
```

### 2.2 关键组件

#### Mailbox结构

```go
type Mailbox struct {
    owner         AgentRole
    queue         *PriorityQueue     // 优先级队列（最小堆）
    inbox         chan *Message      // 接收新消息的channel
    processing    map[string]*Message // 当前处理中的消息
    wal           *WAL               // 持久化日志
    mutex         sync.RWMutex
}
```

#### WAL (Write-Ahead Log)

- **格式**: SequenceID + Timestamp + Operation + Message
- **操作类型**: APPEND / ACK / NACK / DeadLetter
- **策略**: 批量刷盘(100ms/100条)、日志轮转(100MB)

```go
type WALEntry struct {
    SequenceID    int64              // 全局递增序列号
    Timestamp     int64              // Unix纳秒时间戳
    Operation     WALOperation       // 操作类型
    MessageID     string             // 消息唯一ID (UUIDv7)
    Message       *Message           // 完整消息内容
    RetryCount    int                // 当前重试次数
}

type WALOperation int8
const (
    WALOpAppend WALOperation = iota  // 消息入队
    WALOpACK                          // 消息成功处理
    WALOpNACK                         // 消息处理失败（可重试）
    WALOpDeadLetter                   // 进入死信队列
)
```

## 3. 可靠性机制

### 3.1 消息持久化

1. 消息入队前先写WAL
2. 处理完成后写WAL ACK
3. 系统崩溃后从WAL恢复

**恢复流程**:
```
系统启动时:
1. 读取WAL文件，按SequenceID排序
2. 对于WALOpAppend但未WALOpACK的消息:
   - 重新投递到对应Mailbox的queue
3. 重建每个Mailbox的processing表
```

### 3.2 重试策略

- **指数退避**: delay = min(1s * 2^retry, 5min)
- **最大重试**: 3次
- **超时设置**: 
  - Critical=5s
  - High=10s
  - Medium=30s
  - Low=60s

```go
delay = min(baseDelay * (2^retryCount), maxDelay)
// baseDelay = 1秒
// maxDelay = 5分钟
// maxRetryCount = 3次
```

### 3.3 幂等性

- **MessageID**: UUIDv7时间有序
- **去重窗口**: 24小时
- **LRU缓存**: 内存存储最近10万条
- **SQLite持久化**: 定期同步

```go
type IdempotencyChecker struct {
    processedIDs *lru.Cache          // 最近处理的消息ID
    windowSize   time.Duration        // 去重窗口：24小时
}

func (m *Mailbox) ProcessMessage(msg *Message) error {
    // 1. 检查是否已处理
    if m.idempotencyChecker.IsProcessed(msg.MessageID) {
        log.Printf("[去重] 消息 %s 已处理，跳过", msg.MessageID)
        return nil // 幂等：直接返回成功
    }
    
    // 2. 实际处理
    result, err := m.handler(msg)
    
    // 3. 记录已处理
    m.idempotencyChecker.MarkProcessed(msg.MessageID)
    
    return err
}
```

### 3.4 死信队列

**进入DLQ的条件**:
- 消息重试3次仍失败
- 消息处理panic（不可恢复错误）
- 消息格式错误（无法解析）

**DLQ结构**:
```go
type DeadLetterQueue struct {
    messages []*DeadLetterMessage
    storage  *sqlite.DB
}

type DeadLetterMessage struct {
    OriginalMessage *Message
    FailedAt        time.Time
    Reason          string
    RetryCount      int
    StackTrace      string
}
```

**DLQ处理流程**:
```
消息处理失败:
├─> 重试次数 < 3 ?
│   ├─> 是: 计算退避延迟 -> 延迟后重新入队
│   └─> 否: 进入DLQ
│       ├─> 写入WAL (WALOpDeadLetter)
│       ├─> 写入SQLite DLQ表
│       └─> 发送告警通知
└─> 原队列删除消息
```

**SQLite DLQ表结构**:
```sql
CREATE TABLE dead_letter_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id TEXT UNIQUE NOT NULL,
    sender TEXT NOT NULL,
    receiver TEXT NOT NULL,
    content BLOB NOT NULL,
    failed_at TIMESTAMP NOT NULL,
    retry_count INTEGER NOT NULL,
    reason TEXT,
    stack_trace TEXT,
    status TEXT DEFAULT 'pending'
);
```

**DLQ管理策略**:

| 操作 | 触发条件 | 行为 |
|------|----------|------|
| 人工重试 | 管理员手动触发 | 从DLQ取出，重新投递到原Mailbox |
| 自动清理 | 进入DLQ超过30天 | 归档到文件后删除 |
| 告警 | DLQ积压>100条 | 发送邮件/日志告警 |
| 分析 | 定期（每天） | 生成DLQ报告 |

## 4. 可观测性

### 4.1 监控指标

```go
// 消息吞吐指标
messages_sent_total{sender, receiver, message_type}
messages_received_total{receiver, message_type}
messages_processed_total{receiver, status}
message_latency_seconds{receiver, priority}

// 队列指标
mailbox_queue_depth{receiver, priority}
mailbox_processing_duration_seconds{receiver}
mailbox_retry_total{receiver}

// 系统指标
wal_write_latency_seconds
wal_size_bytes
dlq_depth_total
```

### 4.2 链路追踪

```go
type MessageContext struct {
    TraceID    string
    SpanID     string
    ParentID   string
    StartTime  time.Time
}

type Message struct {
    // ... 原有字段
    Context    *MessageContext
}
```

**追踪流程**:
```
CEO发送消息给CTO:
├─> 生成TraceID
├─> Span: "send_message" (CEO)
└─> 消息投递到CTO Mailbox
    └─> Span: "receive_message" (CTO)
        └─> Span: "process_message" (CTO)
            └─> 响应消息继续传播TraceID
```

### 4.3 日志规范

```json
{
  "timestamp": "2026-02-07T19:30:00Z",
  "level": "INFO",
  "trace_id": "abc-123",
  "span_id": "span-456",
  "agent": "cto",
  "event": "message_processed",
  "message_id": "msg-789",
  "sender": "ceo",
  "message_type": "task_assignment",
  "priority": "high",
  "duration_ms": 150,
  "retry_count": 0,
  "status": "success"
}
```

### 4.4 告警规则

| 告警名称 | 条件 | 级别 |
|----------|------|------|
| 消息延迟过高 | p99延迟 > 5秒 | Warning |
| 队列积压 | 队列深度 > 1000 | Critical |
| DLQ增长 | 1小时内新增 > 50条 | Warning |
| 消息处理失败率 | 失败率 > 5% | Critical |
| WAL写入延迟 | 平均延迟 > 100ms | Warning |

## 5. 完整数据流

```
Agent A 发送消息:
├─> 生成MessageID (UUIDv7)
├─> 写入WAL (WALOpAppend)
├─> 投递到Agent B的Mailbox.inbox
├─> Mailbox按Priority插入queue
└─> Agent B worker取出处理
    ├─> 检查幂等性 (MessageID去重)
    ├─> 实际业务处理
    ├─> 写入WAL (WALOpACK)
    └─> 如果失败:
        ├─> 重试次数 < 3 ? 延迟重试 : 进入DLQ
        └─> 写入WAL (WALOpNACK / WALOpDeadLetter)
```

## 6. 接口设计

```go
// Mailbox接口
type Mailbox interface {
    Send(msg *Message) error
    Receive() (*Message, error)
    Ack(msgID string) error
    Nack(msgID string, retryable bool) error
    GetMetrics() MailboxMetrics
}

// WAL接口
type WAL interface {
    Append(entry *WALEntry) error
    Recover() ([]*WALEntry, error)
    Checkpoint() error
}

// 消息结构
type Message struct {
    MessageID       string
    Sender          AgentRole
    Receiver        AgentRole
    MessageType     MessageType
    Content         map[string]any
    Priority        Priority
    Timestamp       time.Time
    Context         *MessageContext
}
```

## 7. 性能预估

| 指标 | 预估 |
|------|------|
| 吞吐量 | >10万消息/秒（单机） |
| 延迟 | p99 < 10ms（WAL批量写入） |
| 内存 | 每个Mailbox约10MB |
| 磁盘 | WAL约1GB/天（高频场景） |

## 8. 下一步实施计划

1. **实现WAL组件**: 顺序写入、批量刷盘、日志轮转
2. **实现Mailbox核心逻辑**: 优先级队列、接收通道、处理循环
3. **集成到现有Agent系统**: 替换现有消息处理机制
4. **添加监控指标**: Prometheus指标暴露、日志集成
5. **压力测试验证**: 验证吞吐量和延迟目标

## 9. 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| WAL文件损坏 | 消息丢失 | 定期checkpoint、多副本写入 |
| 内存溢出 | 系统崩溃 | 队列深度限制、背压机制 |
| 消息积压 | 延迟增加 | 动态扩缩容、优先级调整 |
| 死信堆积 | 磁盘满 | 自动清理、告警通知 |

## 10. 参考

- Raft论文: 日志复制机制
- Kafka设计: 分区有序、批量写入
- Actor模型: Mailbox消息处理模式
- OpenTelemetry: 链路追踪标准
