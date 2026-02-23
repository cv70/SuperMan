<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { fetchAgents, fetchTasks, fetchMessages } from './api/index'
import type { Agent, Task, Message } from './types'


// 从 API 获取的数据
const agents = ref<Agent[]>([])
const tasks = ref<Task[]>([])
const messages = ref<Message[]>([])

// 加载数据的函数
const loadData = async () => {
  try {
    const [agentsData, tasksData, messagesData] = await Promise.all([
      fetchAgents(),
      fetchTasks(),
      fetchMessages()
    ])
    agents.value = agentsData
    tasks.value = tasksData
    messages.value = messagesData
  } catch (error) {
    console.error('加载数据失败:', error)
  }
}

// 初始化时加载数据
const loadInitialData = () => {
  loadData()
  refreshInterval.value = window.setInterval(() => {
    // 仅刷新消息时间戳模拟实时更新
    messages.value.forEach(msg => {
      const seconds = Math.floor(Math.random() * 5)
      msg.timestamp = seconds === 0 ? '刚刚' : `${seconds}秒前`
    })
  }, 3000)
}

const busyAgents = computed(() => agents.value.filter(a => a.status === 'busy'))
const totalTasks = computed(() => tasks.value.length)
const completedTasks = computed(() => tasks.value.filter(t => t.status === 'completed').length)
const pendingTasks = computed(() => tasks.value.filter(t => t.status === 'pending').length)
const criticalTasks = computed(() => tasks.value.filter(t => t.priority === 'critical' && t.status !== 'completed').length)

const priorityStats = computed(() => ({
  critical: tasks.value.filter(t => t.priority === 'critical').length,
  high: tasks.value.filter(t => t.priority === 'high').length,
  medium: tasks.value.filter(t => t.priority === 'medium').length,
  low: tasks.value.filter(t => t.priority === 'low').length
}))

const filteredTasks = ref<Task[]>(tasks.value)
const taskSearch = ref('')
const taskPriorityFilter = ref<string>('all')
const taskStatusFilter = ref<string>('all')

const filteredMessages = ref<Message[]>(messages.value)
const messageSearch = ref('')
const messageSenderFilter = ref<string>('all')
const messageReceiverFilter = ref<string>('all')

const filteredAgents = ref<Agent[]>(agents.value)
const agentSearch = ref('')

watch([taskSearch, taskPriorityFilter, taskStatusFilter], () => {
  filteredTasks.value = tasks.value.filter(task => {
    const matchesSearch = task.title.includes(taskSearch.value) || task.id.includes(taskSearch.value)
    const matchesPriority = taskPriorityFilter.value === 'all' || task.priority === taskPriorityFilter.value
    const matchesStatus = taskStatusFilter.value === 'all' || task.status === taskStatusFilter.value
    return matchesSearch && matchesPriority && matchesStatus
  })
})

watch([messageSearch, messageSenderFilter, messageReceiverFilter], () => {
  filteredMessages.value = messages.value.filter(msg => {
    const matchesSearch = msg.content.includes(messageSearch.value) || msg.sender.includes(messageSearch.value) || msg.receiver.includes(messageSearch.value)
    const matchesSender = messageSenderFilter.value === 'all' || msg.sender === messageSenderFilter.value
    const matchesReceiver = messageReceiverFilter.value === 'all' || msg.receiver === messageReceiverFilter.value
    return matchesSearch && matchesSender && matchesReceiver
  })
})
watch(agentSearch, () => {
  filteredAgents.value = agents.value.filter(agent => 
    agent.name.toLowerCase().includes(agentSearch.value.toLowerCase())
  )
})

const getPriorityColor = (priority: string) => {
  switch (priority) {
    case 'critical': return 'bg-amber-500'
    case 'high': return 'bg-red-500'
    case 'medium': return 'bg-blue-500'
    case 'low': return 'bg-green-500'
    default: return 'bg-gray-500'
  }
}

const getPriorityBg = (priority: string) => {
  switch (priority) {
    case 'critical': return 'bg-amber-500/20 text-amber-500 border-amber-500/30'
    case 'high': return 'bg-red-500/20 text-red-500 border-red-500/30'
    case 'medium': return 'bg-blue-500/20 text-blue-500 border-blue-500/30'
    case 'low': return 'bg-green-500/20 text-green-500 border-green-500/30'
    default: return 'bg-gray-500/20 text-gray-500 border-gray-500/30'
  }
}

