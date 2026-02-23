package api

import (
	"context"
	"fmt"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"superman/agents"
	"superman/ds"
	"superman/mailbox"
	"superman/scheduler"
	"superman/workflow"

	"github.com/gin-gonic/gin"
)

var (
	agentMap          map[string]agents.Agent
	mailboxBus        *mailbox.MailboxBus
	orchestrator      workflow.Orchestrator
	schedulerInstance *scheduler.AutoScheduler
	timerEngine       interface{}
	stopFunc          context.CancelFunc
)

type Server struct {
	engine *gin.Engine
}

type SendRequest struct {
	Sender   string `json:"sender" binding:"required"`
	Receiver string `json:"receiver" binding:"required"`
	Message  string `json:"message" binding:"required"`
}

type SendResponse struct {
	Success bool   `json:"success"`
	Message string `json:"message,omitempty"`
	Error   string `json:"error,omitempty"`
}

type StatusResponse struct {
	SchedulerQueue int            `json:"scheduler_queue"`
	Priorities     map[string]int `json:"priorities"`
	Agents         []AgentStatus  `json:"agents"`
}

type AgentStatus struct {
	Name     string  `json:"name"`
	Workload float64 `json:"workload"`
	Running  bool    `json:"running"`
}

type AgentInfo struct {
	Name     string  `json:"name"`
	Desc     string  `json:"desc"`
	Running  bool    `json:"running"`
	Workload float64 `json:"workload"`
}

type AgentsResponse struct {
	Total  int         `json:"total"`
	Agents []AgentInfo `json:"agents"`
}

type ErrorResponse struct {
	Error string `json:"error"`
}

func NewServer() *Server {
	gin.SetMode(gin.ReleaseMode)
	engine := gin.Default()

	server := &Server{engine: engine}
	server.configureRoutes()
	return server
}

func (s *Server) Start(port string) error {
	addr := ":" + port
	fmt.Printf("Starting HTTP server on port %s\n", port)
	return s.engine.Run(addr)
}

func (s *Server) Stop(ctx context.Context) error {
	fmt.Println("Shutting down HTTP server...")
	return nil
}

func (s *Server) healthHandler(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"status":    "healthy",
		"timestamp": time.Now().Unix(),
	})
}

func (s *Server) readyHandler(c *gin.Context) {
	if mailboxBus == nil || orchestrator == nil || schedulerInstance == nil {
		c.JSON(http.StatusServiceUnavailable, ErrorResponse{Error: "System not initialized"})
		return
	}
	c.JSON(http.StatusOK, gin.H{
		"status":    "ready",
		"timestamp": time.Now().Unix(),
	})
}

func (s *Server) sendHandler(c *gin.Context) {
	var req SendRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, ErrorResponse{Error: err.Error()})
		return
	}

	if req.Sender == "" {
		c.JSON(http.StatusBadRequest, ErrorResponse{Error: "sender is required"})
		return
	}
	if req.Receiver == "" {
		c.JSON(http.StatusBadRequest, ErrorResponse{Error: "receiver is required"})
		return
	}
	if req.Message == "" {
		c.JSON(http.StatusBadRequest, ErrorResponse{Error: "message is required"})
		return
	}

	msg, err := ds.NewRequestMessage(
		req.Sender,
		req.Receiver,
		"message",
		req.Message,
		nil,
	)
	if err != nil {
		c.JSON(http.StatusInternalServerError, ErrorResponse{Error: fmt.Sprintf("failed to create message: %v", err)})
		return
	}

	err = mailboxBus.Send(msg)
	if err != nil {
		c.JSON(http.StatusInternalServerError, ErrorResponse{Error: fmt.Sprintf("failed to send message: %v", err)})
		return
	}

	c.JSON(http.StatusOK, SendResponse{
		Success: true,
		Message: fmt.Sprintf("Message sent from %s to %s", req.Sender, req.Receiver),
	})
}

