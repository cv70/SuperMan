package mailbox

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"sync"
	"time"

	_ "github.com/mattn/go-sqlite3"
	"superman/agents"
)

// DeadLetterMessage 死信消息
type DeadLetterMessage struct {
	ID         int64            `json:"id"`
	MessageID  string           `json:"message_id"`
	Sender     agents.AgentRole `json:"sender"`
	Receiver   agents.AgentRole `json:"receiver"`
	Content    []byte           `json:"content"` // JSON序列化的消息
	FailedAt   time.Time        `json:"failed_at"`
	RetryCount int              `json:"retry_count"`
	Reason     string           `json:"reason"`
	StackTrace string           `json:"stack_trace,omitempty"`
	Status     string           `json:"status"` // pending / retried / archived
}

// DeadLetterQueue 死信队列（SQLite持久化 + Channel通知）
type DeadLetterQueue struct {
	db       *sql.DB
	config   *DLQConfig
	notifyCh chan *DeadLetterMessage // 通知channel
	stopCh   chan struct{}
	wg       sync.WaitGroup
}

// DLQConfig 死信队列配置
type DLQConfig struct {
	DBPath          string        // SQLite数据库路径
	MaxAge          time.Duration // 最大保留时间
	CleanupInterval time.Duration // 清理间隔
	AlertThreshold  int           // 告警阈值
	NotifyBuffer    int           // 通知channel缓冲区大小
}

// DefaultDLQConfig 返回默认配置
func DefaultDLQConfig() *DLQConfig {
	return &DLQConfig{
		DBPath:          "./data/dlq.db",
		MaxAge:          30 * 24 * time.Hour, // 30天
		CleanupInterval: 24 * time.Hour,
		AlertThreshold:  100,
		NotifyBuffer:    1000,
	}
}

// NewDeadLetterQueue 创建新的死信队列
func NewDeadLetterQueue(config *DLQConfig) (*DeadLetterQueue, error) {
	if config == nil {
		config = DefaultDLQConfig()
	}

	// 打开数据库
	db, err := sql.Open("sqlite3", config.DBPath)
	if err != nil {
		return nil, fmt.Errorf("failed to open DLQ database: %w", err)
	}

	dlq := &DeadLetterQueue{
		db:       db,
		config:   config,
		notifyCh: make(chan *DeadLetterMessage, config.NotifyBuffer),
		stopCh:   make(chan struct{}),
	}

	// 创建表
	if err := dlq.createTable(); err != nil {
		db.Close()
		return nil, err
	}

	// 启动清理goroutine
	dlq.wg.Add(1)
	go dlq.cleanup()

	return dlq, nil
}

// createTable 创建表结构
func (dlq *DeadLetterQueue) createTable() error {
	query := `
	CREATE TABLE IF NOT EXISTS dead_letter_queue (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		message_id TEXT UNIQUE NOT NULL,
		sender TEXT NOT NULL,
		receiver TEXT NOT NULL,
		content BLOB NOT NULL,
		failed_at TIMESTAMP NOT NULL,
		retry_count INTEGER NOT NULL DEFAULT 0,
		reason TEXT,
		stack_trace TEXT,
		status TEXT DEFAULT 'pending',
		created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
	);

	CREATE INDEX IF NOT EXISTS idx_status ON dead_letter_queue(status);
	CREATE INDEX IF NOT EXISTS idx_failed_at ON dead_letter_queue(failed_at);
	CREATE INDEX IF NOT EXISTS idx_receiver ON dead_letter_queue(receiver);
	`

	_, err := dlq.db.Exec(query)
	return err
}

// Add 添加消息到死信队列
func (dlq *DeadLetterQueue) Add(msg *Message, retryCount int, reason string, stackTrace string) error {
	content, err := json.Marshal(msg)
	if err != nil {
		return fmt.Errorf("failed to marshal message: %w", err)
	}

	// 开始事务
	tx, err := dlq.db.Begin()
	if err != nil {
		return err
	}
	defer tx.Rollback()

	// 插入数据库
	query := `
	INSERT INTO dead_letter_queue 
	(message_id, sender, receiver, content, failed_at, retry_count, reason, stack_trace, status)
	VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
	ON CONFLICT(message_id) DO UPDATE SET
		retry_count = excluded.retry_count,
		reason = excluded.reason,
		stack_trace = excluded.stack_trace,
		failed_at = excluded.failed_at
	`

	result, err := tx.Exec(
		query,
		msg.MessageID,
		msg.Sender,
		msg.Receiver,
		content,
		time.Now(),
		retryCount,
		reason,
		stackTrace,
		"pending",
	)
	if err != nil {
		return err
	}

	// 获取插入的ID
	id, _ := result.LastInsertId()

	// 提交事务
	if err := tx.Commit(); err != nil {
		return err
	}

	// 创建死信消息对象用于通知
	dlMsg := &DeadLetterMessage{
		ID:         id,
		MessageID:  msg.MessageID,
		Sender:     msg.Sender,
		Receiver:   msg.Receiver,
		FailedAt:   time.Now(),
		RetryCount: retryCount,
		Reason:     reason,
		StackTrace: stackTrace,
		Status:     "pending",
	}

	// 异步通知（非阻塞）
	select {
	case dlq.notifyCh <- dlMsg:
	default:
		// channel已满，记录日志
		fmt.Printf("[DLQ] Warning: notify channel is full\n")
	}

	return nil
}

