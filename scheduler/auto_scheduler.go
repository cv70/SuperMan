package scheduler

import (
	"log/slog"
	"sort"
	"sync"
	"time"

	"superman/ds"
	"superman/state"
)

// TaskDispatcher 任务分发接口（由 Orchestrator 实现）
type TaskDispatcher interface {
	RunTask(task *ds.Task) error
}

// AgentLoad Agent 负载跟踪
type AgentLoad struct {
	Name        string
	MaxTasks    int
	CurrentLoad int
	Hierarchy   int
}

type AutoScheduler struct {
	mu           sync.RWMutex
	taskQueues   map[string]*TaskQueue
	agentLoads   map[string]*AgentLoad
	dispatcher   TaskDispatcher
	globalState  *state.GlobalState
	tickInterval time.Duration
	stopCh       chan struct{}
	wg           sync.WaitGroup
}

func NewAutoScheduler(dispatcher TaskDispatcher, globalState *state.GlobalState, tickInterval time.Duration) *AutoScheduler {
	if tickInterval <= 0 {
		tickInterval = 5 * time.Second
	}
	return &AutoScheduler{
		taskQueues: map[string]*TaskQueue{
			PriorityCritical: NewTaskQueue(),
			PriorityHigh:     NewTaskQueue(),
			PriorityMedium:   NewTaskQueue(),
			PriorityLow:      NewTaskQueue(),
		},
		agentLoads:   make(map[string]*AgentLoad),
		dispatcher:   dispatcher,
		globalState:  globalState,
		tickInterval: tickInterval,
		stopCh:       make(chan struct{}),
	}
}

// Start 启动调度循环
func (s *AutoScheduler) Start() {
	s.wg.Add(1)
	go s.scheduleLoop()
	slog.Info("auto scheduler started", slog.Duration("tick_interval", s.tickInterval))
}

// Stop 停止调度循环
func (s *AutoScheduler) Stop() {
	close(s.stopCh)
	s.wg.Wait()
	slog.Info("auto scheduler stopped")
}

// AddTask 添加任务到优先级队列
func (s *AutoScheduler) AddTask(task *ds.Task, priority string) {
	queue := s.taskQueues[priority]
	if queue == nil {
		queue = NewTaskQueue()
		s.taskQueues[priority] = queue
	}
	queue.Enqueue(task)

	// 同时注册到 GlobalState
	if s.globalState != nil {
		s.globalState.AddTask(task)
	}

	slog.Debug("task added to scheduler",
		slog.String("task_id", task.ID),
		slog.String("title", task.Title),
		slog.String("priority", priority),
	)
}

// AddAgent 注册 Agent 到调度器
func (s *AutoScheduler) AddAgent(agentName string, maxTasks int, hierarchy int) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.agentLoads[agentName] = &AgentLoad{
		Name:        agentName,
		MaxTasks:    maxTasks,
		CurrentLoad: 0,
		Hierarchy:   hierarchy,
	}
}

// OnTaskComplete 任务完成回调，减少 Agent 负载计数
func (s *AutoScheduler) OnTaskComplete(taskID, agentName string, success bool) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if load, exists := s.agentLoads[agentName]; exists {
		if load.CurrentLoad > 0 {
			load.CurrentLoad--
		}
	}
	status := "completed"
	if !success {
		status = "failed"
	}
	slog.Info("task completed",
		slog.String("task_id", taskID),
		slog.String("agent", agentName),
		slog.String("status", status),
	)
}

// GetQueueLength 获取所有队列总长度
func (s *AutoScheduler) GetQueueLength() int {
	total := 0
	for _, queue := range s.taskQueues {
		total += queue.Len()
	}
	return total
}

// GetQueueLengthByPriority 获取指定优先级队列长度
func (s *AutoScheduler) GetQueueLengthByPriority(priority string) int {
	queue := s.taskQueues[priority]
	if queue != nil {
		return queue.Len()
	}
	return 0
}

// scheduleLoop 调度主循环
func (s *AutoScheduler) scheduleLoop() {
	defer s.wg.Done()
	ticker := time.NewTicker(s.tickInterval)
	defer ticker.Stop()

	for {
		select {
		case <-s.stopCh:
			return
		case <-ticker.C:
			s.dispatchTasks()
		}
	}
}

