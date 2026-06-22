<template>
  <div class="chat-page">
    <!-- 顶部栏 -->
    <div class="chat-header">
      <div class="header-left">
        <div class="avatar">🏥</div>
        <div>
          <div class="org-name">{{ orgName }}</div>
          <div class="status-dot">
            <span class="dot"></span> AI 客服在线
          </div>
        </div>
      </div>
      <el-button size="small" @click="goAppointment" style="border-color: #1D9E75; color: #1D9E75">
        立即预约
      </el-button>
    </div>

    <!-- 消息区 -->
    <div class="message-area" ref="messageArea">
      <!-- 欢迎消息 -->
      <div class="msg-row ai">
        <div class="bubble ai-bubble">
          您好！我是 {{ orgName }} 的 AI 客服，有什么可以帮您的吗？<br/>
          <span style="font-size: 12px; color: #9FE1CB">您可以问我：科室介绍、就诊流程、价格收费等问题</span>
        </div>
      </div>

      <!-- 对话消息 -->
      <div
        v-for="msg in messages"
        :key="msg.id"
        class="msg-row"
        :class="msg.role === 'user' ? 'user' : 'ai'"
      >
        <div class="bubble" :class="msg.role === 'user' ? 'user-bubble' : 'ai-bubble'">
          <span v-if="msg.role === 'assistant' && msg.streaming" class="streaming-text">
            {{ filterThink(msg.content) }}<span class="cursor">|</span>
          </span>
          <span v-else>{{ filterThink(msg.content) }}</span>
        </div>
      </div>

      <!-- AI 思考中 -->
      <div v-if="thinking" class="msg-row ai">
        <div class="bubble ai-bubble thinking">
          <span class="dot-flashing"></span>
        </div>
      </div>
    </div>

    <!-- 输入区 -->
    <div class="input-area">
      <div class="quick-questions">
        <span
          v-for="q in quickQuestions"
          :key="q"
          class="quick-tag"
          @click="sendQuestion(q)"
        >{{ q }}</span>
      </div>
      <div class="input-row">
        <el-input
          v-model="inputText"
          placeholder="请输入您的问题..."
          :disabled="isStreaming"
          @keyup.enter="sendMessage"
          size="large"
        />
        <el-button
          type="primary"
          size="large"
          :loading="isStreaming"
          :disabled="!inputText.trim()"
          @click="sendMessage"
          style="background: #1D9E75; border-color: #1D9E75; margin-left: 8px"
        >
          发送
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

// 从 URL 参数获取机构 slug，如 /chat?org=beijing-smile
const orgSlug = (route.query.org as string) || 'demo'
const orgName = ref('医云问诊所')
const messageArea = ref<HTMLElement>()
const inputText = ref('')
const isStreaming = ref(false)
const thinking = ref(false)

// 生成唯一 session_id（患者身份标识）
const sessionId = localStorage.getItem('session_id') || (() => {
  const id = 'session_' + Date.now() + '_' + Math.random().toString(36).slice(2)
  localStorage.setItem('session_id', id)
  return id
})()

// 多轮对话的 dify_conversation_id
let difyConversationId: string | null = null

interface Message {
  id: number
  role: 'user' | 'assistant'
  content: string
  streaming?: boolean
}

const messages = ref<Message[]>([])

// 快捷问题
const quickQuestions = [
  '洗牙多少钱？',
  '如何预约挂号？',
  '体检需要空腹吗？',
  '营业时间是几点？',
]

function filterThink(content: string): string {
  // 先去掉完整的 <think>...</think> 块
  let result = content.replace(/<think>[\s\S]*?<\/think>/g, '')
  // 再去掉还没关闭的 <think>...（流式未结束时）
  result = result.replace(/<think>[\s\S]*/g, '')
  return result.trim()
}

function goAppointment() {
  router.push(`/patient/appointment?org=${orgSlug}`)
}

async function sendQuestion(q: string) {
  inputText.value = q
  await sendMessage()
}

