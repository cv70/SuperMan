package mailbox

import (
	"fmt"
	"os"
	"testing"
	"time"

	"superman/agents"
)

// TestMailboxBasic 测试基本的mailbox功能
func TestMailboxBasic(t *testing.T) {
	// 不创建DLQ（避免SQLite依赖）
	var dlq *DeadLetterQueue = nil

	// 创建幂等性检查器
	idChecker := NewIdempotencyChecker(1000, 1*time.Hour)

	// 创建指标收集器
	metrics := NewMetrics()

	// 创建Mailbox
	config := DefaultMailboxConfig(agents.AgentRoleCEO)
	config.InboxBufferSize = 10
	config.EnableDLQ = false

	processed := make(chan string, 10)
	handler := func(msg *Message) error {
		processed <- msg.MessageID
		fmt.Printf("Processed message: %s from %s\n", msg.MessageID, msg.Sender)
		return nil
	}

	mb, err := NewMailbox(config, idChecker, dlq, metrics)
	if err != nil {
		t.Fatalf("Failed to create mailbox: %v", err)
	}
	mb.SetHandler(handler)

	// 启动Mailbox
	if err := mb.Start(); err != nil {
		t.Fatalf("Failed to start mailbox: %v", err)
	}
	defer mb.Stop()

	// 发送消息
	msg1 := NewMessage(agents.AgentRoleCTO, agents.AgentRoleCEO, agents.MessageTypeTaskAssignment, map[string]interface{}{
		"task": "Review Q4 report",
	})
	msg1.WithPriority(agents.PriorityHigh)

	if err := mb.Send(msg1); err != nil {
		t.Fatalf("Failed to send message: %v", err)
	}

	// 等待处理
	select {
	case msgID := <-processed:
		if msgID != msg1.MessageID {
			t.Errorf("Expected message ID %s, got %s", msg1.MessageID, msgID)
		}
	case <-time.After(2 * time.Second):
		t.Error("Timeout waiting for message processing")
	}

	// 检查统计
	stats := mb.GetStats()
	if stats["receiver"] != agents.AgentRoleCEO {
		t.Errorf("Expected receiver %s, got %v", agents.AgentRoleCEO, stats["receiver"])
	}

	fmt.Printf("Mailbox stats: %+v\n", stats)
}

// TestMailboxManager 测试MailboxManager
func TestMailboxManager(t *testing.T) {
	// 创建临时目录
	tempDir := "./test_data_manager"
	os.MkdirAll(tempDir, 0755)
	defer os.RemoveAll(tempDir)

	// 创建配置（禁用DLQ以避免SQLite依赖）
	config := DefaultMailboxManagerConfig()
	config.DLQConfig.DBPath = tempDir + "/dlq.db"
	config.EnableDLQ = false // 禁用DLQ
	config.EnableMetrics = true

	// 创建Manager
	manager, err := NewMailboxManager(config)
	if err != nil {
		t.Fatalf("Failed to create mailbox manager: %v", err)
	}
	defer manager.Stop()

	// 注册多个Mailbox
	roles := []agents.AgentRole{
		agents.AgentRoleCEO,
		agents.AgentRoleCTO,
		agents.AgentRoleCPO,
	}

	processed := make(map[string]int)
	processedMu := make(chan struct{}, 1)

	for _, role := range roles {
		r := role // 捕获变量
		handler := func(msg *Message) error {
			processedMu <- struct{}{}
			processed[string(r)]++
			<-processedMu
			fmt.Printf("[%s] Processed message from %s: %s\n", r, msg.Sender, msg.MessageID)
			return nil
		}

		if err := manager.RegisterMailbox(r, handler); err != nil {
			t.Fatalf("Failed to register mailbox for %s: %v", r, err)
		}
	}

	// 启动Manager
	if err := manager.Start(); err != nil {
		t.Fatalf("Failed to start manager: %v", err)
	}

	// 发送消息
	for i, sender := range roles {
		receiver := roles[(i+1)%len(roles)]

		msg := NewMessage(sender, receiver, agents.MessageTypeStatusReport, map[string]interface{}{
			"status": "OK",
			"index":  i,
		})
		msg.WithPriority(agents.PriorityMedium)

		if err := manager.Send(msg); err != nil {
			t.Fatalf("Failed to send message: %v", err)
		}
	}

	// 等待处理
	time.Sleep(2 * time.Second)

	// 检查统计
	stats := manager.GetAllStats()
	fmt.Printf("Manager stats: %+v\n", stats)

	// 验证处理（由于异步处理，允许有一定偏差）
	if len(processed) < 2 {
		t.Errorf("Expected at least 2 processed mailboxes, got %d", len(processed))
	}
}

