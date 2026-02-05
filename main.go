package main

import (
	"context"
	"fmt"
	"os"

	"google.golang.org/adk/cmd/launcher/full"

	"superman/agents"
	"superman/config"
	"superman/mailbox"
	"superman/utils"
	"superman/workflow"
)

func main() {
	fmt.Println("SuperMan AI Multi-Agent Company System using Google ADK")
	fmt.Println("=======================================================")

	config.InitConfig()

	ctx := context.Background()

	companyState := agents.CreateEmptyState()
	stateManager := workflow.NewStateManager(companyState)
	router := workflow.NewMessageRouter()

	// 创建Mailbox管理器（禁用DLQ，因为需要SQLite/CGO）
	mailboxConfig := mailbox.DefaultMailboxManagerConfig()
	mailboxConfig.EnableDLQ = false // 禁用死信队列，避免CGO依赖
	mailboxManager, err := mailbox.NewMailboxManager(mailboxConfig)
	if err != nil {
		fmt.Printf("Failed to create mailbox manager: %v\n", err)
		os.Exit(1)
	}

	orchestrator := workflow.NewOrchestrator(stateManager, router, mailboxManager)

	fmt.Println("\n正在创建AI智能体...")

	agentsMap := map[agents.AgentRole]agents.Agent{
		agents.AgentRoleCEO:             agents.NewCEOAgent(),
		agents.AgentRoleCTO:             agents.NewCTOAgent(),
		agents.AgentRoleCPO:             agents.NewCPOAgent(),
		agents.AgentRoleCMO:             agents.NewCMOAgent(),
		agents.AgentRoleCFO:             agents.NewCFOAgent(),
		agents.AgentRoleHR:              agents.NewHRAgent(),
		agents.AgentRoleRD:              agents.NewRDAgent(),
		agents.AgentRoleDataAnalyst:     agents.NewDataAnalystAgent(),
		agents.AgentRoleCustomerSupport: agents.NewCustomerSupportAgent(),
		agents.AgentRoleOperations:      agents.NewOperationsAgent(),
	}

	for role, agent := range agentsMap {
		stateManager.CreateAgentState(role)
		orchestrator.RegisterAgent(role, agent)

		// 为每个agent注册mailbox handler
		handler := createAgentMessageHandler(agent, stateManager)
		if err := mailboxManager.RegisterMailbox(role, handler); err != nil {
			fmt.Printf("  警告: %s 的mailbox注册失败: %v\n", role, err)
		}

		fmt.Printf("  已创建: %s (%s)\n", agents.GetAgentName(agent), role)
	}

	// 启动orchestrator（包含mailbox系统）
	fmt.Println("\n启动Mailbox系统...")
	if err := orchestrator.Start(); err != nil {
		fmt.Printf("Failed to start orchestrator: %v\n", err)
		os.Exit(1)
	}
	fmt.Println("Mailbox系统启动成功")

	fmt.Println("\n=== 系统初始化完成 ===")
	fmt.Printf("智能体总数: %d\n", len(agentsMap))
	fmt.Printf("当前时间: %s\n", utils.FormatTimestamp(stateManager.GetTimestamp()))

	healthReport := stateManager.GetHealthReport()

	fmt.Println("\n=== 系统健康报告 ===")
	agentsStatus := healthReport["agents"].(map[string]workflow.AgentStatus)
	fmt.Printf("智能体总数: %d\n", len(agentsStatus))
	fmt.Printf("任务总数: %d\n", healthReport["total_tasks"].(int))
	fmt.Printf("消息总数: %d\n", healthReport["total_messages"].(int))
	fmt.Printf("\n智能体状态:\n")
	for role, status := range agentsStatus {
		fmt.Printf("  %s: %d 任务, %.1f 负载, 完成: %d\n",
			role, status.TaskCount, status.Workload, status.CompletedCount)
	}

	fmt.Println("\n=== 启动 ADK Launcher ===")
	fmt.Println("访问 http://localhost:8080 查看交互界面")

	launcher := full.NewLauncher()
	launcher.Execute(ctx, nil, os.Args[1:])
}

// createAgentMessageHandler 创建Agent的mailbox消息处理器
func createAgentMessageHandler(agent agents.Agent, stateManager workflow.StateManager) mailbox.MessageHandler {
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

		// 调用ProcessMessage
		err := agent.ProcessMessage(agentMsg)

		return err
	}
}

// convertMailboxContent 转换mailbox content格式
func convertMailboxContent(content map[string]interface{}) map[string]any {
	result := make(map[string]any)
	for k, v := range content {
		result[k] = v
	}
	return result
}