// GetPending 获取待处理的消息
func (dlq *DeadLetterQueue) GetPending(limit int) ([]*DeadLetterMessage, error) {
	if limit <= 0 {
		limit = 100
	}

	query := `
	SELECT id, message_id, sender, receiver, content, failed_at, retry_count, reason, stack_trace, status
	FROM dead_letter_queue
	WHERE status = 'pending'
	ORDER BY failed_at DESC
	LIMIT ?
	`

	rows, err := dlq.db.Query(query, limit)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	return dlq.scanRows(rows)
}

// GetByReceiver 获取指定接收者的消息
func (dlq *DeadLetterQueue) GetByReceiver(receiver agents.AgentRole, limit int) ([]*DeadLetterMessage, error) {
	if limit <= 0 {
		limit = 100
	}

	query := `
	SELECT id, message_id, sender, receiver, content, failed_at, retry_count, reason, stack_trace, status
	FROM dead_letter_queue
	WHERE receiver = ? AND status = 'pending'
	ORDER BY failed_at DESC
	LIMIT ?
	`

	rows, err := dlq.db.Query(query, receiver, limit)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	return dlq.scanRows(rows)
}

// MarkRetried 标记消息为已重试
func (dlq *DeadLetterQueue) MarkRetried(messageID string) error {
	query := `UPDATE dead_letter_queue SET status = 'retried' WHERE message_id = ?`
	_, err := dlq.db.Exec(query, messageID)
	return err
}

// MarkArchived 标记消息为已归档
func (dlq *DeadLetterQueue) MarkArchived(messageID string) error {
	query := `UPDATE dead_letter_queue SET status = 'archived' WHERE message_id = ?`
	_, err := dlq.db.Exec(query, messageID)
	return err
}

// Delete 删除消息
func (dlq *DeadLetterQueue) Delete(messageID string) error {
	query := `DELETE FROM dead_letter_queue WHERE message_id = ?`
	_, err := dlq.db.Exec(query, messageID)
	return err
}

// GetStats 获取统计信息
func (dlq *DeadLetterQueue) GetStats() (map[string]int, error) {
	stats := make(map[string]int)

	query := `
	SELECT status, COUNT(*) 
	FROM dead_letter_queue 
	GROUP BY status
	`

	rows, err := dlq.db.Query(query)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	for rows.Next() {
		var status string
		var count int
		if err := rows.Scan(&status, &count); err != nil {
			return nil, err
		}
		stats[status] = count
	}

	return stats, rows.Err()
}

// GetTotalCount 获取总数
func (dlq *DeadLetterQueue) GetTotalCount() (int, error) {
	var count int
	err := dlq.db.QueryRow("SELECT COUNT(*) FROM dead_letter_queue").Scan(&count)
	return count, err
}

// GetNotifyChannel 获取通知channel（用于监听新消息）
func (dlq *DeadLetterQueue) GetNotifyChannel() <-chan *DeadLetterMessage {
	return dlq.notifyCh
}

// cleanup 定期清理过期消息
func (dlq *DeadLetterQueue) cleanup() {
	defer dlq.wg.Done()

	ticker := time.NewTicker(dlq.config.CleanupInterval)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			if err := dlq.removeExpired(); err != nil {
				fmt.Printf("[DLQ] Failed to cleanup: %v\n", err)
			}
		case <-dlq.stopCh:
			return
		}
	}
}

// removeExpired 移除过期消息
func (dlq *DeadLetterQueue) removeExpired() error {
	cutoff := time.Now().Add(-dlq.config.MaxAge)
	query := `DELETE FROM dead_letter_queue WHERE failed_at < ?`
	_, err := dlq.db.Exec(query, cutoff)
	return err
}

// scanRows 扫描查询结果
func (dlq *DeadLetterQueue) scanRows(rows *sql.Rows) ([]*DeadLetterMessage, error) {
	var messages []*DeadLetterMessage

	for rows.Next() {
		var msg DeadLetterMessage
		var failedAtStr string

		err := rows.Scan(
			&msg.ID,
			&msg.MessageID,
			&msg.Sender,
			&msg.Receiver,
			&msg.Content,
			&failedAtStr,
			&msg.RetryCount,
			&msg.Reason,
			&msg.StackTrace,
			&msg.Status,
		)
		if err != nil {
			return nil, err
		}

		// 解析时间
		msg.FailedAt, _ = time.Parse("2006-01-02 15:04:05", failedAtStr)

		messages = append(messages, &msg)
	}

	return messages, rows.Err()
}

// ShouldAlert 检查是否需要告警
func (dlq *DeadLetterQueue) ShouldAlert() bool {
	count, err := dlq.GetTotalCount()
	if err != nil {
		return false
	}
	return count >= dlq.config.AlertThreshold
}

// Close 关闭死信队列
func (dlq *DeadLetterQueue) Close() error {
	close(dlq.stopCh)
	dlq.wg.Wait()
	close(dlq.notifyCh)
	return dlq.db.Close()
}
