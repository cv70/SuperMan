# SuperMan 24/7 自主运转系统设计文档

**创建日期**: 2026-02-12  
**版本**: v1.0  
**作者**: Sisyphus AI

---

## 1. 概述

本文档描述 SuperMan AI 公司系统的 24 小时自主运转机制设计。系统将通过混合驱动架构，实现多个 AI Agent 的持续、自动、高效协作，构建一个自我演进的虚拟企业。

### 1.1 核心原则

- **混合驱动**：事件驱动 + 时间驱动 + 目标驱动
- **Agent 自驱**：Agent 基于角色职责自动生成任务
- **去中心化**：无中央协调者，Agent 直接通过 Mailbox 通信
- **可预测性**：优先级队列保证关键任务优先执行
- **轻量级**：最小化基础设施，使用 SQLite 持久化

---

## 2. 核心架构设计

### 2.1 架构概览

```
┌─────────────────────────────────────────────────────────────────┐
│                    SuperMan 24/7 System                         │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │   Agent A   │  │   Agent B   │  │   Agent C   │  ...        │
│  │             │  │             │  │             │             │
│  │  +---------+│  │  +---------+│  │  +---------+│             │
│  │  | Self-   |│  │  | Self-   |│  │  | Self-   |│             │
│  │  |Generator|│  │  |Generator|│  │  |Generator|│             │
│  │  +---------+│  │  +---------+│  │  +---------+│             │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘             │
│         │                 │                 │                   │
│         └─────────────────┴─────────────────┘                   │
│                           │                                     │
│              ┌──────────▼──────────┐                            │
│              │     MailboxBus      │                            │
│              │  (Direct Comm)      │                            │
│              └──────────┬──────────┘                            │
│                         │                                       │
│            ┌────────────┴────────────┐                          │
│            │                         │                          │
│    ┌───────▼───────┐     ┌──────────▼──────────┐               │
│    │  AutoScheduler│     │   TimerEngine       │               │
│    │  (Priority Q) │     │   (CRON Tasks)      │               │
│    └───────┬───────┘     └──────────┬──────────┘               │
│            │                         │                          │
│            └──────────┬──────────────┘                          │
│                       │                                         │
│              ┌────────▼────────┐                               │
│              │    WorkList     │                               │
│              │ (Global Task   │                               │
│              │   Pool)         │                               │
│              └────────┬────────┘                               │
│                       │                                         │
│              ┌────────▼────────┐                               │
│              │   SQLite DB     │                               │
│              │  (Persistence)  │                               │
│              └─────────────────┘                               │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 核心组件

| 组件 | 职责 | 关键特性 |
|------|------|----------|
| **AutoScheduler** | 任务调度器 | 优先级队列、负载感知分配 |
| **TimerEngine** | 时间引擎 | CRON 表达式、任务链 |
| **TaskGenerator** | 任务生成器 | Agent 自驱任务入口 |
| **WorkList** | 全局任务池 | 中央任务数据库 |
| **SQLite Persistence** | 持久化层 | 任务、执行历史、事件 |

---

## 3. 自驱任务生成机制

### 3.1 任务生成依据

Agent 自驱任务基于以下三个维度：

1. **角色职责模板**
   - 每个角色定义核心职责任务列表
   - 示例（CEO）：`"审核战略目标"`、`"召开管理层会议"`

2. **状态扫描触发**
   - Agent 定期扫描 GlobalState
   - 异常检测触发任务（如 KPI 异常）

3. **任务依赖扩展**
   - 前置任务完成触发后续任务
   - 流水线式任务链

### 3.2 任务生成流程

```
┌──────────────┐
│ Agent 启动    │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ 加载职责模板   │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ 扫描全局状态   │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ LLM 生成候选 │
│   任务列表    │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ 验证优先级    │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ 添加到        │
│  WorkList     │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ 等待调度      │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ 执行任务      │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ 记录历史      │
└──────────────┘
```

### 3.3 任务结构

```go
type Task struct {
    TaskID        string
    Title         string
    Description   string
    AssignedTo    string
    AssignedBy    string
    Status        string
    Dependencies  []string
    Deliverables  []string
    Deadline      *time.Time
    CreatedAt     time.Time
    UpdatedAt     time.Time
    Metadata      map[string]any
    
    // 自驱任务特有字段
    Source        string        // "auto" | "event" | "scheduled"
    Priority      string        // "Critical" | "High" | "Medium" | "Low"
    GeneratedBy   string        // Agent Name
    GeneratedAt   time.Time
}
```

---

## 4. 优先级队列调度机制

### 4.1 队列设计

**队列结构**：
```
Priority Queue:
  Critical: [Task1, Task2, ...]
  High:     [Task3, Task4, ...]
  Medium:   [Task5, ...]
  Low:      [Task6, Task7, ...]