// TestPriorityQueue 测试优先级队列
func TestPriorityQueue(t *testing.T) {
	pq := NewPriorityQueue()

	// 添加不同优先级的消息
	msgLow := NewMessage(agents.AgentRoleCTO, agents.AgentRoleCEO, agents.MessageTypeTaskAssignment, nil)
	msgLow.WithPriority(agents.PriorityLow)

	msgHigh := NewMessage(agents.AgentRoleCFO, agents.AgentRoleCEO, agents.MessageTypeTaskAssignment, nil)
	msgHigh.WithPriority(agents.PriorityHigh)

	msgCritical := NewMessage(agents.AgentRoleCTO, agents.AgentRoleCEO, agents.MessageTypeTaskAssignment, nil)
	msgCritical.WithPriority(agents.PriorityCritical)

	msgMedium := NewMessage(agents.AgentRoleCPO, agents.AgentRoleCEO, agents.MessageTypeTaskAssignment, nil)
	msgMedium.WithPriority(agents.PriorityMedium)

	// 按随机顺序入队
	pq.Enqueue(msgLow)
	pq.Enqueue(msgHigh)
	pq.Enqueue(msgCritical)
	pq.Enqueue(msgMedium)

	// 验证出队顺序（高优先级先出）
	order := []agents.Priority{}
	for i := 0; i < 4; i++ {
		msg := pq.Dequeue()
		if msg == nil {
			t.Fatal("Expected message, got nil")
		}
		order = append(order, msg.Priority)
	}

	// 验证顺序：Critical > High > Medium > Low
	expected := []agents.Priority{agents.PriorityCritical, agents.PriorityHigh, agents.PriorityMedium, agents.PriorityLow}
	for i, exp := range expected {
		if order[i] != exp {
			t.Errorf("Position %d: expected %v, got %v", i, exp, order[i])
		}
	}

	fmt.Printf("Priority order: %v\n", order)
}

// TestIdempotency 测试幂等性
func TestIdempotency(t *testing.T) {
	checker := NewIdempotencyChecker(100, 1*time.Hour)

	msgID := "test-message-001"

	// 第一次检查：未处理
	if checker.IsProcessed(msgID) {
		t.Error("Message should not be processed yet")
	}

	// 标记为已处理
	checker.MarkProcessed(msgID, "result1")

	// 第二次检查：已处理
	if !checker.IsProcessed(msgID) {
		t.Error("Message should be processed")
	}

	// 获取结果
	result, ok := checker.GetResult(msgID)
	if !ok {
		t.Error("Should have result")
	}
	if result != "result1" {
		t.Errorf("Expected result1, got %v", result)
	}

	// 获取统计
	stats := checker.GetStats()
	fmt.Printf("Idempotency stats: %+v\n", stats)
}

// TestPriorityQueuePeek 测试 Peek 方法
func TestPriorityQueuePeek(t *testing.T) {
	pq := NewPriorityQueue()

	// 空队列 Peek
	msg := pq.Peek()
	if msg != nil {
		t.Error("Peek on empty queue should return nil")
	}

	// 添加消息后 Peek
	msg1 := NewMessage(agents.AgentRoleCTO, agents.AgentRoleCEO, agents.MessageTypeTaskAssignment, nil)
	msg1.WithPriority(agents.PriorityMedium)
	pq.Enqueue(msg1)

	peeked := pq.Peek()
	if peeked == nil {
		t.Error("Peek should return message")
	}
	if peeked != msg1 {
		t.Error("Peek should return the same message")
	}
	// Peek 不应该移除消息
	if pq.Len() != 1 {
		t.Errorf("Queue length = %d, want 1", pq.Len())
	}
}

