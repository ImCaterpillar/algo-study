import { api } from './client'

export const executeApi = {
  run: (data) => api.post('/execute', data).then(res => res.data),
}