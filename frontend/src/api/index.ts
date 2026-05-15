"""前端 API 封装 — 角色、世界书、预设、聊天、备份"""

import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

api.interceptors.response.use(
  (res) => res,
  (err) => {
    console.error('API Error:', err.message)
    return Promise.reject(err)
  },
)

export default api

// ─── 角色 CRUD ───────────────────────

export const charactersApi = {
  list: () => api.get('/characters'),
  get: (id: string) => api.get(`/characters/${id}`),
  create: (data: any) => api.post('/characters', data),
  update: (id: string, data: any) => api.put(`/characters/${id}`, data),
  delete: (id: string) => api.delete(`/characters/${id}`),
  import: (file: File) => {
    const form = new FormData()
    form.append('file', file)
    return api.post('/characters/import', form)
  },
}

// ─── 世界书 CRUD ─────────────────────

export const worldbooksApi = {
  list: () => api.get('/worldbooks'),
  get: (id: string) => api.get(`/worldbooks/${id}`),
  create: (data: any) => api.post('/worldbooks', data),
  update: (id: string, data: any) => api.put(`/worldbooks/${id}`, data),
  delete: (id: string) => api.delete(`/worldbooks/${id}`),
}

// ─── 预设 CRUD ───────────────────────

export const presetsApi = {
  list: () => api.get('/presets'),
  get: (id: string) => api.get(`/presets/${id}`),
  create: (data: any) => api.post('/presets', data),
  update: (id: string, data: any) => api.put(`/presets/${id}`, data),
  delete: (id: string) => api.delete(`/presets/${id}`),
}

// ─── 聊天 ─────────────────────────────

export const chatApi = {
  send: (data: { message: string; character_name?: string; history?: any[] }) =>
    api.post('/chat/send', data),
}

// ─── 备份 ─────────────────────────────

export const backupApi = {
  export: () => api.get('/backup/export', { responseType: 'blob' }),
  import: (file: File) => {
    const form = new FormData()
    form.append('file', file)
    return api.post('/backup/import', form)
  },
}

// ─── 仪表盘 ───────────────────────────

export const dashboardApi = {
  stats: () => api.get('/characters').then(r => ({
    characters: r.data.length,
    active: r.data.filter((c: any) => c.is_active).length,
  })),
}

// ─── 模型配置 ─────────────────────────

export const modelsApi = {
  list: () => api.get('/models'),
  save: (data: any) => api.post('/models', data),
  update: (id: string, data: any) => api.put(`/models/${id}`, data),
}
