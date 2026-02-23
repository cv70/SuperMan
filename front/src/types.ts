export interface Agent {
  id: string
  name: string
  role: string
  status: 'active' | 'idle' | 'busy' | 'error'
  taskCount: number
  lastActivity: string
  health: number
}

export interface Task {
  id: string
  title: string
  priority: 'critical' | 'high' | 'medium' | 'low'
  status: 'pending' | 'processing' | 'completed' | 'failed'
  assignedTo: string
  createdAt: string
  progress: number
  dependencies: string[]
}

export interface Message {
  id: string
  sender: string
  receiver: string
  type: string
  content: string
  timestamp: string
  priority: 'critical' | 'high' | 'medium' | 'low'
}

export interface SystemStatus {
  schedulerQueue: number
  priorities: Record<string, number>
  agents: Array<{ name: string; workload: number; running: boolean }>
}

export interface SendMessageRequest {
  sender: string
  receiver: string
  message: string
}
