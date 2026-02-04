#!/usr/bin/env python
"""SuperMan AI 多智能体公司 - 主入口点

使用方式:
    python main.py start                     - 启动公司
    python main.py status                    - 显示公司状态
    python main.py report                    - 从所有智能体生成报告
    python main.py run-test                  - 运行5步模拟
    python main.py execute-task <task_json>  - 执行任务
"""

import argparse
import json
import asyncio
import sys
import os


def ensure_openai_api_key():
    """检查OpenAI API密钥是否设置。"""
    if not os.getenv("OPENAI_API_KEY"):
        print("错误：未设置OPENAI_API_KEY环境变量。")
        print("请设置您的OpenAI API密钥：")
        print("  export OPENAI_API_KEY=sk-...")
        print("")
        print("您可以在以下位置创建API密钥：https://platform.openai.com/api-keys")
        sys.exit(1)


async def cmd_start():
    """启动公司编排器。"""
    from src.workflow import CompanyOrchestrator, create_empty_state

    ensure_openai_api_key()

    print("正在初始化SuperMan AI公司...")
    orchestrator = CompanyOrchestrator()
    state = create_empty_state()

    print("已初始化所有10个智能体：")
    for role in orchestrator.agents:
        print(f"  - {role.value}: {len(orchestrator.agents[role].capabilities)} 个能力")

    print("")
    print("公司启动成功！")
    print("使用 'status' 查看智能体状态")
    print("使用 'report' 生成报告")
    print("使用 'run-test' 模拟公司运营")

    return orchestrator


async def cmd_status(orchestrator):
    """显示公司状态。"""
    status = await orchestrator.get_status()
    print(f"公司状态 ({status['timestamp']}):")
    print(f"  活跃智能体: {status['agents_active']}")
    print(f"  待处理任务: {status['pending_tasks']}")
    print(f"  进行中任务: {status['in_progress_tasks']}")
    print(f"  已完成任务: {status['completed_tasks']}")


async def cmd_report(orchestrator):
    """从所有智能体生成报告。"""
    report = await orchestrator.generate_report()

    print("=" * 60)
    print("SUPERMAN AI 公司 - 报告")
    print("=" * 60)

    for agent, data in report.get("reports", {}).items():
        status = "OK" if "data" in data else "ERROR"
        print(f"\n[{agent.upper()}] {status}")
        if "data" in data:
            print(f"  类型: {data.get('report_type', '未知')}")
            print(f"  时间戳: {data.get('timestamp', '未知')}")

    print("\n" + "=" * 60)


async def cmd_run_test(orchestrator):
    """运行5步模拟。"""
    print("正在运行5步公司模拟...")
    state = await orchestrator.run_simulation(steps=5)

    print("\n模拟完成！")
    print(f"  处理的消息总数: {len(state.get('messages', []))}")
    print(f"  当前时间: {state.get('current_time', 'N/A')}")

    return state


async def cmd_execute_task(orchestrator, task_json):
    """执行任务。"""
    try:
        task_data = json.loads(task_json)
    except json.JSONDecodeError as e:
        print(f"错误：无效的JSON - {e}")
        sys.exit(1)

    result = await orchestrator.execute_task(task_data)

    if result["status"] == "success":
        print(f"任务 '{task_data.get('title', '未知')}' 执行成功")
        print(f"  任务ID: {result['task_id']}")
        print(f"  结果: {result['result']}")
    else:
        print(f"任务失败: {result.get('error', '未知错误')}")


async def main():
    """主入口点。"""
    parser = argparse.ArgumentParser(description="SuperMan AI公司")
    parser.add_argument(
        "command",
        choices=["start", "status", "report", "run-test", "execute-task"],
        help="要运行的命令",
    )
    parser.add_argument("args", nargs="*", help="附加参数")

    args = parser.parse_args()

    if args.command == "start":
        orchestrator = await cmd_start()

        print("\n交互模式 (Ctrl+C 退出)...")
        print("命令: status, report, run-test")

        while True:
            try:
                cmd = input("\n> ").strip().lower()
                if cmd == "status":
                    await cmd_status(orchestrator)
                elif cmd == "report":
                    await cmd_report(orchestrator)
                elif cmd == "run-test":
                    await cmd_run_test(orchestrator)
                elif cmd == "exit" or cmd == "quit":
                    break
                else:
                    print("未知命令。试试: status, report, run-test")
            except KeyboardInterrupt:
                break
            except EOFError:
                break

    else:
        orchestrator = await cmd_start()

        if args.command == "status":
            await cmd_status(orchestrator)
        elif args.command == "report":
            await cmd_report(orchestrator)
        elif args.command == "run-test":
            await cmd_run_test(orchestrator)
        elif args.command == "execute-task":
            if not args.args:
                print("错误：execute-task 需要任务JSON作为参数")
                sys.exit(1)
            await cmd_execute_task(orchestrator, args.args[0])


if __name__ == "__main__":
    asyncio.run(main())