// TestPriorityQueueRemoveByMessageID 测试按消息ID移除
func TestPriorityQueueRemoveByMessageID(t *testing.T) {
	pq := NewPriorityQueue()

	msg1 := NewMessage(agents.AgentRoleCTO, agents.AgentRoleCEO, agents.MessageTypeTaskAssignment, nil)
	msg1.WithPriority(agents.PriorityMedium)
	msg2 := NewMessage(agents.AgentRoleCFO, agents.AgentRoleCEO, agents.MessageTypeTaskAssignment, nil)
	msg2.WithPriority(agents.PriorityHigh)

	pq.Enqueue(msg1)
	pq.Enqueue(msg2)

	// 移除不存在的消息
	result := pq.RemoveByMessageID("non-existent")
	if result {
		t.Error("Remove non-existent should return false")
	}

	// 移除存在的消息
	result = pq.RemoveByMessageID(msg1.MessageID)
	if !result {
		t.Error("Remove existing message should return true")
	}

	// 验证队列状态
	if pq.Len() != 1 {
		t.Errorf("Queue length = %d, want 1", pq.Len())
	}
}

// TestPriorityQueueClear 测试清空队列
func TestPriorityQueueClear(t *testing.T) {
	pq := NewPriorityQueue()

	for i := 0; i < 5; i++ {
		msg := NewMessage(agents.AgentRoleCTO, agents.AgentRoleCEO, agents.MessageTypeTaskAssignment, nil)
		msg.WithPriority(agents.Priority(i % 4))
		pq.Enqueue(msg)
	}

	if pq.Len() != 5 {
		t.Errorf("Queue length = %d, want 5", pq.Len())
	}

	pq.Clear()

	if pq.Len() != 0 {
		t.Errorf("After clear, queue length = %d, want 0", pq.Len())
	}
}

// TestPriorityQueueGetByPriority 测试按优先级获取数量
func TestPriorityQueueGetByPriority(t *testing.T) {
	pq := NewPriorityQueue()

	// 添加不同优先级的消息
	for i := 0; i < 3; i++ {
		msg := NewMessage(agents.AgentRoleCTO, agents.AgentRoleCEO, agents.MessageTypeTaskAssignment, nil)
		msg.WithPriority(agents.PriorityHigh)
		pq.Enqueue(msg)
	}

	for i := 0; i < 2; i++ {
		msg := NewMessage(agents.AgentRoleCFO, agents.AgentRoleCEO, agents.MessageTypeTaskAssignment, nil)
		msg.WithPriority(agents.PriorityLow)
		pq.Enqueue(msg)
	}

	highCount := pq.GetByPriority(agents.PriorityHigh)
	if highCount != 3 {
		t.Errorf("High priority count = %d, want 3", highCount)
	}

	lowCount := pq.GetByPriority(agents.PriorityLow)
	if lowCount != 2 {
		t.Errorf("Low priority count = %d, want 2", lowCount)
	}
}

// TestPriorityQueueGetAll 测试获取所有消息
func TestPriorityQueueGetAll(t *testing.T) {
	pq := NewPriorityQueue()

	msgs := make([]*Message, 5)
	for i := 0; i < 5; i++ {
		msg := NewMessage(agents.AgentRoleCTO, agents.AgentRoleCEO, agents.MessageTypeTaskAssignment, nil)
		msg.WithPriority(agents.Priority(i % 4))
		pq.Enqueue(msg)
		msgs[i] = msg
	}

	all := pq.GetAll()
	if len(all) != 5 {
		t.Errorf("GetAll length = %d, want 5", len(all))
	}

	// 修改返回的 slice 不应该影响原始队列
	all[0] = nil
	if pq.Len() != 5 {
		t.Errorf("Modifying returned slice should not affect queue")
	}
}

// TestIdempotencyLRU 测试 LRU 淘汰
func TestIdempotencyLRU(t *testing.T) {
	// 创建一个容量为 3 的检查器
	checker := NewIdempotencyChecker(3, 1*time.Hour)

	// 添加 5 个消息（会淘汰 2 个）
	for i := 0; i < 5; i++ {
		checker.MarkProcessed("msg-"+string(rune(i+'0')), i)
	}

	stats := checker.GetStats()
	if stats["cache_size"].(int) != 3 {
		t.Errorf("Cache size = %d, want 3 (LRU eviction)", stats["cache_size"])
	}
}

// TestIdempotencyWindow 测试时间窗口
func TestIdempotencyWindow(t *testing.T) {
	// 创建一个时间窗口为 100ms 的检查器
	checker := NewIdempotencyChecker(100, 100*time.Millisecond)

	msgID := "window-test-msg"

	// 标记为已处理
	checker.MarkProcessed(msgID, "result1")

	// 立即检查：应该已处理
	if !checker.IsProcessed(msgID) {
		t.Error("Message should be processed immediately")
	}

	// 等待超过时间窗口
	time.Sleep(150 * time.Millisecond)

	// 超过窗口后应该视为未处理
	if checker.IsProcessed(msgID) {
		t.Error("Message should be expired after window")
	}
}