func (s *Server) statusHandler(c *gin.Context) {
	response := StatusResponse{
		SchedulerQueue: schedulerInstance.GetQueueLength(),
		Priorities:     make(map[string]int),
		Agents:         make([]AgentStatus, 0),
	}

	for _, priority := range []string{
		scheduler.PriorityCritical,
		scheduler.PriorityHigh,
		scheduler.PriorityMedium,
		scheduler.PriorityLow,
	} {
		response.Priorities[priority] = schedulerInstance.GetQueueLengthByPriority(priority)
	}

	for name, agent := range agentMap {
		response.Agents = append(response.Agents, AgentStatus{
			Name:     name,
			Workload: agent.GetWorkload(),
			Running:  agent.IsRunning(),
		})
	}

	c.JSON(http.StatusOK, response)
}

func (s *Server) agentsHandler(c *gin.Context) {
	response := AgentsResponse{
		Total:  len(agentMap),
		Agents: make([]AgentInfo, 0),
	}

	for name, agent := range agentMap {
		response.Agents = append(response.Agents, AgentInfo{
			Name:     name,
			Desc:     agent.GetDesc(),
			Running:  agent.IsRunning(),
			Workload: agent.GetWorkload(),
		})
	}

	c.JSON(http.StatusOK, response)
}

func (s *Server) shutdownHandler(c *gin.Context) {
	go func() {
		shutdown(timerEngine, schedulerInstance, agentMap)
		os.Exit(0)
	}()

	c.JSON(http.StatusOK, gin.H{
		"status":  "shutting_down",
		"message": "System is shutting down...",
	})
}

func RunServer(port string) error {
	server := NewServer()

	errCh := make(chan error, 1)
	go func() {
		if err := server.Start(port); err != nil && err != http.ErrServerClosed {
			errCh <- err
		}
	}()

	select {
	case err := <-errCh:
		return err
	case <-time.After(2 * time.Second):
	}

	sigCh := make(chan os.Signal, 1)
	signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)

	go func() {
		<-sigCh
		fmt.Println("\nReceived shutdown signal")
		fmt.Printf("Server shutdown error: %v\n", server.Stop(nil))
		shutdown(timerEngine, schedulerInstance, agentMap)
		os.Exit(0)
	}()

	fmt.Println("HTTP server running. Press Ctrl+C to shutdown.")
	select {}
}

func Initialize(
	agentsMap map[string]agents.Agent,
	mb *mailbox.MailboxBus,
	orch workflow.Orchestrator,
	sched *scheduler.AutoScheduler,
	te interface{},
) {
	agentMap = agentsMap
	mailboxBus = mb
	orchestrator = orch
	schedulerInstance = sched
	timerEngine = te
}

func Shutdown() {
	shutdown(timerEngine, schedulerInstance, agentMap)
}

func shutdown(timerEngine interface{}, schedulerInstance *scheduler.AutoScheduler, agentMap map[string]agents.Agent) {
	fmt.Println("stopping timer engine")
	fmt.Println("stopping scheduler")
	schedulerInstance.Stop()

	fmt.Println("stopping agents")
	for name, agent := range agentMap {
		if err := agent.Stop(); err != nil {
			fmt.Println("failed to stop agent:", name, err)
		}
	}
  fmt.Println("shutdown complete")
}

func (s *Server) tasksHandler(c *gin.Context) {
  tasks := make([]gin.H, 0)
  for _, task := range mailboxBus.GetGlobalState().GetTasks() {
    tasks = append(tasks, gin.H{
      "id":           task.ID,
      "title":        task.Title,
      "priority":     string(task.Priority),
      "status":       string(task.Status),
      "assigned_to":  task.AssignedTo,
      "created_at":   task.CreatedAt.Format("2006-01-02 15:04:05"),
      "dependencies": task.Dependencies,
    })
  }
  c.JSON(http.StatusOK, gin.H{"tasks": tasks})
}

func (s *Server) messagesHandler(c *gin.Context) {
  messages := mailboxBus.GetGlobalState().GetMessages()
  result := make([]gin.H, len(messages))
  for i, msg := range messages {
    result[i] = gin.H{
      "id":       msg.ID,
      "sender":   msg.Sender,
      "receiver": msg.Receiver,
      "type":     string(msg.Type),
      "content":  msg.Body,
    }
  }
  c.JSON(http.StatusOK, gin.H{"messages": result})
}