```

**调度算法**：加权轮询
- Critical：40% 权重
- High：30% 权重
- Medium：20% 权重
- Low：10% 权重

### 4.2 Agent 容量管理

- 每个 Agent 最大并发任务数：**3**（可配置）
- 超限时任务排队等待
- 动态负载均衡

### 4.3 任务分配策略

1. 优先分配给任务最少的 Agent
2. 同负载下按角色层级分配（下级→上级递归）
3. 特定任务类型绑定特定 Agent（如财务任务→CFO）

### 4.4 调度流程

```
┌──────────────┐
│ TimerEngine   │
│ 触发任务      │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ AutoScheduler │
│ 取出最高优先级 │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ 检查 Agent    │
│   容量        │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ 分配给空闲    │
│   Agent       │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ 更新任务状态  │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Agent 执行    │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ 归档任务      │
└──────────────┘
```

---

## 5. 时间引擎设计

### 5.1 CRON 表达式支持

**支持格式**（5 字段）：
```
分 时 日 月 周
```

**示例**：
| CRON 表达式 | 含义 |
|------------|------|
| `0 9 * * 1` | 每周一 9:00 |
| `*/5 * * * *` | 每 5 分钟 |
| `0 0 * * *` | 每天 0:00 |
| `0 0 1 * *` | 每月 1 日 0:00 |

### 5.2 配置文件

```yaml
# config/cron.yaml
cron_jobs:
  - name: "CEO_Daily_Report"
    cron: "0 9 * * 1"  # 每周一 9:00
    target_agent: "ceo"
    task_template:
      title: "阅读周报并制定决策"
      description: "CEO 每周接收所有部门周报"
      
  - name: "CFO_Monthly_Report"
    cron: "0 0 1 * *"  # 每月 1 日 0:00
    target_agent: "cfo"
    task_template:
      title: "生成月度财务报告"
      description: "CFO 每月生成公司财务状况报告"
```

### 5.3 任务链支持

支持任务依赖：
- **任务 A 完成后触发任务 B**
- **任务 A、B 完成后触发任务 C**

---

## 6. 数据持久化设计

### 6.1 SQLite 数据库

**文件位置**：`data/superman.db`

**表结构**：

**1. tasks 表**（任务状态）
```sql
CREATE TABLE tasks (
    task_id TEXT PRIMARY KEY,
    title TEXT,
    description TEXT,
    assigned_to TEXT,
    assigned_by TEXT,
    status TEXT,
    dependencies TEXT,  -- JSON
    deliverables TEXT,  -- JSON
    deadline TEXT,
    created_at TEXT,
    updated_at TEXT,
    metadata TEXT,      -- JSON
    source TEXT,
    priority TEXT,
    generated_by TEXT,
    generated_at TEXT
);
```

**2. executions 表**（执行历史）
```sql
CREATE TABLE executions (
    execution_id TEXT PRIMARY KEY,
    task_id TEXT,
    agent_name TEXT,
    action TEXT,
    input TEXT,         -- JSON
    output TEXT,        -- JSON
    status TEXT,
    duration_ms INTEGER,
    error_message TEXT,
    timestamp TEXT
);
```

**3. agents 表**（Agent 配置）
```sql
CREATE TABLE agents (
    agent_name TEXT PRIMARY KEY,
    description TEXT,
    model TEXT,
    hierarchy INTEGER,
    skill_dir TEXT
);
```

**4. cron_jobs 表**（定时任务）
```sql
CREATE TABLE cron_jobs (
    job_id TEXT PRIMARY KEY,
    name TEXT,
    cron_expr TEXT,
    target_agent TEXT,
    task_template TEXT  -- JSON
);
```

**5. events 表**（关键事件）
```sql
CREATE TABLE events (
    event_id TEXT PRIMARY KEY,
    event_type TEXT,
    message TEXT,
    agent_name TEXT,
    timestamp TEXT
);
```

### 6.2 文件存储

| 文件路径 | 内容 |
|---------|------|
| `data/cron_executions.db` | CRON 任务执行历史 |
| `data/dead_letter.db` | 死信队列（失败任务） |
| `data/events.log` | 关键事件日志 |

---

## 7. 错误处理与容错

### 7.1 失败策略

**自动重试**：
- 失败任务延迟后重试
- 指数退避：1s → 2s → 4s

**降级处理**：
- 关键任务失败 → 升级到上级 Agent
- 3 次失败后进入死信队列

### 7.2 容错机制

**Agent 崩溃**：
- 自动重启
- 从 SQLite 恢复状态

**GlobalState 崩溃**：
- 从 SQLite 恢复所有状态

**任务队列持久化**：
- 所有任务写入 SQLite
- 防止内存丢失

### 7.3 死信队列

**触发条件**：
- 重试 3 次仍失败
- 任务超时

**存储位置**：`data/dead_letter.db`

**告警策略**：
- 死信数量 > 10 → 通知 HR
- 连续失败 → 通知 CEO 和 CTO

---

## 8. 实现计划

### Phase 1：核心框架（2-3 天）

- [ ] AutoScheduler（优先级队列实现）
- [ ] TimerEngine（CRON 支持）
- [ ] WorkList（全局任务池）
- [ ] SQLite 持久化层

### Phase 2：Agent 自驱（2 天）

- [ ] TaskGenerator 接口
- [ ] 角色职责模板定义
- [ ] Agent 集成

### Phase 3：系统集成（1 天）

- [ ] 端到端测试
- [ ] 负载测试

### Phase 4：文档完善（0.5 天）

- [ ] 编写 API 文档
- [ ] 操作手册

---

## 9. 参考资料

- Google ADK 文档
- SuperMan 项目 README
- Mailbox 通信协议
- 全局状态管理规范

---

## 10. 变更记录

| 日期 | 版本 | 变更内容 | 作者 |
|------|------|---------|------|
| 2026-02-12 | v1.0 | 初始版本 | Sisyphus AI |