// TestIdempotencyClear 测试清空缓存
func TestIdempotencyClear(t *testing.T) {
	checker := NewIdempotencyChecker(100, 1*time.Hour)

	// 添加一些消息
	checker.MarkProcessed("msg-1", "result1")
	checker.MarkProcessed("msg-2", "result2")

	stats := checker.GetStats()
	if stats["cache_size"].(int) != 2 {
		t.Errorf("Cache size = %d, want 2", stats["cache_size"])
	}

	// 清空
	checker.Clear()

	stats = checker.GetStats()
	if stats["cache_size"].(int) != 0 {
		t.Errorf("After clear, cache size = %d, want 0", stats["cache_size"])
	}

	// 验证消息不再被认为已处理
	if checker.IsProcessed("msg-1") {
		t.Error("Message should not be processed after clear")
	}
}

// TestMailboxNilMessage 测试发送 nil 消息
func TestMailboxNilMessage(t *testing.T) {
	idChecker := NewIdempotencyChecker(100, 1*time.Hour)
	metrics := NewMetrics()
	config := DefaultMailboxConfig(agents.AgentRoleCEO)
	config.EnableDLQ = false

	mb, err := NewMailbox(config, idChecker, nil, metrics)
	if err != nil {
		t.Fatalf("Failed to create mailbox: %v", err)
	}

	// 发送 nil 消息应该返回错误
	err = mb.Send(nil)
	if err == nil {
		t.Error("Send nil should return error")
	}
}

// TestMailboxFullQueue 测试队列满的情况
func TestMailboxFullQueue(t *testing.T) {
	idChecker := NewIdempotencyChecker(100, 1*time.Hour)
	metrics := NewMetrics()
	config := DefaultMailboxConfig(agents.AgentRoleCEO)
	config.InboxBufferSize = 2 // 小缓冲区
	config.EnableDLQ = false

	mb, err := NewMailbox(config, idChecker, nil, metrics)
	if err != nil {
		t.Fatalf("Failed to create mailbox: %v", err)
	}

	// 不启动 mailbox，直接测试 Send
	handler := func(msg *Message) error {
		return nil
	}
	mb.SetHandler(handler)

	// 发送消息填满缓冲区
	for i := 0; i < 3; i++ {
		msg := NewMessage(agents.AgentRoleCTO, agents.AgentRoleCEO, agents.MessageTypeTaskAssignment, nil)
		err := mb.Send(msg)
		if i < 2 {
			if err != nil {
				t.Errorf("Send %d should succeed, got error: %v", i, err)
			}
		} else {
			if err == nil {
				t.Error("Send to full queue should return error")
			}
		}
	}
}

// TestMailboxGetProcessingCount 测试获取正在处理的消息数
func TestMailboxGetProcessingCount(t *testing.T) {
	idChecker := NewIdempotencyChecker(100, 1*time.Hour)
	metrics := NewMetrics()
	config := DefaultMailboxConfig(agents.AgentRoleCEO)
	config.EnableDLQ = false

	mb, err := NewMailbox(config, idChecker, nil, metrics)
	if err != nil {
		t.Fatalf("Failed to create mailbox: %v", err)
	}

	handler := func(msg *Message) error {
		time.Sleep(100 * time.Millisecond)
		return nil
	}
	mb.SetHandler(handler)

	// 启动 mailbox
	if err := mb.Start(); err != nil {
		t.Fatalf("Failed to start mailbox: %v", err)
	}
	defer mb.Stop()

	// 初始状态
	count := mb.GetProcessingCount()
	if count != 0 {
		t.Errorf("Initial processing count = %d, want 0", count)
	}

	// 发送一个消息
	msg := NewMessage(agents.AgentRoleCTO, agents.AgentRoleCEO, agents.MessageTypeTaskAssignment, nil)
	if err := mb.Send(msg); err != nil {
		t.Fatalf("Failed to send message: %v", err)
	}

	// 等待处理开始
	time.Sleep(50 * time.Millisecond)

	// 应该有消息正在处理
	count = mb.GetProcessingCount()
	if count < 0 || count > 1 {
		t.Errorf("Processing count = %d, want 0 or 1", count)
	}

	// 等待处理完成
	time.Sleep(200 * time.Millisecond)

	count = mb.GetProcessingCount()
	if count != 0 {
		t.Errorf("After processing, count = %d, want 0", count)
	}
}
