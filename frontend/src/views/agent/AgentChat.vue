<template>
  <div class="agent-chat">
    <div class="chat-window" ref="chatWindow">
      <div v-if="messages.length === 0" class="empty-hint">
        <p>我是 AI 智能助手，可以帮你：</p>
        <ul>
          <li>查询天气和穿衣建议</li>
          <li>生成图片 / 识别图片内容</li>
          <li>查询工单和任务</li>
        </ul>
      </div>

      <div v-for="(msg, i) in messages" :key="i" :class="['message', msg.role]">
        <div class="avatar">{{ msg.role === 'user' ? '我' : 'AI' }}</div>
        <div class="bubble">
          <div v-if="msg.tools" class="tool-tag">
            已调用: {{ msg.tools.join(', ') }}
          </div>
          <div class="text">
            <template v-for="(part, partIndex) in renderContentParts(msg)" :key="partIndex">
              <span v-if="part.type === 'text'">{{ part.content }}</span>
              <a
                v-else-if="part.type === 'link'"
                :href="part.url"
                target="_blank"
                rel="noopener"
              >
                {{ part.label }}
              </a>
              <img
                v-else
                class="chat-image"
                :src="part.url"
                :alt="part.alt || '聊天图片'"
                @click="previewUrl = part.url"
              />
            </template>
          </div>
          <span v-if="msg.streaming" class="cursor">|</span>
        </div>
      </div>
    </div>

    <div class="input-area">
      <input
        v-model="input"
        type="text"
        placeholder="输入问题，例如：北京今天天气怎么样？"
        :disabled="loading"
        @keydown.enter="send"
      />
      <button :disabled="loading || !input.trim()" @click="send">
        {{ loading ? '思考中...' : '发送' }}
      </button>
    </div>

    <div v-if="previewUrl" class="image-overlay" @click="previewUrl = ''">
      <img :src="previewUrl" class="image-preview" @click.stop />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onBeforeUnmount } from 'vue'
import { chatStream, type SSEMessage } from '../../api/agent'

interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  tools?: string[]
  streaming?: boolean
}

type ContentPart =
  | { type: 'text'; content: string }
  | { type: 'link'; label: string; url: string }
  | { type: 'image'; alt: string; url: string }

const messages = ref<ChatMessage[]>([])
const input = ref('')
const loading = ref(false)
const previewUrl = ref('')
const chatWindow = ref<HTMLElement>()
let controller: AbortController | null = null

function isImageUrl(url: string): boolean {
  // 判断链接是否为常见图片地址，匹配后只渲染图片，不再把完整地址作为文字输出
  return /\.(png|jpe?g|gif|webp|bmp|svg)(\?.*)?$/i.test(url)
}

function splitPlainUrl(url: string): { cleanUrl: string; suffix: string } {
  // 分离纯链接末尾的中文或英文标点，避免标点影响图片链接识别
  const match = url.match(/^(.+?)([，。！？、,.!?]*)$/)
  return {
    cleanUrl: match?.[1] || url,
    suffix: match?.[2] || '',
  }
}

function pushTextPart(parts: ContentPart[], content: string) {
  // 合并连续文本片段，避免流式内容频繁刷新时生成过多 DOM 节点
  if (!content) return
  const lastPart = parts[parts.length - 1]
  if (lastPart?.type === 'text') {
    lastPart.content += content
    return
  }
  parts.push({ type: 'text', content })
}

function renderContentParts(msg: ChatMessage): ContentPart[] {
  // 将消息内容拆成文本、链接、图片，图片只展示加载态和预览，不展示完整 URL
  const content = msg.content || '...'
  const parts: ContentPart[] = []
  const tokenPattern = /!\[([^\]]*)\]\(([^)]+)\)|\[([^\]]+)\]\(([^)]+)\)|(https?:\/\/\S+)/g
  let lastIndex = 0
  let match: RegExpExecArray | null

  while ((match = tokenPattern.exec(content)) !== null) {
    pushTextPart(parts, content.slice(lastIndex, match.index))

    const markdownImageAlt = match[1]
    const markdownImageUrl = match[2]
    const markdownLinkLabel = match[3]
    const markdownLinkUrl = match[4]
    const plainUrl = match[5]

    if (markdownImageUrl) {
      parts.push({ type: 'image', alt: markdownImageAlt, url: markdownImageUrl })
    } else if (markdownLinkUrl && isImageUrl(markdownLinkUrl)) {
      parts.push({ type: 'image', alt: markdownLinkLabel, url: markdownLinkUrl })
    } else if (markdownLinkUrl) {
      parts.push({ type: 'link', label: markdownLinkLabel, url: markdownLinkUrl })
    } else if (plainUrl) {
      const { cleanUrl, suffix } = splitPlainUrl(plainUrl)
      if (isImageUrl(cleanUrl)) {
        parts.push({ type: 'image', alt: '', url: cleanUrl })
      } else {
        parts.push({ type: 'link', label: cleanUrl, url: cleanUrl })
      }
      pushTextPart(parts, suffix)
    }

    lastIndex = tokenPattern.lastIndex
  }

  pushTextPart(parts, content.slice(lastIndex))
  return parts
}

