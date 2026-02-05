package main

import (
	"bufio"
	"context"
	"fmt"
	"os"
	"strings"

	"superman/agents"
	"superman/config"
	"superman/mailbox"
	"superman/types"
	"superman/workflow"

	"github.com/cv70/pkgo/mistake"
)

func main() {
	fmt.Println("SuperMan AI Multi-Agent Company System")
	fmt.Println("=======================================================")

	config.InitConfig()

	mailboxBus := mailbox.NewMailboxBus()

	orchestrator := workflow.NewOrchestrator(mailboxBus)

	fmt.Println("\n正在创建AI智能体...")

	// Create context for agent initialization
	ctx := context.Background()

	// Create all agents with error handling
	chairmanAgent, err := agents.NewChairmanAgent(ctx)
	mistake.Unwrap(err)
	
	ceoAgent, err := agents.NewCEOAgent(ctx)
	mistake.Unwrap(err)
	
	ctoAgent, err := agents.NewCTOAgent(ctx)
	mistake.Unwrap(err)

	cpoAgent, err := agents.NewCPOAgent(ctx)
	mistake.Unwrap(err)

	cmoAgent, err := agents.NewCMOAgent(ctx)
	mistake.Unwrap(err)
	
	cfoAgent, err := agents.NewCFOAgent(ctx)
	mistake.Unwrap(err)
	
	hrAgent, err := agents.NewHRAgent(ctx)
	mistake.Unwrap(err)
	
	rdAgent, err := agents.NewRDAgent(ctx)
	mistake.Unwrap(err)
	
	dataAnalystAgent, err := agents.NewDataAnalystAgent(ctx)
	mistake.Unwrap(err)
	
	customerSupportAgent, err := agents.NewCustomerSupportAgent(ctx)
	mistake.Unwrap(err)
	
	operationsAgent, err := agents.NewOperationsAgent(ctx)
	mistake.Unwrap(err)

	agentsMap := map[types.AgentRole]agents.Agent{
		types.AgentRoleChairman:        chairmanAgent,
		types.AgentRoleCEO:             ceoAgent,
		types.AgentRoleCTO:             ctoAgent,
		types.AgentRoleCPO:             cpoAgent,
		types.AgentRoleCMO:             cmoAgent,
		types.AgentRoleCFO:             cfoAgent,
		types.AgentRoleHR:              hrAgent,
		types.AgentRoleRD:              rdAgent,
		types.AgentRoleDataAnalyst:     dataAnalystAgent,
		types.AgentRoleCustomerSupport: customerSupportAgent,
		types.AgentRoleOperations:      operationsAgent,
	}

	for role, agent := range agentsMap {
		orchestrator.RegisterAgent(role, agent)

		mailbox := agent.GetMailbox()
		if err := mailboxBus.RegisterMailbox(role, mailbox); err != nil {
			fmt.Printf("  警告: %s 的mailbox注册失败: %v\n", role, err)
		}

		// 将全局状态注入到每个agent
		agent.SetGlobalState(mailboxBus.GetGlobalState())

		fmt.Printf("  已创建: %s (%s)\n", agent.GetName(), role)
	}

	fmt.Println("\n=== 系统初始化完成 ===")
	fmt.Printf("智能体总数: %d\n", len(agentsMap))

	// 获取Chairman Agent
	chairmanAgentInstance, ok := agentsMap[types.AgentRoleChairman]
	if !ok {
		fmt.Println("  警告: 未找到Chairman Agent")
	}

	// 启动交互式控制台
	fmt.Println("\n=== 启动交互式控制台 ===")
	fmt.Println("命令说明:")
	fmt.Println("  send <message> - 向Chairman发送消息")
	fmt.Println("  status         - 查看系统状态")
	fmt.Println("  exit           - 退出程序")
	fmt.Println()

	// 启动Chairman Agent
	if chairmanAgentInstance != nil {
		if err := chairmanAgentInstance.Start(); err != nil {
			fmt.Printf("  启动Chairman Agent失败: %v\n", err)
		} else {
			fmt.Println("  Chairman Agent已启动")
		}
	}

	// 读取用户输入
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

		parts := strings.Fields(input)
		if len(parts) == 0 {
			continue
		}

		command := parts[0]

		switch command {
		case "send":
			// 发送消息到Chairman
			message := strings.Join(parts[1:], " ")
			if chairmanAgentInstance != nil {
				msg, err := types.NewMessage(
					types.AgentRole("user"),
					types.AgentRoleChairman,
					types.MessageTypeStatusReport,
					map[string]any{
						"message":   message,
						"timestamp": fmt.Sprintf("%v", types.AgentRoleChairman),
					},
				)
				if err != nil {
					fmt.Printf("创建消息失败: %v\n", err)
				} else {
					chairmanAgentInstance.ReceiveMessage(msg)
					fmt.Printf("[Chairman] 消息已接收: %s\n", message)
				}
			} else {
				fmt.Println("Chairman Agent未找到")
			}

		case "status":
			// 显示系统状态
			fmt.Println("\n--- 系统状态 ---")
			for role, agent := range agentsMap {
				fmt.Printf("%s: %s (工作负载: %.2f)\n", role, agent.GetName(), agent.GetWorkload())
			}
			fmt.Println()

		case "exit":
			fmt.Println("正在退出...")
			if chairmanAgentInstance != nil {
				chairmanAgentInstance.Stop()
			}
			os.Exit(0)

		default:
			fmt.Printf("未知命令: %s\n", command)
			fmt.Println("可用命令: send, status, exit")
		}
	}
}
