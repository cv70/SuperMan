package scheduler

import (
	"context"
	"time"

	"superman/agents"
	"superman/types"
)

type TaskGenerator interface {
	GenerateTasks(ctx context.Context, agent agents.Agent) ([]*types.Task, error)
}

type DefaultTaskGenerator struct {
	roleTemplates map[string][]string
}

func NewDefaultTaskGenerator() *DefaultTaskGenerator {
	return &DefaultTaskGenerator{
		roleTemplates: map[string][]string{
			"ceo":              {"审核战略目标", "召开管理层会议", "审批季度报告"},
			"cto":              {"评估技术架构", "审核代码质量", "监控系统健康"},
			"cpo":              {"规划产品路线图", "分析用户反馈", "定义功能优先级"},
			"cmo":              {"制定市场策略", "监控品牌声量", "评估营销活动"},
			"cfo":              {"审核财务报表", "监控现金流", "分析成本效益"},
			"hr":               {"评估团队绩效", "识别协作瓶颈", "优化资源配置"},
			"rd":               {"修复高优Bug", "优化性能瓶颈", "更新技术文档"},
			"customer_support": {"响应用户咨询", "收集反馈", "分类问题"},
			"data_analyst":     {"生成数据报表", "分析异常模式", "构建预测模型"},
			"operations":       {"监控系统健康", "优化工作流", "处理异常"},
			"chairman":         {"监督公司运营", "审批重大决策", "评估高管绩效"},
		},
	}
}

func (g *DefaultTaskGenerator) GenerateTasks(ctx context.Context, agent agents.Agent) ([]*types.Task, error) {
	roleName := agent.GetName()

	tasks := make([]*types.Task, 0)

	templates := g.roleTemplates[roleName]
	for _, template := range templates {
		task := &types.Task{
			TaskID:      GenerateTaskID(),
			Title:       template,
			Description: template,
			AssignedTo:  roleName,
			AssignedBy:  roleName,
			Status:      "pending",
			Metadata: map[string]any{
				"source":       "auto",
				"priority":     PriorityMedium,
				"generated_by": roleName,
				"generated_at": time.Now().Unix(),
			},
			CreatedAt: time.Now(),
			UpdatedAt: time.Now(),
		}
		tasks = append(tasks, task)
	}

	return tasks, nil
}

func GenerateTaskID() string {
	return "auto_" + time.Now().Format("20060102_150405")
}
