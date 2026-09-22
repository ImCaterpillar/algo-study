import { api } from './client'

export const sandboxApi = {
  execute: (data) => api.post('/sandbox/execute', data).then(res => res.data),
}