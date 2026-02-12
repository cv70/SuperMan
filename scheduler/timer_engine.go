package scheduler

import (
	"sync"
)

type TimerEngine struct {
	mu       sync.RWMutex
	schedule []ScheduleEntry
}

type ScheduleEntry struct {
	ID       string
	Expr     string
	Callback func()
}

func NewTimerEngine() *TimerEngine {
	return &TimerEngine{
		schedule: make([]ScheduleEntry, 0),
	}
}

func (te *TimerEngine) RegisterJob(id, expr string, callback func()) error {
	te.mu.Lock()
	defer te.mu.Unlock()

	for _, job := range te.schedule {
		if job.ID == id {
			return nil
		}
	}

	te.schedule = append(te.schedule, ScheduleEntry{
		ID:       id,
		Expr:     expr,
		Callback: callback,
	})

	return nil
}

func (te *TimerEngine) UnregisterJob(id string) {
	te.mu.Lock()
	defer te.mu.Unlock()

	for i, job := range te.schedule {
		if job.ID == id {
			te.schedule = append(te.schedule[:i], te.schedule[i+1:]...)
			return
		}
	}
}

func (te *TimerEngine) Start() {
}

func (te *TimerEngine) Stop() {
	te.mu.Lock()
	defer te.mu.Unlock()
	te.schedule = nil
}
