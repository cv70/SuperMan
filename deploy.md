# SuperMan AI 多智能体公司系统 - 部署指南

## 📋 目录

- [部署指南](#deploy-guide)
  - [📋 目录](#-目录)
  - [🛠️ 系统要求](#️-系统要求)
  - [🚀 快速开始](#-快速开始)
  - [⚙️ 环境配置](#️-环境配置)
  - [🔧 详细部署步骤](#-详细部署步骤)
  - [🐳 Docker 部署](#-docker-部署)
  - [📊 监控与日志](#-监控与日志)
  - [🔧 故障排查](#-故障排查)
  - [📈 性能优化](#-性能优化)

---

## 🛠️ 系统要求

| 组件 | 最低版本 | 说明 |
|------|---------|------|
| Go | 1.24+ | 项目基于 Go 1.24+ |
| Google ADK | v0.4.0+ | Google Agent Development Kit |
| Git | Latest | 用于克隆项目 |

---

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone <repository-url>
cd SuperMan
```

### 2. 安装依赖

```bash
# 下载 Go 模块依赖
go mod download

# 验证依赖
go mod verify
```

### 3. 构建项目

```bash
# 构建可执行文件
go build -o superman .

# 或者编译所有包
go build ./...
```

### 4. 启动系统

```bash
# 直接运行
go run .

# 或运行编译后的二进制文件
./superman
```

启动成功后，您将看到：

```
SuperMan AI Multi-Agent Company System using Google ADK
=======================================================

正在创建AI智能体...
  已创建: ceo_agent (ceo)
  已创建: cto_agent (cto)
  ...

启动Mailbox系统...
Mailbox系统启动成功

=== 系统初始化完成 ===
智能体总数: 10
当前时间: 2026-02-07T20:12:09

=== 系统健康报告 ===
智能体总数: 10
任务总数: 0
消息总数: 0

=== 启动 ADK Launcher ===
访问 http://localhost:8080 查看交互界面
```

---

## ⚙️ 环境配置

### 基础配置

项目配置主要通过代码中的配置结构和环境变量进行。

#### Mailbox 系统配置

在 `main.go` 中配置 Mailbox 系统：

```go
// 创建Mailbox管理器配置
mailboxConfig := mailbox.DefaultMailboxManagerConfig()

// 是否启用死信队列（需要CGO/SQLite支持）
mailboxConfig.EnableDLQ = false  // 默认禁用，避免CGO依赖

// 幂等性检查配置
mailboxConfig.IdempotencyMaxSize = 100000  // 最大缓存大小
mailboxConfig.IdempotencyWindow = 24        // 窗口时间（小时）

// 是否启用指标收集
mailboxConfig.EnableMetrics = true

mailboxManager, err := mailbox.NewMailboxManager(mailboxConfig)
```

#### Mailbox 配置参数

```go
// 单个Mailbox的配置
type MailboxConfig struct {
    Receiver          agents.AgentRole                  // 接收者角色
    InboxBufferSize   int                               // 收件箱缓冲区 (默认: 1000)
    MaxRetries        int                               // 最大重试次数 (默认: 3)
    BaseDelay         time.Duration                     // 基础退避延迟 (默认: 1s)
    MaxDelay          time.Duration                     // 最大退避延迟 (默认: 5min)
    ProcessingTimeout map[agents.Priority]time.Duration // 各优先级超时
    MaxQueueDepth     int                               // 最大队列深度 (默认: 10000)
    EnableDLQ         bool                              // 是否启用死信队列
}

// 优先级超时配置
timeouts := map[agents.Priority]time.Duration{
    agents.PriorityCritical: 5 * time.Second,   // 紧急: 5秒
    agents.PriorityHigh:     10 * time.Second,  // 高: 10秒
    agents.PriorityMedium:   30 * time.Second,  // 中: 30秒
    agents.PriorityLow:      60 * time.Second,  // 低: 60秒
}
```
---

## 🔧 详细部署步骤

### 步骤 1: 安装 Go 环境

**Linux/macOS:**

```bash
# 下载并安装 Go (以 1.24 为例)
wget https://go.dev/dl/go1.24.linux-amd64.tar.gz
sudo tar -C /usr/local -xzf go1.24.linux-amd64.tar.gz

# 配置环境变量
export PATH=$PATH:/usr/local/go/bin
export GOPATH=$HOME/go
```

**Windows:**

1. 下载 Go 安装包：https://go.dev/dl/
2. 运行安装程序
3. 配置环境变量（安装程序通常会自动配置）

验证安装：

```bash
go version
# 输出: go version go1.24.x xxx/xxx
```

### 步骤 2: 安装依赖

```bash
# 进入项目目录
cd SuperMan

# 下载 Go 模块依赖
go mod download

# 整理 go.mod
go mod tidy
```

### 步骤 3: 运行测试

```bash
# 运行所有测试
go test ./...

# 运行 Mailbox 包测试（带详细输出）
go test ./mailbox/... -v

# 运行特定测试
go test ./mailbox/... -run TestMailboxManager -v
```

### 步骤 4: 构建项目

```bash
# 开发构建
go build -o superman .

# 生产构建（优化）
go build -ldflags="-s -w" -o superman .

# 交叉编译（Linux）
GOOS=linux GOARCH=amd64 go build -o superman-linux .

# 交叉编译（Windows）
GOOS=windows GOARCH=amd64 go build -o superman.exe .
```

### 步骤 5: 启动服务

```bash
# 开发模式
go run .

# 使用编译后的二进制
./superman

# 后台运行（Linux/macOS）
nohup ./superman &

# 使用 systemd（Linux生产环境）
sudo systemctl start superman
```

### 步骤 6: 验证启动

启动成功后，您应该看到：

```
SuperMan AI Multi-Agent Company System using Google ADK
=======================================================

正在创建AI智能体...
  已创建: cto_agent (cto)
  已创建: cpo_agent (cpo)
  已创建: cmo_agent (cmo)
  已创建: cfo_agent (cfo)
  已创建: hr_agent (hr)
  已创建: rd_agent (rd)
  已创建: customer_support_agent (customer_support)
  已创建: ceo_agent (ceo)
  已创建: data_analyst_agent (data_analyst)
  已创建: operations_agent (operations)

启动Mailbox系统...
Mailbox系统启动成功

=== 系统初始化完成 ===
智能体总数: 10
当前时间: 2026-02-07T20:12:09

=== 系统健康报告 ===
智能体总数: 10
任务总数: 0
消息总数: 0

智能体状态:
  ceo: 0 任务, 0.0 负载, 完成: 0
  cto: 0 任务, 0.0 负载, 完成: 0
  ...

=== 启动 ADK Launcher ===
访问 http://localhost:8080 查看交互界面
```
---

## 🐳 Docker 部署

### 1. 创建 Dockerfile

```dockerfile
# 构建阶段
FROM golang:1.24-alpine AS builder

WORKDIR /app

# 安装 git（可能需要拉取私有依赖）
RUN apk add --no-cache git

# 复制 go.mod 和 go.sum
copy go.mod go.sum ./

# 下载依赖
RUN go mod download

# 复制源代码
COPY . .

# 构建二进制文件（禁用 CGO，静态链接）
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o superman .

# 运行阶段
FROM alpine:latest

WORKDIR /app

# 安装 ca-certificates（用于 HTTPS 请求）
RUN apk --no-cache add ca-certificates

# 从构建阶段复制二进制文件
COPY --from=builder /app/superman .

# 创建数据目录
RUN mkdir -p /app/data

# 暴露端口（ADK 默认端口）
EXPOSE 8080

# 启动命令
CMD ["./superman"]
```

### 2. 构建镜像

```bash
# 构建 Docker 镜像
docker build -t superman-ai:latest .

# 查看构建的镜像
docker images | grep superman-ai
```

### 3. 运行容器

```bash
# 前台运行
docker run -it -p 8080:8080 superman-ai:latest

# 后台运行
docker run -d -p 8080:8080 --name superman superman-ai:latest

# 查看日志
docker logs -f superman

# 停止容器
docker stop superman

# 删除容器
docker rm superman
```

### 4. 使用 Docker Compose（推荐用于生产）

创建 `docker-compose.yml`：

```yaml
version: '3.8'

services:
  superman:
    build: .
    container_name: superman-ai
    ports:
      - "8080:8080"
    environment:
      - GO_ENV=production
    volumes:
      - ./data:/app/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # 可选：添加监控
  prometheus:
    image: prom/prometheus:latest
    container_name: superman-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
    depends_on:
      - superman
```

启动：

```bash
docker-compose up -d

docker-compose logs -f
```

---

## 📊 监控与日志

### Mailbox 系统指标

系统内置 Mailbox 指标收集，无需额外配置：

| 指标 | 类型 | 描述 |
|------|------|------|
| `messages_sent_total` | Counter | 消息发送总数（按sender-receiver-type） |
| `messages_received_total` | Counter | 消息接收总数（按receiver-type） |
| `messages_processed_total` | Counter | 消息处理统计（success/failed） |
| `mailbox_queue_depth` | Gauge | 各Mailbox队列深度 |
| `processing_duration_avg` | Gauge | 平均处理耗时 |
| `processing_duration_p99` | Gauge | P99处理耗时 |
| `mailbox_retry_total` | Counter | 重试次数统计 |
| `dlq_depth_total` | Gauge | 死信队列深度 |

### 查看运行时指标

```go
// 在代码中获取指标
stats := orchestrator.GetMailboxManager().GetAllStats()

// JSON 格式示例：
{
  "mailboxes": {
    "ceo": {
      "receiver": "ceo",
      "queue_depth": 5,
      "processing_count": 2,
      "started": true
    },
    "cto": {
      "receiver": "cto",
      "queue_depth": 3,
      "processing_count": 1,
      "started": true
    }
    // ...
  },
  "metrics": {
    "messages_sent_total": {
      "ceo_cto_task_assignment": 10,
      "cto_ceo_status_report": 8
    },
    "messages_received_total": {
      "ceo_task_assignment": 10,
      "cto_status_report": 8
    },
    "messages_processed_total": {
      "ceo_success": 10,
      "cto_success": 8
    },
    "mailbox_queue_depth": {
      "ceo_medium": 5,
      "cto_high": 3
    },
    "processing_duration_avg": 150000000,  // 150ms (纳秒)
    "processing_duration_p99": 500000000   // 500ms (纳秒)
  }
}
```

### 日志输出

系统使用标准输出日志：

```bash
# 查看实时日志
go run . 2>&1 | tee superman.log

# 使用 journalctl（systemd）
sudo journalctl -u superman -f

# 使用 Docker
docker logs -f superman
```

---

## 🔧 故障排查

### 常见问题

#### 1. 编译错误

**症状:**
```
go: module superman: not found
```

**解决:**
```bash
# 确保在项目根目录
cd /path/to/SuperMan

# 初始化模块（如果是新clone的项目）
go mod init superman

# 整理依赖
go mod tidy

# 重新编译
go build .
```

#### 2. Mailbox 启动失败

**症状:**
```
Failed to create mailbox manager: failed to create DLQ: Binary was compiled with 'CGO_ENABLED=0'
```

**解决:**
```go
// 在 main.go 中禁用 DLQ
mailboxConfig := mailbox.DefaultMailboxManagerConfig()
mailboxConfig.EnableDLQ = false  // 禁用死信队列
mailboxManager, err := mailbox.NewMailboxManager(mailboxConfig)
```

#### 3. 端口冲突

**症状:**
```
listen tcp :8080: bind: address already in use
```

**解决:**
```bash
# 查找占用端口的进程
lsof -i :8080
# 或
netstat -tulpn | grep 8080

# 结束占用进程
kill -9 <PID>

# 或修改 ADK 端口（查阅 ADK 文档）
```

#### 4. 消息处理超时

**症状:**
```
[ERROR] Message processing timeout
```

**解决:**
```go
// 调整处理超时时间
config := mailbox.DefaultMailboxConfig(role)
config.ProcessingTimeout = map[agents.Priority]time.Duration{
    agents.PriorityCritical: 10 * time.Second,  // 增加超时
    agents.PriorityHigh:     20 * time.Second,
    agents.PriorityMedium:   60 * time.Second,
    agents.PriorityLow:      120 * time.Second,
}
```

#### 5. 队列积压

**症状:**
队列深度持续增长，消息处理缓慢

**解决:**
```go
// 1. 增加缓冲区大小
config.InboxBufferSize = 5000  // 默认 1000

// 2. 优化 Handler 性能
// 检查 Handler 中是否有阻塞操作

// 3. 查看统计信息定位问题
stats := mailboxManager.GetAllStats()
fmt.Printf("Queue depth: %v\n", stats["metrics"]["mailbox_queue_depth"])
```

---

## 📈 性能优化

### 1. Mailbox 配置优化

```go
// 高吞吐量场景配置
config := &mailbox.MailboxConfig{
    Receiver:        role,
    InboxBufferSize: 5000,              // 更大的缓冲区
    MaxQueueDepth:   50000,             // 更大的队列深度
    MaxRetries:      3,
    BaseDelay:       500 * time.Millisecond,  // 更短的退避
    MaxDelay:        2 * time.Minute,
    ProcessingTimeout: map[agents.Priority]time.Duration{
        agents.PriorityCritical: 5 * time.Second,
        agents.PriorityHigh:     10 * time.Second,
        agents.PriorityMedium:   30 * time.Second,
        agents.PriorityLow:      60 * time.Second,
    },
    EnableDLQ: false,  // 禁用DLQ以减少IO
}
```

### 2. 幂等性缓存优化

```go
// 根据实际消息量调整缓存大小
mailboxConfig.IdempotencyMaxSize = 500000  // 默认 100000
mailboxConfig.IdempotencyWindow = 12        // 缩短窗口（小时）
```

### 3. 编译优化

```bash
# 生产环境编译（去除调试信息，减小体积）
CGO_ENABLED=0 go build -ldflags="-s -w" -o superman .

# 使用 upx 进一步压缩（可选）
upx --best superman
```

### 4. 运行时优化

```bash
# 设置 Go 运行时参数
export GOMAXPROCS=8        # 设置使用的 CPU 核心数
export GOGC=100            # 调整 GC 目标百分比
export GOMEMLIMIT=4GiB     # 设置内存限制

# 运行
./superman
```

---

## 📝 部署检查清单

- [ ] Go 1.24+ 已安装
- [ ] 项目依赖已下载 (`go mod download`)
- [ ] 测试运行通过 (`go test ./...`)
- [ ] 二进制文件已编译 (`go build -o superman .`)
- [ ] Mailbox 配置已调整（队列深度、超时等）
- [ ] DLQ 配置已检查（无CGO时需要禁用）
- [ ] 端口 8080 可用（或已修改）
- [ ] 日志路径已创建并可写

---

## 📞 获取帮助

- **架构文档**: `ARCH.md` - 系统架构详细说明
- **项目说明**: `README.md` - 项目概述和使用说明
- **Go 文档**: https://pkg.go.dev/superman
- **代码结构**:
  - `agents/` - 智能体定义
  - `mailbox/` - Mailbox 消息系统
  - `workflow/` - 工作流编排
  - `main.go` - 程序入口

---

**版本**: 1.0  
**最后更新**: 2026-02-07
