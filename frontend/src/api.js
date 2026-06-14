const API_BASE = '/api'

async function parseJsonResponse(response) {
  const text = await response.text()
  if (!text) {
    if (!response.ok) {
      throw new Error(`服务异常 (${response.status})，请确认后端已启动`)
    }
    return {}
  }
  try {
    return JSON.parse(text)
  } catch {
    throw new Error('服务返回异常，请确认后端已启动')
  }
}

export async function analyzeVideo(url) {
  const response = await fetch(`${API_BASE}/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url }),
  })
  const body = await parseJsonResponse(response)
  if (!response.ok) {
    throw new Error(body.detail || '解析失败')
  }
  return body
}

export async function startDownload(url, formatId) {
  const response = await fetch(`${API_BASE}/download`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url, format_id: formatId }),
  })
  const body = await parseJsonResponse(response)
  if (!response.ok) {
    throw new Error(body.detail || '下载失败')
  }
  return body.task_id
}

export async function getTaskStatus(taskId) {
  const response = await fetch(`${API_BASE}/tasks/${taskId}`)
  const body = await parseJsonResponse(response)
  if (!response.ok) {
    throw new Error(body.detail || '查询失败')
  }
  return body
}

export function getTaskFileUrl(taskId) {
  return `${API_BASE}/tasks/${taskId}/file`
}

export async function downloadTaskFile(taskId, filename = 'video.mp4') {
  const response = await fetch(getTaskFileUrl(taskId))
  if (!response.ok) {
    const body = await parseJsonResponse(response)
    throw new Error(body.detail || `下载文件失败 (${response.status})`)
  }

  const blob = await response.blob()
  const objectUrl = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = objectUrl
  link.download = filename
  link.click()
  URL.revokeObjectURL(objectUrl)
}

export function formatDuration(seconds) {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${String(secs).padStart(2, '0')}`
}
