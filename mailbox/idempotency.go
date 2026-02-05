package mailbox

import (
	"container/list"
	"sync"
	"time"
)

// IdempotencyEntry 幂等性记录项
type IdempotencyEntry struct {
	MessageID   string
	ProcessedAt time.Time
	Result      interface{} // 上次处理结果（用于幂等响应）
}

// IdempotencyChecker 幂等性检查器
type IdempotencyChecker struct {
	mu         sync.RWMutex
	cache      map[string]*list.Element // 快速查找
	lruList    *list.List               // LRU列表
	maxSize    int                      // 最大缓存数量
	windowSize time.Duration            // 去重窗口大小
}

// NewIdempotencyChecker 创建新的幂等性检查器
func NewIdempotencyChecker(maxSize int, windowSize time.Duration) *IdempotencyChecker {
	if maxSize <= 0 {
		maxSize = 100000 // 默认10万条
	}
	if windowSize <= 0 {
		windowSize = 24 * time.Hour // 默认24小时
	}

	ic := &IdempotencyChecker{
		cache:      make(map[string]*list.Element),
		lruList:    list.New(),
		maxSize:    maxSize,
		windowSize: windowSize,
	}

	// 启动清理goroutine
	go ic.cleanup()

	return ic
}

// IsProcessed 检查消息是否已处理
func (ic *IdempotencyChecker) IsProcessed(messageID string) bool {
	ic.mu.RLock()
	defer ic.mu.RUnlock()

	elem, exists := ic.cache[messageID]
	if !exists {
		return false
	}

	entry := elem.Value.(*IdempotencyEntry)

	// 检查是否在窗口期内
	if time.Since(entry.ProcessedAt) > ic.windowSize {
		// 超出窗口，视为未处理
		return false
	}

	// 移动到LRU列表头部（最近使用）
	ic.lruList.MoveToFront(elem)

	return true
}

// MarkProcessed 标记消息为已处理
func (ic *IdempotencyChecker) MarkProcessed(messageID string, result interface{}) {
	ic.mu.Lock()
	defer ic.mu.Unlock()

	// 检查是否已存在
	if elem, exists := ic.cache[messageID]; exists {
		// 更新时间和结果
		entry := elem.Value.(*IdempotencyEntry)
		entry.ProcessedAt = time.Now()
		entry.Result = result
		ic.lruList.MoveToFront(elem)
		return
	}

	// 创建新条目
	entry := &IdempotencyEntry{
		MessageID:   messageID,
		ProcessedAt: time.Now(),
		Result:      result,
	}

	// 添加到LRU列表头部
	elem := ic.lruList.PushFront(entry)
	ic.cache[messageID] = elem

	// 检查是否超出最大容量
	if ic.lruList.Len() > ic.maxSize {
		ic.evict()
	}
}

// GetResult 获取上次处理结果
func (ic *IdempotencyChecker) GetResult(messageID string) (interface{}, bool) {
	ic.mu.RLock()
	defer ic.mu.RUnlock()

	elem, exists := ic.cache[messageID]
	if !exists {
		return nil, false
	}

	entry := elem.Value.(*IdempotencyEntry)

	// 检查是否在窗口期内
	if time.Since(entry.ProcessedAt) > ic.windowSize {
		return nil, false
	}

	return entry.Result, true
}

// evict 淘汰最旧的条目
func (ic *IdempotencyChecker) evict() {
	// 移除LRU列表尾部（最久未使用）
	elem := ic.lruList.Back()
	if elem != nil {
		entry := elem.Value.(*IdempotencyEntry)
		delete(ic.cache, entry.MessageID)
		ic.lruList.Remove(elem)
	}
}

// cleanup 定期清理过期条目
func (ic *IdempotencyChecker) cleanup() {
	ticker := time.NewTicker(5 * time.Minute)
	defer ticker.Stop()

	for range ticker.C {
		ic.removeExpired()
	}
}

// removeExpired 移除过期条目
func (ic *IdempotencyChecker) removeExpired() {
	ic.mu.Lock()
	defer ic.mu.Unlock()

	now := time.Now()
	var toRemove []*list.Element

	// 找出所有过期条目
	for elem := ic.lruList.Back(); elem != nil; elem = elem.Prev() {
		entry := elem.Value.(*IdempotencyEntry)
		if now.Sub(entry.ProcessedAt) > ic.windowSize {
			toRemove = append(toRemove, elem)
		}
	}

	// 移除过期条目
	for _, elem := range toRemove {
		entry := elem.Value.(*IdempotencyEntry)
		delete(ic.cache, entry.MessageID)
		ic.lruList.Remove(elem)
	}
}

// GetStats 获取统计信息
func (ic *IdempotencyChecker) GetStats() map[string]interface{} {
	ic.mu.RLock()
	defer ic.mu.RUnlock()

	return map[string]interface{}{
		"cache_size":  ic.lruList.Len(),
		"max_size":    ic.maxSize,
		"window_size": ic.windowSize.String(),
	}
}

// Clear 清空缓存
func (ic *IdempotencyChecker) Clear() {
	ic.mu.Lock()
	defer ic.mu.Unlock()

	ic.cache = make(map[string]*list.Element)
	ic.lruList.Init()
}
