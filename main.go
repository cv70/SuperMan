package main

import (
	"context"
	"fmt"
	"log/slog"
	"os"
	"os/signal"
	"syscall"
	"time"

	"superman/agents"
	"superman/api"
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

		orchestrator.RegisterAgent(agent)

		mb := agent.GetMailbox()
		err = mailboxBus.RegisterMailbox(agent.GetName(), mb)
		mistake.Unwrap(err)

		agent.SetGlobalState(globalState)

		agent.SetTaskSubmitter(func(task *ds.Task, priority string) {
			schedulerInstance.AddTask(task, priority)
		})

		agent.SetOnTaskComplete(schedulerInstance.OnTaskComplete)

		agentMap[agent.GetName()] = agent

		maxTasks := agentConfig.MaxTasks
		if maxTasks <= 0 {
			maxTasks = 3
		}
		schedulerInstance.AddAgent(agentConfig.Name, maxTasks, agentConfig.Hierarchy)

		err = agent.Start()
		mistake.Unwrap(err)
	}

	schedulerInstance.Start()

	timerEngine := timer.NewTimerEngine(schedulerInstance, config.AppConfig.Timer)
	timerEngine.Start()

	api.Initialize(agentMap, mailboxBus, orchestrator, schedulerInstance, timerEngine)

	slog.Info("system initialized",
		slog.Int("agent_count", len(agentMap)),
		slog.Int("queue_length", schedulerInstance.GetQueueLength()),
	)

	sigCh := make(chan os.Signal, 1)
	signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)

	port := "8080"
	go func() {
		if err := api.RunServer(port); err != nil {
			slog.Error("HTTP server error", slog.Any("error", err))
		}
	}()

	fmt.Printf("HTTP server started on port %s\n", port)
	fmt.Println("Press Ctrl+C to shutdown...")

	<-sigCh
	fmt.Println("\nReceived shutdown signal, shutting down...")

	shutdown(timerEngine, schedulerInstance, agentMap)
}

func shutdown(timerEngine interface{}, schedulerInstance *scheduler.AutoScheduler, agentMap map[string]agents.Agent) {
	slog.Info("stopping timer engine")

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