async function sendMessage() {
  const text = inputText.value.trim()
  if (!text || isStreaming.value) return

  // 1. 把用户消息加入列表
  messages.value.push({ id: Date.now(), role: 'user', content: text })
  inputText.value = ''
  scrollToBottom()

  // 2. 显示"思考中"
  thinking.value = true
  isStreaming.value = true

  // 3. 准备 AI 消息占位
  const aiMsg: Message = { id: Date.now() + 1, role: 'assistant', content: '', streaming: true }

  try {
    const response = await fetch('http://localhost:8000/api/v1/chat/messages', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        session_id: sessionId,
        org_slug: orgSlug,
        question: text,
        conversation_id: difyConversationId,
      }),
    })

    if (!response.ok) throw new Error('请求失败')

    thinking.value = false
    messages.value.push(aiMsg)
    scrollToBottom()

    // 4. 读取 SSE 流
    const reader = response.body!.getReader()
    const decoder = new TextDecoder()

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      const chunk = decoder.decode(value)
      const lines = chunk.split('\n').filter(l => l.startsWith('data: '))

      for (const line of lines) {
        try {
          const data = JSON.parse(line.replace('data: ', ''))

          if (data.event === 'message') {
            // 过滤 <think> 标签
            const filtered = (data.answer || '').replace(/<think>[\s\S]*?<\/think>/g, '')
            aiMsg.content += filtered
            scrollToBottom()
          }

          if (data.event === 'message_end') {
            // 保存 dify_conversation_id 用于下一轮
            difyConversationId = data.conversation_id || difyConversationId
            aiMsg.streaming = false
          }
        } catch { /* 忽略解析错误 */ }
      }
    }

  } catch (err) {
    thinking.value = false
    messages.value.push({
      id: Date.now() + 1,
      role: 'assistant',
      content: '抱歉，服务暂时无法响应，请稍后再试或联系人工客服。',
    })
  } finally {
    isStreaming.value = false
    if (aiMsg.streaming) aiMsg.streaming = false
    scrollToBottom()
  }
}

function scrollToBottom() {
  nextTick(() => {
    if (messageArea.value) {
      messageArea.value.scrollTop = messageArea.value.scrollHeight
    }
  })
}

onMounted(() => {
  // 可以根据 orgSlug 从后端获取机构名
  if (orgSlug !== 'demo') {
    fetch(`http://localhost:8000/api/v1/public/orgs/${orgSlug}`)
      .then(r => r.json())
      .then(d => { if (d.name) orgName.value = d.name })
      .catch(() => {})
  }
})
</script>

<style scoped>
.chat-page {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f0faf5;
  max-width: 750px;
  margin: 0 auto;
}

.chat-header {
  background: #fff;
  padding: 12px 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 0.5px solid #c8e6d4;
  box-shadow: 0 1px 4px rgba(0,0,0,0.05);
}

.header-left { display: flex; align-items: center; gap: 12px; }

.avatar {
  width: 40px;
  height: 40px;
  background: #e1f5ee;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
}

.org-name { font-size: 15px; font-weight: 500; color: #1e293b; }

.status-dot {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  color: #1D9E75;
  margin-top: 2px;
}

.dot {
  width: 6px;
  height: 6px;
  background: #1D9E75;
  border-radius: 50%;
  display: inline-block;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

.message-area {
  flex: 1;
  overflow-y: auto;
  padding: 20px 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.msg-row {
  display: flex;
}

.msg-row.user { justify-content: flex-end; }
.msg-row.ai { justify-content: flex-start; }

.bubble {
  max-width: 70%;
  padding: 10px 14px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.7;
  word-break: break-word;
}

.user-bubble {
  background: #1D9E75;
  color: #fff;
  border-bottom-right-radius: 4px;
}

.ai-bubble {
  background: #fff;
  color: #1e293b;
  border: 0.5px solid #c8e6d4;
  border-bottom-left-radius: 4px;
}

.thinking {
  padding: 14px 20px;
}

.cursor {
  animation: blink 1s infinite;
  color: #1D9E75;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

.dot-flashing {
  width: 8px;
  height: 8px;
  background: #9FE1CB;
  border-radius: 50%;
  display: inline-block;
  animation: dotFlash 1s infinite alternate;
}

@keyframes dotFlash {
  0% { opacity: 0.2; }
  100% { opacity: 1; }
}

.input-area {
  background: #fff;
  border-top: 0.5px solid #c8e6d4;
  padding: 12px 16px;
}

.quick-questions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 10px;
}

.quick-tag {
  font-size: 12px;
  padding: 4px 12px;
  background: #e1f5ee;
  color: #0f6e56;
  border-radius: 20px;
  cursor: pointer;
  border: 0.5px solid #9FE1CB;
  transition: background 0.2s;
}

.quick-tag:hover { background: #c8e6d4; }

.input-row {
  display: flex;
  align-items: center;
}
</style>