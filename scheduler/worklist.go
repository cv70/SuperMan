package scheduler

import (
	"sync"

	"superman/types"
)

type WorkList struct {
	mu         sync.RWMutex
	tasks      map[string]*types.Task
	byPriority map[string][]string
}

func NewWorkList() *WorkList {
	return &WorkList{
		tasks:      make(map[string]*types.Task),
		byPriority: make(map[string][]string),
	}
}

func (wl *WorkList) AddTask(task *types.Task) {
	wl.mu.Lock()
	defer wl.mu.Unlock()

	wl.tasks[task.TaskID] = task

	priority := PriorityLow
	if task.Metadata != nil {
		if p, ok := task.Metadata["priority"]; ok {
			if str, ok := p.(string); ok {
				priority = str
			}
		}
	}

	wl.byPriority[priority] = append(wl.byPriority[priority], task.TaskID)
}

func (wl *WorkList) GetTask(taskID string) *types.Task {
	wl.mu.RLock()
	defer wl.mu.RUnlock()
	return wl.tasks[taskID]
}

func (wl *WorkList) GetTasksByPriority(priority string) []*types.Task {
	wl.mu.RLock()
	defer wl.mu.RUnlock()

	taskIDs := wl.byPriority[priority]
	result := make([]*types.Task, 0, len(taskIDs))
	for _, id := range taskIDs {
		if task, exists := wl.tasks[id]; exists {
			result = append(result, task)
		}
	}
	return result
}

func (wl *WorkList) RemoveTask(taskID string) {
	wl.mu.Lock()
	defer wl.mu.Unlock()

	if _, exists := wl.tasks[taskID]; !exists {
		return
	}

	delete(wl.tasks, taskID)

	for priority, taskIDs := range wl.byPriority {
		for i, id := range taskIDs {
			if id == taskID {
				wl.byPriority[priority] = append(taskIDs[:i], taskIDs[i+1:]...)
				break
			}
		}
	}
}

func (wl *WorkList) GetAllTasks() []*types.Task {
	wl.mu.RLock()
	defer wl.mu.RUnlock()

	result := make([]*types.Task, 0, len(wl.tasks))
	for _, task := range wl.tasks {
		result = append(result, task)
	}
	return result
}

func (wl *WorkList) Len() int {
	wl.mu.RLock()
	defer wl.mu.RUnlock()
	return len(wl.tasks)
}

func (wl *WorkList) LenByPriority(priority string) int {
	wl.mu.RLock()
	defer wl.mu.RUnlock()
	return len(wl.byPriority[priority])
}