const getStatusBg = (status: string) => {
  switch (status) {
    case 'active': return 'bg-green-400'
    case 'busy': return 'bg-yellow-400'
    case 'idle': return 'bg-gray-400'
    case 'error': return 'bg-red-500'
    default: return 'bg-gray-400'
  }
}

const refreshInterval = ref<number | null>(null)

onMounted(() => {
  loadInitialData()
})

onUnmounted(() => {
  if (refreshInterval.value) clearInterval(refreshInterval.value)
})
</script>

<template>
  <div class="min-h-screen bg-[#0a192f]">
    <header class="mb-8 pb-6 border-b border-[#112240]">
      <div class="flex items-center justify-between mb-4">
        <div>
          <h1 class="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-[#2cc8ff] to-[#66fcf1]">
            SuperMan AI 仪表盘
          </h1>
          <p class="text-[#8b9bb4] mt-2">多智能体系统可视化监控</p>
        </div>
        <div class="text-right">
          <div class="text-2xl font-bold text-[#2cc8ff]">{{ agents.filter(a => a.status === 'active').length }} / 11</div>
          <div class="text-sm text-[#8b9bb4]">活跃智能体</div>
        </div>
      </div>
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div class="bg-[#112240] rounded-lg p-4 border border-[#233554] hover:border-[#2cc8ff]/30 transition-all duration-300">
          <div class="flex items-center gap-2 mb-2"><div class="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div><span class="text-sm text-[#8b9bb4]">已完成任务</span></div>
          <div class="text-3xl font-bold text-[#66fcf1]">{{ completedTasks }} / {{ totalTasks }}</div>
        </div>
        <div class="bg-[#112240] rounded-lg p-4 border border-[#233554] hover:border-[#2cc8ff]/30 transition-all duration-300">
          <div class="flex items-center gap-2 mb-2"><div class="w-2 h-2 rounded-full bg-[#2cc8ff]"></div><span class="text-sm text-[#8b9bb4]">待处理任务</span></div>
          <div class="text-3xl font-bold text-[#2cc8ff]">{{ pendingTasks }}</div>
        </div>
        <div class="bg-[#112240] rounded-lg p-4 border border-[#233554] hover:border-[#2cc8ff]/30 transition-all duration-300">
          <div class="flex items-center gap-2 mb-2"><div class="w-2 h-2 rounded-full bg-amber-500"></div><span class="text-sm text-[#8b9bb4]">紧急任务</span></div>
          <div class="text-3xl font-bold text-amber-500">{{ criticalTasks }}</div>
        </div>
        <div class="bg-[#112240] rounded-lg p-4 border border-[#233554] hover:border-[#2cc8ff]/30 transition-all duration-300">
          <div class="flex items-center gap-2 mb-2"><div class="w-2 h-2 rounded-full bg-yellow-500"></div><span class="text-sm text-[#8b9bb4]">忙碌智能体</span></div>
          <div class="text-3xl font-bold text-yellow-500">{{ busyAgents.length }}</div>
        </div>
      </div>
    </header>

    <main class="space-y-6">
      <section class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div class="lg:col-span-2 bg-[#112240] rounded-lg border border-[#233554] overflow-hidden shadow-lg shadow-[#2cc8ff]/5">
          <div class="p-4 border-b border-[#233554] bg-[#0a192f]/50">
            <h2 class="text-xl font-semibold flex items-center"><span class="w-1 h-6 bg-[#2cc8ff] mr-3 rounded-full"></span>智能体健康状态概览</h2>
          </div>
          <div class="p-4 grid grid-cols-1 md:grid-cols-3 gap-4">
            <div v-for="agent in agents.slice(0, 9)" :key="agent.id" class="bg-[#0a192f] rounded-lg p-3 border border-[#233554] hover:border-[#2cc8ff]/40 transition-all duration-300 hover:shadow-lg hover:shadow-[#2cc8ff]/10 cursor-pointer">
              <div class="flex items-center justify-between mb-3">
                <div class="flex items-center gap-3">
                  <div class="w-10 h-10 rounded-full bg-gradient-to-br from-[#2cc8ff] to-[#66fcf1] flex items-center justify-center text-white font-bold text-lg">{{ agent.name.substring(0, 1) }}</div>
                  <div>
                    <div class="font-semibold text-[#89d1c5]">{{ agent.name }}</div>
                    <div class="text-sm text-[#8b9bb4]">{{ agent.role }}</div>
                  </div>
                </div>
                <div :class="['w-3 h-3 rounded-full', getStatusBg(agent.status), agent.status === 'active' ? 'animate-pulse' : '']"></div>
              </div>
              <div class="space-y-2">
                <div class="flex items-center justify-between text-sm px-1"><span class="text-[#8b9bb4] flex items-center gap-1"><span>📋</span>任务数</span><span class="text-[#c5c6c7] font-mono">{{ agent.taskCount }}</span></div>
                <div class="flex items-center justify-between text-sm px-1"><span class="text-[#8b9bb4] flex items-center gap-1"><span>⏱️</span>最后活动</span><span class="text-[#c5c6c7] text-xs">{{ agent.lastActivity }}</span></div>
                <div class="px-1">
                  <div class="flex justify-between text-xs mb-1"><span class="text-[#8b9bb4]">✅ 健康度</span><span class="text-[#c5c6c7] font-mono">{{ agent.health }}%</span></div>
                  <div class="w-full bg-[#233554] rounded-full h-2 overflow-hidden">
                    <div :class="['h-2 rounded-full transition-all duration-500', agent.health > 80 ? 'bg-gradient-to-r from-green-500 to-[#66fcf1]' : agent.health > 60 ? 'bg-gradient-to-r from-yellow-500 to-orange-500' : 'bg-gradient-to-r from-red-500 to-pink-500']" :style="{ width: agent.health + '%' }"></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="bg-[#112240] rounded-lg border border-[#233554] overflow-hidden shadow-lg shadow-[#2cc8ff]/5">
          <div class="p-4 border-b border-[#233554] bg-[#0a192f]/50">
            <h2 class="text-xl font-semibold flex items-center"><span class="w-1 h-6 bg-amber-500 mr-3 rounded-full"></span>任务优先级分布</h2>
          </div>
          <div class="p-6 space-y-6">
            <div v-for="priority in ['critical', 'high', 'medium', 'low']" :key="priority" class="space-y-3 p-3 rounded-lg bg-[#0a192f]/30 border border-[#233554]/30">
              <div class="flex items-center justify-between">
                <span class="capitalize text-sm font-medium text-[#8b9bb4]">{{ priority === 'critical' ? '🔴 紧急' : priority === 'high' ? '🟠 重要' : priority === 'medium' ? '🟡 一般' : '🟢 普通' }}</span>
                <span class="font-mono text-sm text-[#c5c6c7]">{{ priorityStats[priority as keyof typeof priorityStats] }}</span>
              </div>
              <div class="w-full bg-[#233554] rounded-full h-3 overflow-hidden"><div :class="['h-3 rounded-full transition-all duration-500', getPriorityColor(priority)]" :style="{ width: (priorityStats[priority as keyof typeof priorityStats] / totalTasks * 100) + '%' }"></div></div>
              <div class="text-xs text-[#8b9bb4] text-right">{{ Math.round(priorityStats[priority as keyof typeof priorityStats] / totalTasks * 100) }}%</div>
            </div>
          </div>
        </div>
      </section>

      <section class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div class="lg:col-span-2 bg-[#112240] rounded-lg border border-[#233554] overflow-hidden shadow-lg shadow-[#2cc8ff]/5">
          <div class="p-4 border-b border-[#233554] bg-[#0a192f]/50 flex flex-wrap justify-between items-center gap-4">
            <h2 class="text-xl font-semibold flex items-center"><span class="w-1 h-6 bg-blue-500 mr-3 rounded-full"></span>正在进行的任务</h2>
            <div class="flex flex-wrap gap-2">
              <input v-model="taskSearch" placeholder="搜索任务..." class="bg-[#0a192f] border border-[#233554] rounded-lg px-3 py-2 text-sm focus:border-[#2cc8ff] focus:outline-none focus:ring-1 focus:ring-[#2cc8ff]/30 transition-all placeholder-[#8b9bb4]">
              <select v-model="taskPriorityFilter" class="bg-[#0a192f] border border-[#233554] rounded-lg px-3 py-2 text-sm focus:border-[#2cc8ff] focus:outline-none focus:ring-1 focus:ring-[#2cc8ff]/30 transition-all text-[#c5c6c7]">
                <option value="all">全部优先级</option>
                <option value="critical">紧急</option>
                <option value="high">重要</option>
                <option value="medium">一般</option>
                <option value="low">普通</option>
              </select>
              <select v-model="taskStatusFilter" class="bg-[#0a192f] border border-[#233554] rounded-lg px-3 py-2 text-sm focus:border-[#2cc8ff] focus:outline-none focus:ring-1 focus:ring-[#2cc8ff]/30 transition-all text-[#c5c6c7]">
                <option value="all">全部状态</option>
                <option value="pending">待处理</option>
                <option value="processing">处理中</option>
                <option value="completed">已完成</option>
                <option value="failed">失败</option>
              </select>
            </div>
          </div>
          <div class="overflow-x-auto">
            <table class="w-full">
              <thead class="bg-[#0a192f]/50 border-b border-[#233554]">
                <tr><th class="p-3 text-sm font-medium text-[#8b9bb4]">ID</th><th class="p-3 text-sm font-medium text-[#8b9bb4]">任务标题</th><th class="p-3 text-sm font-medium text-[#8b9bb4]">优先级</th><th class="p-3 text-sm font-medium text-[#8b9bb4]">状态</th><th class="p-3 text-sm font-medium text-[#8b9bb4]">负责人</th><th class="p-3 text-sm font-medium text-[#8b9bb4]">进度</th></tr>
              </thead>
              <tbody>
                <tr v-for="task in filteredTasks" :key="task.id" class="border-b border-[#233554]/30 hover:bg-[#112240]/50 transition-colors group cursor-pointer">
                  <td class="p-3 font-mono text-sm text-[#8b9bb4] group-hover:text-[#2cc8ff] transition-colors">{{ task.id }}</td>
                  <td class="p-3 text-sm text-[#c5c6c7] group-hover:text-[#89d1c5] transition-colors">{{ task.title }}</td>
                  <td class="p-3"><span :class="['px-2 py-1 rounded text-xs font-medium capitalize inline-flex items-center gap-1', getPriorityBg(task.priority)]">{{ task.priority === 'critical' ? '🔴 紧急' : task.priority === 'high' ? '🟠 重要' : task.priority === 'medium' ? '🟡 一般' : '🟢 普通' }}</span></td>
                  <td class="p-3"><span :class="['px-2 py-1 rounded text-xs font-medium', { 'bg-green-500/20 text-green-400 border border-green-500/30': task.status === 'completed', 'bg-blue-500/20 text-blue-400 border border-blue-500/30': task.status === 'processing', 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30': task.status === 'pending', 'bg-red-500/20 text-red-400 border border-red-500/30': task.status === 'failed' }]">{{ task.status === 'completed' ? '✅ 已完成' : task.status === 'processing' ? '🟡 处理中' : task.status === 'pending' ? '⏳ 待处理' : '❌ 失败' }}</span></td>
                  <td class="p-3 text-sm text-[#89d1c5] capitalize">{{ task.assignedTo }}</td>
                  <td class="p-3"><div class="flex items-center gap-2"><div class="flex-1 bg-[#233554] rounded-full h-2 max-w-[80px] overflow-hidden"><div :class="['h-2 rounded-full transition-all duration-500', task.progress === 100 ? 'bg-green-500' : 'bg-gradient-to-r from-[#2cc8ff] to-[#66fcf1]']" :style="{ width: task.progress + '%' }"></div></div><span class="text-xs font-mono text-[#8b9bb4]">{{ task.progress }}%</span></div></td>
                </tr>
              </tbody>
            </table>
            <div v-if="filteredTasks.length === 0" class="p-8 text-center text-[#8b9bb4]"><div class="text-4xl mb-2">🔍</div><p>未找到匹配的任务</p></div>
          </div>
        </div>

        <div class="bg-[#112240] rounded-lg border border-[#233554] overflow-hidden shadow-lg shadow-[#2cc8ff]/5">
          <div class="p-4 border-b border-[#233554] bg-[#0a192f]/50">
            <h2 class="text-xl font-semibold flex items-center"><span class="w-1 h-6 bg-[#ff6b6b] mr-3 rounded-full"></span>系统活动流</h2>
          </div>
          <div class="max-h-[400px] overflow-y-auto p-4 space-y-4 custom-scrollbar">
            <div v-for="message in filteredMessages.slice(0, 8)" :key="message.id" class="flex items-start gap-3 p-3 rounded-lg bg-[#0a192f]/30 border border-[#233554]/30 hover:border-[#2cc8ff]/30 transition-all group cursor-pointer">
              <div class="w-8 h-8 rounded-full bg-gradient-to-br from-[#2cc8ff] to-[#66fcf1] flex items-center justify-center text-white font-bold text-xs shadow-lg group-hover:scale-110 transition-transform">{{ message.sender.substring(0, 2).toUpperCase() }}</div>
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2 mb-1.5"><span class="text-sm font-medium capitalize text-[#c5c6c7] hover:text-[#2cc8ff] transition-colors">{{ message.sender }}</span><span class="text-[#8b9bb4]">→</span><span class="text-sm font-medium capitalize text-[#c5c6c7] hover:text-[#2cc8ff] transition-colors">{{ message.receiver }}</span><span :class="['w-1.5 h-1.5 rounded-full', getPriorityColor(message.priority)]" :title="message.priority === 'critical' ? '紧急' : message.priority === 'high' ? '重要' : '普通'"></span></div>
                <div class="text-sm text-[#89d1c5] mb-2 truncate">{{ message.content }}</div>
                <div class="flex items-center gap-3 text-xs text-[#8b9bb4]"><span class="capitalize flex items-center gap-1">{{ message.type === 'request' ? '📩 请求' : message.type === 'response' ? '📤 响应' : message.type === 'task' ? '📋 任务' : message.type === 'notification' ? '🔔 通知' : '💬 消息' }}</span><span>•</span><span>{{ message.timestamp }}</span></div>
              </div>
            </div>
            <div v-if="filteredMessages.length === 0" class="p-8 text-center text-[#8b9bb4]"><div class="text-4xl mb-2">📡</div><p>暂无系统活动</p></div>
          </div>
        </div>
      </section>

      <section class="bg-[#112240] rounded-lg border border-[#233554] overflow-hidden shadow-lg shadow-[#2cc8ff]/5">
        <div class="p-4 border-b border-[#233554] bg-[#0a192f]/50"><h2 class="text-xl font-semibold flex items-center"><span class="w-1 h-6 bg-purple-500 mr-3 rounded-full"></span>智能体目录</h2></div>
        <div class="p-4">
          <div class="mb-4 relative">
            <input v-model="agentSearch" placeholder="搜索智能体..." class="w-full bg-[#0a192f] border border-[#233554] rounded-lg px-4 py-3 pr-10 text-[#c5c6c7] focus:border-[#2cc8ff] focus:outline-none focus:ring-1 focus:ring-[#2cc8ff]/30 transition-all placeholder-[#8b9bb4]">
            <div class="absolute right-3 top-1/2 -translate-y-1/2 text-[#8b9bb4]">🔍</div>
          </div>
          <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
            <div v-for="agent in filteredAgents" :key="agent.id" class="bg-[#0a192f] rounded-lg p-4 border border-[#233554] hover:border-[#2cc8ff]/50 transition-all hover:-translate-y-1 hover:shadow-lg hover:shadow-[#2cc8ff]/20 cursor-pointer group">
              <div class="w-14 h-14 rounded-full bg-gradient-to-br from-[#2cc8ff] via-[#66fcf1] to-purple-500 flex items-center justify-center text-white font-bold text-xl mb-4 mx-auto shadow-lg shadow-[#2cc8ff]/30 group-hover:scale-110 transition-transform">{{ agent.name.substring(0, 1) }}</div>
              <div class="text-center">
                <div class="font-semibold text-[#c5c6c7] capitalize group-hover:text-[#2cc8ff] transition-colors">{{ agent.name }}</div>
                <div class="text-xs text-[#8b9bb4] mt-1.5 capitalize leading-relaxed">{{ agent.name }}</div>
                <div class="mt-3 text-xs text-[#8b9bb4]"><div class="flex items-center justify-center gap-1.5"><div :class="['w-2 h-2 rounded-full', getStatusBg(agent.status)]"></div><span class="capitalize">{{ agent.status === 'active' ? '✅ 运行中' : agent.status === 'busy' ? '🟡 忙碌' : agent.status === 'idle' ? '⏳ 空闲' : '❌ 错误' }}</span></div></div>
                <div class="mt-2 text-center text-xs text-[#8b9bb4]">{{ agent.taskCount }} 个任务</div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>

<style>
.custom-scrollbar::-webkit-scrollbar { width: 6px; }
.custom-scrollbar::-webkit-scrollbar-track { background: #0a192f; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #233554; border-radius: 3px; }
.custom-scrollbar::-webkit-scrollbar-thumb:hover { background: #2cc8ff; }
</style>
