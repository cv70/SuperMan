package main

import (
	"bufio"
	"context"
	"fmt"
	"log/slog"
	"os"
	"strings"

	"superman/agents"
	"superman/config"
	"superman/ds"
	"superman/infra"
	"superman/mailbox"
	"superman/scheduler"
	"superman/workflow"

	"github.com/cv70/pkgo/mistake"
)

func main() {
	fmt.Println("SuperMan AI Multi-Agent Company System")
	fmt.Println("=======================================================")

	err := config.InitConfig()
	mistake.Unwrap(err)

	ctx := context.Background()

	r, err := infra.NewRegistry(ctx, &config.AppConfig)
	mistake.Unwrap(err)

	mailboxBus := mailbox.NewMailboxBus()

	orchestrator := workflow.NewOrchestrator(mailboxBus)

	schedulerInstance := scheduler.NewAutoScheduler()

	fmt.Println("\n正在创建AI智能体...")

	agentMap := make(map[string]agents.Agent)
	for _, agentConfig := range config.AppConfig.Agents {
		agent, err := agents.NewBaseAgent(ctx, r.LLM[agentConfig.Model], agentConfig, config.AppConfig.Agents...)
		mistake.Unwrap(err)
		orchestrator.RegisterAgent(agent)

		mailbox := agent.GetMailbox()
		mailboxBus.RegisterMailbox(agent.GetName(), mailbox)
		mistake.Unwrap(err)

		agent.SetGlobalState(mailboxBus.GetGlobalState())
		agentMap[agent.GetName()] = agent

		err = agent.Start()
		mistake.Unwrap(err)

		schedulerInstance.AddAgent(agentConfig.Name, 3)

		// 调用Agent的GenerateTasks方法生成任务
		tasks, err := agent.GenerateTasks(ctx)
		if err != nil {
			slog.Error("failed to generate tasks", slog.String("agent", agentConfig.Name), slog.Any("error", err))
		} else {
			for _, task := range tasks {
				schedulerInstance.AddTask(task, scheduler.PriorityMedium)
			}
		}
	}

	fmt.Println("\n=== 系统初始化完成 ===")
	fmt.Printf("智能体总数: %d\n", len(agentMap))
	fmt.Printf("任务队列长度: %d\n", schedulerInstance.GetQueueLength())

	fmt.Println("\n=== 启动交互式控制台 ===")
	fmt.Println("命令说明:")
	fmt.Println("  send <message> - 向Chairman发送消息")
	fmt.Println("  status         - 查看系统状态")
	fmt.Println("  exit           - 退出程序")
	fmt.Println()

	reader := bufio.NewReader(os.Stdin)
	for {
		fmt.Print("> ")
		input, err := reader.ReadString('\n')
		if err != nil {
			fmt.Printf("读取输入错误: %v\n", err)
			continue
		}

		input = strings.TrimSpace(input)
		if input == "" {
			continue
		}

		processInput(agentMap, mailboxBus, schedulerInstance, input)
	}
}

func processInput(agentMap map[string]agents.Agent, mailboxBus *mailbox.MailboxBus, schedulerInstance *scheduler.AutoScheduler, input string) {
	parts := strings.Fields(input)
	if len(parts) == 0 {
		return
	}
	defer fmt.Println()

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
			slog.Error("failed to create message", slog.Any("e", err))
			return
		}
		err = mailboxBus.Send(msg)
		if err != nil {
			slog.Error("failed to send message", slog.Any("e", err))
		}
	case "status":
		fmt.Println("\n--- 系统状态 ---")
		fmt.Printf("调度器任务队列长度: %d\n", schedulerInstance.GetQueueLength())
		for _, priority := range []string{scheduler.PriorityCritical, scheduler.PriorityHigh, scheduler.PriorityMedium, scheduler.PriorityLow} {
			fmt.Printf("  [%s] 长度: %d\n", priority, schedulerInstance.GetQueueLengthByPriority(priority))
		}
		for name, agent := range agentMap {
			fmt.Printf("%s (工作负载: %.2f)\n", name, agent.GetWorkload())
		}
	case "exit":
		os.Exit(0)
	default:
		fmt.Printf("未知命令: %s\n", command)
		fmt.Println("可用命令: send, status, exit")
	}
}
