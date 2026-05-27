import request from '../utils/request'

export interface ConversationItem {
  id: number
  title: string
  round_count: number
  updated_at: string | null
}

export interface MessageItem {
  role: string
  content: string
  created_at: string
}

export function listConversations(): Promise<ConversationItem[]> {
  return request.get('/api/conversations').then(r => r.data)
}

export function getMessages(convId: number): Promise<MessageItem[]> {
  return request.get(`/api/conversations/${convId}/messages`).then(r => r.data)
}

export function removeConversation(convId: number): Promise<void> {
  return request.delete(`/api/conversations/${convId}`)
}
