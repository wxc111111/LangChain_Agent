const BASE_URL = 'http://localhost:8002'

export interface SSEMessage {
  type: 'intent' | 'tool_results' | 'content' | 'error'
  tools?: string[]
  reply?: string
  data?: any
}

export function chatStream(
  message: string,
  onMessage: (msg: SSEMessage) => Promise<void>,
  onDone: () => void,
  onError: (err: string) => void,
): AbortController {
  const controller = new AbortController()
  const token = localStorage.getItem('access_token')

  fetch(`${BASE_URL}/api/agent/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ message }),
    signal: controller.signal,
  })
    .then(async (response) => {
      if (response.status === 401) {
        onError('登录已过期，请重新登录')
        return
      }
      if (!response.ok) {
        onError(`请求失败: ${response.status}`)
        return
      }

      const reader = response.body!.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })

        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6)
            if (data === '[DONE]') {
              onDone()
              return
            }
            try {
              await onMessage(JSON.parse(data))
            } catch {
              // skip
            }
          }
        }
      }
      onDone()
    })
    .catch((err) => {
      if (err.name !== 'AbortError') {
        onError(err.message || '网络错误')
      }
    })

  return controller
}
