import { api } from './client'

export const problemApi = {
  list: (params = {}) => api.get('/problems', { params }).then(res => res.data),
  detail: (id) => api.get(`/problems/${id}`).then(res => res.data),
  updateProgress: (id, payload) => api.patch(`/problems/${id}/progress`, payload).then(res => res.data),
}