// dispatchTasks 从队列中取出任务并分配给空闲 Agent
func (s *AutoScheduler) dispatchTasks() {
	for {
		task := s.getNextReady()
		if task == nil {
			break
		}

		agent := s.findBestAgent(task)
		if agent == nil {
			// 所有 Agent 满载，任务回到队列
			s.requeueTask(task)
			break
		}

		// 设置任务分配信息
		task.AssignedTo = agent.Name
		task.Status = ds.TaskStatusAssigned

		// 通过 Dispatcher 分发任务
		err := s.dispatcher.RunTask(task)
		if err != nil {
			slog.Error("failed to dispatch task",
				slog.String("task_id", task.ID),
				slog.String("agent", agent.Name),
				slog.Any("error", err),
			)
			s.requeueTask(task)
			continue
		}

		// 更新 Agent 负载
		s.mu.Lock()
		agent.CurrentLoad++
		s.mu.Unlock()

		slog.Info("task dispatched",
			slog.String("task_id", task.ID),
			slog.String("title", task.Title),
			slog.String("agent", agent.Name),
		)
	}
}

// getNextReady 从优先级队列取出依赖已满足的任务
func (s *AutoScheduler) getNextReady() *ds.Task {
	priorities := []string{PriorityCritical, PriorityHigh, PriorityMedium, PriorityLow}
	for _, priority := range priorities {
		queue := s.taskQueues[priority]
		if queue == nil || queue.IsEmpty() {
			continue
		}
		task := queue.DequeueIf(func(t *ds.Task) bool {
			return s.areDependenciesMet(t)
		})
		if task != nil {
			return task
		}
	}
	return nil
}

// areDependenciesMet 检查任务依赖是否已满足
func (s *AutoScheduler) areDependenciesMet(task *ds.Task) bool {
	if len(task.Dependencies) == 0 {
		return true
	}
	if s.globalState == nil {
		return true
	}
	for _, depID := range task.Dependencies {
		depTask := s.globalState.GetTask(depID)
		if depTask == nil || depTask.Status != ds.TaskStatusCompleted {
			return false
		}
	}
	return true
}

// findBestAgent 选择最佳 Agent 执行任务
func (s *AutoScheduler) findBestAgent(task *ds.Task) *AgentLoad {
	s.mu.RLock()
	defer s.mu.RUnlock()

	// 策略 1：如果任务已指定 AssignedTo，优先使用
	if task.AssignedTo != "" {
		if agent, ok := s.agentLoads[task.AssignedTo]; ok {
			if agent.CurrentLoad < agent.MaxTasks {
				return agent
			}
		}
		// 指定的 Agent 满载，返回 nil 等待
		return nil
	}

	// 策略 2：按负载率排序，选最空闲的 Agent
	var candidates []*AgentLoad
	for _, agent := range s.agentLoads {
		if agent.CurrentLoad < agent.MaxTasks {
			candidates = append(candidates, agent)
		}
	}

	if len(candidates) == 0 {
		return nil
	}

	sort.Slice(candidates, func(i, j int) bool {
		loadI := float64(candidates[i].CurrentLoad) / float64(candidates[i].MaxTasks)
		loadJ := float64(candidates[j].CurrentLoad) / float64(candidates[j].MaxTasks)
		if loadI != loadJ {
			return loadI < loadJ
		}
		// 同负载时，低层级的 Agent 优先（层级数值大 = 层级低 = 一线执行者）
		return candidates[i].Hierarchy > candidates[j].Hierarchy
	})

	return candidates[0]
}

// requeueTask 将任务放回队列
func (s *AutoScheduler) requeueTask(task *ds.Task) {
	priority := string(task.Priority)
	switch priority {
	case "critical":
		priority = PriorityCritical
	case "high":
		priority = PriorityHigh
	case "medium":
		priority = PriorityMedium
	case "low":
		priority = PriorityLow
	default:
		priority = PriorityMedium
	}
	queue := s.taskQueues[priority]
	if queue != nil {
		queue.Enqueue(task)
	}
}