async function scrollBottom() {
  // 等 Vue 完成 DOM 更新后，再等浏览器完成布局计算，确保能滚动到最新高度
  await nextTick()
  requestAnimationFrame(() => {
    if (chatWindow.value) {
      chatWindow.value.scrollTop = chatWindow.value.scrollHeight
    }
  })
}

function send() {
  const text = input.value.trim()
  if (!text || loading.value) return

  messages.value.push({ role: 'user', content: text })
  input.value = ''
  loading.value = true

  const aiMsgIndex = messages.value.length
  messages.value.push({ role: 'assistant', content: '', streaming: true })

  let pending = ''
  let rafId = 0

  controller = chatStream(
    text,
    async (msg: SSEMessage) => {
      switch (msg.type) {
        case 'intent':
          if (msg.tools && msg.tools.length > 0) {
            messages.value[aiMsgIndex].tools = msg.tools
          }
          break
        case 'content':
          pending += msg.data as string
          if (!rafId) {
            rafId = requestAnimationFrame(() => {
              // 通过响应式数组里的消息对象更新内容，保证每个流式分片都能触发界面刷新
              messages.value[aiMsgIndex].content += pending
              pending = ''
              rafId = 0
              scrollBottom()
            })
          }
          break
        case 'error':
          messages.value[aiMsgIndex].content = msg.data as string
          messages.value[aiMsgIndex].streaming = false
          break
      }
    },
    () => {
      if (rafId) cancelAnimationFrame(rafId)
      messages.value[aiMsgIndex].content += pending
      pending = ''
      messages.value[aiMsgIndex].streaming = false
      loading.value = false
      scrollBottom()
    },
    (err: string) => {
      if (rafId) cancelAnimationFrame(rafId)
      messages.value[aiMsgIndex].content = err
      messages.value[aiMsgIndex].streaming = false
      loading.value = false
    },
  )
}

onBeforeUnmount(() => {
  controller?.abort()
})
</script>

<style scoped>
.agent-chat {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 120px);
  max-width: 800px;
  margin: 0 auto;
}

.chat-window {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 16px 0;
}

.empty-hint {
  text-align: center;
  color: #999;
  margin-top: 80px;
}
.empty-hint ul {
  display: inline-block;
  text-align: left;
  margin-top: 12px;
  line-height: 2;
}

.message {
  display: flex;
  gap: 10px;
  margin-bottom: 16px;
}
.message.user {
  flex-direction: row-reverse;
}

.avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: bold;
  flex-shrink: 0;
}
.message.user .avatar {
  background: #1677ff;
  color: #fff;
}
.message.assistant .avatar {
  background: #52c41a;
  color: #fff;
}

.bubble {
  max-width: 75%;
  padding: 10px 14px;
  border-radius: 8px;
  line-height: 1.7;
}
.message.user .bubble {
  background: #1677ff;
  color: #fff;
}
.message.assistant .bubble {
  background: #fff;
  box-shadow: 0 1px 4px rgba(0,0,0,0.08);
}

.tool-tag {
  font-size: 12px;
  color: #999;
  margin-bottom: 4px;
  border-bottom: 1px solid #f0f0f0;
  padding-bottom: 4px;
}

.text {
  white-space: pre-wrap;
  word-break: break-word;
}
.text a {
  color: #1677ff;
}
.chat-image {
  display: block;
  max-width: min(100%, 360px);
  margin: 8px 0;
  border-radius: 8px;
  cursor: pointer;
}

.image-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}
.image-preview {
  max-width: 90vw;
  max-height: 90vh;
  border-radius: 8px;
}

.cursor {
  animation: blink 0.8s infinite;
  color: #1677ff;
}
@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

.input-area {
  display: flex;
  gap: 10px;
  padding: 12px 0;
  border-top: 1px solid #e8e8e8;
}
.input-area input {
  flex: 1;
  padding: 10px 14px;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  font-size: 14px;
  outline: none;
}
.input-area input:focus {
  border-color: #1677ff;
}
.input-area button {
  padding: 10px 24px;
  background: #1677ff;
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
}
.input-area button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
