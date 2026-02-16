package main

import (
	"bufio"
	"context"
	"fmt"
	"log/slog"
	"os"
	"os/signal"
	"strings"
	"syscall"
	"time"

	"superman/agents"
	"superman/config"
	"superman/ds"
	"superman/infra"
	"superman/mailbox"
	"superman/scheduler"
	"superman/timer"
	"superman/workflow"

	"github.com/cv70/pkgo/mistake"
)

func main() {
	slog.Info("SuperMan AI Multi-Agent Company System starting")

	err := config.InitConfig()
	mistake.Unwrap(err)

	ctx := context.Background()

	r, err := infra.NewRegistry(ctx, &config.AppConfig)
	mistake.Unwrap(err)

	// 创建 MailboxBus（全局消息总线）
	mailboxBus := mailbox.NewMailboxBus()
	globalState := mailboxBus.GetGlobalState()

	// 创建 Orchestrator（任务分发器）
	orchestrator := workflow.NewOrchestrator(mailboxBus)

	// 解析调度器轮询间隔
	tickInterval := 5 * time.Second
	if config.AppConfig.Scheduler != nil && config.AppConfig.Scheduler.TickInterval != "" {
		if d, err := time.ParseDuration(config.AppConfig.Scheduler.TickInterval); err == nil {
			tickInterval = d
		}
	}

	// 创建 AutoScheduler（调度器）
	schedulerInstance := scheduler.NewAutoScheduler(orchestrator, globalState, tickInterval)

	slog.Info("creating AI agents")

	agentMap := make(map[string]agents.Agent)
	for _, agentConfig := range config.AppConfig.Agents {
		agent, err := agents.NewBaseAgent(ctx, r.LLM[agentConfig.Model], mailboxBus, agentConfig, config.AppConfig.Agents...)
		mistake.Unwrap(err)

		// 注册 Agent 到 Orchestrator
		orchestrator.RegisterAgent(agent)

		// 注册 Mailbox 到总线
		mb := agent.GetMailbox()
		err = mailboxBus.RegisterMailbox(agent.GetName(), mb)
		mistake.Unwrap(err)

		// 设置全局状态
		agent.SetGlobalState(globalState)

		// 设置回调：任务提交 -> 调度器
		agent.SetTaskSubmitter(func(task *ds.Task, priority string) {
			schedulerInstance.AddTask(task, priority)
		})

		// 设置回调：任务完成 -> 调度器
		agent.SetOnTaskComplete(schedulerInstance.OnTaskComplete)

		agentMap[agent.GetName()] = agent

		// 注册 Agent 到调度器
		maxTasks := agentConfig.MaxTasks
		if maxTasks <= 0 {
			maxTasks = 3
		}
		schedulerInstance.AddAgent(agentConfig.Name, maxTasks, agentConfig.Hierarchy)

		// 启动 Agent
		err = agent.Start()
		mistake.Unwrap(err)
	}

	// 启动 AutoScheduler 调度循环
	schedulerInstance.Start()

	// 创建并启动 TimerEngine
	timerEngine := timer.NewTimerEngine(schedulerInstance, config.AppConfig.Timer)
	timerEngine.Start()

	slog.Info("system initialized",
		slog.Int("agent_count", len(agentMap)),
		slog.Int("queue_length", schedulerInstance.GetQueueLength()),
	)

	// 设置信号处理（优雅关闭）
	sigCh := make(chan os.Signal, 1)
	signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)

	// 启动交互式控制台（在独立 goroutine 中运行）
	inputCh := make(chan string, 1)
	go func() {
		reader := bufio.NewReader(os.Stdin)
		for {
			fmt.Print("> ")
			input, err := reader.ReadString('\n')
			if err != nil {
				return
			}
			input = strings.TrimSpace(input)
			if input != "" {
				inputCh <- input
			}
		}
	}()

	fmt.Println("\n=== SuperMan System Ready ===")
	fmt.Println("Commands: send <msg>, status, exit")
	fmt.Println()

	// 主事件循环
	for {
		select {
		case sig := <-sigCh:
			slog.Info("received signal, shutting down", slog.String("signal", sig.String()))
			shutdown(timerEngine, schedulerInstance, agentMap)
			return
		case input := <-inputCh:
			if input == "exit" {
				slog.Info("exit command received, shutting down")
				shutdown(timerEngine, schedulerInstance, agentMap)
				return
			}
			processInput(agentMap, mailboxBus, schedulerInstance, input)
		}
	}
}

// shutdown 优雅关闭所有组件（按依赖顺序）
func shutdown(timerEngine *timer.TimerEngine, schedulerInstance *scheduler.AutoScheduler, agentMap map[string]agents.Agent) {
	slog.Info("stopping timer engine")
	timerEngine.Stop()

	slog.Info("stopping scheduler")
	schedulerInstance.Stop()

	slog.Info("stopping agents")
	for name, agent := range agentMap {
		if err := agent.Stop(); err != nil {
			slog.Error("failed to stop agent", slog.String("agent", name), slog.Any("error", err))
		}
	}

	slog.Info("shutdown complete")
}

func processInput(agentMap map[string]agents.Agent, mailboxBus *mailbox.MailboxBus, schedulerInstance *scheduler.AutoScheduler, input string) {
	parts := strings.Fields(input)
	if len(parts) == 0 {
		return
	}

	command := parts[0]

	switch command {
	case "send":
		message := strings.Join(parts[1:], " ")
		msg, err := ds.NewRequestMessage(
			"user",
			"chairman",
			"message",
			message,
			nil,
		)
		if err != nil {
			slog.Error("failed to create message", slog.Any("error", err))
			return
		}
		err = mailboxBus.Send(msg)
		if err != nil {
			slog.Error("failed to send message", slog.Any("error", err))
		}
	case "status":
		fmt.Println("\n--- System Status ---")
		fmt.Printf("Scheduler queue: %d\n", schedulerInstance.GetQueueLength())
		for _, priority := range []string{scheduler.PriorityCritical, scheduler.PriorityHigh, scheduler.PriorityMedium, scheduler.PriorityLow} {
			fmt.Printf("  [%s]: %d\n", priority, schedulerInstance.GetQueueLengthByPriority(priority))
		}
		for name, agent := range agentMap {
			fmt.Printf("  %s (workload: %.0f, running: %v)\n", name, agent.GetWorkload(), agent.IsRunning())
		}
		fmt.Println()
	default:
		fmt.Printf("Unknown command: %s\n", command)
		fmt.Println("Commands: send <msg>, status, exit")
	}
}
