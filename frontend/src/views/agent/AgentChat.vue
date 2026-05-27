<template>
  <div class="agent-page">
    <!-- 左侧会话列表 -->
    <aside class="sidebar">
      <button class="new-conv-btn" @click="startNewConversation">+ 新对话</button>
      <div class="conv-list">
        <div v-if="conversations.length === 0" class="empty-conv">暂无对话</div>
        <div
          v-for="c in conversations"
          :key="c.id"
          :class="['conv-item', { active: c.id === currentConvId }]"
          @click="switchConversation(c.id)"
        >
          <div class="conv-title">{{ c.title || '新对话' }}</div>
          <div class="conv-meta">{{ c.round_count }} 轮</div>
          <button class="conv-delete" @click.stop="deleteConversation(c.id)" title="删除对话">×</button>
        </div>
      </div>
    </aside>

    <!-- 右侧对话区 -->
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

      <!-- 缩略图预览 -->
      <div v-if="pendingImages.length > 0" class="image-preview-bar">
        <div v-for="(img, i) in pendingImages" :key="i" class="thumbnail-wrap">
          <img :src="img.previewUrl" class="thumbnail" />
          <button class="remove-btn" @click="removeImage(i)" :disabled="loading">x</button>
          <span v-if="img.uploading" class="upload-spinner">上传中...</span>
        </div>
      </div>

      <div class="input-area">
        <button class="upload-btn" :disabled="loading || pendingImages.length >= 3" @click="triggerUpload">
          +
        </button>
        <input
          v-model="input"
          type="text"
          placeholder="输入问题，也可以上传图片..."
          :disabled="loading"
          @keydown.enter="send"
        />
        <button :disabled="loading || (!input.trim() && pendingImages.length === 0)" @click="send">
          {{ loading ? '思考中...' : '发送' }}
        </button>
      </div>

      <div v-if="previewUrl" class="image-overlay" @click="previewUrl = ''">
        <img :src="previewUrl" class="image-preview" @click.stop />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { chatStream, type SSEMessage } from '../../api/agent'
import { uploadImage } from '../../api/upload'
import { listConversations, getMessages, removeConversation, type ConversationItem, type MessageItem } from '../../api/conversations'

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

interface PendingImage {
  previewUrl: string
  url: string
  uploading: boolean
}

const messages = ref<ChatMessage[]>([])
const conversations = ref<ConversationItem[]>([])
const currentConvId = ref<number | null>(null)
const input = ref('')
const loading = ref(false)
const previewUrl = ref('')
const pendingImages = ref<PendingImage[]>([])
let fileInput: HTMLInputElement | null = null
const chatWindow = ref<HTMLElement>()
let controller: AbortController | null = null

onMounted(async () => {
  try {
    conversations.value = await listConversations()
  } catch { /* 忽略 */ }
})

function isImageUrl(url: string): boolean {
  return /\.(png|jpe?g|gif|webp|bmp|svg)(\?.*)?$/i.test(url)
}

function splitPlainUrl(url: string): { cleanUrl: string; suffix: string } {
  const match = url.match(/^(.+?)([，。！？、,.!?]*)$/)
  return {
    cleanUrl: match?.[1] || url,
    suffix: match?.[2] || '',
  }
}

function pushTextPart(parts: ContentPart[], content: string) {
  if (!content) return
  const lastPart = parts[parts.length - 1]
  if (lastPart?.type === 'text') {
    lastPart.content += content
    return
  }
  parts.push({ type: 'text', content })
}

