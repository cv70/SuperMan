const API_BASE_URL = 'http://localhost:8080'

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

export interface StatusData {
  scheduler_queue: number
  priorities: Record<string, number>
  agents: AgentStatus[]
}

export interface AgentStatus {
  name: string
  workload: number
  running: boolean
}

export async function fetchAgents(): Promise<Agent[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/status`)
    const data: StatusData = await response.json()
    return data.agents?.map((a) => ({
      id: a.name.toLowerCase(),
      name: a.name,
      role: a.name,
      status: a.workload > 0.8 ? 'busy' : a.workload > 0.2 ? 'active' : 'idle',
      taskCount: Math.floor(a.workload * 10) + 1,
      lastActivity: '刚刚',
      health: 90 + Math.floor(Math.random() * 10)
    })) || []
  } catch (error) {
    console.error('获取Agent列表失败:', error)
    return []
  }
}

export async function fetchSystemStatus(): Promise<StatusData | null> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/status`)
    return await response.json()
  } catch (error) {
    console.error('获取系统状态失败:', error)
    return null
  }
}

export async function fetchTasks(): Promise<Task[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/tasks`)
    const result: any = await response.json()
    return (result.tasks || []).map((t: any) => ({
      id: t.id,
      title: t.title,
      priority: t.priority as 'critical' | 'high' | 'medium' | 'low',
      status: t.status as 'pending' | 'processing' | 'completed' | 'failed',
      assignedTo: t.assigned_to || '',
      createdAt: t.created_at || '',
      progress: t.progress || 0,
      dependencies: t.dependencies || []
    }))
  } catch (error) {
    console.error('获取任务列表失败:', error)
    return []
  }
}

export async function fetchMessages(): Promise<Message[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/messages`)
    const result: any = await response.json()
    return (result.messages || []).map((m: any) => ({
      id: m.id,
      sender: m.sender,
      receiver: m.receiver,
      type: m.type || 'message',
      content: m.content || m.body || '',
      timestamp: m.created_at || m.timestamp || '刚刚',
      priority: m.priority as 'critical' | 'high' | 'medium' | 'low' || 'low'
    }))
  } catch (error) {
    console.error('获取消息列表失败:', error)
    return []
  }
}
