package api

func (s *Server) configureRoutes() {
	s.engine.GET("/health", s.healthHandler)
	s.engine.GET("/ready", s.readyHandler)

	api := s.engine.Group("/api")
	api.POST("/send", s.sendHandler)
	api.GET("/status", s.statusHandler)
	api.GET("/agents", s.agentsHandler)
	api.GET("/tasks", s.tasksHandler)
	api.GET("/messages", s.messagesHandler)
	api.POST("/shutdown", s.shutdownHandler)
}