function renderContentParts(msg: ChatMessage): ContentPart[] {
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

function triggerUpload() {
  if (!fileInput) {
    fileInput = document.createElement('input')
    fileInput.type = 'file'
    fileInput.accept = 'image/png,image/jpeg,image/gif,image/webp'
    fileInput.multiple = true
    fileInput.onchange = handleFileChange
  }
  fileInput.click()
}

async function handleFileChange(e: Event) {
  const files = Array.from((e.target as HTMLInputElement).files || [])
  const remaining = 3 - pendingImages.value.length
  if (remaining <= 0) return

  const toUpload = files.slice(0, remaining)
  if (files.length > remaining) {
    alert(`最多上传3张图片，已自动截取前${remaining}张`)
  }

  for (const file of toUpload) {
    if (!['image/png', 'image/jpeg', 'image/gif', 'image/webp'].includes(file.type)) {
      alert(`${file.name} 格式不支持，仅支持 PNG/JPEG/GIF/WebP`)
      continue
    }
    if (file.size > 10 * 1024 * 1024) {
      alert(`${file.name} 超过10MB限制`)
      continue
    }

    const previewUrl = URL.createObjectURL(file)
    pendingImages.value.push({ previewUrl, url: '', uploading: true })
    const idx = pendingImages.value.length - 1

    try {
      const result = await uploadImage(file)
      pendingImages.value[idx].url = result.url
      pendingImages.value[idx].uploading = false
    } catch (err: any) {
      alert(err.message || '上传失败')
      pendingImages.value.splice(idx, 1)
    }
  }

  if (fileInput) fileInput.value = ''
}

function removeImage(i: number) {
  const img = pendingImages.value[i]
  if (img.previewUrl) URL.revokeObjectURL(img.previewUrl)
  pendingImages.value.splice(i, 1)
}

async function scrollBottom() {
  await nextTick()
  requestAnimationFrame(() => {
    if (chatWindow.value) {
      chatWindow.value.scrollTop = chatWindow.value.scrollHeight
    }
  })
}

function startNewConversation() {
  controller?.abort()
  currentConvId.value = null
  messages.value = []
}

async function switchConversation(convId: number) {
  if (convId === currentConvId.value) return
  controller?.abort()
  currentConvId.value = convId
  messages.value = []
  loading.value = false

  try {
    const msgs: MessageItem[] = await getMessages(convId)
    messages.value = msgs.map(m => ({
      role: m.role as 'user' | 'assistant',
      content: m.content,
    }))
    await scrollBottom()
  } catch {
    // ignore
  }
}

async function refreshConversations() {
  try {
    conversations.value = await listConversations()
  } catch { /* ignore */ }
}

async function deleteConversation(convId: number) {
  if (!confirm('确定删除该对话？')) return
  try {
    await removeConversation(convId)
    conversations.value = conversations.value.filter(c => c.id !== convId)
    if (currentConvId.value === convId) {
      currentConvId.value = null
      messages.value = []
    }
  } catch {
    // ignore
  }
}

function send() {
  const text = input.value.trim()
  const hasImages = pendingImages.value.some(img => img.url)
  const hasPending = pendingImages.value.some(img => img.uploading)
  if ((!text && !hasImages) || loading.value) return
  if (hasPending) {
    alert('图片还在上传中，请稍候')
    return
  }

  const images = pendingImages.value.map(img => img.url)
  let content = text || ''
  if (images.length > 0) {
    const imgText = images.map(url => `![图片](${url})`).join('\n')
    content = content ? content + '\n' + imgText : imgText
  }
  messages.value.push({ role: 'user', content })
  input.value = ''

  pendingImages.value.forEach(img => {
    if (img.previewUrl) URL.revokeObjectURL(img.previewUrl)
  })
  pendingImages.value = []
  loading.value = true

  const aiMsgIndex = messages.value.length
  messages.value.push({ role: 'assistant', content: '', streaming: true })

  let pending = ''
  let rafId = 0

  controller = chatStream(
    text,
    images,
    currentConvId.value,
    async (msg: SSEMessage) => {
      switch (msg.type) {
        case 'meta':
          if (msg.conversation_id && !currentConvId.value) {
            currentConvId.value = msg.conversation_id
            refreshConversations()
          }
          break
        case 'intent':
          if (msg.tools && msg.tools.length > 0) {
            messages.value[aiMsgIndex].tools = msg.tools
          }
          break
        case 'content':
          pending += msg.data as string
          if (!rafId) {
            rafId = requestAnimationFrame(() => {
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
      refreshConversations()
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
.agent-page {
  display: flex;
  height: calc(100vh - 120px);
  max-width: 1000px;
  margin: 0 auto;
}

/* ---- sidebar ---- */
.sidebar {
  width: 200px;
  flex-shrink: 0;
  border-right: 1px solid #e8e8e8;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.new-conv-btn {
  margin: 12px;
  padding: 8px 0;
  background: #1677ff;
  color: #fff;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}
.new-conv-btn:hover { background: #4096ff; }
.conv-list {
  flex: 1;
  overflow-y: auto;
}
.empty-conv {
  text-align: center;
  color: #999;
  padding: 24px 12px;
  font-size: 13px;
}
.conv-item {
  padding: 10px 12px;
  cursor: pointer;
  border-bottom: 1px solid #f5f5f5;
  position: relative;
}
.conv-item:hover { background: #f5f5f5; }
.conv-item.active { background: #e6f4ff; }
.conv-delete {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  width: 20px;
  height: 20px;
  border: none;
  border-radius: 50%;
  background: transparent;
  color: #c0c0c0;
  font-size: 16px;
  line-height: 20px;
  cursor: pointer;
  display: none;
  padding: 0;
}
.conv-item:hover .conv-delete { display: block; }
.conv-delete:hover {
  background: #ff4d4f;
  color: #fff;
}
.conv-title {
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.conv-meta {
  font-size: 11px;
  color: #999;
  margin-top: 2px;
}

/* ---- chat ---- */
.agent-chat {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  padding-left: 16px;
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

.image-preview-bar {
  display: flex;
  gap: 8px;
  padding: 8px 0;
  flex-wrap: wrap;
}
.thumbnail-wrap {
  position: relative;
  width: 72px;
  height: 72px;
  border-radius: 6px;
  overflow: hidden;
  border: 1px solid #e8e8e8;
}
.thumbnail {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.remove-btn {
  position: absolute;
  top: 2px;
  right: 2px;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  border: none;
  background: rgba(0,0,0,0.5);
  color: #fff;
  font-size: 11px;
  cursor: pointer;
  line-height: 18px;
  padding: 0;
}
.upload-spinner {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0,0,0,0.4);
  color: #fff;
  font-size: 11px;
}
.upload-btn {
  width: 36px;
  height: 36px;
  border: 1px dashed #d9d9d9;
  border-radius: 6px;
  background: #fafafa;
  font-size: 20px;
  cursor: pointer;
  color: #999;
  flex-shrink: 0;
}
.upload-btn:hover { border-color: #1677ff; color: #1677ff; }
.upload-btn:disabled { opacity: 0.4; cursor: not-allowed; }
</style>
