const BASE_URL = 'http://localhost:8002'

export interface UploadResult {
  id: number
  url: string
  filename: string
  size: number
}

export async function uploadImage(file: File): Promise<UploadResult> {
  const form = new FormData()
  form.append('file', file)
  const token = localStorage.getItem('access_token')

  const resp = await fetch(`${BASE_URL}/api/upload`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: form,
  })

  if (resp.status === 401) {
    throw new Error('登录已过期，请重新登录')
  }
  if (!resp.ok) {
    const detail = await resp.json().catch(() => ({ detail: '上传失败' }))
    throw new Error(detail.detail || '上传失败')
  }
  return resp.json()
}
