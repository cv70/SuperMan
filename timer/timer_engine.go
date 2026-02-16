package timer

import (
	"log/slog"
	"sync"
	"time"

	"superman/config"
	"superman/ds"
	"superman/scheduler"
)

// TimerEngine 定时任务引擎
type TimerEngine struct {
	mu        sync.RWMutex
	jobs      []*TimerJob
	scheduler *scheduler.AutoScheduler
	stopCh    chan struct{}
	wg        sync.WaitGroup
}

// TimerJob 运行时定时任务
type TimerJob struct {
	Name        string
	Interval    time.Duration
	TargetAgent string
	Title       string
	Description string
	Priority    string
	LastRun     time.Time
	Enabled     bool
}

// NewTimerEngine 创建定时任务引擎
func NewTimerEngine(s *scheduler.AutoScheduler, timerConfig *config.TimerConfig) *TimerEngine {
	te := &TimerEngine{
		jobs:      make([]*TimerJob, 0),
		scheduler: s,
		stopCh:    make(chan struct{}),
	}

	if timerConfig != nil && timerConfig.Enabled {
		for _, jobConfig := range timerConfig.Jobs {
			interval, err := time.ParseDuration(jobConfig.Interval)
			if err != nil {
				slog.Error("invalid timer interval, skipping job",
					slog.String("job", jobConfig.Name),
					slog.String("interval", jobConfig.Interval),
					slog.Any("error", err),
				)
				continue
			}

			priority := jobConfig.Task.Priority
			if priority == "" {
				priority = scheduler.PriorityMedium
			}

			te.jobs = append(te.jobs, &TimerJob{
				Name:        jobConfig.Name,
				Interval:    interval,
				TargetAgent: jobConfig.TargetAgent,
				Title:       jobConfig.Task.Title,
				Description: jobConfig.Task.Description,
				Priority:    priority,
				LastRun:     time.Time{}, // 从未运行
				Enabled:     true,
			})

			slog.Info("timer job registered",
				slog.String("name", jobConfig.Name),
				slog.String("interval", jobConfig.Interval),
				slog.String("target", jobConfig.TargetAgent),
			)
		}
	}

	return te
}

// Start 启动定时引擎
func (te *TimerEngine) Start() {
	if len(te.jobs) == 0 {
		slog.Info("timer engine: no jobs configured, skipping start")
		return
	}
	te.wg.Add(1)
	go te.tickLoop()
	slog.Info("timer engine started", slog.Int("job_count", len(te.jobs)))
}

// Stop 停止定时引擎
func (te *TimerEngine) Stop() {
	close(te.stopCh)
	te.wg.Wait()
	slog.Info("timer engine stopped")
}

// tickLoop 定时检查循环
func (te *TimerEngine) tickLoop() {
	defer te.wg.Done()
	ticker := time.NewTicker(30 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-te.stopCh:
			return
		case now := <-ticker.C:
			te.checkAndFire(now)
		}
	}
}

// checkAndFire 检查并触发到期的任务
func (te *TimerEngine) checkAndFire(now time.Time) {
	te.mu.Lock()
	defer te.mu.Unlock()

	for _, job := range te.jobs {
		if !job.Enabled {
			continue
		}

		// 首次运行或已超过间隔
		if job.LastRun.IsZero() || now.Sub(job.LastRun) >= job.Interval {
			te.fireJob(job, now)
			job.LastRun = now
		}
	}
}

// fireJob 触发一个定时任务
func (te *TimerEngine) fireJob(job *TimerJob, now time.Time) {
	taskID := ds.GenerateTaskID()
	task := ds.NewTask(
		taskID,
		job.Title,
		job.Description,
		job.TargetAgent,
		"timer_engine",
		ds.TaskStatusPending,
		ds.TaskPriority(job.Priority),
	)
	task.Metadata["source"] = "timer"
	task.Metadata["timer_job"] = job.Name
	task.Metadata["fired_at"] = now.Format(time.RFC3339)

	te.scheduler.AddTask(task, job.Priority)

	slog.Info("timer job fired",
		slog.String("job", job.Name),
		slog.String("task_id", taskID),
		slog.String("target", job.TargetAgent),
	)
}

// AddJob 动态添加定时任务
func (te *TimerEngine) AddJob(job *TimerJob) {
	te.mu.Lock()
	defer te.mu.Unlock()
	te.jobs = append(te.jobs, job)
}

// GetJobs 获取所有定时任务
func (te *TimerEngine) GetJobs() []*TimerJob {
	te.mu.RLock()
	defer te.mu.RUnlock()
	result := make([]*TimerJob, len(te.jobs))
	copy(result, te.jobs)
	return result
}
